# `log` judges project paths against the process working directory, so a `cd` into a subfolder refuses the project's own CLAUDE.md

Status: OPEN · Priority: LOW · Type: correctness · Cost: none

> Found while building decision 34 (the `written_to` check).

## Symptom

`written_paths.allowed_locations()` takes the project locations
(`CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/skills/`) from `os.getcwd()` of
the `log` process. Claude Code's Bash tool keeps a `cd` between calls, so if
the session has moved into `src/`, a rule truly written to the project root's
`CLAUDE.md` is refused as "outside the places cast2skill writes".

## Evidence

`skills/learn/scripts/cast2skill_core/written_paths.py`, `allowed_locations`:
`cwd = working_dir or os.getcwd()`. Not reproduced in a live session; read
from the code.

## Why it matters

The refusal is safe (nothing false is logged) but the skill would have to log
the write as `none`, losing a true record. Rare: sessions usually stay at the
project root.

## Scope to decide

- Option A: also accept the git top level of the working directory (`git rev-parse --show-toplevel`, stdlib subprocess).
- OR Option B: add a `project_dir:` header line to the log entry, set by the skill, checked to be an ancestor of the cwd.
- OR Option C: leave it, and have SKILL.md say to `cd` back to the project root before logging.

No code change made by this ticket. It is an observation on the record.
