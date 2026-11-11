"""Sources that are already on this machine: pasted text, text files, audio files."""

import hashlib
import os
import re

from . import language, subtitles
from .errors import EMPTY_TEXT, CastError
from .fetch_context import audio_duration_s

TITLE_LENGTH = 60
SUBTITLE_EXTENSIONS = (".vtt", ".srt")


def short_hash(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def first_line_title(text):
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            return line[:TITLE_LENGTH].rstrip() + ("..." if len(line) > TITLE_LENGTH else "")
    return "Pasted text"


def text_language(flag_lang, text):
    """--lang, else the majority script (Hebrew or Latin letters), else None."""
    if flag_lang:
        return flag_lang, "flag"
    hebrew = len(language.HEBREW_LETTERS.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if hebrew or latin:
        return ("he" if hebrew >= latin else "en"), "script"
    return None, None


def save_text(context, text, metadata):
    if not text.strip():
        raise CastError(EMPTY_TEXT, "There is no text to learn from.",
                        "Paste the text, or pass a file or link.")
    lang, how = text_language(context.args.lang, text)
    folder = context.new_folder(metadata["title"])
    metadata.update(kind="text", language=lang, language_reason=how,
                    transcript_source="provided_text", has_speakers=False)
    if context.args.speakers:
        context.warnings.append("speakers_need_audio")
    return context.save_result(folder, metadata, text.rstrip() + "\n")


def fetch_pasted_text(source, context):
    text = source.value
    source_id = "text:" + short_hash(text)
    return context.reuse(source_id) or save_text(
        context, text, {"id": source_id, "title": first_line_title(text)})


def fetch_text_file(source, context):
    with open(source.value, encoding="utf-8", errors="replace") as handle:
        raw = handle.read()
    text = subtitles.clean_subtitles(raw) if source.value.lower().endswith(SUBTITLE_EXTENSIONS) else raw
    source_id = "text:" + short_hash(text)
    title = os.path.splitext(os.path.basename(source.value))[0]
    return context.reuse(source_id) or save_text(
        context, text, {"id": source_id, "title": title, "url": source.value})


def file_identity(path):
    """Stable id for a local file without hashing gigabytes: path + size + mtime."""
    stat = os.stat(path)
    return "file:" + short_hash(f"{path}|{stat.st_size}|{int(stat.st_mtime)}")


def fetch_audio_file(source, context):
    """Local audio is transcribed in place and never deleted (keep_audio is for downloads)."""
    path = source.value
    source_id = file_identity(path)
    reused = context.reuse(source_id)
    if reused:
        return reused
    title = os.path.splitext(os.path.basename(path))[0]
    lang, how = language.require(context.args.lang, None, title, context.config.get("default_lang"))
    folder = context.new_folder(title)
    has_speakers = context.transcribe_audio(folder, path, lang, delete_audio=False)
    return context.save_result(folder, {
        "id": source_id, "kind": "audio", "title": title, "url": path,
        "duration_s": audio_duration_s(path), "language": lang, "language_reason": how,
        "transcript_source": "local_whisper", "has_speakers": has_speakers,
    })
