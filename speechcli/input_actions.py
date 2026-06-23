import os
import subprocess


def _session_type():
    return os.environ.get("XDG_SESSION_TYPE", "").lower()


def _run(command):
    subprocess.run(command, check=True)


def type_text(text):
    try:
        if _session_type() == "wayland":
            _run(["ydotool", "type", text])
        else:
            _run(["xdotool", "type", "--delay", "1", text])
    except Exception as e:
        print(f"\nTyping failed: {e}")


def backspace_text(count):
    if count <= 0:
        return

    try:
        if _session_type() == "wayland":
            for _ in range(count):
                _run(["ydotool", "key", "BackSpace"])
        else:
            _run(["xdotool", "key", "--repeat", str(count), "BackSpace"])
    except Exception as e:
        print(f"\nBackspace failed: {e}")


def press_key_action(action):
    try:
        key_sequence = "+".join(action.keys)
        if _session_type() == "wayland":
            _run(["ydotool", "key", key_sequence])
        else:
            _run(["xdotool", "key", key_sequence])
    except Exception as e:
        print(f"\nKey action failed: {e}")


def press_key_actions(actions):
    for action in actions:
        press_key_action(action)
