import unittest

from speechcli.dictation import DictationOptions, DictationState, format_dictation_text


class DictationFormattingTest(unittest.TestCase):
    def test_punctuation_words_are_converted(self):
        state = DictationState()

        result = format_dictation_text(
            "hello comma how are you question mark",
            state,
        )

        self.assertEqual(result.text, "hello, how are you?")
        self.assertFalse(result.stop)
        self.assertEqual(state.cumulative_text, "hello, how are you?")

    def test_quote_commands_format_without_inner_spaces(self):
        state = DictationState()

        result = format_dictation_text("open quote hello world close quote", state)

        self.assertEqual(result.text, '"hello world"')

    def test_plain_quote_toggles_open_and_close(self):
        state = DictationState()

        result = format_dictation_text("quote hello quote", state)

        self.assertEqual(result.text, '"hello"')

    def test_brace_commands_format_without_inner_spaces(self):
        state = DictationState()

        result = format_dictation_text("open brace hello world close brace", state)

        self.assertEqual(result.text, "{hello world}")

    def test_symbol_commands_are_converted(self):
        state = DictationState()

        result = format_dictation_text("email at sign example", state)

        self.assertEqual(result.text, "email @ example")

    def test_terminal_punctuation_capitalizes_next_sentence(self):
        state = DictationState()

        first = format_dictation_text("hello period", state)
        second = format_dictation_text("next sentence", state)

        self.assertEqual(first.text, "hello.")
        self.assertEqual(second.text, " Next sentence")

    def test_following_chunks_get_separating_space(self):
        state = DictationState()

        first = format_dictation_text("hello world", state)
        second = format_dictation_text("this is next", state)

        self.assertEqual(first.text, "hello world")
        self.assertEqual(second.text, " this is next")
        self.assertEqual(state.cumulative_text, "hello world this is next")

    def test_newline_and_paragraph_commands_are_converted(self):
        state = DictationState()

        line = format_dictation_text("hello new line world", state)
        paragraph = format_dictation_text("new paragraph next sentence", state)

        self.assertEqual(line.text, "hello\nworld")
        self.assertEqual(paragraph.text, "\n\nNext sentence")

    def test_capitalize_command_affects_next_word(self):
        state = DictationState()

        result = format_dictation_text("hello capitalize world", state)

        self.assertEqual(result.text, "hello World")

    def test_uppercase_and_lowercase_commands_affect_next_word(self):
        state = DictationState()

        upper = format_dictation_text("say uppercase hello", state)
        lower = format_dictation_text("lowercase WORLD", state)

        self.assertEqual(upper.text, "say HELLO")
        self.assertEqual(lower.text, " world")

    def test_all_caps_mode_can_be_toggled(self):
        state = DictationState()

        start = format_dictation_text("all caps on", state)
        first = format_dictation_text("hello world", state)
        stop = format_dictation_text("all caps off", state)
        second = format_dictation_text("normal text", state)

        self.assertEqual(start.text, "")
        self.assertEqual(first.text, "HELLO WORLD")
        self.assertEqual(stop.text, "")
        self.assertEqual(second.text, " normal text")

    def test_command_matching_does_not_lowercase_spoken_words(self):
        state = DictationState()

        result = format_dictation_text("OpenAI comma Seattle", state)

        self.assertEqual(result.text, "OpenAI, Seattle")

    def test_stop_command_is_typed_by_default(self):
        state = DictationState()

        result = format_dictation_text("stop dictation", state)

        self.assertFalse(result.stop)
        self.assertEqual(result.text, "stop dictation")
        self.assertEqual(state.cumulative_text, "stop dictation")

    def test_stop_command_can_be_enabled(self):
        state = DictationState()
        options = DictationOptions(allow_voice_stop=True)

        result = format_dictation_text("stop dictation", state, options)

        self.assertTrue(result.stop)
        self.assertEqual(result.text, "")
        self.assertEqual(state.cumulative_text, "")

    def test_delete_that_removes_previous_chunk(self):
        state = DictationState()
        format_dictation_text("hello world", state)
        format_dictation_text("second chunk", state)

        result = format_dictation_text("delete that", state)

        self.assertEqual(result.text, "")
        self.assertEqual(result.backspace_count, len(" second chunk"))
        self.assertEqual(state.cumulative_text, "hello world")

    def test_delete_previous_word_removes_spacing_and_last_word(self):
        state = DictationState()
        format_dictation_text("hello world", state)
        format_dictation_text("delete last word", state)

        self.assertEqual(state.cumulative_text, "hello")

    def test_clear_dictation_removes_all_session_text(self):
        state = DictationState()
        format_dictation_text("hello world", state)

        result = format_dictation_text("clear dictation", state)

        self.assertEqual(result.backspace_count, len("hello world"))
        self.assertEqual(state.cumulative_text, "")
        self.assertTrue(state.is_first_chunk)

    def test_press_enter_returns_key_action_without_text(self):
        state = DictationState()

        result = format_dictation_text("press enter", state)

        self.assertEqual(result.text, "")
        self.assertEqual(result.key_actions[0].keys, ("Return",))
        self.assertEqual(state.cumulative_text, "")
        self.assertTrue(state.is_first_chunk)

    def test_field_navigation_returns_key_actions(self):
        state = DictationState()

        next_result = format_dictation_text("next field", state)
        previous_result = format_dictation_text("previous field", state)

        self.assertEqual(next_result.key_actions[0].keys, ("Tab",))
        self.assertEqual(previous_result.key_actions[0].keys, ("shift", "Tab"))

    def test_select_all_returns_shortcut_key_action(self):
        state = DictationState()

        result = format_dictation_text("select all", state)

        self.assertEqual(result.text, "")
        self.assertEqual(result.key_actions[0].keys, ("ctrl", "a"))

    def test_clipboard_shortcuts_return_key_actions_without_changing_text(self):
        state = DictationState()
        format_dictation_text("hello world", state)

        copy_result = format_dictation_text("copy that", state)
        paste_result = format_dictation_text("paste", state)
        cut_result = format_dictation_text("cut that", state)

        self.assertEqual(copy_result.key_actions[0].keys, ("ctrl", "c"))
        self.assertEqual(paste_result.key_actions[0].keys, ("ctrl", "v"))
        self.assertEqual(cut_result.key_actions[0].keys, ("ctrl", "x"))
        self.assertEqual(state.cumulative_text, "hello world")

    def test_undo_redo_and_delete_selection_return_key_actions(self):
        state = DictationState()

        undo_result = format_dictation_text("undo", state)
        redo_result = format_dictation_text("redo", state)
        delete_result = format_dictation_text("delete selection", state)
        backspace_result = format_dictation_text("press backspace", state)
        press_delete_result = format_dictation_text("press delete", state)

        self.assertEqual(undo_result.key_actions[0].keys, ("ctrl", "z"))
        self.assertEqual(redo_result.key_actions[0].keys, ("ctrl", "y"))
        self.assertEqual(delete_result.key_actions[0].keys, ("BackSpace",))
        self.assertEqual(backspace_result.key_actions[0].keys, ("BackSpace",))
        self.assertEqual(press_delete_result.key_actions[0].keys, ("Delete",))

    def test_selection_navigation_returns_key_actions(self):
        state = DictationState()

        previous_word = format_dictation_text("select previous word", state)
        next_word = format_dictation_text("select next word", state)
        previous_character = format_dictation_text("select previous character", state)
        next_character = format_dictation_text("select next character", state)

        self.assertEqual(previous_word.key_actions[0].keys, ("ctrl", "shift", "Left"))
        self.assertEqual(next_word.key_actions[0].keys, ("ctrl", "shift", "Right"))
        self.assertEqual(previous_character.key_actions[0].keys, ("shift", "Left"))
        self.assertEqual(next_character.key_actions[0].keys, ("shift", "Right"))

    def test_move_to_end_returns_navigation_key_action(self):
        state = DictationState()

        result = format_dictation_text("move to end", state)

        self.assertEqual(result.text, "")
        self.assertEqual(result.key_actions[0].keys, ("End",))

    def test_auto_punctuation_adds_period(self):
        state = DictationState()
        options = DictationOptions(auto_punctuation=True)

        result = format_dictation_text("hello world", state, options)

        self.assertEqual(result.text, "hello world.")
        self.assertEqual(state.cumulative_text, "hello world.")

    def test_auto_punctuation_infers_question_mark(self):
        state = DictationState()
        options = DictationOptions(auto_punctuation=True)

        result = format_dictation_text("how are you", state, options)

        self.assertEqual(result.text, "how are you?")

    def test_auto_punctuation_does_not_double_punctuate(self):
        state = DictationState()
        options = DictationOptions(auto_punctuation=True)

        result = format_dictation_text("hello comma", state, options)

        self.assertEqual(result.text, "hello,")

    def test_auto_punctuation_capitalizes_next_chunk(self):
        state = DictationState()
        options = DictationOptions(auto_punctuation=True)

        first = format_dictation_text("hello world", state, options)
        second = format_dictation_text("next sentence", state, options)

        self.assertEqual(first.text, "hello world.")
        self.assertEqual(second.text, " Next sentence.")


if __name__ == "__main__":
    unittest.main()
