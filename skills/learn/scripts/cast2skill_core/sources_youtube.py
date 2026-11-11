"""The YouTube transcript policy (SPEC section 6.3).

1. Human captions in the video's language: use them.
2. Else, if local transcription works here: download audio and transcribe.
3. Else, auto captions in the video's language, with a quality warning.
4. Else: no_transcript_possible.
--fast skips step 2 entirely: captions only, never audio.
"""

import os

from . import classify, language, subtitles, youtube
from .errors import NO_TRANSCRIPT_POSSIBLE, CastError


def captions_transcript(url, track, automatic, folder):
    caption_file = youtube.download_captions(url, track, automatic, folder)
    with open(caption_file, encoding="utf-8", errors="replace") as handle:
        text = subtitles.clean_subtitles(handle.read())
    os.remove(caption_file)
    return text


def no_transcript_error(context, lang):
    if context.args.fast:
        hint = "This video has no captions in that language. Retry without --fast to transcribe the audio."
    else:
        hint = ("This video has no captions in that language, and local transcription is not "
                "available here (needs Apple Silicon and audio_transcriber; run /cast2skill:doctor).")
    return CastError(NO_TRANSCRIPT_POSSIBLE, f"No way to get a transcript in '{lang}' for this video.", hint)


def choose_route(context, manual, auto):
    """Which transcript to use: 'manual', 'audio', 'auto', or None."""
    if manual:
        return "manual"
    if not context.args.fast and context.local_transcription_available():
        return "audio"
    if auto:
        return "auto"
    return None


def fetch_youtube(source, context):
    video_id = classify.youtube_video_id(source.value)
    if video_id:
        reused = context.reuse(f"youtube:{video_id}")
        if reused:
            return reused

    meta = youtube.fetch_metadata(source.value)
    source_id = f"youtube:{meta['id']}"
    lang, how = language.require(context.args.lang, meta.get("language"), meta.get("title"),
                                 context.config.get("default_lang"))
    manual = youtube.track_for(meta.get("subtitles") or {}, lang)
    auto = youtube.track_for(meta.get("automatic_captions") or {}, lang, prefer_original=True)
    route = choose_route(context, manual, auto)
    if route is None:
        raise no_transcript_error(context, lang)

    url = meta.get("webpage_url") or source.value
    folder = context.new_folder(meta.get("title") or meta["id"])
    metadata = {
        "id": source_id, "kind": "youtube", "title": meta.get("title"),
        "author": meta.get("channel") or meta.get("uploader"), "url": url,
        "duration_s": meta.get("duration"), "language": lang, "language_reason": how,
        "extra": {"caption_track": manual if route == "manual" else auto if route == "auto" else None},
    }
    if route == "audio":
        audio_path = youtube.download_audio(url, folder)
        metadata["has_speakers"] = context.transcribe_audio(folder, audio_path, lang, delete_audio=True)
        metadata["transcript_source"] = "local_whisper"
        return context.save_result(folder, metadata)

    text = captions_transcript(url, manual or auto, route == "auto", folder)
    if not text.strip():
        raise CastError(NO_TRANSCRIPT_POSSIBLE, "The caption track was empty.",
                        "Retry without --fast, or pass an audio file.")
    metadata["transcript_source"] = "manual_captions" if route == "manual" else "auto_captions"
    if route == "auto":
        context.warnings.append("auto_captions_lower_quality")
    if context.args.speakers:
        context.warnings.append("speakers_need_audio")
    return context.save_result(folder, metadata, text)
