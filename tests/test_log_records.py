"""`log` checks every `written_to` against the disk (decision 34), and every
lessons.jsonl row carries the run's outcome, with one row for a run that had
no candidates (decision 35)."""

import json
import os
import shutil
import tempfile

from cast2skill_core import errors, fetch, lessons_log
from tests.support import IsolatedHomeTestCase
from tests.test_fetch_routes import fetch_args

WRITTEN_TO_HINT = "log only files that were actually written; use written_to: none"


def write_file(path, text="x\n"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


class LogTestCase(IsolatedHomeTestCase):
    """A fetched library entry, and a project folder that is the working directory."""

    def setUp(self):
        super().setUp()
        self.folder = fetch.fetch(fetch_args("Name each function after its value."))["library_dir"]
        self.project = tempfile.mkdtemp(prefix="cast2skill-project-")
        self.outside = tempfile.mkdtemp(prefix="cast2skill-outside-")
        for folder in (self.project, self.outside):
            self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.project)

    def candidate(self, written_to, decision="picked", title="Name functions by value"):
        return {"title": title, "type": "rule", "decision": decision, "written_to": written_to,
                "evidence": {"timestamp": "00:01:00", "quote": "name it after what it returns"}}

    def entry(self, *candidates, outcome="written"):
        return {"library_dir": self.folder, "outcome": outcome, "candidates": list(candidates)}

    def log_files(self):
        return [path for path in (os.path.join(self.folder, "lessons.md"), os.path.join(self.home, "lessons.jsonl"))
                if os.path.exists(path)]

    def jsonl_rows(self):
        with open(os.path.join(self.home, "lessons.jsonl"), encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]

    def assert_refused(self, entry, path_in_message, reason=""):
        with self.assertRaises(errors.CastError) as caught:
            lessons_log.record(entry)
        self.assertEqual(caught.exception.code, errors.BAD_LOG_ENTRY)
        self.assertIn(path_in_message, caught.exception.message)
        self.assertIn(reason, caught.exception.message)
        self.assertIn(WRITTEN_TO_HINT, caught.exception.hint.lower())
        self.assertEqual(self.log_files(), [], "a refused entry must write nothing")


