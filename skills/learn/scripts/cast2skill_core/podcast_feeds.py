"""Reading podcast RSS feeds with the standard library.

Feeds are untrusted XML from the internet. ElementTree never resolves
external entities, and a feed that declares its own entities is refused
outright, which rules out entity-expansion attacks whatever the expat version.
"""

import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

from . import http_client
from .errors import BAD_ARGUMENTS, FEED_UNREADABLE, CastError

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
FEED_HINT = "Pass the show's RSS feed URL, or download the episode audio and pass the file."


@dataclass
class Episode:
    title: str
    guid: str = ""
    audio_url: str = ""
    published: str = ""  # ISO date, or ""
    duration_s: object = None
    link: str = ""


@dataclass
class Feed:
    url: str
    title: str = ""
    author: str = ""
    language: str = ""
    episodes: list = field(default_factory=list)  # newest first, audio only


def parse_duration(text):
    """itunes:duration as seconds: '3723', '62:03' or '1:02:03'. None if unreadable."""
    parts = (text or "").strip().split(":")
    try:
        numbers = [float(part) for part in parts if part != ""]
    except ValueError:
        return None
    if not numbers or len(numbers) > 3:
        return None
    seconds = 0.0
    for number in numbers:
        seconds = seconds * 60 + number
    return round(seconds)


def parse_date(text):
    try:
        return parsedate_to_datetime(text.strip()).date().isoformat()
    except (TypeError, ValueError, AttributeError):
        return ""


def child_text(element, tag):
    found = element.find(tag)
    return (found.text or "").strip() if found is not None and found.text else ""


def parse_item(item):
    enclosure = item.find("enclosure")
    return Episode(
        title=child_text(item, "title"),
        guid=child_text(item, "guid"),
        audio_url=(enclosure.get("url") or "").strip() if enclosure is not None else "",
        published=parse_date(child_text(item, "pubDate")),
        duration_s=parse_duration(child_text(item, ITUNES + "duration")),
        link=child_text(item, "link"),
    )


def looks_like_feed(body):
    head = body[:2048].lstrip().lower()
    return head.startswith(b"<?xml") or head.startswith(b"<rss") or b"<rss" in head


def parse_feed(body, url):
    """Parse RSS bytes. Raises feed_unreadable for broken, entity-laden or non-podcast XML."""
    if b"<!ENTITY" in body[:65536]:
        raise CastError(FEED_UNREADABLE, f"Refusing a feed that declares XML entities: {url}", FEED_HINT)
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as exc:
        raise CastError(FEED_UNREADABLE, f"The feed at {url} is not valid XML ({exc}).", FEED_HINT)
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise CastError(FEED_UNREADABLE, f"{url} is XML but not an RSS podcast feed.", FEED_HINT)

    episodes = [episode for episode in (parse_item(item) for item in channel.findall("item"))
                if episode.audio_url and episode.title]
    episodes.sort(key=lambda episode: episode.published, reverse=True)  # stable for undated
    return Feed(url=url, title=child_text(channel, "title"),
                author=child_text(channel, ITUNES + "author") or child_text(channel, "title"),
                language=child_text(channel, "language"), episodes=episodes)


def fetch_feed(url):
    body, content_type = http_client.get_bytes(url, FEED_UNREADABLE, FEED_HINT)
    if not looks_like_feed(body) and "xml" not in content_type.lower():
        raise CastError(BAD_ARGUMENTS, f"{url} is not a podcast feed or audio file.",
                        "Supported links: YouTube, Apple Podcasts, Spotify episodes, RSS feeds, "
                        "direct audio files. For an article, paste its text instead.")
    return parse_feed(body, url)
