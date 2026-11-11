"""Tests run with: python3 -m unittest discover -s tests -t .

Puts the plugin's scripts folder on sys.path so tests import cast2skill_core
the same way cast2skill.py does.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills", "learn", "scripts")
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures")
ENTRY_SCRIPT = os.path.join(SCRIPTS_DIR, "cast2skill.py")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
