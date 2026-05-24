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
import time
import signal
import threading
import queue

PID_FILE = "/tmp/speechcli.pid"
is_first_chunk = True
cumulative_text = ""
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
                # Send SIGINT to toggle/stop it
                os.kill(pid, signal.SIGINT)
                print("SpeechCLI: Stopping existing instance.")
                sys.exit(0)
        except (ValueError, OSError):
            pass
    
    # Write current PID
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
        print(f"\nTyping failed: {e}")

def background_listener(recognizer, source, verbose):
    global running
    try:
        with source:
            while running:
                try:
                    # Listen for speech with a 10-second timeout
                    # It blocks until speech starts, then records the whole phrase
                    audio = recognizer.listen(source, timeout=10)
                    if running:
                        audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    # No speech started within 10 seconds of starting/last phrase
                    if running:
                        audio_queue.put(None)
                    break
    except Exception as e:
        sys.stderr.write(f"\nListener thread error: {e}\n")
        if running:
            audio_queue.put(None)

def main():
    global running, is_first_chunk, cumulative_text
    args = sys.argv[1:]

    should_type = "--type" in args
    should_copy = "--copy" in args
    should_output = "--output" in args
    verbose = "--verbose" in args

    # Toggle check
    handle_existing_instance()

    recognizer = sr.Recognizer()
    # Tune pause threshold to wait slightly longer for pauses (default 0.8)
    # 1.0 second is a very good balance
    recognizer.pause_threshold = 1.0

    source = sr.Microphone()
    try:
        # Calibrate for ambient noise
        log("Calibrating microphone for ambient noise...", verbose)
        with source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        log(f"Adjusted energy threshold to: {recognizer.energy_threshold}", verbose)

        # Notify user that listening has started
        send_notification("SpeechCLI", "🎤 Listening...")
        log("🎤 Listening...", verbose)

        # Start background listener thread
        listener_thread = threading.Thread(
            target=background_listener,
            args=(recognizer, source, verbose),
            daemon=True
        )
        listener_thread.start()

        # Process the queue in the main thread
        while True:
            # We block here waiting for audio chunks from the queue
            # If nothing is added for 15 seconds, we timeout as a safety fallback
            audio = audio_queue.get(block=True, timeout=15)
            
            if audio is None:
                # Background thread timed out or requested exit
                log("Timeout: 10 seconds of inactivity.", verbose)
                break

            try:
                log("Transcribing chunk...", verbose)
                text = recognizer.recognize_google(audio)
                if not text:
                    continue
                
                # Formatting: prepend space if not first chunk
                if not is_first_chunk:
                    if not text.startswith(" ") and not text[0] in ".,!?":
                        text = " " + text
                else:
                    is_first_chunk = False
                
                cumulative_text += text

                if should_copy:
                    pyperclip.copy(cumulative_text)
                    log(f"📋 Copied: {cumulative_text}", verbose)

                if should_type:
                    type_text(text)
                    log(f"⌨️ Typed: {text}", verbose)

                if should_output or not any([should_type, should_copy]):
                    print(text, end="", flush=True)

            except sr.UnknownValueError:
                log("Speech not understood in chunk", verbose)
            except sr.RequestError as e:
                sys.stderr.write(f"\nAPI Error: {e}\n")
            finally:
                audio_queue.task_done()

    except KeyboardInterrupt:
        log("SpeechCLI: Interrupted.", verbose)
    except queue.Empty:
        log("Timeout: 10 seconds of inactivity (queue empty).", verbose)
    finally:
        running = False
        
        # Cleanup PID file
        cleanup_pid_file(verbose)
        
        # Notify user that listening has ended
        send_notification("SpeechCLI", "✅ Speech recognition completed")
        
        if should_output or not any([should_type, should_copy]):
            print()

if __name__ == "__main__":
    main()