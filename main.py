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
CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache")),
    "speechcli",
)
UNCLEAR_AUDIO_DIR = os.path.join(CACHE_DIR, "unclear-audio")
audio_queue = queue.Queue()
running = True
MAX_SHUTDOWN_SETTLE_SECONDS = 5.0
MIN_SHUTDOWN_SETTLE_SECONDS = 0.75
TRANSCRIPT_CONFIDENCE_MARGIN = 0.12


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


def background_listener(recognizer, source, listen_timeout, phrase_time_limit, verbose):
    global running
    if sr is None:
        return

    while running:
        try:
            with source:
                while running:
                    try:
                        audio = recognizer.listen(
                            source,
                            timeout=listen_timeout,
                            phrase_time_limit=phrase_time_limit,
                        )
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


def save_unclear_audio(audio, reason, directory=UNCLEAR_AUDIO_DIR):
    if audio is None or not hasattr(audio, "get_wav_data"):
        return None

    safe_reason = "".join(
        character if character.isalnum() or character in ("-", "_") else "-"
        for character in str(reason)
    ).strip("-") or "unclear"
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{time.time_ns()}-{safe_reason}.wav"
    path = os.path.join(directory, filename)

    try:
        os.makedirs(directory, exist_ok=True)
        with open(path, "wb") as f:
            f.write(audio.get_wav_data())
    except Exception:
        return None

    return path


def handle_unclear_audio(
    audio,
    reason,
    overlay_process,
    verbose,
    archive_unclear_audio=False,
):
    if archive_unclear_audio:
        path = save_unclear_audio(audio, reason)
        if path:
            update_overlay(overlay_process, "status", "Chunk archived")
            log(f"Saved unclear audio chunk for review: {path}", verbose)
        else:
            update_overlay(overlay_process, "status", "Chunk unclear")
            log("Speech not understood in chunk", verbose)
    else:
        update_overlay(overlay_process, "status", "Chunk unclear")
        log("Speech not understood in chunk", verbose)
    return None


def select_best_transcript(response):
    if not isinstance(response, dict):
        return None

    alternatives = response.get("alternative")
    if not alternatives:
        return None

    candidates = []
    for index, alternative in enumerate(alternatives):
        transcript = str(alternative.get("transcript", "")).strip()
        if not transcript:
            continue

        confidence = alternative.get("confidence")
        try:
            confidence_score = float(confidence)
        except (TypeError, ValueError):
            confidence_score = -1.0

        candidates.append({
            "confidence": confidence_score,
            "index": index,
            "text": transcript,
            "word_count": len(transcript.split()),
        })

    if not candidates:
        return None

    best_confidence = max(candidate["confidence"] for candidate in candidates)
    near_best = [
        candidate
        for candidate in candidates
        if candidate["confidence"] >= best_confidence - TRANSCRIPT_CONFIDENCE_MARGIN
    ]

    selected = max(
        near_best,
        key=lambda candidate: (
            candidate["word_count"],
            candidate["confidence"],
            -candidate["index"],
        ),
    )
    return selected["text"]


def recognize_audio(
    recognizer,
    audio,
    language,
    overlay_process,
    verbose,
    allow_after_stop=False,
    max_request_retries=None,
    archive_unclear_audio=False,
):
    unknown_attempts = 0
    request_errors = 0
    while running or allow_after_stop:
        try:
            log("Transcribing chunk...", verbose)
            update_overlay(overlay_process, "status", "Transcribing...")
            response = recognizer.recognize_google(
                audio,
                language=language,
                show_all=True,
            )
            transcript = select_best_transcript(response)
            if transcript:
                return transcript

            unknown_attempts += 1
            if unknown_attempts >= 2:
                return handle_unclear_audio(
                    audio,
                    "empty-recognition",
                    overlay_process,
                    verbose,
                    archive_unclear_audio,
                )

            update_overlay(overlay_process, "status", "Retrying unclear chunk")
            time.sleep(0.25)
        except sr.UnknownValueError:
            unknown_attempts += 1
            if unknown_attempts >= 2:
                return handle_unclear_audio(
                    audio,
                    "unknown-value",
                    overlay_process,
                    verbose,
                    archive_unclear_audio,
                )

            update_overlay(overlay_process, "status", "Retrying unclear chunk")
            time.sleep(0.25)
        except sr.RequestError as e:
            request_errors += 1
            update_overlay(overlay_process, "status", "Recognition error - retrying")
            sys.stderr.write(f"\nAPI Error: {e}\n")
            if max_request_retries is not None and request_errors >= max_request_retries:
                return handle_unclear_audio(
                    audio,
                    "request-error",
                    overlay_process,
                    verbose,
                    archive_unclear_audio,
                )
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


