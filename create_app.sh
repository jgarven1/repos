#!/bin/bash
# Creates Plaud.app in the repos folder.
# Run once: bash create_app.sh
# Then double-click Plaud.app to launch the menu bar app.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/Plaud.app"
MACOS="$APP/Contents/MacOS"
PYTHON="$(which python3)"

mkdir -p "$MACOS"

# Info.plist — LSUIElement hides the app from the Dock
cat > "$APP/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Plaud</string>
    <key>CFBundleExecutable</key>
    <string>Plaud</string>
    <key>CFBundleIdentifier</key>
    <string>com.plaud.menubar</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# Launcher — Python is the direct executable so it can connect to the
# macOS window server and display the menu bar icon. A bash intermediary
# prevents that connection from being established.
cat > "$MACOS/Plaud" << EOF
#!$PYTHON
import sys, os, pathlib, runpy

# Add user site-packages so rumps is importable without shell env
_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
_pkgs = pathlib.Path.home() / f"Library/Python/{_ver}/lib/python/site-packages"
if str(_pkgs) not in sys.path:
    sys.path.insert(0, str(_pkgs))

# Run from the repos directory
_repos = pathlib.Path("$SCRIPT_DIR")
os.chdir(str(_repos))
sys.path.insert(0, str(_repos))

runpy.run_path(str(_repos / "plaud_menu_bar.py"), run_name="__main__")
EOF

chmod +x "$MACOS/Plaud"

echo ""
echo "✓ Plaud.app created at: $APP"
echo ""
echo "Next steps:"
echo "  1. Double-click Plaud.app to launch"
echo "  2. Look for 🎙 in your menu bar"
echo "  Optional: drag Plaud.app to your Applications folder"
echo "  Optional: add Plaud.app to Login Items in System Settings → General → Login Items"
echo ""
