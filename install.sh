#!/usr/bin/env bash

set -e

echo "🚀 Installing / Updating speechcli..."

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------
# Detect distro
# ---------------------------------------

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    DISTRO_LIKE=${ID_LIKE:-}
else
    echo "❌ Could not detect Linux distribution"
    exit 1
fi

echo "🐧 Detected distro: $DISTRO"

INSTALL_TRAY="no"
if [ -t 0 ]; then
    read -r -p "Install SpeechCLI as a system tray app? [y/N] " INSTALL_TRAY_ANSWER
    case "$INSTALL_TRAY_ANSWER" in
        y|Y|yes|YES)
            INSTALL_TRAY="yes"
            ;;
    esac
fi

is_distro_family() {
    FAMILY="$1"
    [ "$DISTRO" = "$FAMILY" ] && return 0

    for LIKE in $DISTRO_LIKE; do
        [ "$LIKE" = "$FAMILY" ] && return 0
    done

    return 1
}

# ---------------------------------------
# Install system dependencies
# ---------------------------------------

install_arch() {
    sudo pacman -S --needed \
        python \
        python-pip \
        tk \
        portaudio \
        xdotool \
        ydotool \
        xclip \
        wl-clipboard

    if [ "$INSTALL_TRAY" = "yes" ]; then
        sudo pacman -S --needed \
            python-gobject \
            gtk3
    fi
}

install_ubuntu() {
    sudo apt update

    sudo apt install -y \
        python3 \
        python3-pip \
        python3-tk \
        portaudio19-dev \
        python3-pyaudio \
        xdotool \
        wl-clipboard \
        xclip

    if [ "$INSTALL_TRAY" = "yes" ]; then
        sudo apt install -y \
            python3-gi \
            gir1.2-gtk-3.0
    fi
}

install_fedora() {
    sudo dnf install -y \
        python3 \
        python3-pip \
        python3-tkinter \
        portaudio-devel \
        xdotool \
        ydotool \
        wl-clipboard \
        xclip

    if [ "$INSTALL_TRAY" = "yes" ]; then
        sudo dnf install -y \
            python3-gobject \
            gtk3
    fi
}

if is_distro_family arch || [ "$DISTRO" = "endeavouros" ] || [ "$DISTRO" = "manjaro" ]; then
    install_arch
elif is_distro_family debian || [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "pop" ] || [ "$DISTRO" = "linuxmint" ]; then
    install_ubuntu
elif is_distro_family fedora; then
    install_fedora
else
    echo "⚠️ Unsupported distro: $DISTRO"
    echo "Please install dependencies manually"
fi

# ---------------------------------------
# Install Python dependencies
# ---------------------------------------

echo "🐍 Installing Python dependencies..."

pip install --break-system-packages \
    SpeechRecognition \
    PyAudio \
    pyperclip

if [ "$INSTALL_TRAY" = "yes" ]; then
    pip install --break-system-packages \
        pillow
fi

# ---------------------------------------
# Create launcher
# ---------------------------------------

echo "🔧 Creating global launcher..."

mkdir -p ~/.local/bin

cat > ~/.local/bin/speechcli << EOF
#!/usr/bin/env bash

python "$PROJECT_DIR/main.py" "\$@"
EOF

chmod +x ~/.local/bin/speechcli

cat > ~/.local/bin/speechcli-settings << EOF
#!/usr/bin/env bash

python "$PROJECT_DIR/main.py" --settings-ui
EOF

chmod +x ~/.local/bin/speechcli-settings

if [ "$INSTALL_TRAY" = "yes" ]; then
    cat > ~/.local/bin/speechcli-tray << EOF
#!/usr/bin/env bash

python "$PROJECT_DIR/main.py" --tray
EOF

    chmod +x ~/.local/bin/speechcli-tray
fi

mkdir -p "$HOME/.local/share/applications"

cat > "$HOME/.local/share/applications/speechcli-settings.desktop" << EOF
[Desktop Entry]
Type=Application
Name=SpeechCLI Settings
Comment=Configure speech dictation settings
Exec=$HOME/.local/bin/speechcli-settings
Terminal=false
Categories=Utility;Accessibility;
EOF