def is_listener_error_item(audio):
    return (
        isinstance(audio, tuple)
        and len(audio) == 2
        and audio[0] == "listener_error"
    )


def process_audio_queue_item(
    audio,
    recognizer,
    dictation_state,
    dictation_options,
    options,
    overlay_process,
    allow_after_stop=False,
):
    if is_listener_error_item(audio):
        handle_listener_error(audio[1], overlay_process, options.verbose)
        return False

    raw_text = recognize_audio(
        recognizer,
        audio,
        options.language,
        overlay_process,
        options.verbose,
        allow_after_stop=allow_after_stop,
        max_request_retries=2 if allow_after_stop else None,
        archive_unclear_audio=bool(getattr(options, "save_unclear_audio", False)),
    )
    if raw_text is None:
        return False

    return process_audio_result(
        raw_text,
        dictation_state,
        dictation_options,
        overlay_process,
        options.should_type,
        options.should_copy,
        options.should_output,
        options.verbose,
    )


def drain_pending_audio(
    pending_queue,
    recognizer,
    dictation_state,
    dictation_options,
    options,
    overlay_process,
):
    drained = 0
    while True:
        try:
            audio = pending_queue.get_nowait()
        except queue.Empty:
            break

        try:
            should_stop = process_audio_queue_item(
                audio,
                recognizer,
                dictation_state,
                dictation_options,
                options,
                overlay_process,
                allow_after_stop=True,
            )
            if not is_listener_error_item(audio):
                drained += 1
            if should_stop:
                break
        finally:
            pending_queue.task_done()

    if drained:
        log(f"Processed {drained} queued audio chunk(s) before shutdown.", options.verbose)

    return drained


def shutdown_settle_timeout(options):
    try:
        pause_threshold = float(options.pause_threshold)
    except (AttributeError, TypeError, ValueError):
        pause_threshold = 1.0

    try:
        phrase_time_limit = float(options.phrase_time_limit)
    except (AttributeError, TypeError, ValueError):
        phrase_time_limit = 0.0

    return min(
        MAX_SHUTDOWN_SETTLE_SECONDS,
        max(
            MIN_SHUTDOWN_SETTLE_SECONDS,
            pause_threshold + 0.75,
            phrase_time_limit,
        ),
    )


def wait_for_listener_to_settle(listener_thread, options):
    if listener_thread is None or not listener_thread.is_alive():
        return

    listener_thread.join(timeout=shutdown_settle_timeout(options))


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
    listener_thread = None

    handle_existing_instance()

    listener_recognizer = sr.Recognizer()
    recognition_recognizer = sr.Recognizer()
    dictation_state = DictationState()
    dictation_options = DictationOptions(
        auto_punctuation=options.auto_punctuation,
    )
    listener_recognizer.pause_threshold = options.pause_threshold

    source = create_microphone(sr, options.device_index)
    try:
        log("Calibrating microphone for ambient noise...", options.verbose)
        with source:
            listener_recognizer.adjust_for_ambient_noise(source, duration=0.5)
        log(
            f"Adjusted energy threshold to: {listener_recognizer.energy_threshold}",
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
                listener_recognizer,
                source,
                options.listen_timeout,
                options.phrase_time_limit,
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

            try:
                should_stop = process_audio_queue_item(
                    audio,
                    recognition_recognizer,
                    dictation_state,
                    dictation_options,
                    options,
                    overlay_process,
                )
                if should_stop:
                    break
            finally:
                audio_queue.task_done()

    except KeyboardInterrupt:
        log("SpeechCLI: Interrupted.", options.verbose)
        running = False
        update_overlay(overlay_process, "status", "Finishing captured speech")
        wait_for_listener_to_settle(listener_thread, options)
        drain_pending_audio(
            audio_queue,
            recognition_recognizer,
            dictation_state,
            dictation_options,
            options,
            overlay_process,
        )
    finally:
        running = False
        cleanup_pid_file(options.verbose)
        stop_overlay(overlay_process)
        send_notification("SpeechCLI", "Speech recognition stopped")

        if options.should_output or not any([options.should_type, options.should_copy]):
            print()


if __name__ == "__main__":
    main()
