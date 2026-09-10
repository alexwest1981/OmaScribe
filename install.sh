#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "=== Installing OmaScribe ==="

# Säkerhetsspärr. Dokumentfiler i projektmappen kan innehålla API-nycklar.
# Inget sådant får följa med till en installation, och ingen ska behöva
# upptäcka det i efterhand — avbryt hellre.
LEAKS="$(find "$SCRIPT_DIR" -maxdepth 1 -type f \
    \( -iname '*.docx' -o -iname '*.doc' -o -iname '*.pdf' -o -iname '*.odt' \
       -o -iname '*.key' -o -iname '*.pem' \) 2>/dev/null || true)"
if [ -n "$LEAKS" ]; then
    echo "AVBRYTER: dokumentfiler hittades i projektmappen." >&2
    echo "De kan innehålla API-nycklar och får inte ingå i en installation:" >&2
    echo "$LEAKS" >&2
    echo "Flytta dem utanfor projektet och kor om." >&2
    exit 1
fi

# Check for uv or python3
if command -v uv >/dev/null 2>&1; then
    echo "Using uv environment..."
    cd "$SCRIPT_DIR"
    uv sync
    RUNNER="uv --directory $SCRIPT_DIR run python $SCRIPT_DIR/main.py"
else
    echo "Using system python..."
    RUNNER="python3 $SCRIPT_DIR/main.py"
fi

mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# Copy Icon
if [ -f "$SCRIPT_DIR/icon.png" ]; then
    cp "$SCRIPT_DIR/icon.png" "$ICON_DIR/omascribe.png"
fi

# Create launcher wrapper in ~/.local/bin
cat << LAUNCHER > "$BIN_DIR/omascribe"
#!/usr/bin/env bash
exec $RUNNER "\$@"
LAUNCHER
chmod +x "$BIN_DIR/omascribe"

# Install Desktop file
cat << DESKTOP > "$DESKTOP_DIR/omascribe.desktop"
[Desktop Entry]
Name=OmaScribe
GenericName=AI Rich Text Editor
Comment=Word-like Rich Text Editor with Real-Time AI Review and Dictation
Exec=$BIN_DIR/omascribe %F
Icon=$ICON_DIR/omascribe.png
Terminal=false
Type=Application
Categories=Office;WordProcessor;TextEditor;Utility;
MimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document;text/markdown;text/plain;text/html;
StartupWMClass=OmaScribe
DESKTOP

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo "=== OmaScribe Installed Successfully! ==="
echo "You can launch it by typing 'omascribe' or from your application menu (Super + Space)."
