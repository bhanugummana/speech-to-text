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
else
    echo "❌ Could not detect Linux distribution"
    exit 1
fi

echo "🐧 Detected distro: $DISTRO"

# ---------------------------------------
# Install system dependencies
# ---------------------------------------

install_arch() {
    sudo pacman -S --needed \
        python \
        python-pip \
        portaudio \
        xdotool \
        ydotool \
        xclip \
        wl-clipboard
}

install_ubuntu() {
    sudo apt update

    sudo apt install -y \
        python3 \
        python3-pip \
        portaudio19-dev \
        python3-pyaudio \
        xdotool \
        wl-clipboard \
        xclip
}

install_fedora() {
    sudo dnf install -y \
        python3 \
        python3-pip \
        portaudio-devel \
        xdotool \
        ydotool \
        wl-clipboard \
        xclip
}

case "$DISTRO" in
    arch|endeavouros|manjaro)
        install_arch
        ;;
    ubuntu|debian|pop|linuxmint)
        install_ubuntu
        ;;
    fedora)
        install_fedora
        ;;
    *)
        echo "⚠️ Unsupported distro: $DISTRO"
        echo "Please install dependencies manually"
        ;;
esac

# ---------------------------------------
# Install Python dependencies
# ---------------------------------------

echo "🐍 Installing Python dependencies..."

pip install --break-system-packages \
    SpeechRecognition \
    PyAudio \
    pyperclip

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
echo "    speechcli --output"
echo "    speechcli --copy"
echo "    speechcli --type"
echo "    speechcli --type --copy --output"
echo "    speechcli --verbose"
echo ""
echo "🎉 speechcli is globally available now"
echo ""