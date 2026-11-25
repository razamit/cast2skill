"""The allow rule that stops cast2skill's own script calls from prompting.

The learn skill's `allowed-tools` grant ends at the user's next message, so
every `check` and `log` call after the user picks lessons asks again. One
Bash allow rule in the user's settings removes those prompts. Doctor shows
that rule and whether the user settings already hold it. It never writes any
settings file: changing permissions is what the plugin's own safety rules
forbid a lesson from doing (decision 36).

Rule syntax, per https://code.claude.com/docs/en/permissions.md#wildcard-patterns:
a `*` in a Bash rule matches any text, spaces included, at the start, in the
middle or at the end. The installed path holds a version folder
(`.../plugins/cache/<marketplace>/<plugin>/<version>/...`), so the
version-free rule puts a `*` there.
"""

import json
import os
import sys

from . import written_paths

SCRIPT_NAME = "cast2skill.py"
CACHE_PARTS = ["plugins", "cache"]
# plugins / cache / <marketplace> / <plugin> / <version>
VERSION_OFFSET_FROM_CACHE = 4


def running_script_path():
    """The script path as the command line named it, which is what a Bash rule matches."""
    invoked = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
    if os.path.basename(invoked) == SCRIPT_NAME:
        return invoked
    scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(scripts_dir, SCRIPT_NAME)


def without_version_folder(script_path):
    """The path with its plugin cache version folder replaced by `*`, or None outside the cache."""
    parts = script_path.split(os.sep)
    for index in range(len(parts) - 1):
        if parts[index:index + 2] != CACHE_PARTS:
            continue
        version_index = index + VERSION_OFFSET_FROM_CACHE
        if version_index < len(parts) - 1:
            return os.sep.join(parts[:version_index] + ["*"] + parts[version_index + 1:])
    return None


def bash_rule(script_path):
    return f"Bash(python3 {script_path} *)"


def user_settings_path():
    return os.path.join(written_paths.user_config_dir(), "settings.json")


def allow_rules_in(settings_path):
    """The `permissions.allow` list of a settings file; None when it cannot be read."""
    try:
        with open(settings_path, encoding="utf-8") as handle:
            settings = json.load(handle)
    except FileNotFoundError:
        return []
    except (OSError, ValueError):
        return None
    allow = (settings.get("permissions") or {}).get("allow") if isinstance(settings, dict) else None
    return [rule for rule in allow if isinstance(rule, str)] if isinstance(allow, list) else []


def permission_report(script_path=None):
    """The fields doctor adds: both rules, the settings file read, and whether a rule is in it."""
    script_path = script_path or running_script_path()
    exact_rule = bash_rule(script_path)
    version_free_path = without_version_folder(script_path)
    rule = bash_rule(version_free_path) if version_free_path else exact_rule
    settings_path = user_settings_path()
    allow_rules = allow_rules_in(settings_path)
    return {
        "permission_rule": rule,
        "permission_rule_this_version": exact_rule,
        "permission_rule_in_settings": None if allow_rules is None
        else (rule in allow_rules or exact_rule in allow_rules),
        "user_settings_file": settings_path,
    }
