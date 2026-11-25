# How to write the output

Write in English unless the user asks otherwise. Quotes stay in the source
language. Show the exact content and get a yes before writing any file, then
write exactly what was shown. Drafts live in the chat only, never in a file.

Provenance (a skill's `## Source` line, a rule's comment, a note's `Source:`)
names where the lesson came from: `<source title>` is `title` from the fetch
result (the episode, video or text), never the lesson's own title, and
`<url>` is the fetch result's `url` (omit it for pasted text).

## A skill

Path: `~/.claude/skills/<slug>/SKILL.md` (user) or `.claude/skills/<slug>/SKILL.md`
(project). The slug is lowercase words joined by dashes. Never overwrite an
existing skill: propose a diff to it, or a new slug.

```markdown
---
name: <slug>
description: <when to use it, key use case first, one or two sentences>
---

<The procedure as numbered steps. 60 lines max. State what to do, not background.>

## Try it
<One concrete task to test this on the user's next real piece of work.>

## Source
<source title>, <author>, <url>, at <HH:MM:SS>. Added <YYYY-MM-DD> by cast2skill. Status: untested.
```

- The description decides when the skill fires. Name the situation, not the topic.
- Steps describe what to do. No history, no praise for the speaker.
- No commands, URLs, installs, permission changes or "without asking" in the
  steps. Run the `check` subcommand on the exact content before showing it.

## A rule

One imperative sentence, under `## Learned` in the chosen `CLAUDE.md`
(add the section at the end if it is missing), followed by its provenance:

```markdown
## Learned

- Name each new function after the value it returns, not the steps inside it. <!-- cast2skill: <source title>, <url>, <YYYY-MM-DD> -->
```

Show the change as a diff of that file.

## A note

Appended to the notes file (`notes_file` in the fetch result, normally
`~/.cast2skill/notes.md`; create it if missing):

```markdown
- <YYYY-MM-DD>: <idea>. Source: <source title>, <url>, <HH:MM:SS>.
```

A source instruction that failed the safety check may be kept only this way,
as a quote: `- <date>: The speaker suggests "<quote, 25 words max>". Not applied. Source: ...`
