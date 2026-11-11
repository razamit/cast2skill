"""Picking one episode out of a feed by title (SPEC section 6.3, episode matching).

Titles are normalized (case, punctuation, whitespace). An exact match wins;
otherwise the best difflib ratio wins if it is at least 0.8. Below that the
top three candidates go back to the skill, which asks the user.
"""

import difflib
import hashlib
import re
import unicodedata

from .errors import NEEDS_EPISODE, CastError

MIN_RATIO = 0.8
CANDIDATE_COUNT = 3
RECENT_COUNT = 10


def normalize_title(text):
    """Lowercase, no punctuation or symbols, single spaces. Works for Hebrew too."""
    folded = unicodedata.normalize("NFKC", text or "").casefold()
    kept = "".join(" " if unicodedata.category(char)[0] in "PSZ" else char for char in folded)
    return re.sub(r"\s+", " ", kept).strip()


def ratio(query, title):
    return difflib.SequenceMatcher(None, normalize_title(query), normalize_title(title)).ratio()


def episode_key(episode):
    """Short hex id for an episode: shell-safe, so the skill reruns with it, never a title."""
    return hashlib.sha1((episode.guid or episode.audio_url).encode("utf-8")).hexdigest()[:16]


def describe(episode):
    return {"episode_id": episode_key(episode), "title": episode.title,
            "published": episode.published, "duration_s": episode.duration_s}


def by_key(episodes, key):
    return next((episode for episode in episodes if episode_key(episode) == key), None)


def exact(episodes, title):
    """Exact match after normalizing, or None. For titles that came from a link."""
    wanted = normalize_title(title)
    return next((episode for episode in episodes if normalize_title(episode.title) == wanted), None)


def by_prefix(episodes, slug):
    """An Apple link slug is the start of the title, cut short. Unique prefix match, or None."""
    wanted = normalize_title(slug)
    if len(wanted.split()) < 3:
        return None
    found = [episode for episode in episodes if normalize_title(episode.title).startswith(wanted)]
    return found[0] if len(found) == 1 else None


def near_misses(episodes, title):
    """Episodes at or above the fuzzy threshold that are not exact: never picked silently."""
    ranked = sorted(episodes, key=lambda episode: ratio(title, episode.title), reverse=True)
    return [episode for episode in ranked[:CANDIDATE_COUNT] if ratio(title, episode.title) >= MIN_RATIO]


def ask_user(message, episodes):
    raise CastError(NEEDS_EPISODE, message,
                    "Ask the user which episode, then rerun with --episode-id <its episode_id>.",
                    candidates=[describe(episode) for episode in episodes])


def match(episodes, query):
    """The episode whose title matches `query`, or raise needs_episode with candidates."""
    if not episodes:
        raise CastError(NEEDS_EPISODE, "The feed lists no episodes with audio.",
                        "Check the feed URL.", candidates=[])
    wanted = normalize_title(query)
    for episode in episodes:
        if normalize_title(episode.title) == wanted:
            return episode
    ranked = sorted(episodes, key=lambda episode: ratio(query, episode.title), reverse=True)
    if ratio(query, ranked[0].title) >= MIN_RATIO:
        return ranked[0]
    ask_user(f"No episode title matches \"{query}\" closely enough.", ranked[:CANDIDATE_COUNT])


def recent_or_match(episodes, query):
    """With a query, match it; without one, ask the user to pick a recent episode."""
    if query:
        return match(episodes, query)
    ask_user("Which episode? This feed has several.", episodes[:RECENT_COUNT])
