import os
import subprocess
import sys
from types import SimpleNamespace

from speechcli.audio import list_microphones
from speechcli.options import (
    DEFAULT_LANGUAGE,
    DEFAULT_LISTEN_TIMEOUT,
    DEFAULT_PAUSE_THRESHOLD,
    DEFAULT_PHRASE_TIME_LIMIT,
    DEFAULT_QUEUE_TIMEOUT,
)
from speechcli.settings import save_settings


LANGUAGE_CHOICES = (
    "en-US",
    "en-IN",
    "hi-IN",
    "kn-IN",
)

MODE_CHOICES = {
    "Type into active app": {
        "should_type": True,
        "should_copy": False,
        "should_output": False,
    },
    "Copy to clipboard": {
        "should_type": False,
        "should_copy": True,
        "should_output": False,
    },
    "Show in terminal": {
        "should_type": False,
        "should_copy": False,
        "should_output": True,
    },
    "Type and copy": {
        "should_type": True,
        "should_copy": True,
        "should_output": False,
    },
}


def tkinter_install_hint():
    distro_id = ""
    distro_like = ""

    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                key, _, value = line.partition("=")
                value = value.strip().strip('"').lower()
                if key == "ID":
                    distro_id = value
                elif key == "ID_LIKE":
                    distro_like = value
    except OSError:
        pass

    distro_tokens = {distro_id, *distro_like.split()}
    if {"arch", "garuda", "endeavouros", "manjaro"} & distro_tokens:
        return "Install it with: sudo pacman -S --needed tk"
    if {"ubuntu", "debian", "pop", "linuxmint"} & distro_tokens:
        return "Install it with: sudo apt install python3-tk"
    if "fedora" in distro_tokens:
        return "Install it with: sudo dnf install python3-tkinter"
    return "Install your distribution's Python Tk/Tkinter package."


def mode_from_settings(settings):
    for label, values in MODE_CHOICES.items():
        if all(bool(settings.get(key, False)) == value for key, value in values.items()):
            return label
    return "Show in terminal"


def settings_to_form_values(settings):
    return {
        "auto_punctuation": bool(settings.get("auto_punctuation", False)),
        "device_index": settings.get("device_index"),
        "language": settings.get("language", DEFAULT_LANGUAGE),
        "listen_timeout": settings.get("listen_timeout", DEFAULT_LISTEN_TIMEOUT),
        "mode": mode_from_settings(settings),
        "overlay": bool(settings.get("overlay", True)),
        "pause_threshold": settings.get("pause_threshold", DEFAULT_PAUSE_THRESHOLD),
        "phrase_time_limit": settings.get("phrase_time_limit", DEFAULT_PHRASE_TIME_LIMIT),
        "queue_timeout": settings.get("queue_timeout", DEFAULT_QUEUE_TIMEOUT),
        "save_unclear_audio": bool(settings.get("save_unclear_audio", False)),
    }


def build_dictation_args(values):
    mode_values = MODE_CHOICES[values["mode"]]
    args = []

    if mode_values["should_type"]:
        args.append("--type")
    if mode_values["should_copy"]:
        args.append("--copy")
    if mode_values["should_output"]:
        args.append("--output")

    args.extend(["--language", values["language"]])
    if values["listen_timeout"] is not None:
        args.extend(["--listen-timeout", str(values["listen_timeout"])])
    args.extend(["--queue-timeout", str(values["queue_timeout"])])
    args.extend(["--phrase-time-limit", str(values["phrase_time_limit"])])
    args.extend(["--pause-threshold", str(values["pause_threshold"])])

    if values["device_index"] is not None:
        args.extend(["--device-index", str(values["device_index"])])
    if values["auto_punctuation"]:
        args.append("--auto-punctuation")
    else:
        args.append("--no-auto-punctuation")
    if values["overlay"]:
        args.append("--overlay")
    else:
        args.append("--no-overlay")
    if values.get("save_unclear_audio"):
        args.append("--save-unclear-audio")
    else:
        args.append("--no-save-unclear-audio")

    return args


def values_to_namespace(values):
    mode_values = MODE_CHOICES[values["mode"]]
    return SimpleNamespace(
        auto_punctuation=values["auto_punctuation"],
        device_index=values["device_index"],
        language=values["language"],
        listen_timeout=values["listen_timeout"],
        overlay=values["overlay"],
        pause_threshold=values["pause_threshold"],
        phrase_time_limit=values["phrase_time_limit"],
        queue_timeout=values["queue_timeout"],
        save_unclear_audio=values.get("save_unclear_audio", False),
        should_copy=mode_values["should_copy"],
        should_output=mode_values["should_output"],
        should_type=mode_values["should_type"],
    )


