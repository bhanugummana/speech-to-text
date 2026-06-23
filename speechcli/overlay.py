import os
import queue
import subprocess
import sys
import threading


OVERLAY_WINDOW_ARG = "--overlay-window"


def run_overlay_window():
    try:
        import tkinter as tk
    except Exception:
        return 1

    command_queue = queue.Queue()

    def read_commands():
        for line in sys.stdin:
            command_queue.put(line.rstrip("\n"))

    def apply_command(line):
        if not line:
            return

        if line == "stop":
            root.destroy()
            return

        command, _, value = line.partition("\t")
        if command == "status":
            status_label.config(text=value or "Listening")
        elif command == "text":
            preview_label.config(text=value[-70:] if value else "")

    def poll_commands():
        while True:
            try:
                apply_command(command_queue.get_nowait())
            except queue.Empty:
                break
        root.after(100, poll_commands)

    root = tk.Tk()
    root.title("SpeechCLI")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    try:
        root.attributes("-type", "dock")
    except tk.TclError:
        pass

    frame = tk.Frame(root, bg="#202124", padx=18, pady=12)
    frame.pack(fill="both", expand=True)

    status_label = tk.Label(
        frame,
        text="Listening",
        bg="#202124",
        fg="#ffffff",
        font=("Sans", 12, "bold"),
    )
    status_label.pack(anchor="w")

    preview_label = tk.Label(
        frame,
        text="",
        bg="#202124",
        fg="#d0d0d0",
        font=("Sans", 10),
        width=42,
        anchor="w",
    )
    preview_label.pack(anchor="w", pady=(4, 0))

    hint_label = tk.Label(
        frame,
        text="Press shortcut again or say stop dictation",
        bg="#202124",
        fg="#9aa0a6",
        font=("Sans", 9),
    )
    hint_label.pack(anchor="w", pady=(7, 0))

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = max(20, screen_height - height - 96)
    root.geometry(f"+{x}+{y}")

    threading.Thread(target=read_commands, daemon=True).start()
    root.after(100, poll_commands)
    root.mainloop()
    return 0


def start_overlay(enabled, script_path, log_func=None):
    if not enabled:
        return None

    try:
        process = subprocess.Popen(
            [sys.executable, os.path.abspath(script_path), OVERLAY_WINDOW_ARG],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        update_overlay(process, "status", "Listening")
        return process
    except Exception as e:
        if log_func is not None:
            log_func(f"Overlay failed to start: {e}")
        return None


def update_overlay(process, command, message):
    if process is None or process.poll() is not None or process.stdin is None:
        return

    safe_message = str(message).replace("\n", " ").replace("\t", " ")
    try:
        process.stdin.write(f"{command}\t{safe_message}\n")
        process.stdin.flush()
    except Exception:
        pass


def stop_overlay(process):
    if process is None:
        return

    update_overlay(process, "stop", "")
    try:
        process.wait(timeout=1)
    except Exception:
        process.terminate()
