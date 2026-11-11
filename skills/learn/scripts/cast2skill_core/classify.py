"""Deciding what kind of source an argument is, without touching the network.

Mirrors the table in SPEC section 6.3. One deliberate difference: a URL or a
local file that matches no row is an error rather than "pasted text", because
treating a link as the text to learn from would silently produce nonsense.
Any other URL is assumed to be a feed and confirmed when it is fetched.
"""

import os
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from .errors import BAD_ARGUMENTS, CastError

AUDIO_EXTENSIONS = (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".mp4")
TEXT_EXTENSIONS = (".txt", ".md", ".vtt", ".srt")
YOUTUBE_HOSTS = ("youtube.com", "youtu.be", "youtube-nocookie.com")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
STDIN_MARKER = "-"

# kinds (the "kind" field of the fetch result)
YOUTUBE, PODCAST, AUDIO, TEXT = "youtube", "podcast", "audio", "text"
# routes: how the kind is resolved
ROUTE_YOUTUBE = "youtube"
ROUTE_APPLE = "apple_podcasts"
ROUTE_SPOTIFY = "spotify"
ROUTE_FEED = "feed_url"
ROUTE_AUDIO_URL = "audio_url"
ROUTE_AUDIO_FILE = "audio_file"
ROUTE_TEXT_FILE = "text_file"
ROUTE_PASTED = "pasted_text"


@dataclass(frozen=True)
class Source:
    kind: str
    route: str
    value: str  # the URL, absolute file path, or the text itself


def is_url(text):
    return bool(re.match(r"^https?://\S+$", text, flags=re.IGNORECASE))


def host_of(url):
    host = (urlparse(url).hostname or "").lower()
    for prefix in ("www.", "m.", "music."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host


def youtube_video_id(url):
    """The 11-character video id from any common YouTube URL shape, or None."""
    parsed = urlparse(url)
    host = host_of(url)
    candidates = []
    if host == "youtu.be":
        candidates.append(parsed.path.strip("/").split("/")[0])
    else:
        candidates += parse_qs(parsed.query).get("v", [])
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in ("shorts", "live", "embed", "v"):
            candidates.append(parts[1])
    for candidate in candidates:
        if YOUTUBE_ID.match(candidate):
            return candidate
    return None


def classify_url(url):
    host = host_of(url)
    path = urlparse(url).path.lower()
    if any(host == known or host.endswith("." + known) for known in YOUTUBE_HOSTS):
        return Source(YOUTUBE, ROUTE_YOUTUBE, url)
    if host == "podcasts.apple.com":
        return Source(PODCAST, ROUTE_APPLE, url)
    if host == "open.spotify.com":
        if "/episode/" not in path:
            raise CastError(BAD_ARGUMENTS, "Only Spotify episode links are supported.",
                            "Open the episode in Spotify, use Share > Copy link, and pass that.")
        return Source(PODCAST, ROUTE_SPOTIFY, url)
    if path.endswith(AUDIO_EXTENSIONS):
        return Source(AUDIO, ROUTE_AUDIO_URL, url)
    return Source(PODCAST, ROUTE_FEED, url)


def classify_file(path):
    lowered = path.lower()
    if lowered.endswith(AUDIO_EXTENSIONS):
        return Source(AUDIO, ROUTE_AUDIO_FILE, path)
    if lowered.endswith(TEXT_EXTENSIONS):
        return Source(TEXT, ROUTE_TEXT_FILE, path)
    raise CastError(BAD_ARGUMENTS, f"Unsupported file type: {os.path.basename(path)}",
                    f"Audio: {' '.join(AUDIO_EXTENSIONS)}. Text: {' '.join(TEXT_EXTENSIONS)}.")


def classify(argument, stdin_text=None):
    """Turn the fetch argument into a Source. `-` means the text is on stdin."""
    text = (argument or "").strip()
    if text == STDIN_MARKER:
        return Source(TEXT, ROUTE_PASTED, stdin_text or "")
    if is_url(text):
        return classify_url(text)
    expanded = os.path.expanduser(text)
    if "\n" not in text and len(text) < 1024 and os.path.isfile(expanded):
        return classify_file(os.path.abspath(expanded))
    return Source(TEXT, ROUTE_PASTED, text)
