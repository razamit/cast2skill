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
