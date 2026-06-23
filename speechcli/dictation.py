from dataclasses import dataclass


PUNCTUATION_WORDS = {
    "period": ".",
    "full stop": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation mark": "!",
    "exclamation point": "!",
    "colon": ":",
    "semicolon": ";",
    "dash": "-",
    "hyphen": "-",
    "open parenthesis": "(",
    "close parenthesis": ")",
    "open bracket": "[",
    "close bracket": "]",
    "left bracket": "[",
    "right bracket": "]",
    "open brace": "{",
    "close brace": "}",
    "left brace": "{",
    "right brace": "}",
    "quote": '"',
    "open quote": '"',
    "close quote": '"',
    "apostrophe": "'",
    "slash": "/",
    "backslash": "\\",
    "at sign": "@",
    "hashtag": "#",
    "number sign": "#",
    "dollar sign": "$",
    "percent sign": "%",
    "ampersand": "&",
    "asterisk": "*",
    "plus sign": "+",
    "equals sign": "=",
    "underscore": "_",
}

CONTROL_PHRASES = {
    "new line": "\n",
    "newline": "\n",
    "new paragraph": "\n\n",
    "tab": "\t",
}

STOP_PHRASES = {
    "stop dictation",
    "stop listening",
    "cancel dictation",
}

DELETE_PREVIOUS_CHUNK_PHRASES = {
    "delete that",
    "scratch that",
    "undo that",
}

DELETE_PREVIOUS_WORD_PHRASES = {
    "delete last word",
    "delete previous word",
}

CLEAR_DICTATION_PHRASES = {
    "clear dictation",
    "clear text",
}

KEY_ACTION_PHRASES = {
    "press enter": ("Return",),
    "enter": ("Return",),
    "press return": ("Return",),
    "press tab": ("Tab",),
    "next field": ("Tab",),
    "previous field": ("shift", "Tab"),
    "last field": ("shift", "Tab"),
    "press escape": ("Escape",),
    "escape": ("Escape",),
    "select all": ("ctrl", "a"),
    "copy": ("ctrl", "c"),
    "copy that": ("ctrl", "c"),
    "cut": ("ctrl", "x"),
    "cut that": ("ctrl", "x"),
    "paste": ("ctrl", "v"),
    "paste that": ("ctrl", "v"),
    "undo": ("ctrl", "z"),
    "redo": ("ctrl", "y"),
    "backspace": ("BackSpace",),
    "press backspace": ("BackSpace",),
    "delete": ("Delete",),
    "press delete": ("Delete",),
    "delete selection": ("BackSpace",),
    "delete selected text": ("BackSpace",),
    "select previous word": ("ctrl", "shift", "Left"),
    "select next word": ("ctrl", "shift", "Right"),
    "select previous character": ("shift", "Left"),
    "select next character": ("shift", "Right"),
    "go to start": ("Home",),
    "go to beginning": ("Home",),
    "move to start": ("Home",),
    "move to beginning": ("Home",),
    "go to end": ("End",),
    "move to end": ("End",),
    "press home": ("Home",),
    "press end": ("End",),
    "move left": ("Left",),
    "move right": ("Right",),
    "move up": ("Up",),
    "move down": ("Down",),
}

CAPITALIZE_NEXT_PHRASES = {
    "capitalize",
    "cap",
}

UPPERCASE_NEXT_PHRASES = {
    "uppercase",
    "upper case",
    "all caps",
}

LOWERCASE_NEXT_PHRASES = {
    "lowercase",
    "lower case",
    "no caps",
}

ALL_CAPS_ON_PHRASES = {
    "all caps on",
    "caps on",
}

ALL_CAPS_OFF_PHRASES = {
    "all caps off",
    "caps off",
}

QUESTION_STARTERS = {
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "is",
    "are",
    "am",
    "do",
    "does",
    "did",
    "can",
    "could",
    "would",
    "should",
    "will",
}

TERMINAL_PUNCTUATION = ".?!"
PUNCTUATION_SUFFIXES = TERMINAL_PUNCTUATION + ",:;)]}\"'"
OPENING_PUNCTUATION = "([{\"'"
CLOSING_PUNCTUATION = ")]}\"'"
STANDALONE_SYMBOLS = {
    "/",
    "\\",
    "@",
    "#",
    "$",
    "%",
    "&",
    "*",
    "+",
    "=",
    "_",
}


