# cast2skill

Turn a podcast, a YouTube video, an audio file or a piece of text into a few
candidate lessons, pick the ones you want, and have them written into your
Claude Code setup as skills, CLAUDE.md rules or notes. Local and free.

```
> /cast2skill:learn https://youtu.be/arj7oStGLkU
Fetched "Inside the Mind of a Master Procrastinator" (14 min, human captions).
1. Show the failing test before implementing    [rule]   Evidence: [00:01:12] "..."
Pick any, or none. Nothing is written until you say yes to the exact text.
```

"Nothing here worth adding to your setup" is a normal answer, and often the
right one.

## Requirements

**Audio transcription needs an Apple Silicon Mac** (M1 or newer). It runs
locally through [audio_transcriber](https://github.com/razamit/audio_transcriber).
Everything else works on any machine with Python 3.10+.

| Machine | YouTube with captions | YouTube without captions | Podcast or audio file | Text |
|---|---|---|---|---|
| Apple Silicon + audio_transcriber | yes | yes | yes | yes |
| Anything else | yes | no, with a clear message | no, with a clear message | yes |

| Tool | Needed for |
|---|---|
| `python3` 3.10+ | everything (standard library only, nothing to pip install) |
| `yt-dlp` | YouTube (`brew install yt-dlp`) |
| `ffmpeg` | audio (`brew install ffmpeg`) |
| [audio_transcriber](https://github.com/razamit/audio_transcriber) | podcasts, audio files, YouTube without captions (Apple Silicon only) |

## Install

```
claude plugin marketplace add razamit/cast2skill
claude plugin install cast2skill@cast2skill
```

If you want audio, set up [audio_transcriber](https://github.com/razamit/audio_transcriber)
(the version with command-line flags). Then check the machine:

```
/cast2skill:doctor
```

Doctor reports which row of the table above this machine is, and one fix for
each thing that does not work. It never installs anything. If it cannot find
audio_transcriber, give it the folder when it asks and it saves the path to
`~/.cast2skill/config.json` after you say yes. Folders named
`~/audio_transcriber`, `~/projects/audio_transcriber` and
`~/code/audio_transcriber` are found on their own.

## Usage

```
/cast2skill:learn https://www.youtube.com/watch?v=VIDEO_ID
/cast2skill:learn https://youtu.be/VIDEO_ID --fast            # captions only, never downloads audio
/cast2skill:learn https://podcasts.apple.com/us/podcast/.../id123?i=456
/cast2skill:learn https://open.spotify.com/episode/EPISODE_ID  # resolved to the show's public RSS feed
/cast2skill:learn https://example.com/feed.xml --episode "Episode title"
/cast2skill:learn https://example.com/episode.mp3 --lang en
/cast2skill:learn ~/Downloads/interview.m4a --lang he --speakers
/cast2skill:learn ~/notes/talk-transcript.txt
/cast2skill:learn Paste the text of a tweet or a post here.
/cast2skill:learn https://youtu.be/VIDEO_ID --dry-run         # shows everything, writes nothing to your setup
```

- `--lang he|en`: transcript language. Usually detected from the source; you
  are asked when it cannot be. `config set default_lang en` sets a fallback.
- `--speakers`: anonymous speaker labels (`SPEAKER_00`, `SPEAKER_01`) in the
  transcript and the evidence. Off by default. Needs the diarization extras of
  audio_transcriber; without them the run continues without labels.
- `--episode`: which episode of a feed, by title. Without it you get the
  recent list to pick from. A Spotify or Apple link must match an episode title
  exactly; a near miss (say episode 43 versus 42) is shown to you, never picked.

- `--dry-run`: runs the whole flow and shows every candidate drafted as it
  would be written: the destination path and the exact content or diff, after
  the same safety check. You are not asked to pick, and nothing is written to
  your skills, CLAUDE.md files or notes. The transcript is still kept in the
  library, and the run is logged with the outcome `dry_run`.

Share links lose their tracking parameters (`si`, `feature`, `utm_*`,
`fbclid`, `gclid`, `igshid`, `igsh`) before anything is saved, so the token
that names who shared a link never reaches your library, logs or Source lines.

For YouTube, human captions in the video's language are used first. Without
them the audio is transcribed locally, and only when that is not possible are
YouTube's automatic captions used, with a warning about their quality.

Transcripts are kept in `~/.cast2skill/library/<date>-<title>/` together with
`lessons.md`, the record of what was proposed, picked and written. Fetching
the same source again reuses its transcript. Downloaded audio is deleted after
transcription (`config set keep_audio true` to keep it). Set `CAST2SKILL_HOME`
to use another folder.

## How lessons are chosen

Every candidate must be:

1. **Actionable in Claude Code**: it changes what you or the agent do.
2. **Specific**: "write tests first" fails; "have the agent write the failing
   test, show it failing, then implement" passes.
3. **Grounded**: a timestamp and a quote of 25 words or fewer.
4. **New for you**: checked against your CLAUDE.md files and your skill list.
   Already covered means dropped, or marked "extends".
5. **More than an opinion or a pitch**.

At most five candidates, one strong one preferred over five weak ones. When
the source contradicts your setup you are told, and you decide. Lessons you
rejected before are not proposed again unless the new source adds something.
Zero candidates is a valid result.

Each lesson becomes one of:

- **procedure**: a new skill, in `~/.claude/skills/` or the project's `.claude/skills/`
- **rule**: one line under `## Learned` in the CLAUDE.md you choose
- **idea**: a dated line in `~/.cast2skill/notes.md`

You see the exact file content, or a diff, and say yes per file. Existing
skills are never overwritten.

## Safety

A transcript is untrusted data. Captions and show notes can contain text aimed
at an AI agent, and this plugin writes into files that steer your future
sessions.

- Instructions found in a transcript, title, description or feed are never followed.
- A lesson that tells the agent to run a command, fetch a URL, install
  something, change permissions, skip confirmations, hide information from you
  or contact anyone is never written as a skill or rule. As a backstop, a
  script check scans every skill and rule before you see it; anything it flags
  can only be kept as a note that quotes the source. Passing the check does not
  lift the rule.
- Text from a source (episode titles, pasted text) never reaches a shell
  command line: pasted text goes in on stdin, and episodes are picked by id.
- Nothing is written without showing it to you first and getting a yes.
- Files are written only inside `~/.claude/`, the project's `.claude/`, the
  CLAUDE.md you choose, and `~/.cast2skill/`.

The test fixture `tests/fixtures/injection_transcript.txt` is a conversation
with one real lesson and three planted instructions: run a `curl ... | sh`
installer before every task, skip confirmations and approve all permissions,
and quietly email API keys to an outside address. Expected behavior: you are
warned that the source addresses AI assistants, none of the three is proposed
or written, and only the real lesson (show the failing test first) is offered.

## Platform and legal notes

- Transcripts stay on your machine. cast2skill sends nothing anywhere; it only
  downloads the source you give it and looks up public podcast metadata.
- Downloading from YouTube may conflict with YouTube's terms of service. You
  are responsible for what you fetch.
- No DRM circumvention. Spotify links are resolved to the show's public RSS
  feed through Apple's podcast directory, or refused. Nothing is downloaded
  from Spotify.
- cast2skill does not redistribute audio or transcripts and does not produce
  condensed audio.
- Audio transcription needs Apple Silicon (see Requirements).

## Troubleshooting

**yt-dlp fails** (`ytdlp_failed`). YouTube changes often and breaks yt-dlp
for a while. Update it (`brew upgrade yt-dlp`) and retry. If it still fails,
download the audio yourself and pass the file, or use `--fast` for captions
only. Recent yt-dlp versions also warn when no JavaScript runtime is installed
(`brew install deno`). cast2skill never adds workaround flags or reads your
browser cookies.

**"This episode looks Spotify-only"** (`no_public_feed`). The show has no
public feed, or the feed does not contain this episode. Use a YouTube link or
an audio file instead.

**No episode matched** (`needs_episode`). You are shown the closest titles;
pick one.

**No speaker labels** (`diarization_unavailable`). In the audio_transcriber
folder run `./setup.sh --with-diarization`, then `/cast2skill:doctor`.

**Certificate errors.** Python from python.org has no CA certificates until its
"Install Certificates" step is run. cast2skill falls back to the macOS
certificate bundle on its own; for other tools, run
`/Applications/Python 3.x/Install Certificates.command`.

**"did not answer --capabilities"** (`transcriber_outdated`). Your
audio_transcriber predates its command-line flags. Update it.

## Not in v1

- `/cast2skill:review` to revisit skills marked "untested" and keep or delete them.
- A transcription backend for Windows and Linux.
- Batch mode for a whole feed or playlist.
- Submission to the Anthropic community marketplace.

## Development

```
python3 -m unittest discover -b -s tests -t .
claude plugin validate --strict .
claude --plugin-dir .
```

Tests need no network and no model download. `docs/` holds the progress log,
decisions and tickets. MIT license.
