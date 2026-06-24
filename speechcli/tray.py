import os
import subprocess
import sys

from speechcli.config_ui import build_dictation_args, settings_to_form_values
from speechcli.settings import load_settings


TRAY_MODE = "Type and copy"


def tray_dependency_message():
    return (
        "System tray support requires GTK/PyGObject and Pillow. Run "
        "./install.sh and choose the system tray option, or install your "
        "distribution's python-gobject/gtk3 packages and: "
        "pip install --break-system-packages pillow\n"
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


def tray_icon_path():
    image = create_tray_icon_image()
    if image is None:
        return None

    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "speechcli")
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "speechcli-tray.png")
    image.save(path)
    return path


def run_tray_app(settings, script_path=None):
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
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

    def quit_tray(icon=None, item=None):
        Gtk.main_quit()

    icon_path = tray_icon_path()
    if icon_path is None:
        sys.stderr.write(tray_dependency_message())
        return 1

    menu = Gtk.Menu()
    for label, callback in (
        ("Speak now", start_dictation),
        ("Settings", open_settings),
        ("Quit", quit_tray),
    ):
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda widget, cb=callback: cb())
        menu.append(item)
    menu.show_all()

    icon = Gtk.StatusIcon.new_from_file(icon_path)
    icon.set_title("SpeechCLI")
    icon.set_tooltip_text("SpeechCLI - left click to speak")
    icon.set_visible(True)
    icon.connect("activate", lambda status_icon: start_dictation())
    icon.connect(
        "popup-menu",
        lambda status_icon, button, activate_time: menu.popup(
            None,
            None,
            None,
            None,
            button,
            activate_time,
        ),
    )

    Gtk.main()
    return 0
