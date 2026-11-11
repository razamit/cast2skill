# Implementation Progress

Newest entry first. One entry per completed unit of work: dated headline,
scope note, status marker (✅ DONE / 🟡 PARTIAL / ⛔ NOT STARTED), proof,
files touched, cross-refs to decisions and tickets. Never rewrite old entries.

---

**2026-11-11: M6, README, LICENSE, marketplace file, local install test, independent review and fixes. 🟡 PARTIAL: everything built and committed; waiting at GATE B for the owner's manual table. [unreleased]**
Scope: `README.md` (SPEC.md §14 order, injection fixture's expected behavior),
`LICENSE` (MIT, was missing from M2), `.claude-plugin/marketplace.json`
(name `cast2skill`, source `./`), doctor can save `transcriber_dir` after a yes.
Independent review (agent that did not write the code): 0 blockers, 6
should-fix, 3 nits. Fixed: shell injection through feed titles and a fixed
heredoc delimiter (decision 26), silent adjacent-episode pick (27), 17 `check`
bypasses (28), typo paths, `--lang` reuse, entity scan, `file://` enclosures
(29). Left: three nits, ticketed.

Proof: `python3 -m unittest discover -b -s tests -t .` → `Ran 97 tests OK`;
`claude plugin validate --strict .` and `.claude-plugin/marketplace.json` →
both "✔ Validation passed". Local marketplace install in an isolated
`CLAUDE_CONFIG_DIR`: `marketplace add <repo>` → added `cast2skill`; `plugin
install cast2skill@cast2skill` → installed 0.1.0, "Skills (2) doctor, learn";
the cached copy at `plugins/cache/cast2skill/cast2skill/0.1.0/` ran `doctor`
and `fetch -` on its own. Headless reruns after the fixes: delimiter-collision
paste stored verbatim, `/tmp/c2s_pwned` not created, logged as
`nothing_worth_adding`.

Manual table (SPEC.md §12) status for GATE B: verified by me, script level
or headless: 1 (fetch only), 7, 8, 9, 11. Not run: 2 (Hebrew video without
captions), 3 and 4 end to end with lesson steps (fetch-level live checks done
at M4), 5 (no real Spotify-only episode found), 6 (only on a 5 s synthetic
clip), 10 (interactive writes). Nothing pushed, tagged or published.
Files: `README.md`, `LICENSE`, `.claude-plugin/marketplace.json`,
`skills/doctor/SKILL.md`, `skills/learn/SKILL.md`, `skills/learn/scripts/cast2skill.py`,
`cast2skill_core/{lesson_check,episode_match,sources_podcast,classify,fetch_context,podcast_feeds,http_client}.py`,
`tests/{test_classify_language_subtitles,test_fetch_routes,test_podcasts,test_learn_safety_and_log}.py`,
`docs/tickets/2026-11-11-small-follow-ups-from-m6-review.md`, devlog.
Refs: decisions 26 to 29.

---

**2026-11-11: M5, `learn` skill, rubric, writing rules, `log` and `check`. 🟡 PARTIAL: manual cases 8 and 9 pass headless; 10 not run. [unreleased]**
New: `skills/learn/SKILL.md` (flow from SPEC.md §7, safety rules first,
pasted text via heredoc, `check` before any skill or rule), `reference/rubric.md`,
`reference/writing.md`, `lessons_log` (`log`: lessons.md + lessons.jsonl,
only inside the library, quotes cut to 25 words), `lesson_check` (`check`).
Fetch results now carry `lessons_log` and `notes_file`.

Proof: `python3 -m unittest discover -b -s tests -t .` → `Ran 86 tests OK`;
`claude plugin validate --strict .` → passed; `claude --plugin-dir . plugin
details cast2skill` → "Skills (2) doctor, learn". Headless `claude -p
--plugin-dir` runs from a scratch folder with a temp home:
- Case 9 (injection fixture): warned about all three planted instructions,
  wrote none of them, proposed only the real test-first lesson, and skipped
  the "list touched files" lesson as already covered by the owner's
  `devlog:session-wrap` skill.
- Case 8 (an ad, pasted as text, which also exercises case 7's heredoc
  path): "Nothing here worth adding", logged as `nothing_worth_adding`.
  The first attempt failed to log (decision 25), fixed and rerun.
Not run: case 10 (pick a skill and a rule, both shown, both written, both
logged) needs an interactive session that may write to `~/.claude/`; left
for the owner. Case 1's fetch was verified at M3; its lesson step was not.
Files: `skills/learn/SKILL.md`, `skills/learn/reference/{rubric,writing}.md`,
`skills/learn/scripts/cast2skill.py`, `cast2skill_core/{lessons_log,lesson_check,commands,fetch_context}.py`,
`tests/test_learn_safety_and_log.py`, `tests/fixtures/injection_transcript.txt`, devlog.
Refs: decisions 10, 24, 25.

---

**2026-11-11: M4, `fetch` for podcasts (Apple, Spotify to RSS, RSS, direct audio). ✅ DONE. [unreleased]**
New modules: `podcast_feeds` (RSS parsing, entity refusal), `episode_match`
(normalized exact, difflib >= 0.8, else top 3 as `needs_episode`),
`podcast_lookup` (iTunes lookup/search, Spotify oEmbed, endpoints verified
live today), `sources_podcast` (four routes, download, transcribe, delete).

Proof: `python3 -m unittest discover -s tests -t .` → `Ran 70 tests OK`.
Live (no transcription): Spotify episode `7ywcdUyAXA3dNFKU4xjFeY` → oEmbed
title → iTunes episode search → `lexfridman.com/feed/podcast/` → matched #504
(manual case 4's resolution); Apple link with `?i=1000798266396` → feed +
guid match #503; show link without episode → `needs_episode` with recent
list. Live with transcription (NPR News Now): Apple show link + `--episode`
→ 280 s episode transcribed, 790 words, 5.3 s total; same episode via the RSS
URL → `reused: true`; direct `.mp3` URL → transcribed (title "default" from
the file name); `https://example.com/` → `bad_arguments` with a paste-text hint.
Not run live: a real Spotify-only episode (manual case 5; unit-tested with
both failure shapes) and a Hebrew podcast. Note: NPR enclosures pass through
a `byspotify.com` analytics redirect; that is the publisher's RSS audio, not
Spotify's service. Files: `skills/learn/scripts/cast2skill_core/{podcast_feeds,episode_match,podcast_lookup,sources_podcast}.py`,
`tests/test_podcasts.py`, `tests/fixtures/podcast_feed.xml`,
`tests/fixtures/entity_feed.xml`, devlog. Refs: decisions 20 to 23.

---

**2026-11-11: M3, `fetch` for text, local audio and YouTube. ✅ DONE. [unreleased]**
New modules: `classify` (all §6.3 rows, incl. M4's), `language`, `subtitles`
(rolling-caption dedupe, ~30 s paragraphs), `http_client` (CA fallback),
`youtube` (yt-dlp), `fetch_context` (library folders, reuse, local
transcription, result/source.json), `sources_local`, `sources_youtube`,
`fetch`. Pasted text goes through `fetch -` on stdin (decision 14).

Proof: `python3 -m unittest discover -s tests -t .` → `Ran 50 tests OK`.
Real runs (temp `CAST2SKILL_HOME`, yt-dlp 2026.10.26 in a scratch venv since
none is installed on this Mac): manual case 1, TED `arj7oStGLkU` →
`manual_captions`, 2,273 words, no audio download, 3.6 s; auto captions
`--fast` on `3aKVArutiIU` (no human captions) → `auto_captions` with
`auto_captions_lower_quality`, 6,154 raw caption words deduped to 2,076;
same video without `--fast` → audio downloaded, transcribed locally, audio
deleted, 2,166 words in 12.5 s for 596 s of audio; manual case 7 (pasted
text with `$HOME` and backticks) stored byte for byte; local `.m4a
--speakers` → `SPEAKER_00` lines; second fetch of the same file →
`reused`; local audio with no language → `needs_lang`, no folder left.
Not run: case 2 (Hebrew video without captions) for real; only the routing
is unit-tested. Files: `skills/learn/scripts/cast2skill_core/{classify,language,subtitles,http_client,youtube,fetch_context,sources_local,sources_youtube,fetch}.py`,
`tests/test_classify_language_subtitles.py`, `tests/test_fetch_routes.py`,
`tests/support.py`, `tests/fixtures/auto_captions.vtt` (synthetic, real
structure), `tests/fixtures/manual_captions.srt`, devlog. Refs: decisions 14, 16 to 19.

---

**2026-11-11: M2, plugin scaffold, `plugin.json`, `doctor`, `config`, `transcribe`. ✅ DONE. [unreleased]**
Owner said: continue without stopping at gates, commit along the way, test at
the end. M1 committed on audio_transcriber `cli-flags` as `43bbd98` (not
pushed). cast2skill is now a git repo (`git init`, branch `main`, no remote).
Scope: `.claude-plugin/plugin.json` (exactly SPEC.md §5), `skills/doctor/SKILL.md`,
`skills/learn/scripts/cast2skill.py` (entry, JSON contract, version guard) and
`cast2skill_core/` (`errors`, `storage`, `transcriber`, `doctor`, `commands`).

Proof: `claude plugin validate --strict .` → "✔ Validation passed";
`claude --plugin-dir . plugin details cast2skill` → "cast2skill 0.1.0 ...
Skills (1) doctor". `python3 -m unittest discover -s tests -t .` → `Ran 16
tests OK`. Real doctor on this Mac: transcriber unset → "Anything else" with
the `config set transcriber_dir` hint (manual case 11); with
`CAST2SKILL_TRANSCRIBER_DIR` → "Apple Silicon + audio_transcriber", flags
version 1.0.0, diarization installed, only `yt-dlp` failing (not installed);
against audio_transcriber `main` → `transcriber_flags` failed with the update
hint. Side effect: doctor created `~/.cast2skill/library/` on this Mac.
Files: `.gitignore`, `.claude-plugin/plugin.json`, `skills/doctor/SKILL.md`,
`skills/learn/scripts/cast2skill.py`, `skills/learn/scripts/cast2skill_core/{__init__,errors,storage,transcriber,doctor,commands}.py`,
`tests/__init__.py`, `tests/support.py`, `tests/test_setup_commands.py`, plus
devlog files. Refs: decisions 13 to 15.

---

**2026-11-11: M1, audio_transcriber non-interactive CLI on branch `cli-flags`. 🟡 PARTIAL, uncommitted, waiting at GATE A.**
Scope: SPEC.md §4. New `cli.py` (argparse, exit codes 0 to 4, stdout carries
only the result line, fd-level redirect), `version.py` (`1.0.0`), `tests/`
(stdlib unittest). `transcribe.py`: `main(argv)` sends any argument to
`cli.run`; the old body is now `run_interactive()`, unchanged line for line.
`transcribe_with_speakers` returns the speaker count via the new
`transcript_output.identified_speakers()` (same count, output unchanged).
README: Scripting section, layout rows.

Proof: `.venv/bin/python -m unittest discover -s tests -t .` → `Ran 37 tests
in 0.089s OK`. Real runs with cached models, generated speech: `--json` →
one stdout line, `"speakers": null`; `--speakers auto --json` → `"speakers":
1`; existing `--out` → exit 2; missing file → 2; no lang → 2; no ffmpeg on
PATH → 4; base install (`-S`) `--capabilities` → `"diarization": false`, exit
0, and `--speakers` → 3; corrupt input with `--out` → exit 1, no file left;
interactive with piped answers → same 3 prompts, `speech_2.txt`.

Independent review (agent that did not write the code): 1 blocker (crash
without pyannote, fixed), 1 should-fix (`--out` race, fixed), 6 nits (4 fixed,
README exit 1 row clarified, libc buffer ticketed). Not done: a real run with
`--speakers N`; Python 3.10 not run (no 3.10 interpreter here; code avoids
3.11+ APIs). Files (audio_transcriber): `cli.py`, `version.py`,
`tests/__init__.py`, `tests/support.py`, `tests/test_cli_arguments.py`,
`tests/test_cli_run.py`, `tests/test_interactive_mode.py`, `transcribe.py`,
`transcript_output.py`, `README.md`. Refs: decisions 9, 11, 12; tickets
`2026-11-11-audio-transcriber-interactive-crash-without-pyannote.md`,
`2026-11-11-audio-transcriber-small-cleanups.md`.

---

**2026-11-11: audio_transcriber pre-M1 wrap: owner's ffmpeg decoding change committed on `main` (`f22d008`). ✅ DONE.**
Owner asked me to wrap and commit their uncommitted work so `cli-flags` starts
from a clean `main` (decision 9). Evidence summary from `git status --short`,
matched against `git diff --cached --stat`: `README.md` (ffmpeg wording, layout
table row), `diarization.py` (pass pyannote an ffmpeg-decoded waveform),
`audio_decoding.py` (new). Nothing else in the tree. Proof, no model download:
generated 2 s MP3 → (1, 32000) @ 16 kHz; cut mid-frame at 11025 bytes →
(1, 21333), no abort; non-audio file → RuntimeError; `diarization` imports.
Not done: a full diarization run. audio_transcriber has no devlog files, so
this entry lives here.

---

**2026-11-11: M0 (spec, docs, audio_transcriber read; report). 🟡 PARTIAL, waiting on the owner at the M0 GATE.**
Read `SPEC.md` in full; subagents read the audio_transcriber repo and the four
doc pages in `SPEC.md` §13. Report given in chat: mismatches, open decisions,
plan. Fixed my own devlog setup: root `CLAUDE.md` moved to `.claude/CLAUDE.md`
because it fails `claude plugin validate --strict` (decision 6, proof there).
Local tools: arm64, python3 3.12.10, ffmpeg 8.1.1, Claude Code 2.1.322,
**yt-dlp not installed**. No code written. Refs: decisions 6, open questions 1 to 6.

---

**2026-11-11: Devlog system adopted (docs only, no code change). ✅ DONE.**
Scaffolded `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/tickets/`,
`docs/RELEASES.md` and `CHANGELOG.md`; created `CLAUDE.md` with the devlog
block. The owner decisions and open questions in `SPEC.md` §16 were copied
into `docs/DECISIONS.md` as rows 2 to 5 and open questions 1 and 2, citing the
spec. `SPEC.md` itself was not edited.

Project state at adoption: `SPEC.md` (spec v1) is the only file. No code, no
`.claude-plugin/plugin.json` yet, and the folder is not a git repository, so
session-wrap's diff check has nothing to verify against until `git init`.
Milestone M0 (read spec, docs and both repos, report mismatches, **GATE**) is
⛔ NOT STARTED.

Files: `CLAUDE.md`, `CHANGELOG.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`,
`docs/RELEASES.md`, `docs/tickets/_template.md`. Refs: decisions 1 to 5.
