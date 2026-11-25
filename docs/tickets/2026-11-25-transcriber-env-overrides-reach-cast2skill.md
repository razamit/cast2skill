# Two new audio_transcriber environment overrides pass through cast2skill unfiltered

Status: OPEN · Priority: LOW · Type: robustness · Cost: none

> Found by the same compatibility check of audio_transcriber `2cee45b`.
> Neither variable was set on the test machine; nothing broke.

## Symptom

cast2skill runs the transcriber with the caller's environment.
1. `TRANSCRIBE_BIDI=on` makes the transcriber write stderr in visual
   (reversed, wrapped) order. Transcript files and the stdout JSON are not
   affected, but the one stderr line cast2skill shows on a failure
   (`transcriber.py:104-106`, used at `:141`) can come out reversed.
2. `TRANSCRIBE_ENGINE` set to an unknown or missing engine makes a
   transcription exit 1 (cast2skill reports `TRANSCRIBER_FAILED` with the
   message), while `--capabilities` still exits 0 with `"engine": null`, so
   doctor passes.

## Evidence

Reviewer runs with a fake unimportable `bidi` package and `TRANSCRIBE_BIDI=on`:
exit 0, same transcript. Engine override read from `select_engine`, which
calls `sys.exit(msg)` on an unknown engine.

## Why it matters

Small. A user would only hit it by setting these variables themselves.

## Scope to decide

- Drop `TRANSCRIBE_BIDI` from the child environment, and have doctor fail
  when `--capabilities` reports `"engine": null`.
- OR leave both and mention them in the README troubleshooting section.

No code change made by this ticket. It is an observation on the record.
