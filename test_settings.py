import os
import tempfile
import unittest

from speechcli.options import parse_args
from speechcli.settings import load_settings, save_settings


class SettingsTest(unittest.TestCase):
    def test_missing_settings_file_returns_empty_dict(self):
        self.assertEqual(load_settings("/tmp/speechcli-missing-settings.json"), {})

    def test_invalid_settings_file_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "settings.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not-json")

            self.assertEqual(load_settings(path), {})

    def test_save_and_load_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "settings.json")
            options = parse_args([
                "--auto-punctuation",
                "--overlay",
                "--device-index",
                "2",
                "--language",
                "hi-IN",
                "--listen-timeout",
                "7",
                "--queue-timeout",
                "11",
                "--pause-threshold",
                "0.6",
                "--phrase-time-limit",
                "22",
                "--save-unclear-audio",
                "--type",
            ])

            saved = save_settings(options, path)
            loaded = load_settings(path)

            self.assertEqual(loaded, saved)
            self.assertEqual(loaded["device_index"], 2)
            self.assertEqual(loaded["language"], "hi-IN")
            self.assertEqual(loaded["phrase_time_limit"], 22)
            self.assertTrue(loaded["auto_punctuation"])
            self.assertTrue(loaded["overlay"])
            self.assertTrue(loaded["save_unclear_audio"])
            self.assertTrue(loaded["should_type"])
            self.assertFalse(loaded["should_copy"])
            self.assertFalse(loaded["should_output"])


if __name__ == "__main__":
    unittest.main()
