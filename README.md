# SpeechCLI 🎤

A lightweight global speech-to-text CLI tool for Linux.

Speak anywhere on your desktop and:

- Type directly into input fields
- Copy speech to clipboard
- Print recognized text in terminal

Supports:

- Arch Linux
- Ubuntu
- Fedora
- Fish
- Bash
- Zsh
- KDE Wayland
- X11

---

# Features

- 🎤 Speech → Text
- 🔁 **Continuous Background Dictation**: Speak continuously and it will transcribe and type phrase-by-phrase.
- 📝 **Dictation Commands**: Say punctuation and layout commands like "comma", "period", "new line", and "new paragraph".
- 🎛️ **Shortcut Toggling**: Press the shortcut to start, press again to stop.
- ⏱️ **User-Controlled Listening**: Keeps listening until you click Stop in the popup.
- 🔔 **Integrated System Notifications**: Shows "Listening..." and "Completed" alerts natively.
- 🪟 **Listening Overlay**: Optional always-on-top status window while dictation is active.
- 🧰 **Settings Window**: Change microphone, language, output mode, punctuation, overlay, and timing from a native UI.
- 📌 **System Tray App**: Optional tray icon that starts dictation into the focused input field and copies text to the clipboard.
- ⌨️ Auto-type into active window
- 📋 Copy to clipboard
- 🖥️ CLI-first workflow
- 🐟 Fish shell support
- 🐧 Linux-first design
- 🔁 Re-runnable installer
- ⚡ Global command support
- 🛣️ Wayland + X11 support
- ⌨️ KDE shortcut support

---

# Demo

```bash
speechcli --type
```

Speak:

```txt
hello how are you
```

Automatically types into the currently focused input field.

---

# Installation

## 1. Clone the project

```bash
git clone https://github.com/bhanugummana/speech-to-text.git
cd speech-to-text
```

---

## 2. Run installer

```bash
chmod +x install.sh
./install.sh
```

The installer automatically:

- Detects your Linux distribution
- Installs system dependencies
- Installs Python dependencies
- Asks whether to install the optional system tray app
- Creates global `speechcli` command
- Configures:
  - Bash
  - Zsh
  - Fish
- Configures `ydotoold`
- Enables Wayland typing support
- Safely updates existing installation

---

# Restart Shell

## Fish

```fish
exec fish
```

## Bash/Zsh

```bash
exec $SHELL
```

---

# Usage

## Open settings window

```bash
speechcli --settings-ui
speechcli-settings
```

This opens a native settings window where you can choose whether dictation types into the active app, copies to the clipboard, prints in the terminal, or types and copies. The same window also lets you choose the microphone, language, punctuation, overlay, and listening timing, then save those choices as defaults.

After installation, you can also open **SpeechCLI Settings** from your desktop app launcher.

## Use system tray app

```bash
speechcli --tray
speechcli-tray
```

If you choose the tray option during `./install.sh`, SpeechCLI creates a tray launcher, adds it to desktop autostart, and starts it when a desktop session is available. Left-click the tray icon to start listening, type into the currently focused input field, and copy the dictated text to the clipboard. Right-click the tray icon to open the menu with **Speak now**, **Settings**, and **Quit**.

## Print recognized text

```bash
speechcli --output
```

---

## Copy to clipboard

```bash
speechcli --copy
```

---

## Type into active input field

```bash
speechcli --type
```

---

## Type with automatic punctuation

```bash
speechcli --type --auto-punctuation
```

Automatically adds simple sentence-ending punctuation at phrase boundaries:

- Question mark for phrases starting with words like `who`, `what`, `when`, `where`, `why`, or `how`
- Period for other phrases
- Capitalization after sentence-ending punctuation

---

## Type with listening overlay

```bash
speechcli --type --copy --auto-punctuation --overlay
```

Shows a small always-on-top status window while dictation is active. The overlay shows whether SpeechCLI is listening or transcribing and previews the current dictated session text.
---

## Choose recognition language

```bash
speechcli --type --language en-US
speechcli --type --language hi-IN
speechcli --type --language kn-IN
```

Use a BCP-47 language code supported by Google Speech Recognition. The default is `en-US`.

---

## Tune listening behavior

```bash
speechcli --type --listen-timeout 10 --pause-threshold 1.0
```

Useful options:

- `--listen-timeout`: optional seconds to wait for speech to start before retrying; by default SpeechCLI keeps listening until stopped
- `--pause-threshold`: seconds of silence that ends the current dictated phrase
- `--queue-timeout`: safety timeout while waiting for recorded audio chunks

---

## Choose microphone

```bash
speechcli --list-microphones
speechcli --type --device-index 2
```

Use `--list-microphones` to find the input device index, then pass that index with `--device-index`.

---

## Save dictation defaults

```bash
speechcli --settings-ui
speechcli --language en-US --device-index 2 --auto-punctuation --overlay --save-settings
speechcli --show-settings
speechcli --type --no-auto-punctuation --no-overlay
```

Saved settings are stored in `~/.config/speechcli/settings.json` and are used as defaults for future runs. Command-line options still override saved values. If you save an output mode from the settings window, running `speechcli` with no `--type`, `--copy`, or `--output` flag uses that saved mode.

---

## Everything together

