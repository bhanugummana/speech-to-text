import argparse


DEFAULT_LANGUAGE = "en-US"
DEFAULT_LISTEN_TIMEOUT = 10.0
DEFAULT_QUEUE_TIMEOUT = 15.0
DEFAULT_PAUSE_THRESHOLD = 1.0


def default_value(defaults, key, fallback):
    if defaults is None:
        return fallback
    return defaults.get(key, fallback)


def positive_float(value):
    try:
        parsed = float(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("must be a number") from e

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value):
    try:
        parsed = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("must be an integer") from e

    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def parse_args(argv, defaults=None):
    parser = argparse.ArgumentParser(
        prog="speechcli",
        description="Dictate text into the active desktop field.",
    )
    parser.add_argument("--type", action="store_true", dest="should_type")
    parser.add_argument("--copy", action="store_true", dest="should_copy")
    parser.add_argument("--output", action="store_true", dest="should_output")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--auto-punctuation",
        action=argparse.BooleanOptionalAction,
        default=default_value(defaults, "auto_punctuation", False),
        help="Enable or disable automatic punctuation.",
    )
    parser.add_argument(
        "--overlay",
        action=argparse.BooleanOptionalAction,
        default=default_value(defaults, "overlay", False),
        help="Enable or disable the listening overlay.",
    )
    parser.add_argument(
        "--save-settings",
        action="store_true",
        help="Save current dictation settings as defaults.",
    )
    parser.add_argument(
        "--show-settings",
        action="store_true",
        help="Print saved dictation settings and exit.",
    )
    parser.add_argument(
        "--list-microphones",
        action="store_true",
        help="List microphone device indexes and exit.",
    )
    parser.add_argument(
        "--device-index",
        type=nonnegative_int,
        default=default_value(defaults, "device_index", None),
        help="Microphone device index from --list-microphones.",
    )
    parser.add_argument(
        "--language",
        default=default_value(defaults, "language", DEFAULT_LANGUAGE),
        help="Recognition language code, for example en-US, hi-IN, or kn-IN.",
    )
    parser.add_argument(
        "--listen-timeout",
        type=positive_float,
        default=default_value(defaults, "listen_timeout", DEFAULT_LISTEN_TIMEOUT),
        help="Seconds to wait for speech to start before stopping.",
    )
    parser.add_argument(
        "--queue-timeout",
        type=positive_float,
        default=default_value(defaults, "queue_timeout", DEFAULT_QUEUE_TIMEOUT),
        help="Safety timeout while waiting for recorded audio chunks.",
    )
    parser.add_argument(
        "--pause-threshold",
        type=positive_float,
        default=default_value(defaults, "pause_threshold", DEFAULT_PAUSE_THRESHOLD),
        help="Seconds of silence that end the current dictated phrase.",
    )
    return parser.parse_args(argv)
