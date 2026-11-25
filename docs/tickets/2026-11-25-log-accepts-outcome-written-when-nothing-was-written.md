# `log` accepts `outcome: written` when no candidate has a file written

Status: OPEN · Priority: LOW · Type: log accuracy · Cost: none

> Found while building decision 34. Related to it, not covered by it.

## Symptom

When the user picks lessons and every write fails or is declined, the skill
now logs each as `decision: picked`, `written_to: none` (decision 37). The
run's `outcome` can still be `written`, and `log` accepts it, including with
zero candidates.

## Evidence

```
$ printf 'library_dir: <dir>\noutcome: written\n---\ntitle: Blocked skill\ntype: procedure\ndecision: picked\nwritten_to: none\n' | python3 skills/learn/scripts/cast2skill.py log
{"logged": 1, "outcome": "written", ...}
```

(`tests/test_log_records.py::test_a_failed_write_is_logged_as_picked_with_none`
logs exactly this and passes.)

## Why it matters

`lessons.md` then reads "written" for a run that wrote nothing, which is the
kind of record decision 34 exists to stop. No outcome value fits "picked but
nothing written" today.

## Scope to decide

- Option A: refuse `outcome: written` unless at least one candidate has `written_to`; add an outcome such as `write_failed`.
- OR Option B: derive the outcome in the script from the candidates and ignore the one sent.
- OR Option C: keep it, and document that `written` means "the user picked".

No code change made by this ticket. It is an observation on the record.
