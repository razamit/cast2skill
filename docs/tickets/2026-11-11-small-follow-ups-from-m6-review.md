# Three small rough edges left after the M6 review: --help is not JSON, feed language outranks a Hebrew title, direct audio titles can be "default"

Status: OPEN · Priority: LOW · Type: polish · Cost: none

> From the independent review before GATE B (nits not fixed in that pass).

## Symptom

1. `cast2skill.py --help` (and `fetch --help`) prints argparse text, not one
   JSON object, unlike every other invocation.
2. Language order puts the feed's `<language>` ahead of Hebrew letters in the
   title (SPEC.md §6.3, decision 17). Some Hebrew shows declare `en` in their
   feed, so their episodes would be transcribed with the English model.
3. A direct audio URL ending in `default.mp3` (NPR's enclosures) gets the
   title "default".

## Evidence

- Reviewer note, 2026-11-11 (M6 review, item 9).
- M4 live run: direct NPR enclosure → `"title": "default"` (docs/PROGRESS.md, M4 entry).

## Why it matters

1 is harmless: the skill never calls `--help`. 2 can produce a wrong-language
transcript for a mislabeled Hebrew feed; `--lang he` fixes it per run. 3 only
affects the library folder name and the card title.

## Scope to decide

- 2: let a Hebrew title outrank a feed `<language>` of `en` (a spec change,
  owner's call), or leave as is.
- 3: fall back to the host name plus file name, or leave.

No code change made by this ticket. It is an observation on the record.
