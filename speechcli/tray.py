import os
import subprocess
import sys

from speechcli.config_ui import build_dictation_args, settings_to_form_values
from speechcli.settings import load_settings


TRAY_MODE = "Type and copy"


def tray_dependency_message():
    return (
        "System tray support requires pystray and Pillow. Run ./install.sh "
        "and choose the system tray option, or install them with: "
        "pip install --break-system-packages pystray pillow\n"
    )


def tray_dictation_values(settings):
    values = settings_to_form_values(settings)
    values["mode"] = TRAY_MODE
    values["listen_timeout"] = None
    values["overlay"] = True
    return values


def build_tray_dictation_command(settings, script_path):
    values = tray_dictation_values(settings)
    return [sys.executable, os.path.abspath(script_path)] + build_dictation_args(values)


def create_tray_icon_image():
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None

    image = Image.new("RGBA", (64, 64), (32, 33, 36, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 8, 46, 38), fill=(66, 133, 244, 255))
    draw.rounded_rectangle((26, 36, 38, 50), radius=4, fill=(66, 133, 244, 255))
    draw.rounded_rectangle((18, 48, 46, 54), radius=3, fill=(95, 99, 104, 255))
    draw.arc((12, 18, 52, 58), 35, 145, fill=(95, 99, 104, 255), width=5)
    return image


def run_tray_app(settings, script_path=None):
    try:
        import pystray
    except Exception:
        sys.stderr.write(tray_dependency_message())
        return 1

    script_path = os.path.abspath(script_path or sys.argv[0])

    def notify(title, message):
        try:
            subprocess.run(["notify-send", title, message], check=False)
        except Exception:
            pass

    def start_dictation(icon=None, item=None):
        command = build_tray_dictation_command(load_settings(), script_path)
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            notify("SpeechCLI", "Listening. Speak into the focused input field.")
        except OSError as e:
            notify("SpeechCLI", f"Could not start dictation: {e}")

    def open_settings(icon=None, item=None):
        try:
            subprocess.Popen(
                [sys.executable, script_path, "--settings-ui"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as e:
            notify("SpeechCLI", f"Could not open settings: {e}")

    def quit_tray(icon, item=None):
        icon.stop()

    image = create_tray_icon_image()
    if image is None:
        sys.stderr.write(tray_dependency_message())
        return 1

    icon = pystray.Icon(
        "speechcli",
        image,
        "SpeechCLI - left click to speak",
        pystray.Menu(
            pystray.MenuItem("Speak now", start_dictation, default=True),
            pystray.MenuItem("Settings", open_settings),
            pystray.MenuItem("Quit", quit_tray),
        ),
    )
    icon.run()
    return 0
