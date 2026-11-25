"""`doctor`: what works on this machine, and one fix per thing that does not.

Reports only. Never installs or changes anything, and never edits Claude
Code settings: the permission rule is shown, not added (permission_rule.py).
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile

from . import permission_rule, storage, transcriber
from .errors import CastError

MIN_PYTHON = (3, 10)


def check(name, ok, detail, hint=""):
    return {"name": name, "ok": bool(ok), "detail": detail, "hint": "" if ok else hint}


def check_python():
    version = ".".join(str(part) for part in sys.version_info[:3])
    return check("python", sys.version_info[:2] >= MIN_PYTHON, f"Python {version}",
                 "Install Python 3.10 or newer (brew install python).")


def tool_version(command):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30,
                                   stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return "version unknown"
    first = (completed.stdout or completed.stderr).strip().splitlines()
    return first[0] if first else "version unknown"


def check_ytdlp():
    path = shutil.which("yt-dlp")
    detail = f"yt-dlp {tool_version(['yt-dlp', '--version'])} at {path}" if path else "not found"
    return check("yt-dlp", path, detail, "Needed for YouTube. Install: brew install yt-dlp")


def check_ffmpeg():
    path = shutil.which("ffmpeg")
    detail = tool_version(["ffmpeg", "-version"]) if path else "not found"
    return check("ffmpeg", path, detail, "Needed for audio. Install: brew install ffmpeg")


def check_cpu():
    detail = f"{sys.platform} {platform.machine()}"
    return check("apple_silicon", transcriber.is_apple_silicon(), detail,
                 "Audio transcription needs an Apple Silicon Mac. "
                 "YouTube captions and text still work here.")


def check_home():
    try:
        home = storage.ensure_home()
        with tempfile.NamedTemporaryFile(dir=home, prefix=".doctor-", delete=True):
            pass
    except (CastError, OSError) as exc:
        return check("home_writable", False, str(exc),
                     f"Set {storage.HOME_ENV_VAR} to a folder you can write to.")
    return check("home_writable", True, home)


def check_transcriber(explicit_dir, config):
    """Two checks: is it there, and does it answer --capabilities. Plus the caps."""
    try:
        found = transcriber.locate(explicit_dir, config)
    except CastError as exc:
        tried = "; tried " + ", ".join(exc.extra.get("tried", [])) if exc.extra.get("tried") else ""
        return [check("transcriber", False, exc.message.rstrip(".") + tried, exc.hint)], None

    located = check("transcriber", True, f"{found['dir']} (from {found['source']})")
    try:
        caps = transcriber.capabilities(found["dir"])
    except CastError as exc:
        return [located, check("transcriber_flags", False, exc.message, exc.hint)], None

    detail = f"version {caps.get('version')}, languages {', '.join(caps.get('languages', []))}"
    return [located, check("transcriber_flags", True, detail)], caps


def speaker_check(caps):
    if caps is None:
        return check("speakers", False, "transcriber not available",
                     "Fix the transcriber checks above first.")
    return check("speakers", caps.get("diarization"),
                 "diarization installed" if caps.get("diarization") else "diarization not installed",
                 "Optional. In the audio_transcriber folder run: ./setup.sh --with-diarization")


def capability_row(results_by_name, caps):
    """The capability matrix row (SPEC section 5) for this machine."""
    ok = {name: result["ok"] for name, result in results_by_name.items()}
    local_audio = ok["apple_silicon"] and ok["ffmpeg"] and caps is not None
    return {
        "youtube_with_captions": ok["yt-dlp"],
        "youtube_without_captions": ok["yt-dlp"] and local_audio,
        "podcast_or_audio_file": local_audio,
        "text": True,
        "speaker_labels": local_audio and bool(caps and caps.get("diarization")),
    }


def run_doctor(explicit_dir=None):
    try:
        config = storage.load_config()
        config_check = check("config", True, storage.config_path())
    except CastError as exc:
        config, config_check = dict(storage.DEFAULT_CONFIG), check("config", False, exc.message, exc.hint)

    results = [check_python(), check_ytdlp(), check_ffmpeg(), check_cpu(), check_home(), config_check]
    transcriber_results, caps = check_transcriber(explicit_dir, config)
    results += transcriber_results + [speaker_check(caps)]

    by_name = {result["name"]: result for result in results}
    on_apple_with_transcriber = by_name["apple_silicon"]["ok"] and caps is not None
    report = {
        "machine": "Apple Silicon + audio_transcriber" if on_apple_with_transcriber else "Anything else",
        "capabilities": capability_row(by_name, caps),
        "checks": results,
        "failed": [result["name"] for result in results if not result["ok"]],
        "home": storage.home_dir(),
        "plugin_scripts": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    }
    report.update(permission_rule.permission_report())
    return report