```bash
speechcli --type --copy --output --auto-punctuation --overlay --language en-US --device-index 0 --pause-threshold 1.0
```

---

# Dictation Commands

SpeechCLI converts common spoken dictation commands before typing or copying text:

| Say | Types |
| --- | --- |
| `period` or `full stop` | `.` |
| `comma` | `,` |
| `question mark` | `?` |
| `exclamation mark` or `exclamation point` | `!` |
| `colon` | `:` |
| `semicolon` | `;` |
| `dash` or `hyphen` | `-` |
| `open quote`, `close quote`, or `quote` | `"` |
| `new line` or `newline` | line break |
| `new paragraph` | blank line, then capitalizes the next word |
| `tab` | tab character |
| `open parenthesis`, `close parenthesis`, `open bracket`, `close bracket`, `open brace`, or `close brace` | matching bracket character |
| `slash`, `backslash`, `at sign`, `hashtag`, `dollar sign`, `percent sign`, `ampersand`, `asterisk`, `plus sign`, `equals sign`, or `underscore` | matching symbol |
| `capitalize` or `cap` | capitalizes the next word |
| `uppercase`, `upper case`, or `all caps` | uppercases the next word |
| `lowercase`, `lower case`, or `no caps` | lowercases the next word |
| `all caps on` or `caps on` | uppercases following dictated words |
| `all caps off` or `caps off` | turns off all-caps mode |
| `delete that`, `scratch that`, or `undo that` | removes the previous dictated phrase |
| `delete last word` or `delete previous word` | removes the previous dictated word |
| `clear dictation` or `clear text` | removes all text typed during the current dictation session |
| `press enter`, `enter`, or `press return` | presses Enter |
| `press tab` or `next field` | presses Tab |
| `previous field` or `last field` | presses Shift+Tab |
| `select all` | presses Ctrl+A |
| `copy` or `copy that` | presses Ctrl+C |
| `cut` or `cut that` | presses Ctrl+X |
| `paste` or `paste that` | presses Ctrl+V |
| `undo` | presses Ctrl+Z |
| `redo` | presses Ctrl+Y |
| `backspace` or `press backspace` | presses Backspace |
| `delete` or `press delete` | presses Delete |
| `delete selection` or `delete selected text` | presses Backspace |
| `select previous word` or `select next word` | presses Ctrl+Shift+Left/Right |
| `select previous character` or `select next character` | presses Shift+Left/Right |
| `go to beginning`, `move to beginning`, or `press home` | presses Home |
| `go to end`, `move to end`, or `press end` | presses End |
| `move left`, `move right`, `move up`, or `move down` | presses the matching arrow key |
| `press escape` or `escape` | presses Escape |

Example:

```txt
hello comma new line capitalize world exclamation mark
```

Types:

```txt
hello,
World!
```

---

# Verbose Mode

```bash
speechcli --verbose
```

Shows internal logs like:

- Listening state
- Clipboard copy status
- Typing status

---

# KDE Shortcut Setup

## Recommended KDE Shortcut Command

```bash
export YDOTOOL_SOCKET="$HOME/.ydotool_socket" && ~/.local/bin/speechcli --type --copy --auto-punctuation --overlay --language en-US
```

This command:

- Starts continuous speech recognition (press again to toggle stop)
- Copies the complete recognized text to your clipboard
- Types recognized text directly into your active input field
- Uses native desktop notifications to indicate listening/completion state

---

# KDE Shortcut Configuration

Open:

```txt
System Settings
→ Shortcuts
→ Custom Shortcuts
```

Add:

- Trigger:
  - `Meta + A`
- Action:
  - Paste the command above

---

# Wayland vs X11

## X11

Uses:

- `xdotool`

## Wayland

Uses:

- `ydotool`
- `ydotoold`

The installer automatically configures Wayland support.

---

# How It Works

1. Records microphone input
2. Converts speech → text using Google Speech Recognition
3. Performs selected actions:
   - Output text
   - Copy clipboard
   - Type into active window

---

# Supported Shells

- Fish
- Bash
- Zsh

Installer automatically configures:

- PATH
- YDOTOOL socket environment

---

# Supported Linux Distributions

- Arch Linux
- EndeavourOS
- Manjaro
- Ubuntu
- Debian
- Pop!\_OS
- Linux Mint
- Fedora

---

# Dependencies

## System

- Python
- PortAudio
- xdotool
- ydotool
- wl-clipboard
- xclip
- libnotify

## Python

- SpeechRecognition
- PyAudio
- pyperclip

---

# Project Structure

```txt
speech-to-text/
├── install.sh
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Updating

Simply rerun:

```bash
./install.sh
```

The installer is idempotent:

- No duplicate PATH entries
- No duplicate shell configs
- No duplicate services
- Existing installation safely updates

---

# Uninstall

Remove launcher:

```bash
rm ~/.local/bin/speechcli
```

Remove ydotool service:

```bash
systemctl --user disable --now ydotool.service
rm ~/.config/systemd/user/ydotool.service
```

Optional Python cleanup:

```bash
pip uninstall SpeechRecognition PyAudio pyperclip
```

---

# Future Improvements

- Offline transcription
- Whisper support
- Wake-word activation
- AI punctuation
- GUI tray icon
- Streaming recognition
- Multi-language support

---
