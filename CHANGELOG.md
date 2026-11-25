# Changelog

What users see in each release, newest first. Each bullet ends with the date
of the progress entry that holds the proof, so `grep '\[X.Y.Z\]'` across
`docs/PROGRESS.md` and this file returns a release and everything in it.

## [Unreleased]

### Added
- `/cast2skill:doctor`: reports what works on this machine (yt-dlp, ffmpeg, Apple Silicon, audio_transcriber, speaker labels) with one fix per failed check (2026-11-11)
- `fetch` for pasted text, text and subtitle files, local audio, and YouTube (human captions first, then local transcription, then auto captions; `--fast` for captions only) (2026-11-11)
- `fetch` for podcasts: Apple Podcasts and Spotify episode links resolved to the show's public RSS feed, RSS feed URLs with episode matching, and direct audio URLs (2026-11-11)
- `/cast2skill:learn`: proposes at most five grounded lessons (zero is a valid answer), lets you pick, shows each skill, rule or note before writing it, and logs every decision; transcripts are treated as untrusted data and a safety check blocks lessons that would run commands, fetch URLs, change permissions or hide anything (2026-11-11)
- `/cast2skill:learn <source> --dry-run`: shows every candidate drafted with its destination and exact content or diff, after the safety check, and writes nothing to your skills, CLAUDE.md files or notes; logged as `dry_run` (2026-11-25)
- The candidate list ends with a "Left out" line naming what was dropped and why (2026-11-25)
- `/cast2skill:doctor` shows the one permission rule that stops the learn skill's script calls from asking again after you pick lessons, and whether your settings already have it; README has a "Fewer permission prompts" section. Doctor never edits your settings (2026-11-25)

### Changed
- `/cast2skill:learn` logs right after the last write attempt instead of waiting for you, names only files it actually wrote in the closing summary, and checks for an existing skill with its Read tool so no extra permission prompt appears (2026-11-25)
- Lessons are compared with every skill in your context (user, project, plugin and built-in), not only user and project skills (2026-11-25)
- The rubric's example of a specific lesson is no longer about test-first, so it no longer suggests that lesson (2026-11-25)

### Fixed
- The lessons log no longer records a file as written unless it exists where cast2skill writes; a blocked or declined write is logged as picked and not written, and a refused entry writes nothing (2026-11-25)
- Every run leaves a line in `lessons.jsonl`, including runs with nothing worth adding, and every line records the run's outcome (2026-11-25)
- Skill Source lines, rule comments and notes name the episode or video, not the lesson; the file written is exactly the one you approved; drafts stay in the chat; lesson cards keep the timestamp on the Evidence line (2026-11-25)
- Share-tracking parameters (`si`, `feature`, `utm_*`, `fbclid`, `gclid`, `igshid`, `igsh`) are removed from source URLs before anything is saved, so a Spotify or YouTube share token no longer reaches the library, the lessons log, Source lines or CLAUDE.md comments (2026-11-25)
- The safety check no longer refuses ordinary sentences with "make" or "eval" ("Make sure...", "make them pass", "write an eval"); `make install`, `$ make -j8` and `eval "$(...)"` are still refused (2026-11-25)
