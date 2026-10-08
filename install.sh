#!/usr/bin/env bash
# install.sh — sätter upp Scribentia på den här maskinen.
#
# Tre saker den här filen INTE får göra, för det var de som gick sönder när
# någon annan än utvecklaren körde den:
#
#   1. anta att `uv` finns. Utan uv skapas en egen .venv med python3 -m venv och
#      beroendena installeras dit. Att falla tillbaka på systemets python utan
#      att installera något gav "ModuleNotFoundError: PyQt6" på en ren maskin.
#   2. anta att Qt:s systembibliotek finns. PyQt6-hjulet bär sina egna Qt-bibliotek,
#      men inte X11-klienterna (libxcb-cursor, libxkbcommon-x11, libGL). Saknas de
#      startar appen aldrig, och felet ser ut som en Qt-krasch utan förklaring.
#   3. lämna en trasig installation. Efteråt startas appen huvudlöst i åtta
#      sekunder; en app som dör direkt ger en annan kod än en som står kvar.
#
#   ./install.sh              installera (eller uppdatera)
#   ./install.sh --uninstall  ta bort startaren, ikonen och menyvalet
#   ./install.sh --check      bara kontrollera, ändra ingenting
#
# Variabelnamnen är ASCII med flit: bash kör en rad med "sökväg=..." som ett
# kommando i stället för en tilldelning, och felet ser ut som något annat.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
VENV_DIR="$SCRIPT_DIR/.venv"
LAUNCHER="$BIN_DIR/scribentia"
DESKTOP_FILE="$DESKTOP_DIR/scribentia.desktop"
ICON_FILE="$ICON_DIR/scribentia.png"

MODE="install"
case "${1:-}" in
    --uninstall) MODE="uninstall" ;;
    --check)     MODE="check" ;;
    "")          ;;
    *) echo "Okänd flagga: $1 (använd --uninstall eller --check)" >&2; exit 2 ;;
esac

echo "=== Scribentia ==="

# ---------------------------------------------------------------- avinstallera
if [ "$MODE" = "uninstall" ]; then
    rm -f "$LAUNCHER" "$DESKTOP_FILE" "$ICON_FILE"
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR"
    echo "Borttaget: startaren, menyvalet och ikonen."
    echo "Kvar med flit: $VENV_DIR (beroendena), dina dokument och din konfiguration."
    exit 0
fi

# ------------------------------------------------------- vilken slags maskin
DISTRO="okänd"
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    DISTRO="$(. /etc/os-release && echo "${ID:-okänd}")"
    ID_LIKE="$(. /etc/os-release && echo "${ID_LIKE:-}")"
else
    ID_LIKE=""
fi
FAMILY="okänd"
case "$DISTRO $ID_LIKE" in
    *arch*|*cachyos*|*endeavouros*|*manjaro*) FAMILY="arch" ;;
    *debian*|*ubuntu*|*mint*|*pop*)            FAMILY="debian" ;;
    *fedora*|*rhel*|*centos*)                  FAMILY="fedora" ;;
    *suse*)                                    FAMILY="suse" ;;
esac
echo "Distribution: $DISTRO ($FAMILY)"

# --------------------------------------------------------- dokumentlackage
# Dokumentfiler i projektmappen kan innehålla API-nycklar. Inget sådant får
# följa med till en installation, och ingen ska behöva upptäcka det i efterhand.
LEAKS="$(find "$SCRIPT_DIR" -maxdepth 1 -type f \
    \( -iname '*.docx' -o -iname '*.doc' -o -iname '*.pdf' -o -iname '*.odt' \
       -o -iname '*.key' -o -iname '*.pem' \) 2>/dev/null || true)"
if [ -n "$LEAKS" ]; then
    echo "AVBRYTER: dokumentfiler hittades i projektmappen." >&2
    echo "$LEAKS" >&2
    echo "Flytta dem utanför projektet och kör om." >&2
    exit 1
fi

