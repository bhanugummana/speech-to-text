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
- ⌨️ Auto-type into active window
- 📋 Copy to clipboard
- 🖥️ CLI-first workflow
- 🐟 Fish shell support
- 🐧 Linux-first design
- 🔁 Re-runnable installer
- ⚡ Global command support
- 🛣️ Wayland + X11 support
- 🔔 KDE notification support
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

## Everything together

```bash
speechcli --type --copy --output
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
export YDOTOOL_SOCKET="$HOME/.ydotool_socket" && notify-send "SpeechCLI" "🎤 Listening..." && ~/.local/bin/speechcli --type --copy && notify-send "SpeechCLI" "✅ Speech recognition completed"
```

This command:

- Starts speech recognition
- Copies recognized text to clipboard
- Types text into active input field
- Shows KDE notifications

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
- Continuous dictation
- Wake-word activation
- AI punctuation
- GUI tray icon
- Streaming recognition
- Multi-language support

---
