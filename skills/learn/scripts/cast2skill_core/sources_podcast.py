"""Podcast routes: Apple link, Spotify link, RSS feed URL, direct audio URL.

All of them end the same way: one episode's audio URL is downloaded into the
library folder, transcribed locally, and deleted unless keep_audio is set.
"""

import os
from urllib.parse import unquote, urlparse

from . import episode_match, http_client, language, podcast_feeds, podcast_lookup
from .errors import NO_PUBLIC_FEED, CastError
from .fetch_context import audio_duration_s, progress
from .sources_local import short_hash

KNOWN_AUDIO_EXTENSIONS = (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".mp4")


def audio_extension(url):
    extension = os.path.splitext(urlparse(url).path)[1].lower()
    return extension if extension in KNOWN_AUDIO_EXTENSIONS else ".mp3"


def download_and_transcribe(context, metadata, audio_url, title_for_language, source_language=None):
    lang, how = language.require(context.args.lang, source_language, title_for_language,
                                 context.config.get("default_lang"))
    folder = context.new_folder(metadata["title"])
    progress(f"Downloading {audio_url} ...")
    audio_path = http_client.download(audio_url, os.path.join(folder, "audio" + audio_extension(audio_url)))
    if not metadata.get("duration_s"):
        metadata["duration_s"] = audio_duration_s(audio_path)
    metadata.update(language=lang, language_reason=how, transcript_source="local_whisper")
    metadata["has_speakers"] = context.transcribe_audio(folder, audio_path, lang, delete_audio=True)
    return context.save_result(folder, metadata)


def episode_id(feed_episode):
    return "podcast:" + short_hash(feed_episode.guid or feed_episode.audio_url)


def transcribe_episode(context, feed, episode, url):
    source_id = episode_id(episode)
    reused = context.reuse(source_id)
    if reused:
        return reused
    metadata = {"id": source_id, "kind": "podcast", "title": episode.title,
                "author": feed.author or feed.title, "url": url,
                "duration_s": episode.duration_s,
                "extra": {"feed_url": feed.url, "show": feed.title, "published": episode.published}}
    return download_and_transcribe(context, metadata, episode.audio_url, episode.title, feed.language)


def episode_from_user(context, episodes):
    """--episode-id (exact) or --episode (spec matching, warned when fuzzy), else None."""
    args = context.args
    if getattr(args, "episode_id", None):
        return episode_match.by_key(episodes, args.episode_id)
    if args.episode:
        episode = episode_match.match(episodes, args.episode)
        if episode_match.normalize_title(episode.title) != episode_match.normalize_title(args.episode):
            context.warnings.append("episode_fuzzy_match")
        return episode
    return None


def episode_from_link(feed, hint):
    """What the link itself identifies: guid, exact title, or a unique slug prefix. Never fuzzy."""
    if hint.guid:
        found = next((episode for episode in feed.episodes if episode.guid == hint.guid), None)
        if found:
            return found
    if hint.title:
        return episode_match.exact(feed.episodes, hint.title)
    if hint.slug:
        return episode_match.by_prefix(feed.episodes, hint.slug)
    return None


def links_to_episode(hint):
    return bool(hint.title or hint.slug or hint.guid)


def user_is_choosing(context, hint):
    """The user named an episode (--episode, --episode-id), or the link names none (a show link)."""
    named = context.args.episode or getattr(context.args, "episode_id", None)
    return bool(named) or not links_to_episode(hint)


def episode_in(feed, context, hint):
    """The wanted episode in this feed, or None. A show link with nothing named raises the list."""
    if user_is_choosing(context, hint):
        episode = episode_from_user(context, feed.episodes)
        if episode is None and not links_to_episode(hint):
            episode_match.recent_or_match(feed.episodes, None)
        return episode
    return episode_from_link(feed, hint)


def fetch_from_hint(context, hint, url):
    """Try each candidate feed until one holds the episode.

    A title from a link is matched exactly: adjacent episodes ("#412" and
    "#413") score above 0.8, so a fuzzy hit is offered to the user, never
    picked. Feeds that fail or lack the episode are skipped (a different show
    with a similar name), except that a single feed's errors go straight back
    when the user is choosing from it.
    """
    near, wanted = [], hint.title or hint.slug
    for feed_url in hint.feed_urls:
        try:
            feed = podcast_feeds.fetch_feed(feed_url)
            episode = episode_in(feed, context, hint)
        except CastError:
            if user_is_choosing(context, hint) and len(hint.feed_urls) == 1:
                raise
            continue
        if episode:
            return transcribe_episode(context, feed, episode, url)
        if wanted:
            near += episode_match.near_misses(feed.episodes, wanted)

    if hint.audio_url and not user_is_choosing(context, hint):  # Apple knows this exact episode's audio
        return transcribe_apple_audio(context, hint, url)
    if near:
        episode_match.ask_user(f"No episode is titled exactly \"{wanted}\". Closest:", near[:3])
    raise CastError(NO_PUBLIC_FEED, f"\"{wanted or 'This episode'}\" is not in any public feed found.",
                    podcast_lookup.SPOTIFY_ONLY_HINT)


def transcribe_apple_audio(context, hint, url):
    source_id = "podcast:" + short_hash(hint.guid or hint.audio_url)
    reused = context.reuse(source_id)
    if reused:
        return reused
    metadata = {"id": source_id, "kind": "podcast", "title": hint.title, "url": url,
                "extra": {"feed_url": hint.feed_urls[0], "not_in_feed": True}}
    return download_and_transcribe(context, metadata, hint.audio_url, hint.title)


def fetch_apple(source, context):
    return fetch_from_hint(context, podcast_lookup.resolve_apple(source.value), source.value)


def fetch_spotify(source, context):
    """Never downloads from Spotify: the episode comes from the show's public RSS feed."""
    return fetch_from_hint(context, podcast_lookup.resolve_spotify(source.value), source.value)


def fetch_feed_url(source, context):
    feed = podcast_feeds.fetch_feed(source.value)
    episode = episode_from_user(context, feed.episodes)
    if episode is None:
        if getattr(context.args, "episode_id", None):
            raise CastError(NO_PUBLIC_FEED, "That episode_id is not in this feed.", "Run without --episode-id to list episodes.")
        episode_match.recent_or_match(feed.episodes, None)  # raises with the recent list
    return transcribe_episode(context, feed, episode, episode.link or source.value)


def fetch_audio_url(source, context):
    source_id = "url:" + short_hash(source.value)
    reused = context.reuse(source_id)
    if reused:
        return reused
    title = os.path.splitext(os.path.basename(unquote(urlparse(source.value).path)))[0] or "audio"
    metadata = {"id": source_id, "kind": "audio", "title": title, "url": source.value}
    return download_and_transcribe(context, metadata, source.value, title)