@dataclass
class DictationState:
    is_first_chunk: bool = True
    capitalize_next: bool = False
    uppercase_next: bool = False
    lowercase_next: bool = False
    all_caps: bool = False
    quote_open: bool = False
    cumulative_text: str = ""
    typed_chunks: list = None

    def __post_init__(self):
        if self.typed_chunks is None:
            self.typed_chunks = []


@dataclass
class DictationResult:
    text: str = ""
    stop: bool = False
    backspace_count: int = 0
    key_actions: list = None

    def __post_init__(self):
        if self.key_actions is None:
            self.key_actions = []


@dataclass
class DictationOptions:
    auto_punctuation: bool = False


@dataclass
class KeyAction:
    keys: tuple


def _match_phrase(words, index, phrases):
    for phrase in sorted(phrases, key=lambda value: len(value.split()), reverse=True):
        phrase_words = phrase.split()
        if words[index:index + len(phrase_words)] == phrase_words:
            return phrase, len(phrase_words)
    return None, 0


def _append_spoken_word(parts, word):
    if not parts:
        parts.append(word)
        return

    previous = parts[-1]
    if previous.endswith(("\n", "\t", " ")):
        parts.append(word)
    elif previous[-1:] in OPENING_PUNCTUATION:
        parts.append(word)
    else:
        parts.append(" " + word)


def _append_punctuation(parts, mark, opening=False, closing=False):
    if opening:
        if parts and not parts[-1].endswith(("\n", "\t", " ")):
            parts.append(" ")
        parts.append(mark)
        return

    if mark in STANDALONE_SYMBOLS:
        if parts and not parts[-1].endswith((" ", "\n", "\t")):
            parts.append(" ")
        parts.append(mark)
        return

    if closing or mark in CLOSING_PUNCTUATION:
        parts.append(mark)
        return

    if mark in OPENING_PUNCTUATION:
        if parts and not parts[-1].endswith(("\n", "\t", " ")):
            parts.append(" ")
        parts.append(mark)
        return

    while parts and parts[-1] == " ":
        parts.pop()
    parts.append(mark)


def _has_terminal_punctuation(text):
    return text.rstrip().endswith(tuple(TERMINAL_PUNCTUATION))


def _infer_terminal_punctuation(words):
    if words and words[0] in QUESTION_STARTERS:
        return "?"
    return "."


def _apply_sentence_capitalization(parts, state):
    if parts and _has_terminal_punctuation(parts[-1]):
        state.capitalize_next = True


def _apply_auto_punctuation(text, words, options, state):
    if (
        not options.auto_punctuation
        or not text.strip()
        or text.rstrip().endswith(tuple(PUNCTUATION_SUFFIXES + "\n\t"))
    ):
        return text

    mark = _infer_terminal_punctuation(words)
    state.capitalize_next = True
    return text + mark


def _delete_previous_word(state):
    text = state.cumulative_text
    if not text:
        return 0

    end = len(text)
    while end > 0 and text[end - 1].isspace():
        end -= 1

    start = end
    while start > 0 and not text[start - 1].isspace():
        start -= 1

    while start > 0 and text[start - 1] == " ":
        start -= 1

    deleted_count = len(text) - start
    state.cumulative_text = text[:start]
    state.typed_chunks = []
    if state.cumulative_text:
        state.typed_chunks.append(state.cumulative_text)
    state.is_first_chunk = not bool(state.cumulative_text)
    return deleted_count


def apply_dictation_edit(normalized, state):
    if normalized in DELETE_PREVIOUS_CHUNK_PHRASES:
        if not state.typed_chunks:
            return DictationResult()

        deleted_text = state.typed_chunks.pop()
        state.cumulative_text = state.cumulative_text[:-len(deleted_text)]
        state.is_first_chunk = not bool(state.cumulative_text)
        return DictationResult(backspace_count=len(deleted_text))

    if normalized in DELETE_PREVIOUS_WORD_PHRASES:
        return DictationResult(backspace_count=_delete_previous_word(state))

    if normalized in CLEAR_DICTATION_PHRASES:
        deleted_count = len(state.cumulative_text)
        state.cumulative_text = ""
        state.typed_chunks = []
        state.is_first_chunk = True
        state.capitalize_next = False
        state.uppercase_next = False
        state.lowercase_next = False
        state.all_caps = False
        state.quote_open = False
        return DictationResult(backspace_count=deleted_count)

    return None