class WrittenToTests(LogTestCase):
    def test_missing_file_is_refused_through_the_cli(self):
        # The e2e failure: a blocked write to .claude/skills logged as written.
        missing = os.path.join(self.project, ".claude", "skills", "red-green-tdd", "SKILL.md")
        code, result, _ = self.run_cli("log", stdin_text=json.dumps(self.entry(self.candidate(missing))))
        self.assertEqual((code, result["error"]["code"]), (1, errors.BAD_LOG_ENTRY))
        self.assertIn(missing, result["error"]["message"])
        self.assertIn("does not exist", result["error"]["message"])
        self.assertIn(WRITTEN_TO_HINT, result["error"]["hint"].lower())
        self.assertEqual(self.log_files(), [])

    def test_path_outside_the_allowed_places_is_refused(self):
        stray = write_file(os.path.join(self.outside, "CLAUDE.md"))
        self.assert_refused(self.entry(self.candidate(stray)), stray, "is outside")
        elsewhere = write_file(os.path.join(self.project, "docs", "notes.md"))
        self.assert_refused(self.entry(self.candidate(elsewhere)), elsewhere, "is outside")

    def test_dot_dot_cannot_escape(self):
        target = write_file(os.path.join(self.outside, "SKILL.md"))
        os.makedirs(os.path.join(self.claude_config, "skills"))
        relative_outside = os.path.relpath(self.outside, os.path.join(self.claude_config, "skills"))
        sneaky = os.path.join(self.claude_config, "skills", relative_outside, "SKILL.md")
        self.assertTrue(os.path.samefile(sneaky, target))
        self.assert_refused(self.entry(self.candidate(sneaky)), sneaky, "is outside")

    def test_symlink_cannot_escape(self):
        write_file(os.path.join(self.outside, "SKILL.md"))
        skills = os.path.join(self.project, ".claude", "skills")
        os.makedirs(skills)
        os.symlink(self.outside, os.path.join(skills, "linked"))
        linked = os.path.join(skills, "linked", "SKILL.md")
        self.assert_refused(self.entry(self.candidate(linked)), linked, "is outside")

    def test_every_allowed_place_is_accepted(self):
        allowed = {
            "user skill": os.path.join(self.claude_config, "skills", "name-by-value", "SKILL.md"),
            "user CLAUDE.md": os.path.join(self.claude_config, "CLAUDE.md"),
            "project CLAUDE.md": os.path.join(self.project, "CLAUDE.md"),
            "project .claude/CLAUDE.md": os.path.join(self.project, ".claude", "CLAUDE.md"),
            "project skill": os.path.join(self.project, ".claude", "skills", "name-by-value", "SKILL.md"),
            "notes file": os.path.join(self.home, "notes.md"),
        }
        for place, path in allowed.items():
            with self.subTest(place=place):
                write_file(path)
                result = lessons_log.record(self.entry(self.candidate(path)))
                self.assertEqual(result["logged"], 1)
                self.assertEqual(self.jsonl_rows()[-1]["written_to"], os.path.realpath(path))

    def test_relative_path_resolves_against_the_working_directory(self):
        write_file(os.path.join(self.project, "CLAUDE.md"))
        lessons_log.record(self.entry(self.candidate("CLAUDE.md")))
        self.assertEqual(self.jsonl_rows()[-1]["written_to"], os.path.realpath(os.path.join(self.project, "CLAUDE.md")))

    def test_written_to_needs_decision_picked(self):
        path = write_file(os.path.join(self.claude_config, "CLAUDE.md"))
        self.assert_refused(self.entry(self.candidate(path, decision="rejected")), "not picked")
        self.assert_refused(self.entry(self.candidate(path, decision="dry_run"), outcome="dry_run"), "not picked")

    def test_one_refused_candidate_refuses_the_whole_entry(self):
        good = write_file(os.path.join(self.claude_config, "CLAUDE.md"))
        missing = os.path.join(self.claude_config, "skills", "never-written", "SKILL.md")
        entry = self.entry(self.candidate(good), self.candidate(missing, title="Blocked skill"))
        self.assert_refused(entry, missing, "does not exist")

    def test_a_failed_write_is_logged_as_picked_with_none(self):
        plain = (f"library_dir: {self.folder}\noutcome: written\n---\ntitle: Blocked skill\ntype: procedure\n"
                 "decision: picked\nwritten_to: none\n")
        code, result, _ = self.run_cli("log", stdin_text=plain)
        self.assertEqual((code, result["logged"]), (0, 1), result)
        self.assertEqual((self.jsonl_rows()[0]["decision"], self.jsonl_rows()[0]["written_to"]), ("picked", None))


class OutcomeRowTests(LogTestCase):
    def test_every_row_stores_the_outcome(self):
        lessons_log.record(self.entry(self.candidate(None, decision="rejected"),
                                      self.candidate(None, decision="rejected", title="Other"),
                                      outcome="nothing_picked"))
        self.assertEqual([row["outcome"] for row in self.jsonl_rows()], ["nothing_picked"] * 2)

    def test_a_run_without_candidates_leaves_one_row(self):
        for outcome in ("nothing_worth_adding", "nothing_picked", "dry_run"):
            with self.subTest(outcome=outcome):
                result = lessons_log.record({"library_dir": self.folder, "outcome": outcome,
                                             "reason": "An ad, no method.", "candidates": []})
                self.assertEqual(result["logged"], 0)
                row = self.jsonl_rows()[-1]
                self.assertEqual((row["outcome"], row["reason"]), (outcome, "An ad, no method."))
                for field in lessons_log.CANDIDATE_FIELDS:
                    self.assertIsNone(row[field], field)
                self.assertTrue(row["source_id"])
        self.assertEqual(len(self.jsonl_rows()), 3)

    def test_old_rows_stay_readable(self):
        old_row = {"title": "Older lesson", "type": "rule", "decision": "rejected", "written_to": None,
                   "date": "2026-11-11T10:00:00", "source_id": "text:abc"}
        write_file(os.path.join(self.home, "lessons.jsonl"), json.dumps(old_row) + "\n")
        lessons_log.record({"library_dir": self.folder, "outcome": "nothing_worth_adding", "candidates": []})
        rows = self.jsonl_rows()
        self.assertEqual(rows[0], old_row)
        self.assertEqual((rows[1]["outcome"], rows[1]["title"]), ("nothing_worth_adding", None))
