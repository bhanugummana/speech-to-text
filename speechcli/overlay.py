import os
import queue
import signal
import subprocess
import sys
import threading


OVERLAY_WINDOW_ARG = "--overlay-window"
OVERLAY_PARENT_PID_ARG = "--parent-pid"
PREVIEW_TEXT_LIMIT = 240


def format_preview_text(value):
    if not value:
        return "Dictated text will appear here."

    if len(value) <= PREVIEW_TEXT_LIMIT:
        return value

    return "..." + value[-(PREVIEW_TEXT_LIMIT - 3):]


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
        "bg": "#f4f7f5",
        "panel": "#ffffff",
        "panel_2": "#eef7f2",
        "text": "#17201c",
        "muted": "#5f6f66",
        "line": "#d4ded8",
        "teal": "#0f8f73",
        "blue": "#2563eb",
        "green": "#16a34a",
        "amber": "#b7791f",
        "red": "#dc2626",
        "red_soft": "#fff1f2",
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
            preview_text = format_preview_text(value)
            canvas.itemconfig(preview_text_item, text=preview_text)

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
        status_label = "Listening"
        helper = "Capturing speech"
        if "transcrib" in normalized:
            color = palette["blue"]
            status_label = "Transcribing"
            helper = "Processing chunk"
        elif "finish" in normalized:
            color = palette["blue"]
            status_label = "Finishing"
            helper = "Finishing captured speech"
        elif "error" in normalized or "retry" in normalized:
            color = palette["amber"]
            status_label = "Retrying"
            helper = "Retrying chunk"
        elif "unclear" in normalized:
            color = palette["amber"]
            status_label = "Unclear"
            helper = "Chunk unclear"
        elif "archiv" in normalized:
            color = palette["amber"]
            status_label = "Archived"
            helper = "Saved unclear chunk"
        elif "stop" in normalized:
            color = palette["red"]
            status_label = "Stopping"
            helper = "Stopping dictation"

        canvas.itemconfig(status_dot_shape, fill=color)
        canvas.itemconfig(status_text_item, text=status_label)
        canvas.itemconfig(helper_text_item, text=helper)

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

    def rounded_rect(canvas, x1, y1, x2, y2, radius=22, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def draw_canvas_settings_icon(canvas, x, y, color, tag):
        canvas.create_oval(x + 7, y + 7, x + 25, y + 25, outline=color, width=2, tags=tag)
        canvas.create_oval(x + 13, y + 13, x + 19, y + 19, outline=color, width=2, tags=tag)
        for x1, y1, x2, y2 in (
            (x + 16, y + 2, x + 16, y + 7),
            (x + 16, y + 25, x + 16, y + 30),
            (x + 2, y + 16, x + 7, y + 16),
            (x + 25, y + 16, x + 30, y + 16),
        ):
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2, capstyle="round", tags=tag)

    def draw_canvas_stop_icon(canvas, x, y, color, tag):
        canvas.create_rectangle(x + 9, y + 9, x + 23, y + 23, fill=color, outline=color, tags=tag)

    def canvas_button(x, y, label, icon_drawer, command, danger=False):
        tag = f"button_{label.lower()}"
        bg_tag = f"{tag}_bg"
        fill = "#f8fbf9" if not danger else palette["red_soft"]
        hover_fill = "#e7f5ee" if not danger else "#ffe4e6"
        outline = palette["line"] if not danger else "#fecdd3"
        text_color = palette["text"] if not danger else "#991b1b"
        rounded_rect(canvas, x, y, x + 128, y + 46, 14, fill=fill, outline=outline, width=1, tags=(tag, bg_tag))
        icon_drawer(canvas, x + 14, y + 8, text_color, tag)
        canvas.create_text(
            x + 54,
            y + 23,
            text=label,
            fill=text_color,
            font=("Sans", 10, "bold"),
            anchor="w",
            tags=tag,
        )

        def enter(event):
            canvas.itemconfig(bg_tag, fill=hover_fill)

        def leave(event):
            canvas.itemconfig(bg_tag, fill=fill)

        canvas.tag_bind(tag, "<Button-1>", lambda event: command())
        canvas.tag_bind(tag, "<Enter>", enter)
        canvas.tag_bind(tag, "<Leave>", leave)
        return tag

    root = tk.Tk()
    root.title("SpeechCLI")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.resizable(False, False)
    try:
        root.attributes("-alpha", 0.98)
    except tk.TclError:
        pass

    try:
        root.attributes("-type", "dock")
    except tk.TclError:
        pass

    window_width = 540
    window_height = 252
    canvas = tk.Canvas(
        root,
        width=window_width,
        height=window_height,
        bg=palette["bg"],
        bd=0,
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)

    drag = {"x": 0, "y": 0}

    def start_drag(event):
        drag["x"] = event.x
        drag["y"] = event.y

    def move_window(event):
        root.geometry(f"+{event.x_root - drag['x']}+{event.y_root - drag['y']}")

    canvas.bind("<ButtonPress-1>", start_drag)
    canvas.bind("<B1-Motion>", move_window)

    rounded_rect(canvas, 10, 10, window_width - 10, window_height - 10, 24, fill=palette["panel"], outline=palette["line"], width=1)
    rounded_rect(canvas, 24, 24, window_width - 24, 88, 18, fill=palette["panel_2"], outline="#d9e6de", width=1)
    canvas.create_oval(42, 41, 72, 71, fill=palette["teal"], outline="#a7f3d0", width=2)
    canvas.create_rectangle(54, 68, 60, 78, fill=palette["teal"], outline=palette["teal"])
    canvas.create_line(47, 80, 68, 80, fill="#8aa59a", width=2, capstyle="round")
    canvas.create_text(
        88,
        39,
        text="SpeechCLI",
        fill=palette["text"],
        font=("Sans", 17, "bold"),
        anchor="nw",
    )
    helper_text_item = canvas.create_text(
        88,
        64,
        text="Capturing speech",
        fill=palette["muted"],
        font=("Sans", 10),
        anchor="nw",
    )

    rounded_rect(canvas, 378, 37, 500, 73, 14, fill="#ffffff", outline=palette["line"], width=1)
    status_dot_shape = canvas.create_oval(396, 51, 408, 63, fill=palette["green"], outline="")
    status_text_item = canvas.create_text(
        418,
        57,
        text="Listening",
        fill=palette["text"],
        font=("Sans", 11, "bold"),
        anchor="w",
    )

    rounded_rect(canvas, 24, 102, window_width - 24, 192, 18, fill="#fbfdfc", outline=palette["line"], width=1)
    canvas.create_text(
        44,
        121,
        text="Latest transcript",
        fill=palette["muted"],
        font=("Sans", 9, "bold"),
        anchor="nw",
    )
    preview_text_item = canvas.create_text(
        44,
        145,
        text="Dictated text will appear here.",
        fill=palette["text"],
        font=("Sans", 12),
        anchor="nw",
        width=452,
    )

    canvas_button(266, 196, "Settings", draw_canvas_settings_icon, open_settings)
    canvas_button(404, 196, "Stop", draw_canvas_stop_icon, stop_dictation, danger=True)

    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width - window_width) / 2)
    y = max(20, screen_height - window_height - 96)
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