if [ "$INSTALL_TRAY" = "yes" ]; then
    cat > "$HOME/.local/share/applications/speechcli-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=SpeechCLI Tray
Comment=Start speech dictation from the system tray
Exec=$HOME/.local/bin/speechcli-tray
Terminal=false
Categories=Utility;Accessibility;
EOF

    mkdir -p "$HOME/.config/autostart"

    cat > "$HOME/.config/autostart/speechcli-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=SpeechCLI Tray
Comment=Start speech dictation from the system tray
Exec=$HOME/.local/bin/speechcli-tray
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
fi

# ---------------------------------------
# Configure PATH for ALL shells
# ---------------------------------------

echo "🐚 Configuring shell PATH..."

add_path_if_missing() {
    FILE="$1"
    LINE="$2"

    mkdir -p "$(dirname "$FILE")"
    touch "$FILE"

    if ! grep -Fxq "$LINE" "$FILE"; then
        echo "" >> "$FILE"
        echo "$LINE" >> "$FILE"
    fi
}

# bash
add_path_if_missing \
    "$HOME/.bashrc" \
    'export PATH="$HOME/.local/bin:$PATH"'

# zsh
add_path_if_missing \
    "$HOME/.zshrc" \
    'export PATH="$HOME/.local/bin:$PATH"'

# fish
add_path_if_missing \
    "$HOME/.config/fish/config.fish" \
    'fish_add_path ~/.local/bin'

# sh profile
add_path_if_missing \
    "$HOME/.profile" \
    'export PATH="$HOME/.local/bin:$PATH"'




# ---------------------------------------
# Setup ydotoold for Wayland
# ---------------------------------------

echo "⌨️ Configuring ydotoold..."

mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/ydotool.service" << EOF
[Unit]
Description=ydotool daemon

[Service]
ExecStart=/usr/bin/ydotoold --socket-path=%h/.ydotool_socket
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now ydotool.service

# ---------------------------------------
# Add env variable to ALL shells
# ---------------------------------------

add_path_if_missing \
    "$HOME/.bashrc" \
    'export YDOTOOL_SOCKET="$HOME/.ydotool_socket"'

add_path_if_missing \
    "$HOME/.zshrc" \
    'export YDOTOOL_SOCKET="$HOME/.ydotool_socket"'

add_path_if_missing \
    "$HOME/.profile" \
    'export YDOTOOL_SOCKET="$HOME/.ydotool_socket"'

add_path_if_missing \
    "$HOME/.config/fish/config.fish" \
    'set -gx YDOTOOL_SOCKET $HOME/.ydotool_socket'

# ---------------------------------------
# Finished
# ---------------------------------------

echo ""
echo "✅ speechcli installed / updated successfully"
echo ""
echo "Restart your shell:"
echo ""
echo "    exec \$SHELL"
echo ""
echo "Usage:"
echo ""
echo "    speechcli"
echo "    speechcli --settings-ui"
echo "    speechcli --tray"
echo "    speechcli --output"
echo "    speechcli --copy"
echo "    speechcli --type"
echo "    speechcli --type --auto-punctuation"
echo "    speechcli --type --language hi-IN"
echo "    speechcli --list-microphones"
echo "    speechcli --type --device-index 0"
echo "    speechcli --language en-US --device-index 0 --auto-punctuation --save-settings"
echo "    speechcli --show-settings"
echo "    speechcli --type --no-auto-punctuation --no-overlay"
echo "    speechcli --type --listen-timeout 10 --pause-threshold 1.0"
echo "    speechcli --type --copy --output --auto-punctuation --overlay --language en-US"
echo "    speechcli --verbose"
echo ""
if [ "$INSTALL_TRAY" = "yes" ]; then
    echo "System tray app:"
    echo ""
    echo "    speechcli-tray"
    echo ""
    echo "It has also been added to desktop autostart."
    echo ""

    if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
        if ! pgrep -f "main.py --tray" >/dev/null 2>&1; then
            nohup "$HOME/.local/bin/speechcli-tray" >/dev/null 2>&1 &
            echo "SpeechCLI tray started."
            echo ""
        fi
    fi
fi
echo "🎉 speechcli is globally available now"
echo ""
