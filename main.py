import os

# Suppress ALSA warnings
os.environ["PYTHONWARNINGS"] = "ignore"

from ctypes import *

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
except Exception:
    pass


try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

import queue
import signal
import subprocess
import sys
import threading
import time

from speechcli.audio import create_microphone, print_microphones
from speechcli.config_ui import run_settings_window
from speechcli.dictation import (
    DictationOptions,
    DictationState,
    format_dictation_text,
)
from speechcli.input_actions import (
    backspace_text,
    press_key_actions,
    type_text,
)
from speechcli.options import parse_args
from speechcli.overlay import (
    OVERLAY_WINDOW_ARG,
    run_overlay_window,
    start_overlay,
    stop_overlay,
    update_overlay,
)
from speechcli.settings import load_settings, save_settings
from speechcli.tray import run_tray_app


PID_FILE = "/tmp/speechcli.pid"
audio_queue = queue.Queue()
running = True


def log(message, verbose=False):
    if verbose:
        print(message)


def is_pid_running(pid):
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def handle_existing_instance():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if is_pid_running(pid):
                os.kill(pid, signal.SIGINT)
                print("SpeechCLI: Stopping existing instance.")
                sys.exit(0)
        except (ValueError, OSError):
            pass

    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write PID file: {e}\n")


def cleanup_pid_file(verbose=False):
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(PID_FILE)
        log("PID file cleaned up.", verbose)
    except Exception:
        pass


def send_notification(title, message):
    try:
        subprocess.run(["notify-send", title, message], check=False)
    except Exception:
        pass


def print_settings(settings):
    if not settings:
        print("No saved settings.")
        return

    for key in sorted(settings):
        print(f"{key}: {settings[key]}")


def background_listener(recognizer, source, listen_timeout, verbose):
    global running
    if sr is None:
        return

    while running:
        try:
            with source:
                while running:
                    try:
                        audio = recognizer.listen(source, timeout=listen_timeout)
                        if running:
                            audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        log("No speech yet; still listening.", verbose)
                        continue
        except Exception as e:
            sys.stderr.write(f"\nListener thread error: {e}\n")
            if running:
                audio_queue.put(("listener_error", str(e)))
                time.sleep(1)


def queue_get_timeout(queue_timeout):
    return queue_timeout if queue_timeout and queue_timeout > 0 else 1


def handle_listener_error(error_message, overlay_process, verbose):
    update_overlay(overlay_process, "status", "Audio error - retrying")
    log(f"Audio error, retrying: {error_message}", verbose)


def recognize_audio(recognizer, audio, language, overlay_process, verbose):
    while running:
        try:
            log("Transcribing chunk...", verbose)
            update_overlay(overlay_process, "status", "Transcribing...")
            return recognizer.recognize_google(audio, language=language)
        except sr.UnknownValueError:
            update_overlay(overlay_process, "status", "Listening")
            log("Speech not understood in chunk", verbose)
            return None
        except sr.RequestError as e:
            update_overlay(overlay_process, "status", "Recognition error - retrying")
            sys.stderr.write(f"\nAPI Error: {e}\n")
            time.sleep(1)

    return None


def require_runtime_dependencies(args):
    if sr is None:
        sys.stderr.write(
            "Missing dependency: SpeechRecognition. Run ./install.sh or "
            "install requirements.txt.\n"
        )
        sys.exit(1)
    if args.should_copy and pyperclip is None:
        sys.stderr.write(
            "Missing dependency: pyperclip. Run ./install.sh or install "
            "requirements.txt.\n"
        )
        sys.exit(1)


