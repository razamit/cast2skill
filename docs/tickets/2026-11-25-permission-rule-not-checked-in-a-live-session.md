# The doctor's `permission_rule` has not been checked in a logged-in Claude Code session

Status: OPEN · Priority: MEDIUM · Type: verification gap · Cost: one interactive run

> Follows decision 36. The rule's syntax is from the docs; its effect is not observed.

## Symptom

Three things are unverified: (1) that the rule
`Bash(python3 <home>/.claude/plugins/cache/cast2skill/cast2skill/*/skills/learn/scripts/cast2skill.py *)`
approves the `check` and `log` calls, which carry a heredoc on stdin;
(2) whether Claude Code shows the "allows any option at its *" startup row for
it; (3) that `fetch` with a single-quoted argument is approved too.

## Evidence

```
$ CLAUDE_CONFIG_DIR=<empty scratch dir> claude -p "reply ok" --settings '{"permissions":{"allow":["Bash(python3 /Users/u/.claude/plugins/cache/cast2skill/cast2skill/*/skills/learn/scripts/cast2skill.py *)"]}}'
Not logged in · Please run /login
```

The isolated config dir is not logged in, and the brief for this work forbade
touching `~/.claude`.

## Why it matters

README and doctor now tell users to add this rule. If it does not cover the
heredoc calls, the prompts it promises to remove remain.

## Scope to decide

- Option A: owner adds the rule from `/cast2skill:doctor` in a real session, runs `/cast2skill:learn` on short pasted text, picks a rule, and notes whether `check` and `log` prompt.
- OR Option B: a headless run with `--settings` and `--output-format stream-json` in a logged-in profile, reading the permission decisions from the stream.

No code change made by this ticket. It is an observation on the record.
