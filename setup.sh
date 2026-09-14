#!/bin/bash

set -e

echo "====================================="
echo " LCARS Fedora Desktop Installer"
echo "====================================="

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo
echo "[1/5] Installing required packages..."

sudo dnf install -y \
    sway \
    python3-pyside6 \
    python3-psutil \
    iputils \
    xdg-utils

echo
echo "[2/5] Installing LCARS application..."

mkdir -p "$HOME/lcars-shell"

cp "$PROJECT_DIR/main.py" \
   "$HOME/lcars-shell/main.py"

cp "$PROJECT_DIR/startup.py" \
   "$HOME/lcars-shell/startup.py"

echo
echo "[3/5] Installing Sway configuration..."

mkdir -p "$HOME/.config/lcars-sway"

cp "$PROJECT_DIR/config/sway-config" \
   "$HOME/.config/lcars-sway/config"

echo
echo "[4/5] Installing LCARS login session..."

sudo cp "$PROJECT_DIR/session/lcars-session" \
    /usr/local/bin/lcars-session

sudo chmod +x /usr/local/bin/lcars-session

sudo cp "$PROJECT_DIR/session/lcars.desktop" \
    /usr/share/wayland-sessions/lcars.desktop

echo
echo "[5/5] Checking Python files..."

python3 -m py_compile "$HOME/lcars-shell/main.py"
python3 -m py_compile "$HOME/lcars-shell/startup.py"

echo
echo "====================================="
echo " INSTALLATION COMPLETE"
echo "====================================="
echo
echo "Log out of Fedora."
echo "Select 'LCARS Desktop' at the login screen."
