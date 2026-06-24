import os
import queue
import signal
import subprocess
import sys
import threading


OVERLAY_WINDOW_ARG = "--overlay-window"
OVERLAY_PARENT_PID_ARG = "--parent-pid"


def overlay_parent_pid(argv):
    if OVERLAY_PARENT_PID_ARG not in argv:
        return None

    try:
        index = argv.index(OVERLAY_PARENT_PID_ARG)
        return int(argv[index + 1])
    except (IndexError, ValueError):
        return None


def run_overlay_window():
    try:
        import tkinter as tk
    except Exception:
        return 1

    command_queue = queue.Queue()
    parent_pid = overlay_parent_pid(sys.argv)
    palette = {
        "bg": "#0f172a",
        "panel": "#111827",
        "panel_2": "#1f2937",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "line": "#334155",
        "blue": "#38bdf8",
        "green": "#22c55e",
        "amber": "#f59e0b",
        "red": "#ef4444",
    }

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
            set_status(value or "Listening")
        elif command == "text":
            preview_text = value[-110:] if value else "Dictated text will appear here."
            preview_label.config(text=preview_text)

    def poll_commands():
        while True:
            try:
                apply_command(command_queue.get_nowait())
            except queue.Empty:
                break
        root.after(100, poll_commands)

    def open_settings():
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    os.path.abspath(sys.argv[0]),
                    "--settings-ui",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            pass

    def stop_dictation():
        if parent_pid:
            try:
                os.kill(parent_pid, signal.SIGINT)
            except OSError:
                pass
        root.destroy()

    def set_status(message):
        normalized = message.lower()
        color = palette["green"]
        if "transcrib" in normalized:
            color = palette["blue"]
        elif "error" in normalized or "retry" in normalized:
            color = palette["amber"]
        elif "stop" in normalized:
            color = palette["red"]

        status_dot.itemconfig(status_dot_shape, fill=color)
        status_label.config(text=message)

    def draw_settings_icon(canvas, color):
        canvas.create_oval(9, 9, 27, 27, outline=color, width=2)
        canvas.create_oval(15, 15, 21, 21, outline=color, width=2)
        for x1, y1, x2, y2 in (
            (18, 4, 18, 9),
            (18, 27, 18, 32),
            (4, 18, 9, 18),
            (27, 18, 32, 18),
        ):
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2, capstyle="round")

    def draw_stop_icon(canvas, color):
        canvas.create_rectangle(11, 11, 25, 25, fill=color, outline=color)

    def icon_button(parent, label, draw_icon, command, danger=False):
        normal_bg = "#7f1d1d" if danger else palette["panel_2"]
        hover_bg = "#991b1b" if danger else "#273449"
        fg = "#fecaca" if danger else palette["text"]
        frame = tk.Frame(
            parent,
            bg=normal_bg,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground="#3f4b61",
        )
        frame.pack(side="left", padx=(0, 8))

        canvas = tk.Canvas(
            frame,
            width=36,
            height=36,
            bg=normal_bg,
            bd=0,
            highlightthickness=0,
        )
        canvas.pack(side="left", padx=(10, 0), pady=8)
        draw_icon(canvas, fg)

        text_label = tk.Label(
            frame,
            text=label,
            bg=normal_bg,
            fg=fg,
            font=("Sans", 10, "bold"),
            padx=10,
        )
        text_label.pack(side="left", padx=(0, 12))

        def set_button_bg(bg):
            frame.config(bg=bg)
            canvas.config(bg=bg)
            text_label.config(bg=bg)

        def handle_enter(event):
            set_button_bg(hover_bg)

        def handle_leave(event):
            set_button_bg(normal_bg)

        for widget in (frame, canvas, text_label):
            widget.bind("<Button-1>", lambda event: command())
            widget.bind("<Return>", lambda event: command())
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)

        return frame

    root = tk.Tk()
    root.title("SpeechCLI")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    try:
        root.attributes("-type", "dock")
    except tk.TclError:
        pass

    frame = tk.Frame(
        root,
        bg=palette["bg"],
        padx=18,
        pady=16,
        highlightthickness=1,
        highlightbackground=palette["line"],
    )
    frame.pack(fill="both", expand=True)

    header = tk.Frame(frame, bg=palette["bg"])
    header.pack(fill="x")

    status_pill = tk.Frame(header, bg=palette["panel_2"], padx=10, pady=6)
    status_pill.pack(side="left")

    status_dot = tk.Canvas(
        status_pill,
        width=14,
        height=14,
        bg=palette["panel_2"],
        bd=0,
        highlightthickness=0,
    )
    status_dot.pack(side="left", padx=(0, 8))
    status_dot_shape = status_dot.create_oval(3, 3, 11, 11, fill=palette["green"], outline="")

    status_label = tk.Label(
        status_pill,
        text="Listening",
        bg=palette["panel_2"],
        fg=palette["text"],
        font=("Sans", 11, "bold"),
    )
    status_label.pack(side="left")

    title_label = tk.Label(
        frame,
        text="SpeechCLI",
        bg=palette["bg"],
        fg=palette["text"],
        font=("Sans", 16, "bold"),
    )
    title_label.pack(anchor="w", pady=(16, 2))

    preview_label = tk.Label(
        frame,
        text="Dictated text will appear here.",
        bg=palette["panel"],
        fg=palette["text"],
        font=("Sans", 11),
        width=46,
        height=3,
        anchor="w",
        justify="left",
        padx=14,
        pady=10,
        wraplength=430,
    )
    preview_label.pack(anchor="w", fill="x", pady=(8, 0))

    hint_label = tk.Label(
        frame,
        text="Listening stays on until you press Stop.",
        bg=palette["bg"],
        fg=palette["muted"],
        font=("Sans", 9),
    )
    hint_label.pack(anchor="w", pady=(10, 0))

    button_row = tk.Frame(frame, bg=palette["bg"])
    button_row.pack(anchor="e", pady=(14, 0))

    icon_button(button_row, "Settings", draw_settings_icon, open_settings)
    icon_button(button_row, "Stop", draw_stop_icon, stop_dictation, danger=True)

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
            [
                sys.executable,
                os.path.abspath(script_path),
                OVERLAY_WINDOW_ARG,
                OVERLAY_PARENT_PID_ARG,
                str(os.getpid()),
            ],
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
