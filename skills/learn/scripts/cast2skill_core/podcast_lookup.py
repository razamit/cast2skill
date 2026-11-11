"""Resolving Apple Podcasts and Spotify links to a public RSS feed and an episode.

Endpoints, checked against the live services on 2026-11-11:

- iTunes Lookup `itunes.apple.com/lookup?id=<show>&entity=podcastEpisode`
  returns the show's feedUrl and its 200 most recent episodes (trackId, title,
  guid, audio URL). Looking up an episode id alone returns nothing.
- Spotify oEmbed `open.spotify.com/oembed?url=<episode>` returns the episode
  title only. The show name is in the episode page's og:description
  ("<Show> · Episode").
- iTunes Search `itunes.apple.com/search?entity=podcastEpisode|podcast`
  finds episodes and shows by name, with their feedUrl.

Nothing is ever downloaded from Spotify itself; only its public metadata is read.
"""

import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, quote, urlencode, urlparse

from . import http_client
from .episode_match import MIN_RATIO, ratio
from .errors import BAD_ARGUMENTS, LOOKUP_FAILED, NO_PUBLIC_FEED, CastError

LOOKUP_HINT = "Pass the show's RSS feed URL or an audio file instead."
SPOTIFY_ONLY_HINT = "This episode looks Spotify-only. Give me a YouTube link or an audio file instead."


@dataclass
class EpisodeHint:
    """What a link tells us about the episode before the feed is read."""

    feed_urls: list  # candidate feeds, best first
    title: str = ""
    guid: str = ""
    audio_url: str = ""  # Apple's own copy of the enclosure URL, a fallback
    slug: str = ""  # title-like text from the link itself


def itunes(path, **params):
    return http_client.get_json(f"https://itunes.apple.com/{path}?{urlencode(params)}",
                                LOOKUP_FAILED, LOOKUP_HINT).get("results", [])


# --------------------------------------------------------------------------
# Apple Podcasts
# --------------------------------------------------------------------------

def parse_apple_url(url):
    """(show id, episode id or None, path slug) from a podcasts.apple.com link."""
    parsed = urlparse(url)
    show = re.search(r"/id(\d+)", parsed.path)
    if not show:
        raise CastError(BAD_ARGUMENTS, "That Apple Podcasts link has no show id.",
                        "Copy the episode link from the Apple Podcasts app or website.")
    episode = (parse_qs(parsed.query).get("i") or [None])[0]
    parts = [part for part in parsed.path.split("/") if part]
    slug = parts[parts.index("podcast") + 1] if "podcast" in parts and len(parts) > parts.index("podcast") + 2 else ""
    return show.group(1), episode, slug.replace("-", " ")


def resolve_apple(url):
    show_id, episode_id, slug = parse_apple_url(url)
    results = itunes("lookup", id=show_id, entity="podcastEpisode", limit=200)
    show = next((item for item in results if item.get("kind") == "podcast"), None)
    if not show or not show.get("feedUrl"):
        raise CastError(NO_PUBLIC_FEED, "Apple lists no public RSS feed for this show.",
                        "Give me a YouTube link or an audio file instead.")
    hint = EpisodeHint(feed_urls=[show["feedUrl"]], slug=slug if episode_id else "")
    for item in results:
        if episode_id and str(item.get("trackId")) == episode_id:
            hint.title = item.get("trackName", "")
            hint.guid = item.get("episodeGuid", "")
            hint.audio_url = item.get("episodeUrl", "")
    return hint


# --------------------------------------------------------------------------
# Spotify (metadata only)
# --------------------------------------------------------------------------

def spotify_episode_title(url):
    oembed = http_client.get_json("https://open.spotify.com/oembed?url=" + quote(url, safe=""),
                                  LOOKUP_FAILED, LOOKUP_HINT)
    title = (oembed.get("title") or "").strip()
    if not title:
        raise CastError(LOOKUP_FAILED, "Spotify's oEmbed endpoint returned no title.", LOOKUP_HINT)
    return title


def spotify_show_name(url):
    """The show name from the episode page's og:description, or '' if absent."""
    try:
        body, _ = http_client.get_bytes(url, LOOKUP_FAILED, LOOKUP_HINT)
    except CastError:
        return ""
    found = re.search(rb'<meta property="og:description" content="([^"]+)"', body)
    if not found:
        return ""
    description = html.unescape(found.group(1).decode("utf-8", "replace"))
    return description.split(" · ")[0].strip()


def feeds_for_episode_title(title):
    """Feeds of iTunes episodes whose title matches closely, best first."""
    results = itunes("search", term=title, media="podcast", entity="podcastEpisode", limit=10)
    ranked = sorted(results, key=lambda item: ratio(title, item.get("trackName", "")), reverse=True)
    return [item["feedUrl"] for item in ranked
            if item.get("feedUrl") and ratio(title, item.get("trackName", "")) >= MIN_RATIO]


def feeds_for_show(name):
    if not name:
        return []
    results = itunes("search", term=name, media="podcast", entity="podcast", limit=5)
    return [item["feedUrl"] for item in results if item.get("feedUrl")]


def resolve_spotify(url):
    title = spotify_episode_title(url)
    feeds = feeds_for_episode_title(title)
    feeds += [feed for feed in feeds_for_show(spotify_show_name(url)) if feed not in feeds]
    if not feeds:
        raise CastError(NO_PUBLIC_FEED, f"No public feed found for \"{title}\".", SPOTIFY_ONLY_HINT)
    return EpisodeHint(feed_urls=feeds[:3], title=title)