def apply_key_action(normalized):
    keys = KEY_ACTION_PHRASES.get(normalized)
    if keys is None:
        return None
    return DictationResult(key_actions=[KeyAction(keys)])


def apply_casing_mode(normalized, state):
    if normalized in ALL_CAPS_ON_PHRASES:
        state.all_caps = True
        state.capitalize_next = False
        state.lowercase_next = False
        state.uppercase_next = False
        return DictationResult()

    if normalized in ALL_CAPS_OFF_PHRASES:
        state.all_caps = False
        state.uppercase_next = False
        return DictationResult()

    return None


def apply_word_casing(word, state):
    if state.lowercase_next:
        state.lowercase_next = False
        return word.lower()

    if state.uppercase_next or state.all_caps:
        state.uppercase_next = False
        state.capitalize_next = False
        return word.upper()

    if state.capitalize_next:
        state.capitalize_next = False
        return word[:1].upper() + word[1:]

    return word


def format_dictation_text(raw_text, state, options=None):
    if options is None:
        options = DictationOptions()

    raw_words = raw_text.strip().split()
    words = [word.lower() for word in raw_words]
    if not words:
        return DictationResult()

    normalized = " ".join(words)
    if normalized in STOP_PHRASES:
        return DictationResult(stop=True)

    casing_result = apply_casing_mode(normalized, state)
    if casing_result is not None:
        return casing_result

    edit_result = apply_dictation_edit(normalized, state)
    if edit_result is not None:
        return edit_result

    key_result = apply_key_action(normalized)
    if key_result is not None:
        return key_result

    parts = []
    index = 0
    while index < len(words):
        phrase, length = _match_phrase(words, index, STOP_PHRASES)
        if phrase and len(words) == length:
            return DictationResult("".join(parts), stop=True)

        phrase, length = _match_phrase(words, index, CONTROL_PHRASES)
        if phrase:
            parts.append(CONTROL_PHRASES[phrase])
            state.capitalize_next = phrase == "new paragraph"
            index += length
            continue

        phrase, length = _match_phrase(words, index, PUNCTUATION_WORDS)
        if phrase:
            mark = PUNCTUATION_WORDS[phrase]
            opening = phrase.startswith(("open ", "left "))
            closing = phrase.startswith(("close ", "right "))
            if phrase == "quote":
                opening = not state.quote_open
                closing = state.quote_open
                state.quote_open = not state.quote_open
            elif phrase == "open quote":
                state.quote_open = True
            elif phrase == "close quote":
                state.quote_open = False
            _append_punctuation(parts, mark, opening=opening, closing=closing)
            if mark in TERMINAL_PUNCTUATION:
                state.capitalize_next = True
            index += length
            continue

        phrase, length = _match_phrase(words, index, CAPITALIZE_NEXT_PHRASES)
        if phrase and index + length < len(words):
            state.capitalize_next = True
            state.uppercase_next = False
            state.lowercase_next = False
            index += length
            continue

        phrase, length = _match_phrase(words, index, UPPERCASE_NEXT_PHRASES)
        if phrase and index + length < len(words):
            state.uppercase_next = True
            state.lowercase_next = False
            state.capitalize_next = False
            index += length
            continue

        phrase, length = _match_phrase(words, index, LOWERCASE_NEXT_PHRASES)
        if phrase and index + length < len(words):
            state.lowercase_next = True
            state.uppercase_next = False
            state.capitalize_next = False
            index += length
            continue

        word = raw_words[index]
        word = apply_word_casing(word, state)
        _append_spoken_word(parts, word)
        index += 1

    text = "".join(parts)
    if not text:
        return DictationResult()

    text = _apply_auto_punctuation(text, words, options, state)
    _apply_sentence_capitalization([text], state)

    if not state.is_first_chunk and text[0] not in ".,!?:;\n\t)]":
        text = " " + text
    state.is_first_chunk = False
    state.cumulative_text += text
    state.typed_chunks.append(text)
    return DictationResult(text=text)
