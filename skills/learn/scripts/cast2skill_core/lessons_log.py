"""`log`: recording what was proposed, picked, rejected and written.

Input on stdin is either the plain `key: value` format the skill uses (see
parse_plain_entry) or one JSON object with the same fields:

    {"library_dir": ".../library/2026-11-11-some-talk",
     "outcome": "written" | "nothing_picked" | "nothing_worth_adding",
     "reason": "one sentence, used when nothing was worth adding",
     "candidates": [{"title", "type": "procedure|rule|idea", "what_changes",
                     "evidence": {"timestamp", "speaker", "quote"},
                     "versus_setup", "confidence",
                     "decision": "picked|rejected", "written_to": path or null}]}

Two files are appended, both inside the cast2skill home only:
`<library_dir>/lessons.md` (readable) and `lessons.jsonl` (one line per
candidate, read at the next run to avoid proposing the same thing twice).
Quotes are cut to 25 words here too (SPEC section 10, rule 5).
"""

import datetime
import json
import os

from . import storage
from .errors import BAD_LOG_ENTRY, CastError

TYPES = ("procedure", "rule", "idea")
DECISIONS = ("picked", "rejected")
OUTCOMES = ("written", "nothing_picked", "nothing_worth_adding")
MAX_QUOTE_WORDS = 25


def fail(message):
    raise CastError(BAD_LOG_ENTRY, message, "Fix the JSON and run `log` again.")


def short_quote(text):
    words = (text or "").split()
    return " ".join(words[:MAX_QUOTE_WORDS]) + (" ..." if len(words) > MAX_QUOTE_WORDS else "")


def checked_library_dir(path):
    """The library folder, which must be inside this home's library."""
    folder = os.path.realpath(os.path.expanduser(path or ""))
    root = os.path.realpath(storage.library_root())
    if not path or os.path.dirname(folder) != root or not os.path.isdir(folder):
        fail(f"library_dir must be an existing folder directly inside {root}.")
    return folder


def checked_candidate(raw):
    if not isinstance(raw, dict) or not raw.get("title"):
        fail("Every candidate needs at least a title.")
    if raw.get("type") not in TYPES:
        fail(f"Candidate type must be one of {', '.join(TYPES)}: {raw.get('title')}")
    if raw.get("decision") not in DECISIONS:
        fail(f"Candidate decision must be picked or rejected: {raw.get('title')}")
    evidence = raw.get("evidence") or {}
    return {
        "title": str(raw["title"]), "type": raw["type"], "decision": raw["decision"],
        "what_changes": str(raw.get("what_changes") or ""),
        "evidence": {"timestamp": str(evidence.get("timestamp") or ""),
                     "speaker": str(evidence.get("speaker") or ""),
                     "quote": short_quote(str(evidence.get("quote") or ""))},
        "versus_setup": str(raw.get("versus_setup") or ""),
        "confidence": str(raw.get("confidence") or ""),
        "written_to": raw.get("written_to") if raw["decision"] == "picked" else None,
    }


def markdown_section(stamp, outcome, reason, candidates):
    lines = [f"## {stamp}: {outcome.replace('_', ' ')}", ""]
    if reason:
        lines += [reason, ""]
    for number, item in enumerate(candidates, 1):
        where = f", written to `{item['written_to']}`" if item["written_to"] else ""
        evidence = item["evidence"]
        lines += [f"{number}. **{item['title']}** [{item['type']}]: {item['decision']}{where}",
                  f"   - What changes: {item['what_changes']}",
                  f"   - Evidence: [{evidence['timestamp']}] {evidence['speaker']} \"{evidence['quote']}\"",
                  f"   - Versus setup: {item['versus_setup']}. Confidence: {item['confidence']}"]
    return "\n".join(lines) + "\n\n"


def append(path, text):
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def record(entry, now=None):
    if not isinstance(entry, dict):
        fail("Expected one JSON object.")
    folder = checked_library_dir(entry.get("library_dir"))
    outcome = entry.get("outcome")
    if outcome not in OUTCOMES:
        fail(f"outcome must be one of {', '.join(OUTCOMES)}.")
    candidates = [checked_candidate(raw) for raw in entry.get("candidates") or []]
    source = storage.read_source_json(folder) or {}
    stamp = (now or datetime.datetime.now()).isoformat(timespec="seconds")

    append(os.path.join(folder, "lessons.md"),
           markdown_section(stamp, outcome, str(entry.get("reason") or ""), candidates))
    lines = [json.dumps(dict(item, date=stamp, source_id=source.get("id"), source_title=source.get("title"),
                             source_url=source.get("url")), ensure_ascii=False) for item in candidates]
    if lines:
        append(os.path.join(storage.home_dir(), "lessons.jsonl"), "\n".join(lines) + "\n")
    written = [os.path.join(folder, "lessons.md")]
    if lines:
        written.append(os.path.join(storage.home_dir(), "lessons.jsonl"))
    return {"logged": len(candidates), "outcome": outcome, "files_written": written}


EVIDENCE_KEYS = ("timestamp", "speaker", "quote")


def parse_plain_entry(text):
    """The brace-free format the skill sends (Claude Code's Bash check flags `{"`).

    Blocks are separated by a line holding only `---`. The first block holds
    library_dir, outcome and reason; every later block is one candidate.
    Each line is `key: value`; timestamp, speaker and quote fill `evidence`.
    """
    blocks = [block for block in text.replace("\r\n", "\n").split("\n---\n")]
    parsed = []
    for block in blocks:
        fields = {}
        for line in block.splitlines():
            if not line.strip():
                continue
            key, separator, value = line.partition(":")
            if not separator:
                fail(f"Expected `key: value`, got: {line.strip()[:60]}")
            fields[key.strip().lower()] = value.strip()
        parsed.append(fields)
    header, candidates = parsed[0], [fields for fields in parsed[1:] if fields]
    for fields in candidates:
        fields["evidence"] = {key: fields.pop(key, "") for key in EVIDENCE_KEYS}
        if fields.get("written_to", "").lower() in ("", "null", "none", "-"):
            fields["written_to"] = None
    return dict(header, candidates=candidates)


def record_from_stdin(stream):
    text = stream.read()
    if text.lstrip().startswith("{"):
        try:
            return record(json.loads(text))
        except ValueError as exc:
            fail(f"stdin is not valid JSON: {exc}")
    if not text.strip():
        fail("Nothing on stdin.")
    return record(parse_plain_entry(text))
