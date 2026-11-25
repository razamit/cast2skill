# Learn writes a mid-run status line in the source's language, not the user's

Status: OPEN · Priority: LOW · Type: UX (language) · Cost: none

> Found in the owner's clean-install test from the marketplace (0.1.0),
> 2026-11-25.

## Symptom

On a Hebrew YouTube video (OC0_m6x1nf0, `--dry-run`), the model's progress
line after fetch was in Hebrew ("הסרטון ... נשלף כתמליל של כ-3,588 מילים ...
אני ממשיך לעבד אותו."), while the user wrote in English and the final
summary was in English.

## Evidence

Owner's pasted session output, installed plugin 0.1.0 from
`razamit/cast2skill`, model as set in that session. SKILL.md has no rule on
the language of messages to the user.

## Why it matters

Mixed-language output reads as a glitch, and right-to-left text in a
left-to-right terminal is hard to read. Lesson content quoting the source
should keep the source's words; everything said to the user should not.

## Scope to decide

- Add one line to SKILL.md: talk to the user in the language they wrote in;
  quotes stay in the source language.
- OR also translate quotes in the Evidence line, keeping the original beside it.

No code change made by this ticket. It is an observation on the record.