# ----------------------------------------------------------------- python
PY_BASE="${SCRIBENTIA_PY_BASE:-python3}"
if ! command -v "$PY_BASE" >/dev/null 2>&1; then
    echo "AVBRYTER: hittar ingen python3. Installera python först." >&2
    [ "$FAMILY" = "arch" ]   && echo "  sudo pacman -S python" >&2
    [ "$FAMILY" = "debian" ] && echo "  sudo apt install python3 python3-venv" >&2
    [ "$FAMILY" = "fedora" ] && echo "  sudo dnf install python3" >&2
    exit 1
fi
PY_VERSION="$("$PY_BASE" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
KORT="${PY_VERSION%%.*}"; LANG="${PY_VERSION#*.}"
if [ "$KORT" -lt 3 ] || { [ "$KORT" -eq 3 ] && [ "$LANG" -lt 11 ]; }; then
    echo "AVBRYTER: Scribentia kräver Python 3.11 eller nyare, du har $PY_VERSION." >&2
    exit 1
fi
echo "Python: $PY_VERSION"

# --------------------------------------------------------- Qt:s systembibliotek
# PyQt6-hjulen bär Qt men inte X11-klienterna. ldd på plattformspluginen är det
# enda svar som gäller den här maskinen — listan över "vanliga" bibliotek är inte
# samma sak som listan över vad som saknas här.
QTBIB=$(find "$VENV_DIR" /usr/lib/python3*/site-packages -name 'libqxcb.so' 2>/dev/null | head -1)
if [ -z "$QTBIB" ]; then
    QTBIB=$(find "$HOME" -path '*PyQt6/Qt6/plugins/platforms/libqxcb.so' 2>/dev/null | head -1)
fi
SYSTEM_MISSING=""
if [ -n "$QTBIB" ]; then
    SYSTEM_MISSING="$(ldd "$QTBIB" 2>/dev/null | awk '/not found/ {print $1}')"
fi
if [ -n "$SYSTEM_MISSING" ]; then
    echo "Saknade systembibliotek:"
    echo "$SYSTEM_MISSING" | sed 's/^/  /'
    case "$FAMILY" in
        arch)   echo "  sudo pacman -S xcb-util-cursor xcb-util-wm libxkbcommon-x11 libglvnd fontconfig dbus libxcb" ;;
        debian) echo "  sudo apt install libxcb-cursor0 libxcb-icccm4 libxkbcommon-x11-0 libgl1 libfontconfig1 libdbus-1-3 libxcb-xinerama0" ;;
        fedora) echo "  sudo dnf install xcb-util-cursor xcb-util-wm libxkbcommon-x11 mesa-libGL fontconfig dbus-libs xcb-util" ;;
        *)      echo "  Leta upp paketen: apt-file search <bibliotek> | dnf provides <bibliotek> | pacman -F <bibliotek>" ;;
    esac
    echo "  (Qt startar inte utan dem. Installera och kör om.)"
elif [ -n "$QTBIB" ]; then
    echo "Qt:s systembibliotek: alla finns"
else
    echo "Qt:s systembibliotek: libqxcb.so hittades inte än (installeras nedan)"
fi

