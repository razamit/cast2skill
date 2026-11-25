"""Podcasts without network: feed parsing, episode matching, Apple and Spotify
resolution, and the four podcast routes with downloads and the transcriber faked."""

import json
import os
from unittest import mock

from cast2skill_core import (episode_match, errors, fetch, http_client, podcast_feeds,
                             podcast_lookup, sources_podcast)
from tests.support import IsolatedHomeTestCase, fixture_path
from tests.test_fetch_routes import LocalTranscriptionFakes, fetch_args

FEED_URL = "https://feeds.example.com/show.xml"


def feed_bytes(name="podcast_feed.xml"):
    with open(fixture_path(name), "rb") as handle:
        return handle.read()


def sample_feed():
    return podcast_feeds.parse_feed(feed_bytes(), FEED_URL)


class FeedParsingTests(IsolatedHomeTestCase):
    def test_channel_and_episodes(self):
        feed = sample_feed()
        self.assertEqual((feed.title, feed.author, feed.language),
                         ("Shipping With Agents", "Example Studio", "en-us"))
        self.assertEqual([episode.guid for episode in feed.episodes],
                         ["guid-42", "guid-41", "guid-40", "guid-39"])  # newest first, no audio-less item
        newest = feed.episodes[0]
        self.assertEqual((newest.published, newest.duration_s, newest.audio_url),
                         ("2026-11-10", 3723, "https://cdn.example.com/ep42.m4a"))
        self.assertEqual(feed.episodes[1].duration_s, 3723)  # 1:02:03
        self.assertEqual(feed.episodes[2].duration_s, 2710)  # 45:10

    def test_entity_declarations_are_refused(self):
        with self.assertRaises(errors.CastError) as caught:
            podcast_feeds.parse_feed(feed_bytes("entity_feed.xml"), FEED_URL)
        self.assertEqual(caught.exception.code, errors.FEED_UNREADABLE)

    def test_non_rss_and_broken_xml(self):
        for body in (b"<feed xmlns='http://www.w3.org/2005/Atom'></feed>", b"<rss><channel>"):
            with self.subTest(body=body), self.assertRaises(errors.CastError) as caught:
                podcast_feeds.parse_feed(body, FEED_URL)
            self.assertEqual(caught.exception.code, errors.FEED_UNREADABLE)

    def test_entity_declaration_after_a_long_comment_is_refused(self):
        body = b'<?xml version="1.0"?>\n<!--' + b"x" * 70000 + b'-->\n' + feed_bytes("entity_feed.xml").split(b"\n", 1)[1]
        with self.assertRaises(errors.CastError) as caught:
            podcast_feeds.parse_feed(body, FEED_URL)
        self.assertEqual(caught.exception.code, errors.FEED_UNREADABLE)

    def test_non_web_links_are_refused(self):
        for url in ("file:///etc/passwd", "ftp://x/y.mp3"):
            with self.subTest(url=url), self.assertRaises(errors.CastError) as caught:
                http_client.download(url, os.path.join(self.home, "a.mp3"))
            self.assertEqual(caught.exception.code, errors.DOWNLOAD_FAILED)

    def test_download_size_cap(self):
        import io
        with self.assertRaises(errors.CastError):
            http_client.copy_with_limit(io.BytesIO(b"x" * 3000), io.BytesIO(), limit=1000)

    def test_html_page_is_not_a_feed(self):
        with mock.patch.object(http_client, "get_bytes", return_value=(b"<!doctype html><html>", "text/html")):
            with self.assertRaises(errors.CastError) as caught:
                podcast_feeds.fetch_feed("https://example.com/")
        self.assertEqual(caught.exception.code, errors.BAD_ARGUMENTS)


