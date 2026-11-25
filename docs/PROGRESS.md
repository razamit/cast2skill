# Implementation Progress

Newest entry first. One entry per completed unit of work: dated headline,
scope note, status marker (✅ DONE / 🟡 PARTIAL / ⛔ NOT STARTED), proof,
files touched, cross-refs to decisions and tickets. Never rewrite old entries.

---

**2026-11-25: Release 0.1.0: first release; fetch for text, YouTube and podcasts, the learn and doctor skills, `--dry-run` (release, changelog + registry). ✅ DONE**
Carriers before/after: `.claude-plugin/plugin.json` 0.1.0 → 0.1.0 (set at M2,
never released before; decision row 5). `marketplace.json` carries no version.
`grep -n '"version"' .claude-plugin/*.json` shows 0.1.0 in plugin.json only.
Section `## [0.1.0] - 2026-11-25`: bullets from 10 stamped entries (2026-11-25
x5, 2026-11-11 M2 to M6); one bullet added for M6 (install from the
marketplace), which had none. Backfilled stamps: 0.
Tests: 131 OK; `claude plugin validate --strict .` passes (ICON_MISSING warning).
Not yet published: no git remote, so the README install command does not work
until the repo is pushed; audio needs audio_transcriber's `cli-flags` branch
on its public `main`. Tag: v0.1.0 → 337bd80.
Files: CHANGELOG.md, docs/PROGRESS.md, docs/RELEASES.md.


**2026-11-25: learn skill reads the setup with Read; a flagged draft changes meaning or becomes a note (skill text, `check` verdict string, one contract test; two headless Haiku runs, about $0.04). ✅ DONE [0.1.0]**
Scope: ticket `2026-11-25-learn-setup-reads-and-check-rewording.md`.
1. Step 3: "Use the Read tool for every file here. Never use Bash (`ls`,
   `cat`, `grep`)"; each CLAUDE.md is read whole, a missing one is fine;
   skill folders are not listed (names come from context). `allowed-tools`
   unchanged, no Glob or Grep (decision 40).
2. Step 7.3: "Never reword a flagged draft to pass: a synonym or a new
   phrasing with the same meaning is the same lesson." Not essential: remove
   that idea (not just its words), tell the user, check again. Essential: note
   with the source quote only (decision 39, supersedes row 24's "one rewrite"
   clause). Replaces "rewrite it without the flagged parts".
Proof:
```
$ python3 -m unittest discover -b -s tests -t .
Ran 131 tests in 0.955s
OK
$ claude plugin validate --strict .   (Claude Code 2.1.332)
✔ Validation passed   (exit 0, known ICON_MISSING directory warning)
```
New test `test_setup_reads_use_read_and_flags_change_meaning`. Two headless
`--dry-run` runs through the real skill (`claude -p --plugin-dir . --model
haiku --no-session-persistence`, pasted text, scratch `CAST2SKILL_HOME` and
project in the session scratchpad, writes to `~/.claude` and `~/.cast2skill`
disallowed; the real `~/.claude/CLAUDE.md` was read, nothing written there):
- `d1` (69 s, $0.020): setup read with Read only (`~/.claude/CLAUDE.md`,
  project `CLAUDE.md`, missing `.claude/CLAUDE.md`), `permission_denials: []`.
  A rule draft was flagged `contact: message`; the model removed the clause
  "in the message", told the user what it removed, re-checked (ok). No
  synonym swap. 3 candidates logged `dry_run`.
- `d2` (56 s, $0.018): a "permissions allow list" lesson went straight to a
  note quoting the speaker ("Not applied: it changes permissions"); one rule
  passed `check`. Setup read with Read only, `permission_denials: []`.
Not observed: a flag on an essential part going through `check` and then
being turned into a note; in `d2` the model applied safety rule 2 before
drafting a rule, so that branch of 7.3 ran in neither run.
Ticket filed and closed in the same unit: `2026-11-25-check-verdict-says-remove-the-flagged-parts.md`.
`check`'s verdict now says "remove that idea (not a reworded copy of it) and
check again" instead of "remove them and check again" (`lesson_check.py:96`);
131 tests OK after the change. No model run was redone for this string.
Files: `skills/learn/SKILL.md` (164 lines, was 158),
`skills/learn/scripts/cast2skill_core/lesson_check.py`,
`tests/test_learn_safety_and_log.py`, `docs/DECISIONS.md` (rows 39, 40),
`docs/PROGRESS.md`, `CHANGELOG.md`, the closed ticket and the new one.