def process_audio_result(
    raw_text,
    dictation_state,
    dictation_options,
    overlay_process,
    should_type,
    should_copy,
    should_output,
    verbose,
):
    result = format_dictation_text(raw_text, dictation_state, dictation_options)
    if result.stop:
        update_overlay(overlay_process, "status", "Stopping...")
        log("Stop command recognized.", verbose)
        return True

    text = result.text
    if result.key_actions and should_type:
        press_key_actions(result.key_actions)
        log("Pressed dictation command key action.", verbose)

    if result.backspace_count and should_type:
        backspace_text(result.backspace_count)
        log(f"⌫ Deleted {result.backspace_count} characters", verbose)
        update_overlay(overlay_process, "text", dictation_state.cumulative_text)

    if should_copy:
        pyperclip.copy(dictation_state.cumulative_text)
        log(f"📋 Copied: {dictation_state.cumulative_text}", verbose)

    if result.backspace_count and (should_output or not any([should_type, should_copy])):
        print("\b \b" * result.backspace_count, end="", flush=True)

    if not text:
        update_overlay(overlay_process, "status", "Listening")
        return False

    if should_type:
        type_text(text)
        log(f"⌨️ Typed: {text}", verbose)

    if should_output or not any([should_type, should_copy]):
        print(text, end="", flush=True)

    update_overlay(overlay_process, "text", dictation_state.cumulative_text)
    update_overlay(overlay_process, "status", "Listening")
    return False


def main():
    global running
    args = sys.argv[1:]

    if OVERLAY_WINDOW_ARG in args:
        sys.exit(run_overlay_window())

    saved_settings = load_settings()
    options = parse_args(args, saved_settings)

    if options.settings_ui:
        sys.exit(run_settings_window(saved_settings, sr, __file__))

    if options.tray:
        sys.exit(run_tray_app(saved_settings, __file__))

    if options.show_settings:
        print_settings(saved_settings)
        return

    if options.save_settings:
        saved_settings = save_settings(options)
        print_settings(saved_settings)
        return

    require_runtime_dependencies(options)

    if options.list_microphones:
        print_microphones(sr)
        return

    overlay_process = None

    handle_existing_instance()

    recognizer = sr.Recognizer()
    dictation_state = DictationState()
    dictation_options = DictationOptions(
        auto_punctuation=options.auto_punctuation,
    )
    recognizer.pause_threshold = options.pause_threshold

    source = create_microphone(sr, options.device_index)
    try:
        log("Calibrating microphone for ambient noise...", options.verbose)
        with source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        log(
            f"Adjusted energy threshold to: {recognizer.energy_threshold}",
            options.verbose,
        )

        send_notification("SpeechCLI", "Listening...")
        log("Listening...", options.verbose)
        overlay_process = start_overlay(
            options.overlay,
            __file__,
            lambda message: log(message, options.verbose),
        )

        listener_thread = threading.Thread(
            target=background_listener,
            args=(
                recognizer,
                source,
                options.listen_timeout,
                options.verbose,
            ),
            daemon=True
        )
        listener_thread.start()

        while True:
            try:
                audio = audio_queue.get(
                    block=True,
                    timeout=queue_get_timeout(options.queue_timeout),
                )
            except queue.Empty:
                update_overlay(overlay_process, "status", "Listening")
                continue

            if (
                isinstance(audio, tuple)
                and len(audio) == 2
                and audio[0] == "listener_error"
            ):
                handle_listener_error(audio[1], overlay_process, options.verbose)
                audio_queue.task_done()
                continue

            try:
                raw_text = recognize_audio(
                    recognizer,
                    audio,
                    options.language,
                    overlay_process,
                    options.verbose,
                )
                if raw_text is None:
                    continue

                should_stop = process_audio_result(
                    raw_text,
                    dictation_state,
                    dictation_options,
                    overlay_process,
                    options.should_type,
                    options.should_copy,
                    options.should_output,
                    options.verbose,
                )
                if should_stop:
                    break
            finally:
                audio_queue.task_done()

    except KeyboardInterrupt:
        log("SpeechCLI: Interrupted.", options.verbose)
    finally:
        running = False
        cleanup_pid_file(options.verbose)
        stop_overlay(overlay_process)
        send_notification("SpeechCLI", "Speech recognition stopped")

        if options.should_output or not any([options.should_type, options.should_copy]):
            print()


if __name__ == "__main__":
    main()
