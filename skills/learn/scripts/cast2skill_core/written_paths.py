"""Where a logged `written_to` may point, and the check that the file is there.

The learn skill writes skills, rules and notes, and `log` records where. A
path in the log that was never written (a blocked write, a guess) makes the
record lie, so `log` refuses it. The allowed places mirror safety rule 4 in
skills/learn/SKILL.md:

- the user's Claude Code config folder (`$CLAUDE_CONFIG_DIR`, else
  `~/.claude`): anything under its `skills/` folder, and its `CLAUDE.md`
- the current working directory: `CLAUDE.md`, `.claude/CLAUDE.md`, and
  anything under `.claude/skills/`
- the cast2skill notes file (`notes.md` in the cast2skill home)

Both sides are compared as real paths, so a symlink or a `..` cannot lead a
logged path out of these places.
"""

import os

from . import storage

CONFIG_DIR_ENV_VAR = "CLAUDE_CONFIG_DIR"
EMPTY_VALUES = ("", "none", "null", "-")


def user_config_dir():
    """Claude Code's user folder: `$CLAUDE_CONFIG_DIR` when set, else `~/.claude`."""
    return os.path.abspath(os.path.expanduser(os.environ.get(CONFIG_DIR_ENV_VAR) or "~/.claude"))


def allowed_locations(working_dir=None):
    """(allowed files, allowed folders), each as a real path."""
    config = user_config_dir()
    cwd = working_dir or os.getcwd()
    files = (os.path.join(config, "CLAUDE.md"), os.path.join(cwd, "CLAUDE.md"),
             os.path.join(cwd, ".claude", "CLAUDE.md"), os.path.join(storage.home_dir(), "notes.md"))
    folders = (os.path.join(config, "skills"), os.path.join(cwd, ".claude", "skills"))
    return [os.path.realpath(path) for path in files], [os.path.realpath(path) for path in folders]


def is_allowed_location(real_path, working_dir=None):
    files, folders = allowed_locations(working_dir)
    return real_path in files or any(real_path.startswith(folder + os.sep) for folder in folders)


def is_empty(value):
    return value is None or str(value).strip().lower() in EMPTY_VALUES


def problem_with_written_path(value, working_dir=None):
    """(real path, None) for a file that exists in an allowed place, else (None, reason)."""
    given = str(value).strip()
    real_path = os.path.realpath(os.path.abspath(os.path.expanduser(given)))
    if not os.path.isfile(real_path):
        return None, f"written_to {given} does not exist"
    if not is_allowed_location(real_path, working_dir):
        return None, (f"written_to {given} (really {real_path}) is outside the places cast2skill "
                      "writes: skills or CLAUDE.md under the Claude Code config folder, this "
                      "folder's CLAUDE.md, .claude/CLAUDE.md or .claude/skills, and the notes file")
    return real_path, None