**2026-11-25: README says lesson quality depends on the session model; case 2 (captionless Hebrew YouTube) passes. ✅ DONE [0.1.0]**
Scope: owner chose option B (decision 38): the skill does not set a model;
README "How lessons are chosen" says a stronger model gives better candidates
and suggests `/model`. Its "Specific" example now matches the rubric (no
longer test-first).
Proof, manual case 2 through the real skill, headless, `--dry-run`, Haiku 5.5
(the session default), scratch home and project:
```
video F0wjoK584JU (Hebrew, 2291 s): manual subtitles: none, auto: iw, iw-orig
fetch: transcript_source local_whisper, words 6366, warnings []
whole run 358 s, cost $0.023, 2 candidates (1 rule, 1 idea), Left out line,
nothing written to the setup, both candidates logged as dry_run
```
Earlier the same day a captioned video (OC0_m6x1nf0, finance) took the
manual-captions route in 20 s and gave a correct "nothing worth adding".
Ticket filed: `2026-11-25-learn-setup-reads-and-check-rewording.md` (step 3
tried Bash reads of ~/.claude and was denied; a flagged draft passed `check`
after a one-word synonym swap).
Files: README.md, docs/DECISIONS.md, docs/PROGRESS.md, CHANGELOG.md, one ticket.

**2026-11-25: learn skill wording: log in the same turn, summary names written files, slug check via Read. ✅ DONE: skill text only, no model run redone for this wording. [0.1.0]**
Scope: three wording fixes from the independent end-to-end run at b93cbb9
(runs tB1 to tB4 in the session scratchpad, `e2e2/runs`).
1. After the last write attempt (written, declined or failed), go to step 8 in
   the same turn; a run that stops after writing still leaves a log row.
2. Closing summary names the files actually written in step 7 plus the log
   files from `files_written`, never a file whose write failed (`log`'s
   `files_written` lists only the log files).
3. Slug existence is checked with the Read tool, not Bash `ls` or `cat`.
Proof (unit tests only; no model run was redone for this wording):
```
Ran 130 tests in 0.952s

OK
(claude plugin validate --strict .: Validation passed)
```
Tickets: filed `2026-11-25-heredoc-delimiter-suffixes-look-alike.md` and
`2026-11-25-doctor-home-check-touches-the-folder.md`; updated
`2026-11-25-permission-rule-not-checked-in-a-live-session.md` with headless
evidence (rule verified for the checkout path, not the installed-cache path).
Files: skills/learn/SKILL.md, docs/PROGRESS.md, CHANGELOG.md, three tickets.

**2026-11-25: fixes from the independent end-to-end run: `log` checks `written_to`, every run leaves a jsonl row, skill text fixes, permission rule in doctor. ✅ DONE: all nine items built and tested at script level; the new skill wording and the permission rule have not been run in a live session. [0.1.0]**
Scope: fixes from an independent end-to-end run through the real skill
(evidence in the session scratchpad, `e2e/runs/` and `e2e/home/lessons.jsonl`).
Key failure: a skill write was blocked by Claude Code's `.claude/`
protection, yet the model logged `written_to: .../red-green-tdd/SKILL.md`
(no such file) and then appended a fake "(correction)" candidate.
1. `log` refuses a `written_to` that does not exist, lies outside the allowed
   places (user config `skills/` and `CLAUDE.md`, the working directory's
   `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/skills/`, the notes file), or
   belongs to a candidate that was not picked; symlinks and `..` resolved on
   both sides; `$CLAUDE_CONFIG_DIR` honoured; nothing written when any
   candidate is refused (decision 34).
2. Every jsonl row stores `outcome`; a run with no candidates writes one
   run-level row with the candidate fields null (decision 35).
