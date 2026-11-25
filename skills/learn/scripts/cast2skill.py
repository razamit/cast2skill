#!/usr/bin/env python3
"""cast2skill command line: the deterministic half of the plugin.

    cast2skill.py doctor [--transcriber-dir DIR]
    cast2skill.py fetch SOURCE [--lang he|en] [--speakers] [--fast] [--episode QUERY | --episode-id ID]
    cast2skill.py transcribe FILE --lang he|en [--speakers] [--out PATH]
    cast2skill.py config get|set KEY [VALUE]
    cast2skill.py log < entries.json
    cast2skill.py check < lesson.md

Every subcommand prints exactly one JSON object on stdout. Human-readable
progress goes to stderr. On failure the object is
{"error": {"code", "message", "hint", ...}} and the exit code is non-zero
(2 for bad arguments, 1 for everything else).

Standard library only, Python 3.10+. The work lives in cast2skill_core/.
"""

import argparse
import json
import sys
import traceback

MIN_PYTHON = (3, 10)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False))


if sys.version_info[:2] < MIN_PYTHON:
    emit({"error": {
        "code": "python_too_old",
        "message": f"cast2skill needs Python 3.10+, this is {sys.version.split()[0]}.",
        "hint": "Install a newer Python (brew install python) and make sure python3 points to it.",
    }})
    sys.exit(1)

from cast2skill_core import commands  # noqa: E402  (after the version guard on purpose)
from cast2skill_core.errors import BAD_ARGUMENTS, UNEXPECTED, CastError  # noqa: E402


DRY_RUN_HINT = ("--dry-run belongs to /cast2skill:learn, not to this script. "
                "Run the same command without it; fetch only writes inside the cast2skill home.")


class JsonArgumentParser(argparse.ArgumentParser):
    """Usage errors become a bad_arguments error object, not argparse's text."""

    def error(self, message):
        if "--dry-run" in message:  # a learn-skill flag; the script itself never takes it
            raise CastError(BAD_ARGUMENTS, message, DRY_RUN_HINT)
        raise CastError(BAD_ARGUMENTS, message, f"Run `{self.prog} --help` for usage.")


def build_parser():
    parser = JsonArgumentParser(prog="cast2skill.py", allow_abbrev=False,
                                description="Fetch and transcribe sources for /cast2skill:learn.")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=JsonArgumentParser)

    doctor = sub.add_parser("doctor", help="report what works on this machine")
    doctor.add_argument("--transcriber-dir")

    fetch = sub.add_parser("fetch", help="get a transcript for a source")
    fetch.add_argument("source", nargs="+", help="URL, file path, or pasted text")
    fetch.add_argument("--lang", type=str.lower, choices=["he", "en"])
    fetch.add_argument("--speakers", action="store_true", help="anonymous speaker labels")
    fetch.add_argument("--fast", action="store_true", help="captions only, never download audio")
    fetch.add_argument("--episode", help="which podcast episode, by title")
    fetch.add_argument("--episode-id", help="which podcast episode, by the episode_id a candidate list gave")
    fetch.add_argument("--transcriber-dir")

    transcribe = sub.add_parser("transcribe", help="transcribe one local audio file")
    transcribe.add_argument("file")
    transcribe.add_argument("--lang", type=str.lower, choices=["he", "en"], required=True)
    transcribe.add_argument("--speakers", action="store_true")
    transcribe.add_argument("--out")
    transcribe.add_argument("--transcriber-dir")

    config = sub.add_parser("config", help="read or change settings")
    config.add_argument("action", choices=["get", "set"])
    config.add_argument("key")
    config.add_argument("value", nargs="?")

    sub.add_parser("log", help="record proposed lessons and decisions (JSON on stdin)")
    sub.add_parser("check", help="scan a lesson's text (stdin) for things it must never instruct")
    return parser


def main(argv):
    try:
        args = build_parser().parse_args(argv)
        emit(commands.dispatch(args))
        return 0
    except CastError as exc:
        emit(exc.as_json())
        print(f"{exc.message}\n{exc.hint}".strip(), file=sys.stderr)
        return 2 if exc.code == BAD_ARGUMENTS else 1
    except Exception as exc:  # last resort: still answer in JSON
        traceback.print_exc(file=sys.stderr)
        emit(CastError(UNEXPECTED, f"Unexpected error: {exc}",
                       "This is a bug in cast2skill. The traceback is on stderr.").as_json())
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
