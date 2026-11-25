"""`log`: recording what was proposed, picked, rejected and written.

Input on stdin is either the plain `key: value` format the skill uses (see
parse_plain_entry) or one JSON object with the same fields:

    {"library_dir": ".../library/2026-11-11-some-talk",
     "outcome": "written" | "nothing_picked" | "nothing_worth_adding" | "dry_run",
     "reason": "one sentence, used when nothing was worth adding",
     "candidates": [{"title", "type": "procedure|rule|idea", "what_changes",
                     "evidence": {"timestamp", "speaker", "quote"},
                     "versus_setup", "confidence",
                     "decision": "picked|rejected|dry_run", "written_to": path or null}]}

A dry run (`/cast2skill:learn <source> --dry-run`) writes nothing to the
setup, so its outcome and every candidate's decision are `dry_run`, and
`written_to` is always null. The two never mix with the other values.

`written_to` is checked, not trusted (written_paths.py): a set value needs
`decision: picked`, and must name a file that exists in a place the skill may
write. One refused candidate refuses the whole entry, and nothing is logged.

Two files are appended, both inside the cast2skill home only:
`<library_dir>/lessons.md` (readable) and `lessons.jsonl` (one line per
candidate, read at the next run to avoid proposing the same thing twice).
Every jsonl row carries the run's `outcome`. A run with no candidates still
writes one run-level row, with the candidate fields null and its `reason`,
so every run leaves a trace. Rows written before 2026-11-25 have no
`outcome`. Quotes are cut to 25 words here too (SPEC section 10, rule 5).
"""

import datetime
import json
import os

from . import storage, written_paths
from .errors import BAD_LOG_ENTRY, CastError
from .url_cleaning import strip_tracking_parameters

TYPES = ("procedure", "rule", "idea")
DRY_RUN = "dry_run"
DECISIONS = ("picked", "rejected", DRY_RUN)
OUTCOMES = ("written", "nothing_picked", "nothing_worth_adding", DRY_RUN)
MAX_QUOTE_WORDS = 25
CANDIDATE_FIELDS = ("title", "type", "decision", "what_changes", "evidence",
                    "versus_setup", "confidence", "written_to")
WRITTEN_TO_HINT = ("Log only files that were actually written; use written_to: none "
                   "for a write that failed or was declined.")


def fail(message, hint="Fix the entry and run `log` again."):
    raise CastError(BAD_LOG_ENTRY, message, hint)


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


def checked_written_to(raw):
    """None when nothing was written; otherwise the real path of a file that exists."""
    value = raw.get("written_to")
    if written_paths.is_empty(value):
        return None
    if raw["decision"] != "picked":
        fail(f"written_to is set for a candidate that was not picked ({raw['decision']}): "
             f"{raw['title']}", WRITTEN_TO_HINT)
    real_path, problem = written_paths.problem_with_written_path(value)
    if problem:
        fail(f"{problem}: {raw['title']}", WRITTEN_TO_HINT)
    return real_path


def checked_candidate(raw):
    if not isinstance(raw, dict) or not raw.get("title"):
        fail("Every candidate needs at least a title.")
    if raw.get("type") not in TYPES:
        fail(f"Candidate type must be one of {', '.join(TYPES)}: {raw.get('title')}")
    if raw.get("decision") not in DECISIONS:
        fail(f"Candidate decision must be one of {', '.join(DECISIONS)}: {raw.get('title')}")
    written_to = checked_written_to(raw)
    evidence = raw.get("evidence") or {}
    return {
        "title": str(raw["title"]), "type": raw["type"], "decision": raw["decision"],
        "what_changes": str(raw.get("what_changes") or ""),
        "evidence": {"timestamp": str(evidence.get("timestamp") or ""),
                     "speaker": str(evidence.get("speaker") or ""),
                     "quote": short_quote(str(evidence.get("quote") or ""))},
        "versus_setup": str(raw.get("versus_setup") or ""),
        "confidence": str(raw.get("confidence") or ""),
        "written_to": written_to,
    }


def check_dry_run_consistency(outcome, candidates):
    """A dry run's candidates are all dry_run, and dry_run appears only in a dry run."""
    for item in candidates:
        if (outcome == DRY_RUN) != (item["decision"] == DRY_RUN):
            fail(f"outcome dry_run and decision dry_run go together: {item['title']}")


def markdown_section(stamp, outcome, reason, candidates):
    lines = [f"## {stamp}: {outcome.replace('_', ' ')}", ""]
    if reason:
        lines += [reason, ""]
    for number, item in enumerate(candidates, 1):
        where = f", written to `{item['written_to']}`" if item["written_to"] else ""
        evidence = item["evidence"]
        lines += [f"{number}. **{item['title']}** [{item['type']}]: {item['decision'].replace('_', ' ')}{where}",
                  f"   - What changes: {item['what_changes']}",
                  f"   - Evidence: [{evidence['timestamp']}] {evidence['speaker']} \"{evidence['quote']}\"",
                  f"   - Versus setup: {item['versus_setup']}. Confidence: {item['confidence']}"]
    return "\n".join(lines) + "\n\n"


def append(path, text):
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def run_level_row(reason):
    """The one jsonl row of a run that had no candidates."""
    return dict(dict.fromkeys(CANDIDATE_FIELDS), reason=reason or None)


def jsonl_rows(outcome, reason, candidates, stamp, source):
    rows = candidates or [run_level_row(reason)]
    return [json.dumps(dict(row, outcome=outcome, date=stamp, source_id=source.get("id"),
                            source_title=source.get("title"),
                            source_url=strip_tracking_parameters(source.get("url"))), ensure_ascii=False)
            for row in rows]


def record(entry, now=None):
    """Check the whole entry first, then append; a refused entry writes nothing."""
    if not isinstance(entry, dict):
        fail("Expected one JSON object.")
    folder = checked_library_dir(entry.get("library_dir"))
    outcome = entry.get("outcome")
    if outcome not in OUTCOMES:
        fail(f"outcome must be one of {', '.join(OUTCOMES)}.")
    candidates = [checked_candidate(raw) for raw in entry.get("candidates") or []]
    check_dry_run_consistency(outcome, candidates)
    reason = str(entry.get("reason") or "")
    source = storage.read_source_json(folder) or {}
    stamp = (now or datetime.datetime.now()).isoformat(timespec="seconds")

    markdown_path = os.path.join(folder, "lessons.md")
    jsonl_path = os.path.join(storage.home_dir(), "lessons.jsonl")
    append(markdown_path, markdown_section(stamp, outcome, reason, candidates))
    append(jsonl_path, "\n".join(jsonl_rows(outcome, reason, candidates, stamp, source)) + "\n")
    return {"logged": len(candidates), "outcome": outcome, "files_written": [markdown_path, jsonl_path]}


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
        if written_paths.is_empty(fields.get("written_to")):
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