class EpisodeMatchingTests(IsolatedHomeTestCase):
    def test_exact_after_normalizing(self):
        episode = episode_match.match(sample_feed().episodes, "ep 42 tests first ALWAYS")
        self.assertEqual(episode.guid, "guid-42")

    def test_fuzzy_above_threshold(self):
        episode = episode_match.match(sample_feed().episodes, "Ep 41: Reviews that catch real bug")
        self.assertEqual(episode.guid, "guid-41")

    def test_below_threshold_returns_top_three(self):
        with self.assertRaises(errors.CastError) as caught:
            episode_match.match(sample_feed().episodes, "reviews")
        self.assertEqual(caught.exception.code, errors.NEEDS_EPISODE)
        candidates = caught.exception.extra["candidates"]
        self.assertEqual(len(candidates), 3)
        self.assertEqual(set(candidates[0]), {"episode_id", "title", "published", "duration_s"})
        self.assertRegex(candidates[0]["episode_id"], r"^[0-9a-f]{16}$")

    def test_hebrew_titles(self):
        episode = episode_match.match(sample_feed().episodes, "פרק 39 - סוכנים בדיקות ומה שביניהם")
        self.assertEqual(episode.guid, "guid-39")


def apple_lookup_results(episode_in_feed=True):
    return [
        {"kind": "podcast", "feedUrl": FEED_URL, "trackName": "Shipping With Agents"},
        {"kind": "podcast-episode", "trackId": 555, "trackName": "Ep. 41: Reviews that catch real bugs",
         "episodeGuid": "guid-41" if episode_in_feed else "gone",
         "episodeUrl": "https://apple-cdn.example.com/ep41.mp3"},
    ]


