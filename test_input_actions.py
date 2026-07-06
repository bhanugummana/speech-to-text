import unittest
import subprocess
from unittest.mock import patch

from speechcli import input_actions


class FakeClipboard:
    def __init__(self, initial="previous"):
        self.value = initial
        self.copied = []

    def paste(self):
        return self.value

    def copy(self, text):
        self.value = text
        self.copied.append(text)


class InputActionsTest(unittest.TestCase):
    def test_paste_text_copies_text_pastes_and_restores_clipboard(self):
        clipboard = FakeClipboard("old clipboard")

        with patch.object(input_actions, "pyperclip", clipboard):
            with patch.object(input_actions, "_session_type", return_value="x11"):
                with patch.object(input_actions, "_run") as run_command:
                    with patch.object(input_actions.time, "sleep") as sleep:
                        self.assertTrue(input_actions.paste_text("hello world"))

        run_command.assert_called_once_with(["xdotool", "key", "ctrl+v"])
        sleep.assert_called_once_with(input_actions.CLIPBOARD_RESTORE_DELAY_SECONDS)
        self.assertEqual(clipboard.copied, ["hello world", "old clipboard"])

    def test_paste_text_uses_ydotool_on_wayland(self):
        clipboard = FakeClipboard()

        with patch.object(input_actions, "pyperclip", clipboard):
            with patch.object(input_actions, "_session_type", return_value="wayland"):
                with patch.object(input_actions, "_run") as run_command:
                    with patch.object(input_actions.time, "sleep"):
                        self.assertTrue(input_actions.paste_text("hello"))

        run_command.assert_called_once_with(["ydotool", "key", "ctrl+v"])

    def test_type_text_falls_back_to_simulated_typing_when_paste_fails(self):
        with patch.object(input_actions, "paste_text", return_value=False):
            with patch.object(input_actions, "_session_type", return_value="x11"):
                with patch.object(input_actions, "_run") as run_command:
                    input_actions.type_text("fallback text")

        run_command.assert_called_once_with([
            "xdotool",
            "type",
            "--clearmodifiers",
            "--delay",
            "2",
            "fallback text",
        ])

    def test_paste_text_restores_clipboard_when_paste_command_fails(self):
        clipboard = FakeClipboard("old clipboard")

        with patch.object(input_actions, "pyperclip", clipboard):
            with patch.object(input_actions, "_session_type", return_value="x11"):
                with patch.object(input_actions, "_run", side_effect=subprocess.CalledProcessError(1, "xdotool")):
                    self.assertFalse(input_actions.paste_text("dictated text"))

        self.assertEqual(clipboard.copied, ["dictated text", "old clipboard"])
        self.assertEqual(clipboard.value, "old clipboard")


if __name__ == "__main__":
    unittest.main()
