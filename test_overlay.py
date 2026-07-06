import unittest

from speechcli.overlay import PREVIEW_TEXT_LIMIT, format_preview_text


class OverlayTest(unittest.TestCase):
    def test_empty_preview_text_uses_placeholder(self):
        self.assertEqual(
            format_preview_text(""),
            "Dictated text will appear here.",
        )

    def test_short_preview_text_is_unchanged(self):
        self.assertEqual(format_preview_text("hello world"), "hello world")

    def test_long_preview_text_keeps_tail_with_visible_ellipsis(self):
        text = "word " * 80

        preview = format_preview_text(text)

        self.assertEqual(len(preview), PREVIEW_TEXT_LIMIT)
        self.assertTrue(preview.startswith("..."))
        self.assertEqual(preview[3:], text[-(PREVIEW_TEXT_LIMIT - 3):])


if __name__ == "__main__":
    unittest.main()
