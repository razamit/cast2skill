# Local transcription is refused on any machine that is not Apple Silicon, though audio_transcriber now runs there

Status: OPEN · Priority: MEDIUM · Type: platform reach · Cost: none

> Found by the read-only compatibility check of audio_transcriber `2cee45b`
> (branch `cli-flags`) against cast2skill, 2026-11-25.

## Symptom

audio_transcriber `2cee45b` runs on Windows, Linux and Intel Macs through
faster-whisper (`engines/selection.choose_engine_key`; `requirements.txt`
installs mlx-whisper only on darwin/arm64). cast2skill still refuses local
transcription off Apple Silicon (`skills/learn/scripts/cast2skill_core/transcriber.py:39-47`,
`doctor.py:52-56`), and the README platform table says audio is Apple
Silicon only.

## Evidence

```
--capabilities at 2cee45b on this Mac:
{"diarization": true, "engine": "mlx", "languages": ["he", "en"], "version": "1.1.0"}
```

The new `engine` field tells cast2skill which engine would run. Nothing was
tested off Apple Silicon.

## Why it matters

Podcasts, audio files and captionless YouTube are unavailable to most users,
while the dependency can now serve them. Not a defect in 0.1.0: the README
states the limit honestly.

## Scope to decide

- Allow local transcription whenever `--capabilities` reports a non-null
  `engine`; update doctor, README table, and test on one Windows or Linux box.
- OR keep Apple Silicon only until faster-whisper output is checked for
  quality and speed (CPU transcription of a 1 hour podcast may be slow).

No code change made by this ticket. It is an observation on the record.
