"""config, storage, transcriber lookup, doctor, and the CLI's JSON contract."""

import datetime
import json
import os
import subprocess
from unittest import mock

from cast2skill_core import doctor, errors, permission_rule, storage, transcriber
from tests import ENTRY_SCRIPT
from tests.support import IsolatedHomeTestCase

CACHED_SCRIPT = "/Users/u/.claude/plugins/cache/cast2skill/cast2skill/0.1.0/skills/learn/scripts/cast2skill.py"


def make_fake_transcriber(folder):
    """A folder that passes looks_like_transcriber (transcribe.py + executable venv python)."""
    os.makedirs(os.path.join(folder, ".venv", "bin"))
    open(os.path.join(folder, "transcribe.py"), "w").close()
    python = transcriber.venv_python(folder)
    with open(python, "w") as handle:
        handle.write("#!/bin/sh\n")
    os.chmod(python, 0o755)
    return folder


class ConfigTests(IsolatedHomeTestCase):
    def test_defaults_without_file(self):
        self.assertEqual(storage.load_config(),
                         {"transcriber_dir": None, "default_lang": None, "keep_audio": False})

    def test_set_and_get_through_the_cli(self):
        code, result, _ = self.run_cli("config", "set", "default_lang", "EN")
        self.assertEqual((code, result), (0, {"key": "default_lang", "value": "en"}))
        code, result, _ = self.run_cli("config", "get", "default_lang")
        self.assertEqual(result["value"], "en")
        with open(os.path.join(self.home, "config.json")) as handle:
            self.assertEqual(json.load(handle)["default_lang"], "en")

    def test_value_parsing(self):
        self.assertIs(storage.parse_config_value("keep_audio", "TRUE"), True)
        self.assertIsNone(storage.parse_config_value("default_lang", "null"))
        self.assertEqual(storage.parse_config_value("transcriber_dir", "~/x"),
                         os.path.expanduser("~/x"))

    def test_bad_key_and_value_codes(self):
        code, result, _ = self.run_cli("config", "get", "colour")
        self.assertEqual((code, result["error"]["code"]), (1, errors.BAD_CONFIG_KEY))
        code, result, _ = self.run_cli("config", "set", "keep_audio", "maybe")
        self.assertEqual(result["error"]["code"], errors.BAD_CONFIG_VALUE)

    def test_broken_config_file_is_reported(self):
        with open(os.path.join(self.home, "config.json"), "w") as handle:
            handle.write("{not json")
        with self.assertRaises(errors.CastError) as caught:
            storage.load_config()
        self.assertEqual(caught.exception.code, errors.BAD_CONFIG_VALUE)


class LibraryTests(IsolatedHomeTestCase):
    def test_slugify(self):
        self.assertEqual(storage.slugify("Episode 12: Agents, Tests & You!"),
                         "episode-12-agents-tests-you")
        self.assertEqual(storage.slugify("פרק 3 על סוכנים"), "פרק-3-על-סוכנים")
        self.assertEqual(storage.slugify("!!!"), "source")
        self.assertLessEqual(len(storage.slugify("x" * 200)), storage.MAX_SLUG_LENGTH)

    def test_entry_folders_never_collide(self):
        day = datetime.date(2026, 11, 11)
        first = storage.new_entry_folder("Same Title", day)
        second = storage.new_entry_folder("Same Title", day)
        self.assertTrue(first.endswith("2026-11-11-same-title"))
        self.assertTrue(second.endswith("2026-11-11-same-title-2"))

    def test_find_existing_entry_needs_a_transcript(self):
        folder = storage.new_entry_folder("t")
        storage.write_json_atomically(os.path.join(folder, "source.json"), {"id": "youtube:abc"})
        self.assertIsNone(storage.find_existing_entry("youtube:abc"))
        open(os.path.join(folder, "transcript.txt"), "w").close()
        self.assertEqual(storage.find_existing_entry("youtube:abc"), folder)
        self.assertIsNone(storage.find_existing_entry("youtube:other"))


class TranscriberLookupTests(IsolatedHomeTestCase):
    def test_lookup_order(self):
        flag_dir = make_fake_transcriber(os.path.join(self.home, "flag"))
        env_dir = make_fake_transcriber(os.path.join(self.home, "env"))
        config_dir = make_fake_transcriber(os.path.join(self.home, "config"))
        config = {"transcriber_dir": config_dir}
        with mock.patch.dict(os.environ, {transcriber.ENV_VAR: env_dir}):
            self.assertEqual(transcriber.locate(flag_dir, config)["source"], "--transcriber-dir")
            self.assertEqual(transcriber.locate(None, config)["dir"], env_dir)
        self.assertEqual(transcriber.locate(None, config)["source"], "config.json")

    def test_named_folder_that_is_wrong_does_not_fall_back(self):
        with self.assertRaises(errors.CastError) as caught:
            transcriber.locate(os.path.join(self.home, "nothing-here"), {})
        self.assertEqual(caught.exception.code, errors.TRANSCRIBER_MISSING)
        self.assertIn("--transcriber-dir", caught.exception.message)

    def test_old_transcriber_without_flags_is_outdated(self):
        folder = make_fake_transcriber(os.path.join(self.home, "old"))
        cancelled = subprocess.CompletedProcess([], 1, stdout="Language: ", stderr="\nCancelled.\n")
        with mock.patch.object(transcriber, "run_transcriber", return_value=cancelled):
            with self.assertRaises(errors.CastError) as caught:
                transcriber.capabilities(folder)
        self.assertEqual(caught.exception.code, errors.TRANSCRIBER_OUTDATED)
        self.assertIn("Cancelled.", caught.exception.message)

    def test_transcribe_refuses_off_apple_silicon(self):
        with mock.patch.object(transcriber, "is_apple_silicon", return_value=False):
            with self.assertRaises(errors.CastError) as caught:
                transcriber.transcribe("/x", "/a.m4a", "en", False)
        self.assertEqual(caught.exception.code, errors.TRANSCRIPTION_UNSUPPORTED)