class RouteTests(IsolatedHomeTestCase):
    def setUp(self):
        super().setUp()
        self.transcriber = LocalTranscriptionFakes(self)
        self.start_patch(mock.patch.object(podcast_feeds, "fetch_feed", side_effect=self.feed_for))
        self.downloads = self.start_patch(mock.patch.object(http_client, "download", side_effect=self.fake_download))
        self.feeds = {FEED_URL: sample_feed()}

    def feed_for(self, url):
        if url not in self.feeds:
            raise errors.CastError(errors.FEED_UNREADABLE, "no", "")
        return self.feeds[url]

    def fake_download(self, url, destination):
        open(destination, "wb").close()
        return destination

    def test_feed_url_without_episode_asks_with_recent_list(self):
        with self.assertRaises(errors.CastError) as caught:
            fetch.fetch(fetch_args(FEED_URL))
        self.assertEqual(caught.exception.code, errors.NEEDS_EPISODE)
        self.assertEqual(len(caught.exception.extra["candidates"]), 4)

    def test_feed_url_with_episode(self):
        result = fetch.fetch(fetch_args(FEED_URL, episode="Tests first, always?"))
        self.assertEqual((result["kind"], result["language"], result["author"]), ("podcast", "en", "Example Studio"))
        self.assertEqual(self.downloads.call_args.args[0], "https://cdn.example.com/ep42.m4a")
        self.assertEqual(sorted(os.listdir(result["library_dir"])), ["source.json", "transcript.txt"])

    def test_apple_episode_link_matches_by_guid(self):
        with mock.patch.object(podcast_lookup, "itunes", return_value=apple_lookup_results()):
            result = fetch.fetch(fetch_args("https://podcasts.apple.com/us/podcast/ep-41/id123?i=555"))
        self.assertEqual(result["title"], "Ep. 41: Reviews that catch real bugs")
        self.assertEqual(self.downloads.call_args.args[0], "https://cdn.example.com/ep41.mp3")

    def test_apple_episode_missing_from_feed_uses_apples_audio_url(self):
        results = apple_lookup_results(episode_in_feed=False)
        results[1]["trackName"] = "An episode the feed dropped"
        with mock.patch.object(podcast_lookup, "itunes", return_value=results):
            result = fetch.fetch(fetch_args("https://podcasts.apple.com/us/podcast/x/id123?i=555", lang="en"))
        self.assertEqual(self.downloads.call_args.args[0], "https://apple-cdn.example.com/ep41.mp3")
        self.assertEqual(result["kind"], "podcast")

    def test_apple_link_slug_used_for_older_episodes(self):
        with mock.patch.object(podcast_lookup, "itunes", return_value=apple_lookup_results()[:1]):
            result = fetch.fetch(fetch_args(
                "https://podcasts.apple.com/us/podcast/ep-40-planning-before-prompting/id123?i=999"))
        self.assertEqual(result["title"], "Ep. 40: Planning before prompting")

    def test_apple_show_without_feed(self):
        with mock.patch.object(podcast_lookup, "itunes", return_value=[{"kind": "podcast"}]):
            with self.assertRaises(errors.CastError) as caught:
                fetch.fetch(fetch_args("https://podcasts.apple.com/us/podcast/x/id123?i=1"))
        self.assertEqual(caught.exception.code, errors.NO_PUBLIC_FEED)

    def spotify(self, oembed_title, episode_search, show_search=(), show_name="",
                url="https://open.spotify.com/episode/4rOoJ6Egrf8K2IrywzwOMk"):
        def itunes(path, **params):
            return list(episode_search) if params.get("entity") == "podcastEpisode" else list(show_search)
        self.start_patch(mock.patch.object(podcast_lookup, "itunes", side_effect=itunes))
        self.start_patch(mock.patch.object(http_client, "get_json", return_value={"title": oembed_title}))
        self.start_patch(mock.patch.object(podcast_lookup, "spotify_show_name", return_value=show_name))
        return fetch.fetch(fetch_args(url))

    def test_spotify_resolves_through_the_public_feed_and_never_downloads_from_spotify(self):
        hit = {"trackName": "Ep. 42: Tests first, always?", "feedUrl": FEED_URL}
        result = self.spotify("Ep. 42: Tests first, always?", [hit])
        self.assertEqual(result["title"], "Ep. 42: Tests first, always?")
        downloaded = self.downloads.call_args.args[0]
        self.assertNotIn("spotify", downloaded)

    def test_spotify_share_token_is_never_stored_and_reuse_ignores_it(self):
        hit = {"trackName": "Ep. 42: Tests first, always?", "feedUrl": FEED_URL}
        clean = "https://open.spotify.com/episode/4rOoJ6Egrf8K2IrywzwOMk"
        first = self.spotify(hit["trackName"], [hit], url=clean + "?si=05890d41c8764a22")
        self.assertEqual(first["url"], clean)
        with open(os.path.join(first["library_dir"], "source.json"), encoding="utf-8") as handle:
            self.assertNotIn("si=", handle.read())
        again = fetch.fetch(fetch_args(clean))
        self.assertEqual((again["reused"], again["library_dir"], again["url"]), (True, first["library_dir"], clean))

    def test_audio_url_with_and_without_tracking_reuses_one_transcript(self):
        first = fetch.fetch(fetch_args("https://cdn.example.com/a.mp3?utm_source=share", lang="en"))
        again = fetch.fetch(fetch_args("https://cdn.example.com/a.mp3", lang="en"))
        self.assertEqual((first["url"], again["reused"]), ("https://cdn.example.com/a.mp3", True))
        self.assertEqual(again["id"], first["id"])

    def test_entry_saved_before_cleaning_is_reused_with_a_clean_url(self):
        first = fetch.fetch(fetch_args("https://cdn.example.com/b.mp3", lang="en"))
        source_path = os.path.join(first["library_dir"], "source.json")
        with open(source_path, encoding="utf-8") as handle:
            stored = json.load(handle)
        stored["url"] = "https://cdn.example.com/b.mp3?si=old"
        with open(source_path, "w", encoding="utf-8") as handle:
            json.dump(stored, handle)
        self.assertEqual(fetch.fetch(fetch_args("https://cdn.example.com/b.mp3?si=new"))["url"],
                         "https://cdn.example.com/b.mp3")

    def test_spotify_skips_a_similar_show_without_the_episode(self):
        self.feeds["https://other.example.com/feed"] = podcast_feeds.Feed(url="x", episodes=[])
        result = self.spotify("Ep. 42: Tests first, always?", [],
                              [{"feedUrl": "https://other.example.com/feed"}, {"feedUrl": FEED_URL}], "Shipping")
        self.assertEqual(self.downloads.call_args.args[0], "https://cdn.example.com/ep42.m4a")
        self.assertEqual(result["kind"], "podcast")

    def test_spotify_adjacent_episode_is_offered_not_picked(self):
        # "Ep. 43" is not in the feed; "Ep. 42: ..." scores above 0.8 and must not be picked silently.
        hit = {"trackName": "Ep. 43: Tests first, always?", "feedUrl": FEED_URL}
        with self.assertRaises(errors.CastError) as caught:
            self.spotify("Ep. 43: Tests first, always?", [hit])
        self.assertEqual(caught.exception.code, errors.NEEDS_EPISODE)
        self.assertEqual(caught.exception.extra["candidates"][0]["title"], "Ep. 42: Tests first, always?")
        self.downloads.assert_not_called()

    def test_rerun_with_episode_id_from_the_candidates(self):
        key = episode_match.episode_key(sample_feed().episodes[0])
        result = fetch.fetch(fetch_args(FEED_URL, episode_id=key))
        self.assertEqual(result["title"], "Ep. 42: Tests first, always?")

    def test_user_typed_fuzzy_episode_is_warned(self):
        result = fetch.fetch(fetch_args(FEED_URL, episode="Ep 41: Reviews that catch real bug"))
        self.assertIn("episode_fuzzy_match", result["warnings"])

    def test_apple_truncated_slug_matches_by_prefix(self):
        with mock.patch.object(podcast_lookup, "itunes", return_value=apple_lookup_results()[:1]):
            result = fetch.fetch(fetch_args("https://podcasts.apple.com/us/podcast/ep-40-planning-before/id123?i=999"))
        self.assertEqual(result["title"], "Ep. 40: Planning before prompting")

    def test_spotify_only_episode(self):
        for searches in (([], []), ([], [{"feedUrl": FEED_URL}])):
            with self.subTest(searches=searches), self.assertRaises(errors.CastError) as caught:
                self.spotify("A Spotify Original Nobody Else Has", *searches, show_name="Original")
            self.assertEqual(caught.exception.code, errors.NO_PUBLIC_FEED)
            self.assertEqual(caught.exception.hint, podcast_lookup.SPOTIFY_ONLY_HINT)
        self.downloads.assert_not_called()

    def test_direct_audio_url(self):
        result = fetch.fetch(fetch_args("https://cdn.example.com/talks/agent%20review.mp3", lang="he"))
        self.assertEqual((result["kind"], result["title"], result["language"]), ("audio", "agent review", "he"))

    def test_failed_download_cleans_up(self):
        self.downloads.side_effect = errors.CastError(errors.DOWNLOAD_FAILED, "x", "y")
        with self.assertRaises(errors.CastError):
            fetch.fetch(fetch_args("https://cdn.example.com/a.mp3", lang="en"))
        self.assertEqual(self.library_entries(), [])


class AppleUrlTests(IsolatedHomeTestCase):
    def test_parse(self):
        self.assertEqual(podcast_lookup.parse_apple_url(
            "https://podcasts.apple.com/us/podcast/ep-1-hello/id123?i=456"), ("123", "456", "ep 1 hello"))
        self.assertEqual(podcast_lookup.parse_apple_url(
            "https://podcasts.apple.com/us/podcast/show/id123")[:2], ("123", None))
        with self.assertRaises(errors.CastError):
            podcast_lookup.parse_apple_url("https://podcasts.apple.com/us/browse")
