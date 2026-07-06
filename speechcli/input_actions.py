import os
import subprocess
import time

try:
    import pyperclip
except Exception:
    pyperclip = None


CLIPBOARD_RESTORE_DELAY_SECONDS = 0.2


def _session_type():
    return os.environ.get("XDG_SESSION_TYPE", "").lower()


def _run(command):
    subprocess.run(command, check=True)


def paste_text(text):
    if pyperclip is None:
        return False

    previous_clipboard = None
    should_restore = False
    try:
        previous_clipboard = pyperclip.paste()
        should_restore = True
        pyperclip.copy(text)
        if _session_type() == "wayland":
            _run(["ydotool", "key", "ctrl+v"])
        else:
            _run(["xdotool", "key", "ctrl+v"])
        time.sleep(CLIPBOARD_RESTORE_DELAY_SECONDS)
        return True
    except Exception:
        return False
    finally:
        if should_restore:
            try:
                pyperclip.copy(previous_clipboard)
            except Exception:
                pass


def type_text(text):
    if paste_text(text):
        return

    try:
        if _session_type() == "wayland":
            _run(["ydotool", "type", text])
        else:
            _run(["xdotool", "type", "--clearmodifiers", "--delay", "2", text])
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
