---
name: doctor
description: Check what cast2skill can do on this machine (yt-dlp, ffmpeg, Apple Silicon, audio_transcriber, speaker labels) and explain how to fix what is missing.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/learn/scripts/cast2skill.py doctor*)
---

# cast2skill doctor

Run this and read the JSON it prints. It only reports; it never installs anything.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/learn/scripts/cast2skill.py doctor
```

If the user named a transcriber folder in `$ARGUMENTS`, add `--transcriber-dir <that folder>`.

Then answer the user in their language, in this order:

1. One line: which row of the capability matrix this machine is (`machine`), and what that means:
   - `youtube_with_captions`, `youtube_without_captions`, `podcast_or_audio_file`, `text`, `speaker_labels`: say which work and which do not.
2. For every entry in `failed`: the check name, its `detail`, and its `hint` as the fix. Keep the hint's command exactly as given.
3. If `transcriber` failed because no folder was found or configured, tell the user the one command that fixes it:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/learn/scripts/cast2skill.py config set transcriber_dir /path/to/audio_transcriber`
4. If nothing failed, say everything works and suggest `/cast2skill:learn <a link or file>`.

Do not run any fix yourself. If the output is an `{"error": ...}` object instead, show its `message` and `hint`.
