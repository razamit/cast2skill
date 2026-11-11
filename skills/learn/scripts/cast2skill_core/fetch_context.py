"""State shared by one fetch run: args, config, warnings, library folders,
local-transcription availability, and writing the result.

Every source route (text, audio, YouTube, podcasts) ends in save_result(), so
the result JSON and source.json have one shape no matter how the transcript
was obtained.
"""

import os
import shutil
import subprocess
import sys

from . import storage, transcriber
from .errors import FFMPEG_MISSING, CastError

TRANSCRIPT_NAME = "transcript.txt"


def progress(message):
    """One short human-readable line on stderr. stdout stays JSON only."""
    print(message, file=sys.stderr, flush=True)


class FetchContext:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.warnings = []
        self.created_folders = []
        self._local = None  # (found, caps) once checked
        self._local_error = None

    # ------------------------------------------------------------------
    # Library folders and reuse
    # ------------------------------------------------------------------

    def new_folder(self, title):
        folder = storage.new_entry_folder(title)
        self.created_folders.append(folder)
        return folder

    def discard_unfinished_folders(self):
        """After a failure: remove folders this run created that hold no transcript."""
        for folder in self.created_folders:
            if not os.path.isfile(os.path.join(folder, TRANSCRIPT_NAME)):
                shutil.rmtree(folder, ignore_errors=True)

    def reuse(self, source_id):
        """The stored result for this source id, if a transcript already exists."""
        folder = storage.find_existing_entry(source_id)
        if not folder:
            return None
        stored = storage.read_source_json(folder) or {}
        if self.args.speakers and not stored.get("has_speakers"):
            return None  # the old transcript lacks what was asked for now
        if self.args.lang and stored.get("language") != self.args.lang:
            return None  # asked for another language: fetch again
        stored["reused"] = True
        stored["warnings"] = list(stored.get("warnings", [])) + ["reused_existing_transcript"]
        stored["transcript_path"] = os.path.join(folder, TRANSCRIPT_NAME)
        stored["library_dir"] = folder
        stored["lessons_log"] = os.path.join(storage.home_dir(), "lessons.jsonl")
        stored["notes_file"] = os.path.join(storage.home_dir(), "notes.md")
        for internal in ("fetched_by", "language_reason", "extra"):
            stored.pop(internal, None)
        return stored

    # ------------------------------------------------------------------
    # Local transcription (Apple Silicon + ffmpeg + audio_transcriber)
    # ------------------------------------------------------------------

    def _check_local(self):
        if self._local or self._local_error:
            return
        try:
            transcriber.require_apple_silicon()
            if not shutil.which("ffmpeg"):
                raise CastError(FFMPEG_MISSING, "ffmpeg is not installed.", "brew install ffmpeg")
            found = transcriber.locate(getattr(self.args, "transcriber_dir", None), self.config)
            self._local = (found, transcriber.capabilities(found["dir"]))
        except CastError as exc:
            self._local_error = exc

    def local_transcription_available(self):
        self._check_local()
        return self._local is not None

    def transcribe_audio(self, folder, audio_path, lang, delete_audio):
        """Transcribe into folder/transcript.txt. Returns has_speakers."""
        self._check_local()
        if self._local_error:
            raise self._local_error
        found, caps = self._local
        with_speakers = bool(self.args.speakers and caps.get("diarization"))
        if self.args.speakers and not with_speakers:
            self.warnings.append("diarization_unavailable")
        output = os.path.join(folder, TRANSCRIPT_NAME)
        progress(f"Transcribing locally ({lang}{', with speakers' if with_speakers else ''}). "
                 "This takes about a minute per 10 minutes of audio.")
        transcriber.transcribe(found["dir"], audio_path, lang, with_speakers, output)
        if delete_audio and not self.config.get("keep_audio"):
            os.remove(audio_path)
        return with_speakers

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    def save_result(self, folder, metadata, transcript_text=None):
        """Write transcript (if given) and source.json; return the fetch result."""
        transcript_path = os.path.join(folder, TRANSCRIPT_NAME)
        if transcript_text is not None:
            with open(transcript_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(transcript_text)
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            words = len(handle.read().split())

        result = {
            "id": metadata["id"], "kind": metadata["kind"],
            "title": metadata.get("title"), "author": metadata.get("author"),
            "url": metadata.get("url"), "duration_s": metadata.get("duration_s"),
            "language": metadata.get("language"),
            "transcript_path": transcript_path,
            "transcript_source": metadata["transcript_source"],
            "has_speakers": bool(metadata.get("has_speakers")),
            "words": words,
            "warnings": self.warnings + list(metadata.get("warnings", [])),
            "library_dir": folder, "reused": False,
            "lessons_log": os.path.join(storage.home_dir(), "lessons.jsonl"),
            "notes_file": os.path.join(storage.home_dir(), "notes.md"),
        }
        stored = dict(result, fetched_by="cast2skill", language_reason=metadata.get("language_reason"),
                      extra=metadata.get("extra", {}))
        storage.write_json_atomically(os.path.join(folder, "source.json"), stored)
        return result


def audio_duration_s(path):
    """Duration via ffprobe (ships with ffmpeg), or None if unavailable."""
    if not shutil.which("ffprobe"):
        return None
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        return round(float(completed.stdout.strip()))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