3 to 8. SKILL.md: read writing.md before drafting (dry run too); provenance
   uses the fetch result's `title`; write exactly what was shown, re-ask on
   any change; drafts in chat only; fresh heredoc suffix every time, literal
   `q7Rk2mXa` example removed; card timestamp in the Evidence line; a failed
   write is told and logged as picked with `written_to: none`. Safety rule 4
   now lists the exact files. writing.md uses `<source title>` (decision 37).
   SKILL.md is 158 lines (was 155).
9. Doctor reports `permission_rule`, `permission_rule_this_version`,
   `permission_rule_in_settings` (read-only look at `permissions.allow` in
   the user settings) and `user_settings_file`; doctor SKILL.md tells the
   user how to add it and never adds it; README "Fewer permission prompts"
   section (decision 36). Rule syntax checked against
   https://code.claude.com/docs/en/permissions.md#wildcard-patterns ("A `*`
   can go anywhere in the rule"), protected paths against
   https://code.claude.com/docs/en/permission-modes.md#protected-paths, and
   the one-turn `allowed-tools` grant against
   https://code.claude.com/docs/en/skills.md#pre-approve-tools-for-a-skill.

Proof: before, at 4003a1e: `python3 -m unittest discover -b -s tests -t .`
→ `Ran 112 tests ... OK`; the e2e log entry (picked, `written_to` a missing
`.claude/skills/red-green-tdd/SKILL.md`) through `log` → exit 0,
`{"logged": 1, "outcome": "written", ...}`. The new test files run against
4003a1e in a scratch worktree → `Ran 126 tests`, `FAILED (failures=16,
errors=9)`. After: the same suite → `Ran 130 tests in 0.903s OK`; the same
entry → exit 1, `{"error": {"code": "bad_log_entry", "message": "written_to
<path> does not exist: Red-green TDD with locked tests", "hint": "Log only
files that were actually written; use written_to: none for a write that
failed or was declined."}}`, no `lessons.jsonl` created; a
`nothing_worth_adding` run → one row `{"title": null, ..., "reason": "An ad,
no method.", "outcome": "nothing_worth_adding", ...}`. Doctor from this
checkout → `permission_rule` `Bash(python3 ~/Projects/Utilities/cast2skill/skills/learn/scripts/cast2skill.py *)`,
`permission_rule_in_settings: false`. `claude plugin validate --strict .`
(Claude Code 2.1.332) → "✔ Validation passed", exit 0, with the known
ICON_MISSING directory warning. New tests: `tests/test_log_records.py`
(`WrittenToTests` 9, `OutcomeRowTests` 3), `PermissionRuleTests` (4), two
SKILL.md/writing.md contract tests; existing log tests now use real files in
a temp `CLAUDE_CONFIG_DIR`, which every test now gets.
Not verified: a model following the new SKILL.md lines; whether the
permission rule approves the heredoc `check`/`log` calls and whether Claude
Code warns about its middle `*` (an isolated config dir is not logged in;
ticket filed).
Files: `skills/learn/SKILL.md`, `skills/learn/reference/writing.md`,
`skills/doctor/SKILL.md`,
`cast2skill_core/{written_paths (new),permission_rule (new),lessons_log,doctor}.py`,
`tests/{test_log_records (new),support,test_learn_safety_and_log,test_setup_commands}.py`,
`README.md`, `CHANGELOG.md`, `docs/DECISIONS.md`, four new tickets
(`2026-11-25-log-project-paths-follow-the-working-directory.md`,
`2026-11-25-log-accepts-outcome-written-when-nothing-was-written.md`,
`2026-11-25-skill-commands-break-on-paths-with-spaces.md`,
`2026-11-25-permission-rule-not-checked-in-a-live-session.md`), this file.
Refs: decisions 34 to 37. Release: canonical 0.1.0 in
`.claude-plugin/plugin.json`, no tags, no drift; entries since the initial
build remain unreleased.

---

**2026-11-25: dry-run follow-ups: `--dry-run`, tracking parameters stripped, `check` and `make`, skill comparison, "Left out" line, rubric example. ✅ DONE: all six items built and tested; the new skill wording has not been run end to end by a model yet. [0.1.0]**
Scope: six fixes from the owner's dry run of `/cast2skill:learn` on a Spotify
episode ("73 - Harness Engineering").
1. Share-tracking parameters (`si`, `feature`, `utm_*`, `fbclid`, `gclid`,
   `igshid`, `igsh`) are stripped in `classify` before any route runs, and
   again in `save_result`, reuse and `log` for entries saved earlier
   (decision 31). Apple `i`, YouTube `v`/`t`/`list` and other parameters stay.
