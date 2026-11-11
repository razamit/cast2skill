"""Finding and calling the owner's audio_transcriber through its flag mode.

audio_transcriber is a separate install with its own virtualenv. This module
never imports it; it runs `<dir>/.venv/bin/python <dir>/transcribe.py` with
flags, so a transcriber without those flags (an old checkout) is detected
rather than left waiting at an interactive prompt: stdin is always closed.
"""

import json
import os
import platform
import subprocess
import sys

from .errors import (
    FFMPEG_MISSING,
    FILE_NOT_FOUND,
    TRANSCRIBER_FAILED,
    TRANSCRIBER_MISSING,
    TRANSCRIBER_OUTDATED,
    TRANSCRIPTION_UNSUPPORTED,
    CastError,
)

ENV_VAR = "CAST2SKILL_TRANSCRIBER_DIR"
FALLBACK_DIRS = ("~/audio_transcriber", "~/projects/audio_transcriber", "~/code/audio_transcriber")
CAPABILITIES_TIMEOUT_S = 120
REPO_URL = "https://github.com/razamit/audio_transcriber"
OUTDATED_HINT = (
    "Update audio_transcriber to a version with command-line flags "
    "(`transcribe.py --capabilities` must work), then run /cast2skill:doctor."
)
SETUP_HINT = (
    f"Install audio_transcriber ({REPO_URL}), then point cast2skill at it: "
    "`cast2skill.py config set transcriber_dir /path/to/audio_transcriber`."
)


def is_apple_silicon():
    return sys.platform == "darwin" and platform.machine() == "arm64"


def candidate_dirs(explicit_dir, config):
    """(where it came from, path) in lookup order. Unset sources are skipped."""
    configured = [
        ("--transcriber-dir", explicit_dir),
        (ENV_VAR, os.environ.get(ENV_VAR)),
        ("config.json", config.get("transcriber_dir")),
    ]
    found = [(source, os.path.expanduser(path)) for source, path in configured if path]
    found += [("default location", os.path.expanduser(path)) for path in FALLBACK_DIRS]
    return found


def venv_python(directory):
    return os.path.join(directory, ".venv", "bin", "python")


def looks_like_transcriber(directory):
    return os.path.isfile(os.path.join(directory, "transcribe.py")) and \
        os.access(venv_python(directory), os.X_OK)


def locate(explicit_dir, config):
    """The transcriber folder, or raise TRANSCRIBER_MISSING listing what was tried.

    A folder named explicitly (flag, env or config) that is not a transcriber
    is an error rather than a reason to fall back: the user asked for that one.
    """
    tried = []
    for source, directory in candidate_dirs(explicit_dir, config):
        if looks_like_transcriber(directory):
            return {"dir": os.path.abspath(directory), "source": source}
        tried.append(f"{directory} ({source})")
        if source != "default location":
            raise CastError(TRANSCRIBER_MISSING,
                            f"No audio_transcriber with a .venv at {directory} (from {source}).",
                            SETUP_HINT, tried=tried)
    raise CastError(TRANSCRIBER_MISSING, "audio_transcriber was not found.", SETUP_HINT, tried=tried)


def run_transcriber(directory, flags, timeout=None):
    """Run transcribe.py with flags; never interactive. Returns CompletedProcess."""
    command = [venv_python(directory), os.path.join(directory, "transcribe.py")] + flags
    return subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=timeout)


def last_json_line(stdout):
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON line on stdout")


def last_error_line(stderr):
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    return lines[-1] if lines else "no error output"


def capabilities(directory):
    """`transcribe.py --capabilities` as a dict, or TRANSCRIBER_OUTDATED."""
    try:
        completed = run_transcriber(directory, ["--capabilities"], CAPABILITIES_TIMEOUT_S)
        if completed.returncode == 0:
            return last_json_line(completed.stdout)
        detail = last_error_line(completed.stderr)
    except subprocess.TimeoutExpired:
        detail = f"no answer within {CAPABILITIES_TIMEOUT_S}s"
    except (OSError, ValueError) as exc:
        detail = str(exc)
    raise CastError(TRANSCRIBER_OUTDATED,
                    f"audio_transcriber at {directory} did not answer --capabilities ({detail}).",
                    OUTDATED_HINT)


def transcribe(directory, audio_path, lang, with_speakers, output_path=None):
    """Run one transcription. Returns the transcriber's JSON result line.

    The transcriber's stderr carries the whole transcript as it runs, so it is
    captured and only its last line is surfaced, on failure.
    """
    if not is_apple_silicon():
        raise CastError(TRANSCRIPTION_UNSUPPORTED,
                        "Local transcription needs an Apple Silicon Mac.",
                        "Use a YouTube link with captions (--fast), or a text file.")
    flags = ["--file", audio_path, "--lang", lang, "--json"]
    if output_path:
        flags += ["--out", output_path]
    if with_speakers:
        flags += ["--speakers", "auto"]
    completed = run_transcriber(directory, flags)
    if completed.returncode == 0:
        return last_json_line(completed.stdout)

    detail = last_error_line(completed.stderr)
    if completed.returncode == 4:
        raise CastError(FFMPEG_MISSING, "ffmpeg is not installed.", "brew install ffmpeg")
    if completed.returncode == 2:
        raise CastError(FILE_NOT_FOUND, f"The transcriber rejected the input: {detail}",
                        "Check the audio file and try again.")
    raise CastError(TRANSCRIBER_FAILED, f"Transcription failed: {detail}",
                    "Run /cast2skill:doctor, or try the transcriber on this file directly.")
