import unittest

from speechcli.config_ui import build_dictation_args, settings_to_form_values


class ConfigUiTest(unittest.TestCase):
    def test_saved_type_mode_is_shown_in_form_values(self):
        values = settings_to_form_values({
            "should_copy": False,
            "should_output": False,
            "should_type": True,
        })

        self.assertEqual(values["mode"], "Type into active app")

    def test_build_dictation_args_includes_selected_controls(self):
        args = build_dictation_args({
            "auto_punctuation": True,
            "device_index": 2,
            "language": "hi-IN",
            "listen_timeout": 7.0,
            "mode": "Type and copy",
            "overlay": True,
            "pause_threshold": 0.6,
            "queue_timeout": 11.0,
        })

        self.assertEqual(args[:2], ["--type", "--copy"])
        self.assertIn("--auto-punctuation", args)
        self.assertIn("--overlay", args)
        self.assertIn("--device-index", args)
        self.assertIn("2", args)
        self.assertIn("--language", args)
        self.assertIn("hi-IN", args)


if __name__ == "__main__":
    unittest.main()
