# LCARS Fedora Desktop

A custom Fedora Linux desktop environment inspired by the LCARS interface from Star Trek.

## Features

- Custom LCARS-style Fedora desktop
- Dedicated Sway / Wayland login session
- Animated planetary startup screen
- Live CPU and memory monitoring
- System uptime and Fedora information
- Network status and IP information
- Real ping operations
- File browser
- File metadata
- Image preview
- Delete confirmation
- Firefox launcher
- Terminal launcher
- Logout, restart, and shutdown controls
- Touch-friendly interface

## Architecture

Fedora Linux
-> Wayland
-> Sway
-> Python / PySide6 LCARS shell

## Installation

Clone the repository:

    git clone https://github.com/Roshan1078/LCARS-Fedora-Desktop.git
    cd LCARS-Fedora-Desktop

Then install:

    chmod +x setup.sh
    ./setup.sh

After installation, log out of Fedora.

At the Fedora login screen choose:

LCARS Desktop

Then log in normally.

## Emergency Controls

- Super + 1 - Return to LCARS
- Super + Enter - Emergency terminal
- Super + Shift + Esc - Exit LCARS session

## Project Files

- main.py - Main LCARS desktop interface
- startup.py - Planet startup animation
- config/sway-config - Sway desktop configuration
- session/lcars-session - LCARS session launcher
- session/lcars.desktop - Fedora login entry
- setup.sh - Installer
