"""YouTube through yt-dlp: metadata, choosing a caption track, downloading.

Policy for which transcript to use lives in sources_youtube.py; this module
only talks to yt-dlp. No workaround flags and no browser cookies, ever: when
YouTube breaks yt-dlp, the user updates yt-dlp (SPEC section 6.3).
"""

import glob
import json
import os
import shutil
import subprocess
import sys

from . import http_client, language
from .errors import YTDLP_FAILED, YTDLP_MISSING, CastError

FAILED_HINT = "Update yt-dlp, then retry. If it still fails, pass an audio file or use --fast."
METADATA_TIMEOUT_S = 180


def require_ytdlp():
    path = shutil.which("yt-dlp")
    if not path:
        raise CastError(YTDLP_MISSING, "yt-dlp is not installed.",
                        "Install it with: brew install yt-dlp")
    return path


def run_ytdlp(arguments, timeout=None):
    """Run yt-dlp; on failure raise ytdlp_failed with yt-dlp's own last error line."""
    command = [require_ytdlp(), "--no-playlist", "--no-warnings"] + arguments
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                   stdin=subprocess.DEVNULL, env=http_client.subprocess_env())
    except subprocess.TimeoutExpired:
        raise CastError(YTDLP_FAILED, f"yt-dlp did not finish within {timeout}s.", FAILED_HINT)
    if completed.returncode != 0:
        lines = [line for line in completed.stderr.splitlines() if line.strip()]
        errors = [line for line in lines if line.startswith("ERROR")] or lines or ["no output"]
        raise CastError(YTDLP_FAILED, f"yt-dlp failed: {errors[-1].strip()}", FAILED_HINT)
    return completed.stdout


def fetch_metadata(url):
    stdout = run_ytdlp(["--dump-json", "--skip-download", url], METADATA_TIMEOUT_S)
    try:
        return json.loads(stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise CastError(YTDLP_FAILED, "yt-dlp returned no metadata.", FAILED_HINT)


def track_for(tracks, lang, prefer_original=False):
    """The caption key in `tracks` that is in `lang`, or None.

    For auto captions YouTube lists machine translations under plain codes
    ("iw" translated from English), so the "-orig" track wins when present.
    """
    keys = [key for key in tracks if key != "live_chat" and language.normalize(key) == lang]
    if not keys:
        return None

    def rank(key):
        if prefer_original and key.endswith("-orig"):
            return 0
        return 1 if "-" not in key else 2  # "en" before "en-GB"

    return sorted(keys, key=lambda key: (rank(key), len(key), key))[0]


def download_captions(url, track, automatic, folder):
    """Download one caption track as VTT into `folder`. Returns the file path."""
    flags = ["--skip-download", "--write-auto-subs" if automatic else "--write-subs",
             "--sub-langs", track, "--sub-format", "vtt/best",
             "-o", os.path.join(folder, "captions.%(ext)s"), url]
    run_ytdlp(flags, METADATA_TIMEOUT_S)
    found = sorted(glob.glob(os.path.join(folder, "captions*.vtt")) +
                   glob.glob(os.path.join(folder, "captions*.srt")))
    if not found:
        raise CastError(YTDLP_FAILED, f"yt-dlp wrote no caption file for track {track}.", FAILED_HINT)
    return found[0]


def download_audio(url, folder):
    """Best audio-only stream as-is (no re-encode). Returns the file path."""
    print("Downloading audio with yt-dlp ...", file=sys.stderr, flush=True)
    run_ytdlp(["-f", "bestaudio[ext=m4a]/bestaudio/best",
               "-o", os.path.join(folder, "audio.%(ext)s"), url])
    found = [path for path in glob.glob(os.path.join(folder, "audio.*")) if not path.endswith(".part")]
    if not found:
        raise CastError(YTDLP_FAILED, "yt-dlp downloaded no audio file.", FAILED_HINT)
    return found[0]