def run_settings_window(settings, sr_module=None, script_path=None):
    try:
        import tkinter as tk
        from tkinter import messagebox
        from tkinter import ttk
    except Exception:
        sys.stderr.write(
            "Tkinter is required for the settings UI. Install python3-tk or "
            f"your distribution's Tk package. {tkinter_install_hint()}\n"
        )
        return 1

    form_values = settings_to_form_values(settings)
    script_path = os.path.abspath(script_path or sys.argv[0])

    try:
        root = tk.Tk()
    except tk.TclError as e:
        sys.stderr.write(f"Could not open settings UI: {e}\n")
        return 1
    root.title("SpeechCLI Settings")
    root.minsize(660, 690)
    root.configure(bg="#f4f7f5")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("App.TFrame", background="#f4f7f5")
    style.configure("Header.TFrame", background="#e8f4ed")
    style.configure("Card.TFrame", background="#ffffff", bordercolor="#d4ded8", relief="solid")
    style.configure("Title.TLabel", background="#e8f4ed", foreground="#17201c", font=("Sans", 20, "bold"))
    style.configure("Subtitle.TLabel", background="#e8f4ed", foreground="#5f6f66", font=("Sans", 10))
    style.configure("SectionTitle.TLabel", background="#f4f7f5", foreground="#17201c", font=("Sans", 11, "bold"))
    style.configure("TLabel", background="#ffffff", foreground="#17201c", font=("Sans", 10))
    style.configure("Helper.TLabel", background="#ffffff", foreground="#5f6f66", font=("Sans", 9))
    style.configure("Status.TLabel", background="#f4f7f5", foreground="#0f8f73", font=("Sans", 10, "bold"))
    style.configure("Action.TButton", padding=(16, 10), background="#0f8f73", foreground="#ffffff")
    style.map("Action.TButton", background=[("active", "#0b755f"), ("disabled", "#a7b8b0")])
    style.configure("TButton", padding=(12, 9))
    style.configure("TCheckbutton", background="#ffffff", foreground="#17201c", padding=(0, 5))
    style.configure("TRadiobutton", background="#ffffff", foreground="#17201c", padding=(0, 5))
    style.configure("Mode.TRadiobutton", background="#ffffff", foreground="#17201c", padding=(12, 9))
    style.map(
        "Mode.TRadiobutton",
        background=[("selected", "#e8f4ed"), ("active", "#f2faf5")],
        foreground=[("selected", "#0f5f50")],
    )
    style.configure("TEntry", padding=(6, 5))
    style.configure("TCombobox", padding=(6, 5))

    container = ttk.Frame(root, padding=24, style="App.TFrame")
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)

    header = ttk.Frame(container, padding=(18, 16), style="Header.TFrame")
    header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
    header.columnconfigure(0, weight=1)

    ttk.Label(header, text="SpeechCLI", style="Title.TLabel").grid(
        row=0,
        column=0,
        sticky="w",
    )
    ttk.Label(
        header,
        text="Choose output, microphone, language, and chunk timing for reliable dictation.",
        style="Subtitle.TLabel",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    mode_var = tk.StringVar(value=form_values["mode"])
    language_var = tk.StringVar(value=form_values["language"])
    auto_punctuation_var = tk.BooleanVar(value=form_values["auto_punctuation"])
    overlay_var = tk.BooleanVar(value=form_values["overlay"])
    save_unclear_audio_var = tk.BooleanVar(value=form_values["save_unclear_audio"])
    listen_timeout_var = tk.StringVar(
        value="" if form_values["listen_timeout"] is None else str(form_values["listen_timeout"])
    )
    queue_timeout_var = tk.StringVar(value=str(form_values["queue_timeout"]))
    pause_threshold_var = tk.StringVar(value=str(form_values["pause_threshold"]))
    phrase_time_limit_var = tk.StringVar(value=str(form_values["phrase_time_limit"]))

    devices = [("Default microphone", None)]
    if sr_module is not None:
        try:
            devices.extend(
                (f"{index}: {name}", index)
                for index, name in enumerate(list_microphones(sr_module))
            )
        except Exception:
            pass

    device_labels = [label for label, _ in devices]
    device_by_label = dict(devices)
    current_device = form_values["device_index"]
    device_var = tk.StringVar(value="Default microphone")
    for label, index in devices:
        if index == current_device:
            device_var.set(label)
            break

    def section(row, title):
        ttk.Label(container, text=title, style="SectionTitle.TLabel").grid(
            row=row,
            column=0,
            sticky="w",
            pady=(0, 6),
        )
        frame = ttk.Frame(container, padding=14, style="Card.TFrame")
        frame.grid(row=row + 1, column=0, sticky="ew", pady=(0, 14))
        return frame

    mode_frame = section(1, "Dictation output")
    mode_frame.columnconfigure(0, weight=1)
    mode_frame.columnconfigure(1, weight=1)

    for index, label in enumerate(MODE_CHOICES):
        ttk.Radiobutton(
            mode_frame,
            text=label,
            value=label,
            variable=mode_var,
            style="Mode.TRadiobutton",
        ).grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)

    settings_frame = section(3, "Recognition settings")
    settings_frame.columnconfigure(1, weight=1)

    ttk.Label(settings_frame, text="Microphone").grid(row=0, column=0, sticky="w")
    ttk.Combobox(
        settings_frame,
        textvariable=device_var,
        values=device_labels,
        state="readonly",
    ).grid(row=0, column=1, sticky="ew", padx=(14, 0), pady=(0, 8))

    ttk.Label(settings_frame, text="Language").grid(row=1, column=0, sticky="w")
    ttk.Combobox(
        settings_frame,
        textvariable=language_var,
        values=LANGUAGE_CHOICES,
    ).grid(row=1, column=1, sticky="ew", padx=(14, 0), pady=(0, 8))

    ttk.Checkbutton(
        settings_frame,
        text="Add simple punctuation automatically",
        variable=auto_punctuation_var,
    ).grid(row=2, column=0, columnspan=2, sticky="w")

    ttk.Checkbutton(
        settings_frame,
        text="Show floating listening overlay",
        variable=overlay_var,
    ).grid(row=3, column=0, columnspan=2, sticky="w")

    ttk.Checkbutton(
        settings_frame,
        text="Save unclear audio chunks for review",
        variable=save_unclear_audio_var,
    ).grid(row=4, column=0, columnspan=2, sticky="w")

    timing_frame = section(5, "Timing")
    timing_frame.columnconfigure(1, weight=1)

    timing_fields = (
        ("Listen timeout", listen_timeout_var, "blank keeps listening until stopped"),
        ("Queue timeout", queue_timeout_var, "safety timeout in seconds"),
        ("Chunk length", phrase_time_limit_var, "12-15 sec is best for fewer missed words"),
        ("Pause threshold", pause_threshold_var, "seconds of silence per phrase"),
    )
    for row, (label, variable, helper) in enumerate(timing_fields):
        ttk.Label(timing_frame, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(
            timing_frame,
            textvariable=variable,
            width=10,
        ).grid(row=row, column=1, sticky="w", padx=(14, 10), pady=(0, 8))
        ttk.Label(timing_frame, text=helper, style="Helper.TLabel").grid(row=row, column=2, sticky="w")

    status_var = tk.StringVar(value="")
    status_label = ttk.Label(container, textvariable=status_var, style="Status.TLabel")
    status_label.grid(row=7, column=0, sticky="w", pady=(0, 12))

    button_bar = ttk.Frame(container, style="App.TFrame")
    button_bar.grid(row=8, column=0, sticky="ew")
    button_bar.columnconfigure(0, weight=1)

    def parse_positive_float(label, value):
        if label == "Listen timeout" and not value.strip():
            return None

        try:
            parsed = float(value)
        except ValueError as e:
            raise ValueError(f"{label} must be a number.") from e
        if parsed <= 0:
            raise ValueError(f"{label} must be greater than zero.")
        return parsed

    def collect_values():
        language = language_var.get().strip()
        if not language:
            raise ValueError("Language is required.")

        device_label = device_var.get()
        if device_label not in device_by_label:
            raise ValueError("Choose a microphone from the list.")

        return {
            "auto_punctuation": auto_punctuation_var.get(),
            "device_index": device_by_label[device_label],
            "language": language,
            "listen_timeout": parse_positive_float(
                "Listen timeout",
                listen_timeout_var.get(),
            ),
            "mode": mode_var.get(),
            "overlay": overlay_var.get(),
            "pause_threshold": parse_positive_float(
                "Pause threshold",
                pause_threshold_var.get(),
            ),
            "phrase_time_limit": parse_positive_float(
                "Chunk length",
                phrase_time_limit_var.get(),
            ),
            "queue_timeout": parse_positive_float(
                "Queue timeout",
                queue_timeout_var.get(),
            ),
            "save_unclear_audio": save_unclear_audio_var.get(),
        }

    def save_current_settings():
        try:
            values = collect_values()
            save_settings(values_to_namespace(values))
        except ValueError as e:
            messagebox.showerror("SpeechCLI Settings", str(e))
            return None
        except OSError as e:
            messagebox.showerror("SpeechCLI Settings", f"Could not save settings: {e}")
            return None

        status_var.set("Settings saved.")
        return values

    def start_dictation():
        values = save_current_settings()
        if values is None:
            return

        command = [sys.executable, script_path] + build_dictation_args(values)
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as e:
            messagebox.showerror("SpeechCLI Settings", f"Could not start dictation: {e}")
            return

        status_var.set("Dictation started. Press Start / Stop again to stop it.")

    ttk.Button(
        button_bar,
        text="Save Settings",
        command=save_current_settings,
    ).grid(row=0, column=1, padx=(0, 8))
    ttk.Button(
        button_bar,
        text="Start / Stop Dictation",
        style="Action.TButton",
        command=start_dictation,
    ).grid(row=0, column=2, padx=(0, 8))
    ttk.Button(button_bar, text="Close", command=root.destroy).grid(row=0, column=3)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    root.geometry(f"+{x}+{max(20, y)}")

    root.mainloop()
    return 0
