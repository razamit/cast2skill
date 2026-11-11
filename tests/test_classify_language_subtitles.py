"""Pure logic: source classification (every row of SPEC 6.3), language choice,
subtitle cleaning, and the error object shape."""

import os
import tempfile
import unittest

from cast2skill_core import classify, errors, language, subtitles
from tests.support import fixture_path, read_fixture


class ClassifierTests(unittest.TestCase):
    def assertRoute(self, argument, kind, route):
        source = classify.classify(argument)
        self.assertEqual((source.kind, source.route), (kind, route), argument)

    def test_url_rows(self):
        rows = [
            ("https://www.youtube.com/watch?v=arj7oStGLkU", "youtube", classify.ROUTE_YOUTUBE),
            ("https://youtu.be/arj7oStGLkU", "youtube", classify.ROUTE_YOUTUBE),
            ("https://m.youtube.com/shorts/arj7oStGLkU", "youtube", classify.ROUTE_YOUTUBE),
            ("https://music.youtube.com/watch?v=arj7oStGLkU", "youtube", classify.ROUTE_YOUTUBE),
            ("https://podcasts.apple.com/us/podcast/x/id123?i=456", "podcast", classify.ROUTE_APPLE),
            ("https://open.spotify.com/episode/4rOoJ6Egrf8K2IrywzwOMk?si=x", "podcast", classify.ROUTE_SPOTIFY),
            ("https://feeds.example.com/show.xml", "podcast", classify.ROUTE_FEED),
            ("https://example.com/feed", "podcast", classify.ROUTE_FEED),
            ("https://cdn.example.com/ep12.MP3?token=1", "audio", classify.ROUTE_AUDIO_URL),
            ("https://cdn.example.com/talk.m4a", "audio", classify.ROUTE_AUDIO_URL),
        ]
        for argument, kind, route in rows:
            with self.subTest(argument=argument):
                self.assertRoute(argument, kind, route)

    def test_spotify_show_link_is_refused(self):
        with self.assertRaises(errors.CastError) as caught:
            classify.classify("https://open.spotify.com/show/abc")
        self.assertEqual(caught.exception.code, errors.BAD_ARGUMENTS)

    def test_local_file_rows(self):
        folder = tempfile.mkdtemp()
        for extension in classify.AUDIO_EXTENSIONS + classify.TEXT_EXTENSIONS:
            path = os.path.join(folder, "file" + extension.upper())
            open(path, "w").close()
            kind = "audio" if extension in classify.AUDIO_EXTENSIONS else "text"
            with self.subTest(extension=extension):
                self.assertEqual(classify.classify(path).kind, kind)
        other = os.path.join(folder, "file.pdf")
        open(other, "w").close()
        with self.assertRaises(errors.CastError):
            classify.classify(other)

    def test_anything_else_is_pasted_text(self):
        self.assertRoute("Have the agent write the failing test first.", "text", classify.ROUTE_PASTED)
        self.assertRoute("/no/such/file.mp3", "text", classify.ROUTE_PASTED)
        source = classify.classify("-", stdin_text="from stdin")
        self.assertEqual((source.route, source.value), (classify.ROUTE_PASTED, "from stdin"))

    def test_youtube_ids(self):
        for url in ("https://youtu.be/arj7oStGLkU?t=3", "https://www.youtube.com/watch?v=arj7oStGLkU&list=x",
                    "https://youtube.com/live/arj7oStGLkU", "https://www.youtube.com/embed/arj7oStGLkU"):
            self.assertEqual(classify.youtube_video_id(url), "arj7oStGLkU", url)
        self.assertIsNone(classify.youtube_video_id("https://www.youtube.com/@channel"))


class LanguageTests(unittest.TestCase):
    def test_order(self):
        self.assertEqual(language.choose("en", "he", "שלום", "he"), ("en", "flag"))
        self.assertEqual(language.choose(None, "en-US", "שלום", "he"), ("en", "source"))
        self.assertEqual(language.choose(None, "iw", "", None), ("he", "source"))
        self.assertEqual(language.choose(None, "fr", "פרק 12", None), ("he", "hebrew_title"))
        self.assertEqual(language.choose(None, None, "Episode 12", "en"), ("en", "config_default"))
        self.assertEqual(language.choose(None, None, "Episode 12", None), (None, None))

    def test_require_raises_needs_lang(self):
        with self.assertRaises(errors.CastError) as caught:
            language.require(None, None, "Episode 12", None)
        self.assertEqual(caught.exception.code, errors.NEEDS_LANG)


class SubtitleTests(unittest.TestCase):
    def test_rolling_auto_captions_are_deduped(self):
        cleaned = subtitles.clean_subtitles(read_fixture("auto_captions.vtt"))
        self.assertEqual(cleaned.count("so today I want to show you how I review code"), 1)
        self.assertEqual(cleaned.count("fail proves nothing at all"), 1)
        self.assertNotIn("<c>", cleaned)
        self.assertNotIn("align:", cleaned)
        self.assertNotIn("[Music]", cleaned)
        self.assertIn("the change & that order", cleaned)

    def test_one_timestamp_per_paragraph_about_every_30_seconds(self):
        cleaned = subtitles.clean_subtitles(read_fixture("auto_captions.vtt"))
        paragraphs = cleaned.strip().split("\n\n")
        self.assertEqual(len(paragraphs), 2)
        self.assertTrue(paragraphs[0].startswith("[00:00:00] so today"))
        self.assertTrue(paragraphs[1].startswith("[00:00:32] "))

    def test_srt_tags_removed(self):
        cleaned = subtitles.clean_subtitles(read_fixture("manual_captions.srt"))
        self.assertEqual(cleaned,
                         "[00:00:01] Welcome back. Today: one habit that changed how I ship. "
                         "Write the plan down before the code.\n\n"
                         "[00:00:35] Then check the plan against what actually shipped.\n")

    def test_empty_input(self):
        self.assertEqual(subtitles.clean_subtitles("WEBVTT\n\n"), "")


class ErrorShapeTests(unittest.TestCase):
    def test_every_code_has_the_documented_shape(self):
        codes = [value for name, value in vars(errors).items() if name.isupper() and isinstance(value, str)]
        self.assertGreater(len(codes), 15)
        for code in codes:
            body = errors.CastError(code, "message", "hint").as_json()
            self.assertEqual(set(body), {"error"})
            self.assertEqual(body["error"], {"code": code, "message": "message", "hint": "hint"})

    def test_extra_fields_are_added(self):
        body = errors.CastError(errors.NEEDS_EPISODE, "m", "h", candidates=[1]).as_json()
        self.assertEqual(body["error"]["candidates"], [1])


if __name__ == "__main__":
    unittest.main()
