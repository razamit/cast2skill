"""One function per subcommand. Each returns the JSON-ready result dict."""

import os
import sys

from . import doctor, storage, transcriber
from .errors import BAD_ARGUMENTS, FILE_NOT_FOUND, CastError


def run_doctor_command(args):
    return doctor.run_doctor(args.transcriber_dir)


def run_config_command(args):
    if args.action == "get":
        config = storage.load_config()
        if args.key not in config:
            storage.parse_config_value(args.key, "")  # raises the unknown-key error
        return {"key": args.key, "value": config[args.key]}
    if args.value is None:
        raise CastError(BAD_ARGUMENTS, "config set needs a value.",
                        "Example: config set default_lang en")
    return {"key": args.key, "value": storage.set_config_value(args.key, args.value)}


def run_transcribe_command(args):
    """Thin wrapper over audio_transcriber's flag mode, usable on its own."""
    audio_path = os.path.abspath(os.path.expanduser(args.file))
    if not os.path.isfile(audio_path):
        raise CastError(FILE_NOT_FOUND, f"No such file: {audio_path}", "Check the path.")
    found = transcriber.locate(args.transcriber_dir, storage.load_config())
    with_speakers = args.speakers and transcriber.capabilities(found["dir"]).get("diarization")
    warnings = [] if with_speakers or not args.speakers else ["diarization_unavailable"]
    # Without --out the transcriber picks a free name next to the audio itself.
    output = os.path.abspath(os.path.expanduser(args.out)) if args.out else None
    print(f"Transcribing {audio_path} ...", file=sys.stderr)
    result = transcriber.transcribe(found["dir"], audio_path, args.lang, with_speakers, output)
    return {
        "transcript_path": result["output"],
        "language": result["language"],
        "has_speakers": bool(with_speakers),
        "speakers": result.get("speakers"),
        "elapsed_s": result.get("elapsed_s"),
        "warnings": warnings,
    }


def run_fetch_command(args):
    from . import fetch  # imported lazily: the heaviest module, not needed by doctor

    return fetch.fetch(args)


def run_log_command(args):
    from . import lessons_log

    return lessons_log.record_from_stdin(sys.stdin)


HANDLERS = {
    "doctor": run_doctor_command,
    "config": run_config_command,
    "transcribe": run_transcribe_command,
    "fetch": run_fetch_command,
    "log": run_log_command,
}


def dispatch(args):
    return HANDLERS[args.command](args)
