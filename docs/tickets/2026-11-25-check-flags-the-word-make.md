# `check` refuses any draft containing the English word "make"

Status: CLOSED (2026-11-25), fixed in the progress entry "2026-11-25: dry-run follow-ups" (decision row 32)
Found: 2026-11-25, dry run of `/cast2skill:learn` on a Spotify episode (73 - Harness Engineering)

## Symptom

The `shell_command` pattern in `skills/learn/scripts/cast2skill_core/lesson_check.py`
matches `make` as a bare, case-insensitive word. Ordinary rules such as
"make them pass" or "Make sure the agent shows its work" come back `ok: false`
and the skill tells the user they can only be notes.

## Evidence

```
$ printf -- '- Make sure the agent shows its work.\n' | python3 skills/learn/scripts/cast2skill.py check
{"ok": false, "flags": [{"rule": "shell_command", "match": "Make"}], ...}
```

In the dry run, the rule "write the failing tests first ... then make them pass
by changing only the code" was refused and had to be reworded to "get them passing".

## Why it matters

"Make" is one of the most common verbs in instructions. False refusals teach
the user to ignore the checker, and the model has to keep rewording drafts.
The checker is the safety backstop, so any loosening needs care.

## Scope to decide

- Drop `make` from the bare-word list, or only match it in a command shape
  (start of line or after a backtick, followed by a target such as `make install`).
- Check the other bare words (`exec`, `eval`, `nc`) for the same problem.
- Add a regression test with "make sure" and "make it pass" next to a real
  `make install` case.

## Fix

`make` and `eval` are now flagged only in a command shape (decision row 32):
inside inline code, after a `$` prompt or `&&`/`||`, with flags
(`make -j8`) or `VAR=value`, before a target that is never English after
"make" (`install`, `deploy`, `lint`, ...), or before a target that could be
English (`test`, `build`, `clean`, `all`, ...) only when it ends the clause
("Run make test."). `eval` needs a quote, `$` or backtick after it, or `eval(`.
`exec` and `nc` stay bare words: rare in English lessons, and direct shell
primitives.

Regression tests in `tests/test_learn_safety_and_log.py`:
`test_everyday_make_and_eval_pass` ("Make sure the agent shows its work",
"make them pass", "Write an eval before changing a prompt") and
`test_make_and_eval_in_command_shape_are_flagged` ("run `make install`",
"make install", "$ make -j8", "Run make test.", "exec summary first").

```
$ printf -- '- Make sure the agent shows its work.\n' | python3 skills/learn/scripts/cast2skill.py check
{"ok": true, "flags": [], "verdict": "no flags; the safety rules still apply"}
```
