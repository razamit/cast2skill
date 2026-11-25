# `check`'s verdict text still invites removing the flagged words

Status: CLOSED (2026-11-25), fixed in the same unit of work · Priority: LOW · Type: wording (script output read by the model) · Cost: none

> Follows `2026-11-25-learn-setup-reads-and-check-rewording.md` (closed) and
> decision row 39. That fix changed SKILL.md only; the brief limited it to
> the skill text, so the script string was left as is.

## Symptom

`skills/learn/scripts/cast2skill_core/lesson_check.py:96` returns, for any
flagged draft:
`"verdict": "note only: show the user the flagged parts as a quote, or remove them and check again"`.
"remove them" can be read as "remove the flagged words", which is the
synonym-swap pattern row 39 forbids. SKILL.md step 7.3 now says to remove the
flagged idea, not just its words, so the two texts the model reads disagree in
tone.

## Evidence

```
$ printf '%s\n' '- Before approving a permission request, read the exact command it will run.' | python3 skills/learn/scripts/cast2skill.py check
{"ok": false, "flags": [{"rule": "permissions", "match": "permission"}], "verdict": "note only: show the user the flagged parts as a quote, or remove them and check again"}
```

In the headless dry run after the fix (progress entry 2026-11-25, run `d1`),
the model was flagged on "message" and removed the clause "in the message",
telling the user what it removed. It followed SKILL.md; the verdict text did
not mislead it there, but it could.

## Why it matters

The model reads both strings. A verdict that says "remove them" weakens the
SKILL.md rule a little. Not urgent: SKILL.md is the stronger instruction and
it was followed in the one observed flag.

## Scope to decide

- Change the verdict to something like "note only: show the user the flags;
  remove the flagged idea, not just its words, or offer it as a note with the
  quote" (no test pins the current string; `grep -rn "remove them" tests`
  finds nothing).
- OR drop the second clause and leave the rule to SKILL.md alone.

## Resolution (2026-11-25)

First option taken. The verdict now reads `note only: show the user the flagged
parts as a quote, or remove that idea (not a reworded copy of it) and check
again`, matching SKILL.md step 7.3 and decision row 39. Tests: 131 OK.
