"""fetch end to end without network: text, local audio and the YouTube policy,
with yt-dlp and the transcriber replaced by fakes."""

import argparse
import io
import json
import os
from unittest import mock

from cast2skill_core import errors, fetch, fetch_context, http_client, sources_youtube, transcriber, youtube
from tests.support import IsolatedHomeTestCase, fixture_path, read_fixture


def fetch_args(*source, **overrides):
    values = dict(source=list(source), lang=None, speakers=False, fast=False, episode=None,
                  episode_id=None, transcriber_dir=None)
    values.update(overrides)
    return argparse.Namespace(**values)


def fake_transcribe(directory, audio_path, lang, with_speakers, output_path=None):
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("[00:00:00] SPEAKER_00: one two three\n" if with_speakers else "[00:00:00] one two three\n")
    return {"output": output_path, "language": lang, "speakers": 1 if with_speakers else None}


class LocalTranscriptionFakes:
    """Patch the machine checks so local transcription is (or is not) available."""

    def __init__(self, test, available=True, diarization=True):
        test.start_patch(mock.patch.object(transcriber, "is_apple_silicon", return_value=available))
        test.start_patch(mock.patch.object(fetch_context.shutil, "which", return_value="/bin/ffmpeg"))
        test.start_patch(mock.patch.object(transcriber, "locate", return_value={"dir": "/t", "source": "x"}))
        test.start_patch(mock.patch.object(transcriber, "capabilities",
                                           return_value={"diarization": diarization}))
        self.transcribe = test.start_patch(mock.patch.object(
            transcriber, "transcribe", side_effect=fake_transcribe))


class TextRouteTests(IsolatedHomeTestCase):
    def test_pasted_text_from_stdin_through_the_cli(self):
        tweet = 'Tip: run the failing test first. "$HOME" `x` stays literal.\n'
        code, result, _ = self.run_cli("fetch", "-", stdin_text=tweet)
        self.assertEqual(code, 0)
        self.assertEqual((result["kind"], result["transcript_source"]), ("text", "provided_text"))
        with open(result["transcript_path"], encoding="utf-8") as handle:
            self.assertEqual(handle.read(), tweet)
        with open(os.path.join(result["library_dir"], "source.json")) as handle:
            self.assertEqual(json.load(handle)["id"], result["id"])

    def test_result_has_every_spec_field(self):
        result = fetch.fetch(fetch_args("Write", "the", "plan", "first."))
        for field in ("id", "kind", "title", "author", "url", "duration_s", "language",
                      "transcript_path", "transcript_source", "has_speakers", "words", "warnings"):
            self.assertIn(field, result)
        self.assertEqual(result["words"], 4)

    def test_subtitle_file_is_cleaned(self):
        result = fetch.fetch(fetch_args(fixture_path("auto_captions.vtt")))
        with open(result["transcript_path"]) as handle:
            self.assertNotIn("<c>", handle.read())

    def test_hebrew_text_language(self):
        self.assertEqual(fetch.fetch(fetch_args("כתוב את הבדיקה שנכשלת קודם"))["language"], "he")

    def test_same_text_twice_is_reused(self):
        first = fetch.fetch(fetch_args("same words"))
        second = fetch.fetch(fetch_args("same words"))
        self.assertEqual(second["transcript_path"], first["transcript_path"])
        self.assertTrue(second["reused"])
        self.assertIn("reused_existing_transcript", second["warnings"])

    def test_different_lang_is_not_reused(self):
        fetch.fetch(fetch_args("same words", lang="en"))
        second = fetch.fetch(fetch_args("same words", lang="he"))
        self.assertEqual((second["reused"], second["language"]), (False, "he"))

    def test_empty_stdin(self):
        with self.assertRaises(errors.CastError) as caught:
            fetch.fetch(fetch_args("-"), stdin=io.StringIO("   "))
        self.assertEqual(caught.exception.code, errors.EMPTY_TEXT)


class LocalAudioTests(IsolatedHomeTestCase):
    def setUp(self):
        super().setUp()
        self.audio = os.path.join(self.home, "talk.m4a")
        open(self.audio, "wb").close()

    def test_transcribed_in_place_and_never_deleted(self):
        fakes = LocalTranscriptionFakes(self)
        result = fetch.fetch(fetch_args(self.audio, lang="en", speakers=True))
        self.assertEqual((result["transcript_source"], result["has_speakers"]), ("local_whisper", True))
        self.assertTrue(os.path.exists(self.audio))
        self.assertEqual(fakes.transcribe.call_args.args[1:4], (self.audio, "en", True))

    def test_speakers_without_diarization_warns_and_continues(self):
        LocalTranscriptionFakes(self, diarization=False)
        result = fetch.fetch(fetch_args(self.audio, lang="he", speakers=True))
        self.assertFalse(result["has_speakers"])
        self.assertIn("diarization_unavailable", result["warnings"])

    def test_needs_lang_leaves_no_folder(self):
        LocalTranscriptionFakes(self)
        with self.assertRaises(errors.CastError) as caught:
            fetch.fetch(fetch_args(self.audio))
        self.assertEqual(caught.exception.code, errors.NEEDS_LANG)
        self.assertEqual(self.library_entries(), [])

    def test_off_apple_silicon_is_a_clear_error_and_cleans_up(self):
        LocalTranscriptionFakes(self, available=False)
        with self.assertRaises(errors.CastError) as caught:
            fetch.fetch(fetch_args(self.audio, lang="en"))
        self.assertEqual(caught.exception.code, errors.TRANSCRIPTION_UNSUPPORTED)
        self.assertEqual(self.library_entries(), [])


