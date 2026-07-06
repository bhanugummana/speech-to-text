import json
import os


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "speechcli")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

SETTING_KEYS = (
    "auto_punctuation",
    "device_index",
    "language",
    "listen_timeout",
    "overlay",
    "pause_threshold",
    "phrase_time_limit",
    "queue_timeout",
    "save_unclear_audio",
    "should_copy",
    "should_output",
    "should_type",
)


def load_settings(path=CONFIG_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return {
        key: data[key]
        for key in SETTING_KEYS
        if key in data
    }


def settings_from_options(options):
    return {
        key: getattr(options, key)
        for key in SETTING_KEYS
        if hasattr(options, key)
    }


def save_settings(options, path=CONFIG_PATH):
    settings = settings_from_options(options)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, sort_keys=True)
        f.write("\n")
    return settings
