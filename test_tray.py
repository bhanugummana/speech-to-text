import unittest

from speechcli.tray import build_tray_dictation_command, tray_dictation_values


class TrayTest(unittest.TestCase):
    def test_tray_forces_type_and_copy_mode(self):
        values = tray_dictation_values({
            "language": "hi-IN",
            "listen_timeout": 5.0,
            "overlay": False,
            "should_copy": False,
            "should_output": True,
            "should_type": False,
        })

        self.assertEqual(values["mode"], "Type and copy")
        self.assertEqual(values["language"], "hi-IN")
        self.assertIsNone(values["listen_timeout"])
        self.assertTrue(values["overlay"])

    def test_tray_command_types_and_copies_into_focused_field(self):
        command = build_tray_dictation_command({
            "auto_punctuation": True,
            "device_index": 2,
            "language": "kn-IN",
            "listen_timeout": 7.0,
            "overlay": True,
            "pause_threshold": 0.7,
            "queue_timeout": 12.0,
        }, "/app/main.py")

        self.assertIn("--type", command)
        self.assertIn("--copy", command)
        self.assertNotIn("--output", command)
        self.assertIn("--overlay", command)
        self.assertNotIn("--listen-timeout", command)
        self.assertIn("--language", command)
        self.assertIn("kn-IN", command)
        self.assertIn("--device-index", command)
        self.assertIn("2", command)


if __name__ == "__main__":
    unittest.main()