def video_metadata(manual=(), auto=(), lang="en"):
    return {"id": "abcdefghijk", "title": "A talk", "channel": "Chan", "duration": 600,
            "language": lang, "webpage_url": "https://www.youtube.com/watch?v=abcdefghijk",
            "subtitles": {key: [] for key in manual},
            "automatic_captions": {key: [] for key in auto}}


class YouTubePolicyTests(IsolatedHomeTestCase):
    URL = "https://youtu.be/abcdefghijk"

    def setUp(self):
        super().setUp()
        self.captions = self.start_patch(mock.patch.object(
            youtube, "download_captions", side_effect=self.write_vtt))
        self.audio = self.start_patch(mock.patch.object(youtube, "download_audio", side_effect=self.write_audio))

    def write_vtt(self, url, track, automatic, folder):
        path = os.path.join(folder, "captions.vtt")
        with open(path, "w") as handle:
            handle.write(read_fixture("auto_captions.vtt"))
        return path

    def write_audio(self, url, folder):
        path = os.path.join(folder, "audio.m4a")
        open(path, "wb").close()
        return path

    def run_fetch(self, meta, **overrides):
        self.start_patch(mock.patch.object(youtube, "fetch_metadata", return_value=meta))
        return fetch.fetch(fetch_args(self.URL, **overrides))

    def test_human_captions_win_and_no_audio(self):
        LocalTranscriptionFakes(self)
        result = self.run_fetch(video_metadata(manual=["en", "iw"], auto=["en-orig"]))
        self.assertEqual(result["transcript_source"], "manual_captions")
        self.assertEqual(self.captions.call_args.args[1:3], ("en", False))
        self.audio.assert_not_called()

    def test_translated_human_captions_are_not_used(self):
        LocalTranscriptionFakes(self)
        result = self.run_fetch(video_metadata(manual=["iw"]))
        self.assertEqual(result["transcript_source"], "local_whisper")

    def test_audio_when_local_works_and_audio_deleted(self):
        LocalTranscriptionFakes(self)
        result = self.run_fetch(video_metadata(auto=["en-orig", "en"]))
        self.assertEqual(result["transcript_source"], "local_whisper")
        self.assertEqual(sorted(os.listdir(result["library_dir"])), ["source.json", "transcript.txt"])

    def test_keep_audio_keeps_it(self):
        LocalTranscriptionFakes(self)
        self.run_cli("config", "set", "keep_audio", "true")
        result = self.run_fetch(video_metadata())
        self.assertTrue(os.path.exists(os.path.join(result["library_dir"], "audio.m4a")))

    def test_auto_captions_when_no_local_with_warning(self):
        LocalTranscriptionFakes(self, available=False)
        result = self.run_fetch(video_metadata(auto=["iw", "en-orig", "en"]))
        self.assertEqual(result["transcript_source"], "auto_captions")
        self.assertIn("auto_captions_lower_quality", result["warnings"])
        self.assertEqual(self.captions.call_args.args[1:3], ("en-orig", True))

    def test_fast_never_downloads_audio(self):
        LocalTranscriptionFakes(self)
        result = self.run_fetch(video_metadata(auto=["en-orig"]), fast=True)
        self.assertEqual(result["transcript_source"], "auto_captions")
        self.audio.assert_not_called()

    def test_nothing_possible(self):
        LocalTranscriptionFakes(self, available=False)
        with self.assertRaises(errors.CastError) as caught:
            self.run_fetch(video_metadata(auto=["fr"]))
        self.assertEqual(caught.exception.code, errors.NO_TRANSCRIPT_POSSIBLE)
        self.assertEqual(self.library_entries(), [])

    def test_needs_lang_when_video_language_unknown(self):
        LocalTranscriptionFakes(self)
        with self.assertRaises(errors.CastError) as caught:
            self.run_fetch(video_metadata(lang=None))
        self.assertEqual(caught.exception.code, errors.NEEDS_LANG)

    def test_reuse_skips_ytdlp(self):
        LocalTranscriptionFakes(self)
        self.run_fetch(video_metadata(manual=["en"]))
        with mock.patch.object(youtube, "fetch_metadata", side_effect=AssertionError("network")):
            self.assertTrue(fetch.fetch(fetch_args(self.URL))["reused"])

    def test_ytdlp_failure_carries_its_last_error_line(self):
        failed = mock.Mock(returncode=1, stderr="WARNING: x\nERROR: [youtube] abc: Sign in to confirm\n")
        with mock.patch.object(youtube.shutil, "which", return_value="/bin/yt-dlp"), \
                mock.patch.object(youtube.subprocess, "run", return_value=failed):
            with self.assertRaises(errors.CastError) as caught:
                youtube.fetch_metadata(self.URL)
        self.assertEqual(caught.exception.code, errors.YTDLP_FAILED)
        self.assertIn("Sign in to confirm", caught.exception.message)
        self.assertEqual(caught.exception.hint, youtube.FAILED_HINT)


class CertificateFallbackTests(IsolatedHomeTestCase):
    def test_uses_system_bundle_only_when_python_store_is_empty(self):
        empty = mock.Mock(cert_store_stats=mock.Mock(return_value={"x509_ca": 0}))
        full = mock.Mock(cert_store_stats=mock.Mock(return_value={"x509_ca": 150}))
        os.environ.pop("SSL_CERT_FILE", None)
        with mock.patch.object(http_client.ssl, "create_default_context", return_value=empty), \
                mock.patch.object(http_client.os.path, "isfile", return_value=True):
            self.assertEqual(http_client.ca_bundle_override(), http_client.SYSTEM_CA_BUNDLE)
        with mock.patch.object(http_client.ssl, "create_default_context", return_value=full):
            self.assertIsNone(http_client.ca_bundle_override())
