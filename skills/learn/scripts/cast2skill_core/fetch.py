"""`fetch`: classify the source, route it, and always clean up after a failure."""

import sys

from . import classify, sources_local, sources_youtube, storage
from .errors import BAD_ARGUMENTS, CastError
from .fetch_context import FetchContext

MAX_STDIN_BYTES = 5 * 1024 * 1024


def podcast_routes():
    """Imported on demand so text and YouTube fetches never load feed code."""
    from . import sources_podcast

    return {
        classify.ROUTE_APPLE: sources_podcast.fetch_apple,
        classify.ROUTE_SPOTIFY: sources_podcast.fetch_spotify,
        classify.ROUTE_FEED: sources_podcast.fetch_feed_url,
        classify.ROUTE_AUDIO_URL: sources_podcast.fetch_audio_url,
    }


ROUTES = {
    classify.ROUTE_PASTED: sources_local.fetch_pasted_text,
    classify.ROUTE_TEXT_FILE: sources_local.fetch_text_file,
    classify.ROUTE_AUDIO_FILE: sources_local.fetch_audio_file,
    classify.ROUTE_YOUTUBE: sources_youtube.fetch_youtube,
}


def read_stdin_text(stream):
    text = stream.read(MAX_STDIN_BYTES + 1)
    if len(text) > MAX_STDIN_BYTES:
        raise CastError(BAD_ARGUMENTS, "Pasted text is larger than 5 MB.", "Save it to a file and pass the file.")
    return text


def fetch(args, stdin=None):
    argument = " ".join(args.source)
    stdin_text = read_stdin_text(stdin or sys.stdin) if argument.strip() == classify.STDIN_MARKER else None
    source = classify.classify(argument, stdin_text)
    handler = ROUTES.get(source.route) or podcast_routes()[source.route]

    context = FetchContext(args, storage.load_config())
    try:
        return handler(source, context)
    except BaseException:
        context.discard_unfinished_folders()
        raise
