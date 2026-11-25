# Skill command lines put `${CLAUDE_SKILL_DIR}` unquoted, so an install path with a space would split the command

Status: OPEN · Priority: LOW · Type: robustness · Cost: none

> Noticed while writing the permission rule (decision 36), which embeds the
> same path. Not reproduced.

## Symptom

`skills/learn/SKILL.md` runs `python3 ${CLAUDE_SKILL_DIR}/scripts/cast2skill.py ...`
and `skills/doctor/SKILL.md` runs `python3 ${CLAUDE_PLUGIN_ROOT}/skills/learn/scripts/cast2skill.py ...`,
both unquoted. If the substituted path holds a space (a home folder such as
`/Users/Jane Doe`, or a `CLAUDE_CONFIG_DIR` with a space), the shell splits it
and python3 gets a wrong path. `permission_rule` from doctor would hold the
same unquoted path.

## Evidence

```
$ grep -n 'python3 \${CLAUDE' skills/learn/SKILL.md skills/doctor/SKILL.md
```

Whether Claude Code quotes the substituted value is not checked; the skills
docs describe the substitution as literal text.

## Why it matters

Every script call would fail for such a user, with a Python "can't open file"
error rather than cast2skill's JSON. macOS account names with spaces are
uncommon but exist.

## Scope to decide

- Option A: quote the path in every command (`python3 "${CLAUDE_SKILL_DIR}/scripts/cast2skill.py"`), then recheck the `allowed-tools` pattern and `permission_rule` still match the quoted form.
- OR Option B: document the limit in README.

No code change made by this ticket. It is an observation on the record.
