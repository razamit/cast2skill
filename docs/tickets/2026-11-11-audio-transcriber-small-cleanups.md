# audio_transcriber: stale references to the removed diarize.py, a duplicated line, and an unflushed libc buffer risk

Status: OPEN · Priority: LOW · Type: cleanup (audio_transcriber) · Cost: none

> Observed at M0/M1, outside SPEC.md §4 scope, so not touched on `cli-flags`.

## Symptom

1. `speaker_names.py:13` docstring and `requirements-diarize.txt:1` comment
   still mention `diarize.py`, which no longer exists. A stale
   `__pycache__/diarize.cpython-312.pyc` is left over (ignored by git).
2. `diarization.py`, in `load_diarization_pipeline`'s CPU fallback:
   `device = torch.device("cpu")` appears twice in a row.
3. `cli.stdout_to_stderr()` flushes Python's stdout and swaps fd 1, but does
   not flush the C library's `stdout` buffer. If native code `printf`s into a
   pipe without flushing, that text could reach the real stdout after fd 1 is
   restored. Not observed: the real-process test with Python- and fd-level
   noise passes, and real Whisper runs gave a single stdout line.

## Evidence

Reported by the M0 repo reader (1, 2) and the M1 independent reviewer (3,
"low confidence, not observed").

## Why it matters

1 and 2 are cosmetic. 3 would break the "stdout carries only the result line"
contract for cast2skill if a future native library prints to stdout.

## Scope to decide

- Fix 1 and 2 in a separate small commit on `main`.
- For 3: call `fflush(NULL)` via ctypes before restoring fd 1, or wait until
  it is observed.

No code change made by this ticket. It is an observation on the record.
