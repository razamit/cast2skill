"""Where cast2skill keeps things: the home folder, config.json, and the library.

Layout under the home folder (default ~/.cast2skill, or CAST2SKILL_HOME):

    config.json                 user settings
    lessons.jsonl               one line per proposed lesson and its decision
    notes.md                    ideas the user chose to keep as notes
    library/<date>-<slug>/      one folder per source:
        source.json             metadata and how the transcript was obtained
        transcript.txt
        lessons.md              what was proposed, picked, rejected, written
"""

import datetime
import json
import os
import re
import unicodedata

from .errors import BAD_CONFIG_KEY, BAD_CONFIG_VALUE, HOME_NOT_WRITABLE, CastError

HOME_ENV_VAR = "CAST2SKILL_HOME"
DEFAULT_CONFIG = {"transcriber_dir": None, "default_lang": None, "keep_audio": False}
LANGUAGES = ("he", "en")
MAX_SLUG_LENGTH = 60


def home_dir():
    return os.path.abspath(os.path.expanduser(os.environ.get(HOME_ENV_VAR) or "~/.cast2skill"))


def ensure_home():
    """Create the home and library folders, or fail with a clear hint."""
    home = home_dir()
    try:
        os.makedirs(os.path.join(home, "library"), exist_ok=True)
    except OSError as exc:
        raise CastError(HOME_NOT_WRITABLE, f"Cannot create {home}: {exc.strerror}",
                        f"Set {HOME_ENV_VAR} to a folder you can write to.")
    return home


# --------------------------------------------------------------------------
# config.json
# --------------------------------------------------------------------------

def config_path():
    return os.path.join(home_dir(), "config.json")


def load_config():
    """Defaults merged with whatever config.json holds. A broken file is an error."""
    config = dict(DEFAULT_CONFIG)
    path = config_path()
    if not os.path.exists(path):
        return config
    try:
        with open(path, encoding="utf-8") as handle:
            stored = json.load(handle)
    except (OSError, ValueError) as exc:
        raise CastError(BAD_CONFIG_VALUE, f"{path} is not valid JSON: {exc}",
                        "Fix or delete the file; defaults will be used.")
    config.update({key: stored[key] for key in DEFAULT_CONFIG if key in stored})
    return config


def parse_config_value(key, raw):
    """Turn the text given to `config set` into the stored value, validated."""
    if key not in DEFAULT_CONFIG:
        raise CastError(BAD_CONFIG_KEY, f"Unknown setting: {key}",
                        f"Known settings: {', '.join(DEFAULT_CONFIG)}")
    text = raw.strip()
    if key == "keep_audio":
        if text.lower() not in ("true", "false"):
            raise CastError(BAD_CONFIG_VALUE, "keep_audio must be true or false.")
        return text.lower() == "true"
    if text.lower() in ("", "null", "none"):
        return None
    if key == "default_lang":
        if text.lower() not in LANGUAGES:
            raise CastError(BAD_CONFIG_VALUE, f"default_lang must be one of {', '.join(LANGUAGES)} or null.")
        return text.lower()
    return os.path.abspath(os.path.expanduser(text))


def set_config_value(key, raw):
    config = load_config()
    config[key] = parse_config_value(key, raw)
    ensure_home()
    write_json_atomically(config_path(), config)
    return config[key]


def write_json_atomically(path, payload):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


# --------------------------------------------------------------------------
# Library folders
# --------------------------------------------------------------------------

def slugify(text):
    """Lowercase ASCII-and-Hebrew-safe slug: letters, digits and single dashes."""
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    slug = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-_")
    slug = re.sub(r"[-_]+", "-", slug)
    return slug[:MAX_SLUG_LENGTH].strip("-") or "source"


def library_root():
    return os.path.join(home_dir(), "library")


def find_existing_entry(source_id):
    """The library folder whose source.json has this id and a transcript, or None."""
    root = library_root()
    if not os.path.isdir(root):
        return None
    for name in sorted(os.listdir(root), reverse=True):
        folder = os.path.join(root, name)
        metadata = read_source_json(folder)
        if metadata and metadata.get("id") == source_id and \
                os.path.isfile(os.path.join(folder, "transcript.txt")):
            return folder
    return None


def read_source_json(folder):
    try:
        with open(os.path.join(folder, "source.json"), encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def new_entry_folder(title, today=None):
    """Create library/<YYYY-MM-DD>-<slug>/, adding -2, -3... if the name is taken."""
    ensure_home()
    stamp = (today or datetime.date.today()).isoformat()
    base = os.path.join(library_root(), f"{stamp}-{slugify(title)}")
    candidate, counter = base, 2
    while os.path.exists(candidate):
        candidate = f"{base}-{counter}"
        counter += 1
    os.makedirs(candidate)
    return candidate
