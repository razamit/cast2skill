"""The one error type every subcommand raises, and the codes the skill reacts to.

A CastError always carries a stable machine-readable code, a message for the
user, and a hint saying what to do next. The skill branches on the code, so
codes are never renamed once shipped.
"""

# Codes the learn skill handles specially (SKILL.md, step 1).
NEEDS_LANG = "needs_lang"
NEEDS_EPISODE = "needs_episode"

# Everything else is shown to the user as message + hint.
BAD_ARGUMENTS = "bad_arguments"
PYTHON_TOO_OLD = "python_too_old"
HOME_NOT_WRITABLE = "home_not_writable"
BAD_CONFIG_KEY = "bad_config_key"
BAD_CONFIG_VALUE = "bad_config_value"
FILE_NOT_FOUND = "file_not_found"
EMPTY_TEXT = "empty_text"
FFMPEG_MISSING = "ffmpeg_missing"
YTDLP_MISSING = "ytdlp_missing"
YTDLP_FAILED = "ytdlp_failed"
TRANSCRIBER_MISSING = "transcriber_missing"
TRANSCRIBER_OUTDATED = "transcriber_outdated"
TRANSCRIBER_FAILED = "transcriber_failed"
TRANSCRIPTION_UNSUPPORTED = "transcription_unsupported"
NO_TRANSCRIPT_POSSIBLE = "no_transcript_possible"
NO_PUBLIC_FEED = "no_public_feed"
LOOKUP_FAILED = "lookup_failed"
FEED_UNREADABLE = "feed_unreadable"
DOWNLOAD_FAILED = "download_failed"
BAD_LOG_ENTRY = "bad_log_entry"
UNEXPECTED = "unexpected"


class CastError(Exception):
    """A failure the user can act on. `extra` adds fields to the error object."""

    def __init__(self, code, message, hint="", **extra):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.extra = extra

    def as_json(self):
        body = {"code": self.code, "message": self.message, "hint": self.hint}
        body.update(self.extra)
        return {"error": body}
