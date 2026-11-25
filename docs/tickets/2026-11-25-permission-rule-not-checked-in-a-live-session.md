# The doctor's `permission_rule` has not been checked in a logged-in Claude Code session

Status: CLOSED (2026-11-25), verified in the owner's live session · Priority: MEDIUM · Type: verification gap · Cost: one interactive run

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

## Update 2026-11-25: headless evidence (partial)

An independent end-to-end test at b93cbb9 resumed a headless turn with
`--settings` holding the middle-`*` rule against the checkout path. The
heredoc `check` and `log` calls ran with `permission_denials: []`; the control
turn without the rule was denied. This confirms point (1) in a headless
session for the checkout path. Still unverified: the real installed
plugin-cache path shape, the startup "allows any option at its *" row (2), and
`fetch` with a single-quoted argument (3). Evidence: session scratchpad
`e2e2/runs`, files tB1 to tB4.

## Resolution 2026-11-25: verified in a live session

Owner's clean install from the marketplace (plugin 0.1.0, user scope, cache
folder `~/.claude/plugins/cache/cast2skill/cast2skill/0.1.0/`). The rule with
the middle `*`, copied from doctor, was added through `/permissions` to user
settings, and the session restarted.
1. `check` (two drafts) and `log` ran in turns after the owner answered the
   picker and the write questions, with no permission prompt ("no prompts or
   anything"). Before the user's next message the skill's own
   `allowed-tools` covers these calls, so only these later turns prove the rule.
2. No startup warning about the rule.
3. `fetch` always runs in the first turn, where `allowed-tools` already
   covers it, so a single-quoted fetch argument never depends on the rule.

No code change made by this ticket.