class DoctorTests(IsolatedHomeTestCase):
    def test_unset_transcriber_gives_a_fix_hint(self):
        with mock.patch.object(transcriber, "FALLBACK_DIRS", (os.path.join(self.home, "none"),)):
            report = doctor.run_doctor()
        failing = {check["name"]: check for check in report["checks"] if not check["ok"]}
        self.assertIn("transcriber", failing)
        self.assertIn("config set transcriber_dir", failing["transcriber"]["hint"])
        self.assertEqual(report["machine"], "Anything else")
        self.assertFalse(report["capabilities"]["podcast_or_audio_file"])
        self.assertTrue(report["capabilities"]["text"])

    def test_full_machine(self):
        folder = make_fake_transcriber(os.path.join(self.home, "t"))
        caps = {"diarization": True, "languages": ["he", "en"], "version": "1.0.0"}
        with mock.patch.object(transcriber, "capabilities", return_value=caps), \
                mock.patch.object(transcriber, "is_apple_silicon", return_value=True), \
                mock.patch.object(doctor.shutil, "which", return_value="/bin/tool"), \
                mock.patch.object(doctor, "tool_version", return_value="1"):
            report = doctor.run_doctor(folder)
        self.assertEqual(report["machine"], "Apple Silicon + audio_transcriber")
        self.assertEqual(report["failed"], [])
        self.assertTrue(all(report["capabilities"].values()))


class PermissionRuleTests(IsolatedHomeTestCase):
    """Doctor shows the allow rule and never writes settings (decision 36)."""

    def write_user_settings(self, text):
        with open(os.path.join(self.claude_config, "settings.json"), "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_installed_path_gets_a_version_free_rule(self):
        report = permission_rule.permission_report(CACHED_SCRIPT)
        self.assertEqual(report["permission_rule"], "Bash(python3 /Users/u/.claude/plugins/cache/cast2skill/"
                                                    "cast2skill/*/skills/learn/scripts/cast2skill.py *)")
        self.assertEqual(report["permission_rule_this_version"], f"Bash(python3 {CACHED_SCRIPT} *)")

    def test_a_checkout_gets_its_exact_path(self):
        report = permission_rule.permission_report("/src/cast2skill/skills/learn/scripts/cast2skill.py")
        self.assertEqual(report["permission_rule"], report["permission_rule_this_version"])
        self.assertIsNone(permission_rule.without_version_folder("/x/plugins/cache/cast2skill.py"))

    def test_reports_whether_user_settings_hold_the_rule(self):
        settings_path = os.path.join(self.claude_config, "settings.json")
        report = permission_rule.permission_report(CACHED_SCRIPT)
        self.assertEqual((report["permission_rule_in_settings"], report["user_settings_file"]), (False, settings_path))
        for rule in (report["permission_rule"], report["permission_rule_this_version"]):
            with self.subTest(rule=rule):
                self.write_user_settings(json.dumps({"permissions": {"allow": ["Read", rule]}}))
                self.assertTrue(permission_rule.permission_report(CACHED_SCRIPT)["permission_rule_in_settings"])
        self.write_user_settings("{not json")
        self.assertIsNone(permission_rule.permission_report(CACHED_SCRIPT)["permission_rule_in_settings"])

    def test_doctor_reports_the_running_script_and_writes_no_settings(self):
        code, result, _ = self.run_cli("doctor", "--transcriber-dir", os.path.join(self.home, "none"))
        self.assertEqual(code, 0)
        self.assertEqual(result["permission_rule"], f"Bash(python3 {ENTRY_SCRIPT} *)")
        self.assertFalse(result["permission_rule_in_settings"])
        self.assertEqual(os.listdir(self.claude_config), [])


class CliContractTests(IsolatedHomeTestCase):
    def test_bad_arguments_are_json_with_exit_2(self):
        for argv in (["nonsense"], [], ["config", "get"], ["fetch", "x", "--lang", "fr"]):
            with self.subTest(argv=argv):
                code, result, _ = self.run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertEqual(set(result["error"]), {"code", "message", "hint"})
                self.assertEqual(result["error"]["code"], errors.BAD_ARGUMENTS)

    def test_doctor_prints_one_json_object(self):
        code, result, _ = self.run_cli("doctor", "--transcriber-dir", os.path.join(self.home, "none"))
        self.assertEqual(code, 0)
        self.assertIn("capabilities", result)
