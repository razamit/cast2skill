"""Removing share-tracking query parameters from a source URL.

A share link such as `open.spotify.com/episode/...?si=05890d41c8764a22`
carries a token that can identify the person who shared it. The fetch result,
source.json, lessons.jsonl and every Source line or provenance comment the
skill writes would repeat it, so the URL is cleaned once, before anything is
classified or saved.

Only parameters on the list below are removed. Everything else stays, in its
original order and spelling: YouTube `v`, `t` and `list`, Apple's `i` (which
selects the episode), and any parameter a feed or audio host needs.
"""

from urllib.parse import urlsplit, urlunsplit

TRACKING_PARAMETERS = frozenset({"si", "feature", "fbclid", "gclid", "igshid", "igsh"})
TRACKING_PREFIXES = ("utm_",)


def is_tracking_parameter(name):
    lowered = name.lower()
    return lowered in TRACKING_PARAMETERS or lowered.startswith(TRACKING_PREFIXES)


def strip_tracking_parameters(url):
    """The URL without tracking parameters. Non-URLs and None come back unchanged."""
    if not url or "?" not in url:
        return url
    parts = urlsplit(url)
    if not parts.query:
        return url
    kept = [pair for pair in parts.query.split("&")
            if pair and not is_tracking_parameter(pair.split("=", 1)[0])]
    return urlunsplit(parts._replace(query="&".join(kept)))
