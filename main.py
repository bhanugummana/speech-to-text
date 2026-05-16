import os

# Suppress ALSA warnings
os.environ["PYTHONWARNINGS"] = "ignore"

from ctypes import *
from contextlib import contextmanager

# Suppress ALSA stderr
ERROR_HANDLER_FUNC = CFUNCTYPE(
    None,
    c_char_p,
    c_int,
    c_char_p,
    c_int,
    c_char_p
)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

try:
    asound = cdll.LoadLibrary("libasound.so")
    asound.snd_lib_error_set_handler(c_error_handler)
except:
    pass


import speech_recognition as sr
import pyperclip
import subprocess
import sys



def log(message, verbose=False):
    if verbose:
        print(message)


def speech_to_text(verbose=False):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        log("🎤 Listening...", verbose)

        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        return text

    except sr.UnknownValueError:
        print("Could not understand audio")
        sys.exit(1)

    except sr.RequestError as e:
        print(f"API Error: {e}")
        sys.exit(1)


def type_text(text):
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()

    try:
        if session == "wayland":
            subprocess.run(["ydotool", "type", text], check=True)
        else:
            subprocess.run(
                ["xdotool", "type", "--delay", "1", text],
                check=True
            )

    except Exception as e:
        print(f"Typing failed: {e}")


def copy_text(text):
    pyperclip.copy(text)


def main():
    args = sys.argv[1:]

    should_type = "--type" in args
    should_copy = "--copy" in args
    should_output = "--output" in args
    verbose = "--verbose" in args

    text = speech_to_text(verbose)

    # Always print clean output
    if should_output or not any([should_type, should_copy]):
        print(text)

    if should_copy:
        copy_text(text)
        log("📋 Copied to clipboard", verbose)

    if should_type:
        type_text(text)
        log("⌨️ Typed text", verbose)


if __name__ == "__main__":
    main()