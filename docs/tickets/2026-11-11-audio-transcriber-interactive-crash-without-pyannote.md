# audio_transcriber: answering "y" to speakers on a base install crashes with a traceback instead of printing the install help

Status: OPEN · Priority: MEDIUM · Type: bug (audio_transcriber, interactive mode) · Cost: none

> Found by the independent review at M1. Left unfixed on purpose: SPEC.md §4
> requires the no-args behavior to stay exactly as it is, and the fix changes
> it. Flag mode is already guarded (`cli.diarization_installed()`).

## Symptom

`diarization.diarization_is_available()` (`diarization.py:88-90`) calls
`importlib.util.find_spec("pyannote.audio")`. When the parent package
`pyannote` is not installed (the base `./setup.sh` install), `find_spec`
raises `ModuleNotFoundError` instead of returning None. In interactive mode,
answering `y` at "Label speakers?" therefore dies with a traceback, not the
intended `INSTALL_HELP` message.

## Evidence

```
$ .venv/bin/python -S transcribe.py --capabilities      # on cli-flags before the fix
  File ".../diarization.py", line 90, in diarization_is_available
    return importlib.util.find_spec("pyannote.audio") is not None
ModuleNotFoundError: No module named 'pyannote'
$ .venv/bin/python -c "import importlib.util; importlib.util.find_spec('nosuchpkg.audio')"
ModuleNotFoundError: No module named 'nosuchpkg'
```
(`-S` drops site-packages, which reproduces a venv without the extras.)

## Why it matters

The README promises that answering `y` without the extras "exits immediately
with the install command". Base-install users get a stack trace instead.
Owner's own venv has pyannote, so it never showed up there.

## Scope to decide

- Option A: catch `ImportError` inside `diarization_is_available()` and drop
  the cli-side wrapper. Changes interactive behavior (traceback becomes the
  help text), so it needs the owner's yes as a change to the no-args path.
- OR Option B: leave interactive mode as is.

No code change made by this ticket. It is an observation on the record.
