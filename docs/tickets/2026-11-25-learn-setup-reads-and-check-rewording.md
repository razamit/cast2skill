# Learn skill: setup reads via Bash, and a flagged draft reworded with a synonym

Status: CLOSED (2026-11-25), fixed in the progress entry "2026-11-25: learn skill reads the setup with Read; a flagged draft changes meaning or becomes a note" (decision rows 39 and 40)
Found: 2026-11-25, headless dry run on a captionless Hebrew YouTube video (F0wjoK584JU), Haiku 5.5

## Symptom

1. In step 3 the model ran `ls ~/.claude/skills` and `grep "## Learned" ~/.claude/CLAUDE.md`
   through Bash. Both were denied (headless, outside the skill's allowed tools),
   so its "Versus your setup" rested only on the skill list in context and the
   CLAUDE.md it had read.
2. A rule draft about approving requests was flagged by `check` for the word
   "permission". The model replaced the word with "access request" and the
   check passed. The rule itself was harmless (ask before approving), but the
   pattern is swapping a synonym to get past the backstop, which SKILL.md does
   not forbid: it says "rewrite it without the flagged parts".

## Evidence

Run JSON `permission_denials` lists the two Bash calls. The final answer says:
"The first draft used the word "permission" and was flagged, so I reworded it."
Scratch run: `scratchpad/yt2/run.json` in session c238761a.

## Why it matters

1. Step 3 reads should not prompt or fail; Read is already allowed.
2. If synonyms pass, the check only catches vocabulary, not meaning. A harmful
   draft could be reworded the same way.

## Scope to decide

- Step 3: say "read them with the Read tool", as step 7 already does for slugs.
- Step 7: when `check` flags a draft, remove the flagged idea, not just the
  word; if the idea itself is the lesson, offer it as a note with the quote.
  Decide whether to tell the user what was flagged and how it was changed.

## Resolution (2026-11-25)

- Step 3 now says to use the Read tool for every setup file and never Bash
  (`ls`, `cat`, `grep`); skill names come from context, so skill folders are
  not listed. Glob and Grep were not added to `allowed-tools` (row 40).
- Step 7.3 now says never reword a flagged draft to pass; remove the flagged
  idea (not just its words) and tell the user what was removed, or, if the
  flagged part is essential, offer it only as a note with the source quote
  (row 39).
- Left open: the `check` script's own verdict text still says "remove them
  and check again", filed as
  `2026-11-25-check-verdict-says-remove-the-flagged-parts.md`.
