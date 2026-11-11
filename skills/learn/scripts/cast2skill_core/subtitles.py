"""Turning VTT or SRT subtitles into a readable transcript.

YouTube's auto captions are "rolling": each cue repeats the line before it and
adds one new line, and words carry inline timing tags. Read raw, every
sentence appears two or three times. This module:

1. parses cues (start time + text lines) from VTT or SRT,
2. strips tags, positioning and entities, and drops sound labels like [Music],
3. drops any line identical to one of the two lines emitted just before it,
4. groups what is left into paragraphs of about 30 seconds, each starting
   with one `[HH:MM:SS]` timestamp.
"""

import html
import re

PARAGRAPH_SECONDS = 30
TIMING = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")
INLINE_TAG = re.compile(r"<[^>]*>")
SSA_OVERRIDE = re.compile(r"\{\\[^}]*\}")
SOUND_LABEL = re.compile(r"^\s*[\[(][^\])]{1,40}[\])]\s*$")


def seconds_from(hours, minutes, seconds, millis):
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0


def format_timestamp(seconds):
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clean_line(raw):
    text = SSA_OVERRIDE.sub("", INLINE_TAG.sub("", raw))
    text = html.unescape(text).replace("​", "")
    text = re.sub(r"\s+", " ", text).strip()
    if not text or SOUND_LABEL.match(text):
        return ""
    return text


def parse_cues(raw_text):
    """[(start_seconds, [clean lines])] for VTT or SRT. Headers, notes and indexes skipped."""
    cues = []
    current = None
    for raw_line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        match = TIMING.search(raw_line)
        if match:
            current = (seconds_from(*match.groups()[:4]), [])
            cues.append(current)
            continue
        if raw_line == "":
            current = None  # only a truly empty line ends a cue
            continue
        if current is None:
            continue  # header, NOTE block, or SRT index number
        line = clean_line(raw_line)  # whitespace-only payload lines become ""
        if line:
            current[1].append(line)
    return [cue for cue in cues if cue[1]]


def dedupe(cues, window=2):
    """[(start, line)] with rolling repeats removed.

    A line equal to one of the last `window` lines kept is a carry-over from
    the previous cue, not new speech, and is dropped.
    """
    kept = []
    for start, lines in cues:
        for line in lines:
            if any(previous == line for _, previous in kept[-window:]):
                continue
            kept.append((start, line))
    return kept


def paragraphs(timed_lines, span=PARAGRAPH_SECONDS):
    """Join lines into ~span-second paragraphs: [(start, text)]."""
    grouped = []
    for start, line in timed_lines:
        if grouped and start - grouped[-1][0] < span:
            grouped[-1][1].append(line)
        else:
            grouped.append((start, [line]))
    return [(start, " ".join(lines)) for start, lines in grouped]


def clean_subtitles(raw_text):
    """The readable transcript text for a VTT or SRT file. Empty string if no speech."""
    body = paragraphs(dedupe(parse_cues(raw_text)))
    return "\n\n".join(f"[{format_timestamp(start)}] {text}" for start, text in body) + \
        ("\n" if body else "")
