"""Shared test helpers: an isolated cast2skill home, and running the real CLI."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests import ENTRY_SCRIPT, FIXTURES_DIR


def fixture_path(name):
    return os.path.join(FIXTURES_DIR, name)


def read_fixture(name):
    with open(fixture_path(name), encoding="utf-8") as handle:
        return handle.read()


class IsolatedHomeTestCase(unittest.TestCase):
    """CAST2SKILL_HOME points at a fresh temp folder; transcriber env cleared."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="cast2skill-test-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        patcher = mock.patch.dict(os.environ, {"CAST2SKILL_HOME": self.home})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("CAST2SKILL_TRANSCRIBER_DIR", None)

    def library_entries(self):
        library = os.path.join(self.home, "library")
        return sorted(os.listdir(library)) if os.path.isdir(library) else []

    def start_patch(self, patcher):
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started

    def run_cli(self, *argv, stdin_text=None, extra_env=None):
        """Run cast2skill.py in a real process. Returns (exit code, parsed stdout, stderr)."""
        env = dict(os.environ, **(extra_env or {}))
        completed = subprocess.run(
            [sys.executable, ENTRY_SCRIPT] + list(argv), input=stdin_text,
            capture_output=True, text=True, env=env,
            stdin=None if stdin_text is not None else subprocess.DEVNULL,
        )
        lines = completed.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1, f"stdout must be one JSON line:\n{completed.stdout}\n{completed.stderr}")
        return completed.returncode, json.loads(lines[0]), completed.stderr
