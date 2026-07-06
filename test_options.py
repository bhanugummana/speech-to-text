import unittest

from speechcli.options import (
    DEFAULT_LANGUAGE,
    DEFAULT_LISTEN_TIMEOUT,
    DEFAULT_PAUSE_THRESHOLD,
    DEFAULT_PHRASE_TIME_LIMIT,
    DEFAULT_QUEUE_TIMEOUT,
    parse_args,
)


class OptionsTest(unittest.TestCase):
    def test_default_language_is_english_us(self):
        options = parse_args([])

        self.assertEqual(options.language, DEFAULT_LANGUAGE)

    def test_language_can_be_overridden(self):
        options = parse_args(["--language", "hi-IN"])

        self.assertEqual(options.language, "hi-IN")

    def test_saved_defaults_are_applied(self):
        options = parse_args([], {
            "auto_punctuation": True,
            "device_index": 3,
            "language": "kn-IN",
            "listen_timeout": 8.0,
            "overlay": True,
            "pause_threshold": 0.6,
            "phrase_time_limit": 22.0,
            "queue_timeout": 12.0,
            "should_copy": False,
            "should_output": False,
            "should_type": True,
        })

        self.assertTrue(options.auto_punctuation)
        self.assertEqual(options.device_index, 3)
        self.assertEqual(options.language, "kn-IN")
        self.assertEqual(options.listen_timeout, 8.0)
        self.assertTrue(options.overlay)
        self.assertEqual(options.pause_threshold, 0.6)
        self.assertEqual(options.phrase_time_limit, 22.0)
        self.assertEqual(options.queue_timeout, 12.0)
        self.assertTrue(options.should_type)
        self.assertFalse(options.should_copy)
        self.assertFalse(options.should_output)

    def test_cli_values_override_saved_defaults(self):
        options = parse_args(["--language", "en-IN"], {"language": "hi-IN"})

        self.assertEqual(options.language, "en-IN")

    def test_boolean_defaults_can_be_disabled(self):
        options = parse_args([
            "--no-auto-punctuation",
            "--no-overlay",
            "--no-save-unclear-audio",
        ], {
            "auto_punctuation": True,
            "overlay": True,
            "save_unclear_audio": True,
        })

        self.assertFalse(options.auto_punctuation)
        self.assertFalse(options.overlay)
        self.assertFalse(options.save_unclear_audio)

    def test_default_listener_timing(self):
        options = parse_args([])

        self.assertEqual(options.listen_timeout, DEFAULT_LISTEN_TIMEOUT)
        self.assertEqual(options.phrase_time_limit, DEFAULT_PHRASE_TIME_LIMIT)
        self.assertEqual(options.queue_timeout, DEFAULT_QUEUE_TIMEOUT)
        self.assertEqual(options.pause_threshold, DEFAULT_PAUSE_THRESHOLD)

    def test_listener_timing_can_be_overridden(self):
        options = parse_args([
            "--listen-timeout",
            "6.5",
            "--queue-timeout",
            "9",
            "--phrase-time-limit",
            "22",
            "--pause-threshold",
            "0.7",
        ])

        self.assertEqual(options.listen_timeout, 6.5)
        self.assertEqual(options.queue_timeout, 9)
        self.assertEqual(options.phrase_time_limit, 22)
        self.assertEqual(options.pause_threshold, 0.7)

    def test_listener_timing_must_be_positive(self):
        with self.assertRaises(SystemExit):
            parse_args(["--listen-timeout", "0"])

    def test_microphone_options(self):
        options = parse_args(["--list-microphones", "--device-index", "2"])

        self.assertTrue(options.list_microphones)
        self.assertEqual(options.device_index, 2)

    def test_device_index_must_be_nonnegative(self):
        with self.assertRaises(SystemExit):
            parse_args(["--device-index", "-1"])

    def test_existing_flags_are_preserved(self):
        options = parse_args([
            "--type",
            "--copy",
            "--auto-punctuation",
            "--overlay",
            "--save-unclear-audio",
            "--save-settings",
            "--show-settings",
        ])

        self.assertTrue(options.should_type)
        self.assertTrue(options.should_copy)
        self.assertTrue(options.auto_punctuation)
        self.assertTrue(options.overlay)
        self.assertTrue(options.save_unclear_audio)
        self.assertTrue(options.save_settings)
        self.assertTrue(options.show_settings)

    def test_explicit_action_overrides_saved_action_defaults(self):
        options = parse_args(["--copy"], {
            "should_copy": False,
            "should_output": False,
            "should_type": True,
        })

        self.assertFalse(options.should_type)
        self.assertTrue(options.should_copy)
        self.assertFalse(options.should_output)

    def test_settings_ui_flag(self):
        options = parse_args(["--settings-ui"])

        self.assertTrue(options.settings_ui)

    def test_tray_flag(self):
        options = parse_args(["--tray"])

        self.assertTrue(options.tray)


if __name__ == "__main__":
    unittest.main()