# --------------------------------------------------------------- miljön
if [ "$MODE" = "install" ]; then
    if command -v uv >/dev/null 2>&1; then
        echo "Miljö: uv sync"
        uv sync --directory "$SCRIPT_DIR" >/dev/null || { echo "uv sync misslyckades" >&2; exit 1; }
        PY="$VENV_DIR/bin/python"
        [ -x "$PY" ] || PY="$SCRIPT_DIR/.venv/bin/python"
    else
        if [ ! -x "$VENV_DIR/bin/python" ]; then
            echo "Miljö: skapar .venv (uv finns inte på den här maskinen)"
            if ! "$PY_BASE" -m venv "$VENV_DIR"; then
                echo "AVBRYTER: kunde inte skapa en virtuell miljö." >&2
                [ "$FAMILY" = "debian" ] && echo "  sudo apt install python3-venv" >&2
                exit 1
            fi
        fi
        PY="$VENV_DIR/bin/python"
        echo "Miljö: installerar beroendena i .venv"
        # En venv skapad av uv har inget pip. Det är samma venv som användaren
        # kan ha från en tidigare installation med uv, så den kan inte antas ha
        # pip bara för att den finns.
        if ! "$PY" -m pip --version >/dev/null 2>&1; then
            echo "  (venven saknar pip — lägger in det)"
            "$PY" -m ensurepip --upgrade >/dev/null 2>&1 \
                || { echo "AVBRYTER: kunde inte lägga in pip i .venv." >&2; exit 1; }
        fi
        "$PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 \
            || echo "  (pip kunde inte uppgraderas — fortsätter med den som finns)"
        "$PY" -m pip install --quiet "$SCRIPT_DIR" || {
            echo "AVBRYTER: beroendena gick inte att installera (nätverk, proxy eller byggverktyg)." >&2
            exit 1
        }
    fi
else
    PY="$VENV_DIR/bin/python"
    [ -x "$PY" ] || PY="$PY_BASE"
fi

# ------------------------------------------------------------ startare och meny
if [ "$MODE" = "install" ]; then
    mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
    [ -f "$SCRIPT_DIR/icon.png" ] && cp "$SCRIPT_DIR/icon.png" "$ICON_FILE"

    # Startaren kör trädet den ligger i — alltid senaste versionen, och samma väg
    # för menyn och terminalen. PATH:en sätts i skriptet: en menyikon får inte
    # räkna med användarens PATH.
    cat > "$LAUNCHER" << LAUNCHER_END
#!/usr/bin/env bash
export PATH="\$HOME/.local/bin:\$PATH"
cd "$SCRIPT_DIR" || exit 1
exec "$PY" "$SCRIPT_DIR/main.py" "\$@"
LAUNCHER_END
    chmod +x "$LAUNCHER"

    cat > "$DESKTOP_FILE" << DESKTOP_END
[Desktop Entry]
Type=Application
Name=Scribentia
GenericName=Word processor for manuscripts
Comment=Word processor for manuscripts, with a deterministic analysis, DOCX/PDF/EPUB export and eleven languages
Exec=$LAUNCHER %F
Icon=$ICON_FILE
Terminal=false
Categories=Office;WordProcessor;TextEditor;Utility;
MimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document;text/markdown;text/plain;text/html;application/epub+zip;
StartupWMClass=Scribentia
DESKTOP_END

    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR"
    echo "Startare: $LAUNCHER"
    echo "Menyval:  $DESKTOP_FILE"
    echo "Ikon:     $ICON_FILE"
fi

# ------------------------------------------------------------- startar den?
# Samma kontroll som grinden kör: appen ska leva efter åtta sekunder, utan
# traceback. En app som dör direkt ger en annan kod.
START_LOG="$(mktemp)"
timeout 8 env QT_QPA_PLATFORM=offscreen SCRIBENTIA_CONFIG_PATH="$(mktemp)" "$PY" "$SCRIPT_DIR/main.py" >"$START_LOG" 2>&1
START_CODE=$?
if [ "$START_CODE" -eq 124 ] && ! grep -q "Traceback" "$START_LOG"; then
    echo "Provstart: appen startar och står kvar (stoppad efter 8 s)"
    START_OK=1
else
    echo "Provstart: MISSLYCKADES (exit $START_CODE)" >&2
    tail -12 "$START_LOG" >&2
    START_OK=0
fi
rm -f "$START_LOG"

if [ "$MODE" = "check" ]; then
    [ "$START_OK" = "1" ] && { echo "Kontrollen är grön."; exit 0; }
    exit 1
fi

if [ "$START_OK" = "1" ]; then
    echo "Klart. Starta med 'scribentia' eller från menyn."
else
    echo "Installationen ligger på plats men appen startar inte — se felet ovan." >&2
    exit 1
fi
