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


def find_in_feed(feed, hint, query):
    """Match by guid, then title, then the link's slug; else needs_episode."""
    if hint.guid:
        for episode in feed.episodes:
            if episode.guid == hint.guid:
                return episode
    return episode_match.recent_or_match(feed.episodes, query or hint.title or hint.slug)


def fetch_from_hint(context, hint, url):
    """Try each candidate feed until one contains the episode.

    With no known title (an Apple show link) or with --episode, the user is
    choosing from one feed, so its errors, including the candidate list, go
    straight back. With a known title, a feed that fails or lacks the episode
    is skipped: it may be a different show with a similar name.
    """
    for feed_url in hint.feed_urls:
        try:
            feed = podcast_feeds.fetch_feed(feed_url)
            episode = find_in_feed(feed, hint, context.args.episode)
        except CastError:
            if not hint.title or context.args.episode:
                raise
            continue
        return transcribe_episode(context, feed, episode, url)

    if hint.audio_url:  # Apple still knows where the audio is
        source_id = "podcast:" + short_hash(hint.guid or hint.audio_url)
        reused = context.reuse(source_id)
        if reused:
            return reused
        metadata = {"id": source_id, "kind": "podcast", "title": hint.title, "url": url,
                    "extra": {"feed_url": hint.feed_urls[0], "not_in_feed": True}}
        return download_and_transcribe(context, metadata, hint.audio_url, hint.title)
    raise CastError(NO_PUBLIC_FEED, f"\"{hint.title}\" is not in any public feed found.",
                    podcast_lookup.SPOTIFY_ONLY_HINT)


def fetch_apple(source, context):
    return fetch_from_hint(context, podcast_lookup.resolve_apple(source.value), source.value)


def fetch_spotify(source, context):
    """Never downloads from Spotify: the episode comes from the show's public RSS feed."""
    return fetch_from_hint(context, podcast_lookup.resolve_spotify(source.value), source.value)


def fetch_feed_url(source, context):
    feed = podcast_feeds.fetch_feed(source.value)
    episode = episode_match.recent_or_match(feed.episodes, context.args.episode)
    return transcribe_episode(context, feed, episode, episode.link or source.value)


def fetch_audio_url(source, context):
    source_id = "url:" + short_hash(source.value)
    reused = context.reuse(source_id)
    if reused:
        return reused
    title = os.path.splitext(os.path.basename(unquote(urlparse(source.value).path)))[0] or "audio"
    metadata = {"id": source_id, "kind": "audio", "title": title, "url": source.value}
    return download_and_transcribe(context, metadata, source.value, title)
