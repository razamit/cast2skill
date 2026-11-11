"""Choosing the transcript language: Hebrew or English.

Order (SPEC section 6.3, plus the config default as the last resort before
asking): --lang, then the source's own language field (YouTube or RSS), then
Hebrew if the title has Hebrew letters, then config default_lang. Otherwise
the caller raises needs_lang so the skill asks the user.
"""

import re

from .errors import NEEDS_LANG, CastError

SUPPORTED = ("he", "en")
# YouTube and older feeds still use "iw", the withdrawn ISO code for Hebrew.
ALIASES = {"iw": "he", "heb": "he", "eng": "en"}
HEBREW_LETTERS = re.compile(r"[א-ת]")


def normalize(code):
    """'en-US' -> 'en', 'iw' -> 'he'. Returns None for anything unsupported."""
    if not code:
        return None
    base = re.split(r"[-_]", str(code).strip().lower())[0]
    base = ALIASES.get(base, base)
    return base if base in SUPPORTED else None


def choose(flag_lang=None, source_lang=None, title="", default_lang=None):
    """(language, how it was chosen), or (None, None) when nothing decides it."""
    if flag_lang:
        return normalize(flag_lang), "flag"
    if normalize(source_lang):
        return normalize(source_lang), "source"
    if HEBREW_LETTERS.search(title or ""):
        return "he", "hebrew_title"
    if normalize(default_lang):
        return normalize(default_lang), "config_default"
    return None, None


def require(flag_lang=None, source_lang=None, title="", default_lang=None):
    """Like choose(), but raises needs_lang instead of returning None."""
    chosen, how = choose(flag_lang, source_lang, title, default_lang)
    if chosen is None:
        raise CastError(NEEDS_LANG, "Could not tell whether this is Hebrew or English.",
                        "Ask the user, then rerun with --lang he or --lang en.")
    return chosen, how