2. `check` flags `make` and `eval` only in a command shape; `exec` and `nc`
   stay bare (decision 32). Ticket `2026-11-25-check-flags-the-word-make.md`
   closed.
3. Step 3 compares candidates with every skill listed in context (user,
   project, plugin, built-in), still without opening skill bodies.
4. Step 5 ends with one "Left out:" line (dropped candidates, a few words
   each). Display only, not logged: the log has no cheap place for candidates
   that were never shown as cards.
5. Rubric and writing.md examples moved from test-first to naming functions
   (decision 33).
6. `--dry-run` (owner approved Option A, decision 30): SKILL.md argument-hint,
   a short intro paragraph and one "Dry run" line in steps 5 to 8; the skill
   strips the flag before `fetch`, and `fetch` rejects it with a hint naming
   `/cast2skill:learn`. `log` accepts `dry_run` as outcome and decision (JSON
   and plain formats); the two never mix with picked/rejected. README
   paragraph added. SKILL.md is 155 lines (was 142).

Proof: before, at b49a38c in a scratch worktree:
`python3 -m unittest discover -b -s tests -t .` → `Ran 97 tests ... OK`, and
`printf -- '- Make sure the agent shows its work.\n' | python3 skills/learn/scripts/cast2skill.py check`
→ `{"ok": false, "flags": [{"rule": "shell_command", "match": "Make"}], ...}`.
After: the same suite → `Ran 112 tests in 1.214s OK`; the same `check` →
`{"ok": true, "flags": [], "verdict": "no flags; the safety rules still apply"}`;
`fetch 'hello there' --dry-run` → exit 2, `bad_arguments` with the
`/cast2skill:learn` hint, no library folder created;
`claude plugin validate --strict .` (Claude Code 2.1.332) → "✔ Validation
passed", exit 0, with one plugin directory warning (ICON_MISSING), filed as a
ticket. New tests: `TrackingParameterTests` (3), Spotify token never stored
and reuse with/without it, audio URL reuse with/without `utm_source`, old
entry reused with a clean URL, everyday `make`/`eval` pass, command-shape
`make`/`eval`/`exec`/`nc` flagged, `dry_run` log in both formats, no mixing,
`log` cleans an old `source_url`, fetch refuses `--dry-run`, SKILL.md dry-run
contract, setup comparison and "Left out", rubric example not about testing.
Not verified: a model following the new dry-run lines interactively or
headless; known `check` gap "make test and restart" passes (decision 32).
Files: `skills/learn/SKILL.md`, `skills/learn/reference/{rubric,writing}.md`,
`skills/learn/scripts/cast2skill.py`,
`cast2skill_core/{url_cleaning (new),classify,fetch_context,lessons_log,lesson_check}.py`,
`tests/{test_classify_language_subtitles,test_podcasts,test_learn_safety_and_log}.py`,
`README.md`, `CHANGELOG.md`, `docs/DECISIONS.md`,
`docs/tickets/2026-11-25-check-flags-the-word-make.md` (closed),
`docs/tickets/2026-11-25-plugin-has-no-directory-icon.md` (new), this file.
Refs: decisions 30 to 33.

---

**2026-11-11: M6, README, LICENSE, marketplace file, local install test, independent review and fixes. 🟡 PARTIAL: everything built and committed; waiting at GATE B for the owner's manual table. [0.1.0]**
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

**2026-11-11: M5, `learn` skill, rubric, writing rules, `log` and `check`. 🟡 PARTIAL: manual cases 8 and 9 pass headless; 10 not run. [0.1.0]**
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

**2026-11-11: M4, `fetch` for podcasts (Apple, Spotify to RSS, RSS, direct audio). ✅ DONE. [0.1.0]**
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

**2026-11-11: M3, `fetch` for text, local audio and YouTube. ✅ DONE. [0.1.0]**
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

**2026-11-11: M2, plugin scaffold, `plugin.json`, `doctor`, `config`, `transcribe`. ✅ DONE. [0.1.0]**
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
