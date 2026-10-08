#!/usr/bin/env bash
# install.sh — gör maskinen redo och installerar Scribentia.
#
# Ordningen är inte godtycklig, och den var fel förut: Qt:s behov mäts med ldd
# på libqxcb.so, och den filen kommer med PyQt6. Mätte man innan beroendena
# fanns tittade kontrollen på en fil som inte fanns och sa att allt var bra —
# på en ren maskin upptäcktes aldrig de saknade X11-biblioteken. Alltså:
#
#   1. python 3.11+ (och venv-modulen, som är ett eget paket på Debian)
#   2. .venv med beroendena (uv om det finns, annars python3 -m venv + pip)
#   3. systembiblioteken Qt och mikrofonen behöver — ldd säger vilka, och de
#      installeras med maskinens egen pakethanterare i stället för att skrivas ut
#   4. startare, ikon och menyval
#   5. provstart i åtta sekunder: en app som inte startar rapporteras inte som klar
#
#   ./install.sh              installera eller uppdatera
#   ./install.sh --check      bara kontrollera, ändra ingenting
#   ./install.sh --uninstall  ta bort startaren, ikonen och menyvalet
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

# Vad systemet behöver, per familj. Hela listan installeras när något saknas —
# den är kort, pakethanteraren hoppar över det som redan finns, och en
# bibliotek-till-paket-tabell för hand blir fel så snart en distribution byter
# namn. python3-venv ligger med av samma skäl: steg 2 kan behöva den.
case "$FAMILY" in
    arch)   PACKAGES="python libxcb xcb-util-cursor xcb-util-wm libxkbcommon-x11 libglvnd fontconfig dbus portaudio"
            PM="pacman -S --needed --noconfirm" ;;
    debian) PACKAGES="python3 python3-venv python3-pip libxcb1 libxcb-cursor0 libxcb-icccm4 libxkbcommon-x11-0 libgl1 libfontconfig1 libdbus-1-3 libxcb-xinerama0 libportaudio2"
            PM="apt-get install -y" ;;
    fedora) PACKAGES="python3 python3-pip libxcb xcb-util-cursor xcb-util-wm libxkbcommon-x11 mesa-libGL fontconfig dbus-libs portaudio"
            PM="dnf install -y" ;;
    suse)   PACKAGES="python3 libxcb1 libxkbcommon-x11-0 libglvnd fontconfig libdbus-1-3 portaudio"
            PM="zypper install -y" ;;
    *)      PACKAGES=""; PM="" ;;
esac

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 && SUDO="sudo"
fi

install_packages() {
    # $1: vad som saknades, till beskedet när det inte går att installera.
    if [ -z "$PM" ]; then
        echo "  Okänt paketsystem ($DISTRO). Installera själv: $1" >&2
        return 1
    fi
    if [ "$(id -u)" -ne 0 ] && [ -z "$SUDO" ]; then
        echo "  Behöver root eller sudo för att installera: $1" >&2
        return 1
    fi
    echo "  Saknas, installerar: $PACKAGES"
    [ "$FAMILY" = "debian" ] && $SUDO apt-get update -qq
    # shellcheck disable=SC2086
    $SUDO $PM $PACKAGES || return 1
    return 0
}

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
    echo "AVBRYTER: hittar ingen python3." >&2
    [ -n "$PM" ] && echo "  Försök: $SUDO $PM python" >&2
    exit 1
fi
PY_VERSION="$("$PY_BASE" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
KORT="${PY_VERSION%%.*}"; LANG="${PY_VERSION#*.}"
if [ "$KORT" -lt 3 ] || { [ "$KORT" -eq 3 ] && [ "$LANG" -lt 11 ]; }; then
    echo "AVBRYTER: Scribentia kräver Python 3.11 eller nyare, du har $PY_VERSION." >&2
    exit 1
fi
echo "Python: $PY_VERSION"

# venv-modulen är ett eget paket på Debian och Ubuntu.
if ! "$PY_BASE" -m venv --help >/dev/null 2>&1; then
    echo "Python: venv-modulen saknas"
    if [ "$MODE" != "check" ]; then
        install_packages "python3-venv"
        "$PY_BASE" -m venv --help >/dev/null 2>&1 \
            || { echo "AVBRYTER: utan venv-modulen går ingen egen miljö att skapa." >&2; exit 1; }
    fi
fi

# --------------------------------------------------------------- miljön
# Beroendena först: Qt:s systembibliotek går inte att mäta förrän PyQt6 finns,
# och PyQt6 kommer med dem. Motsatt ordning mäter en fil som inte finns.
if [ "$MODE" = "install" ]; then
    if command -v uv >/dev/null 2>&1; then
        echo "Miljö: uv sync"
        uv sync --directory "$SCRIPT_DIR" >/dev/null || { echo "uv sync misslyckades" >&2; exit 1; }
    else
        if [ ! -x "$VENV_DIR/bin/python" ]; then
            echo "Miljö: skapar .venv (uv finns inte på den här maskinen)"
            "$PY_BASE" -m venv "$VENV_DIR" || { echo "AVBRYTER: kunde inte skapa en virtuell miljö." >&2; exit 1; }
        fi
        PY="$VENV_DIR/bin/python"
        echo "Miljö: installerar beroendena i .venv"
        # En venv skapad av uv har inget pip, och samma .venv kan komma från en
        # tidigare installation med uv — pip kan inte antas bara för att den finns.
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
fi

PY="$VENV_DIR/bin/python"
[ -x "$PY" ] || PY="$PY_BASE"

# ------------------------------------------------- Qt och mikrofonen
# PyQt6-hjulet bär Qt men inte X11-klienterna, och sounddevice paketerar inte
# PortAudio. ldd på plattformspluginen är det enda svar som gäller den här
# maskinen — en lista över vad som är vanligt att saknas är inte samma sak som
# vad som saknas här. Båda kontrolleras, båda installeras, och svaret mäts om.
QTBIB=""
for kandidat in "$VENV_DIR"/lib/python*/site-packages/PyQt6/Qt6/plugins/platforms/libqxcb.so \
                /usr/lib/python3*/site-packages/PyQt6/Qt6/plugins/platforms/libqxcb.so \
                "$HOME"/.local/lib/python3*/site-packages/PyQt6/Qt6/plugins/platforms/libqxcb.so; do
    if [ -f "$kandidat" ]; then QTBIB="$kandidat"; break; fi
done

saknat_bibliotek() {
    [ -n "$QTBIB" ] && ldd "$QTBIB" 2>/dev/null | awk '/not found/ {print $1}' | tr '\n' ' '
}
har_portaudio() {
    ldconfig -p 2>/dev/null | grep -q "libportaudio.so"
}

forsok=1
while :; do
    MISSING="$(saknat_bibliotek)"
    if har_portaudio; then PORTAUDIO="ja"; else PORTAUDIO="nej"; fi

    if [ -n "$QTBIB" ] && [ -z "$MISSING" ] && [ "$PORTAUDIO" = "ja" ]; then
        echo "Systembibliotek: Qt:s klienter och PortAudio finns"
        break
    fi
    if [ -z "$QTBIB" ]; then
        echo "Systembibliotek: går inte att mäta (PyQt6 saknas i miljön)"
        break
    fi

    SAKNAS="${MISSING# }"
    [ "$PORTAUDIO" = "nej" ] && SAKNAS="${SAKNAS:+$SAKNAS }libportaudio.so.2"
    echo "Systembibliotek: $SAKNAS"

    if [ "$MODE" = "check" ]; then
        echo "  Skulle installeras: $PACKAGES"
        break
    fi
    if [ "$forsok" -gt 1 ]; then
        echo "  De installerades inte (se felet ovan). Startar appen ändå går det" >&2
        echo "  bra att använda den — men dikteringen behöver PortAudio, och Qt:s" >&2
        echo "  X11-klienter behövs för att ett fönster skall komma upp alls." >&2
        break
    fi
    install_packages "$SAKNAS" || true
    forsok=2
done

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
# traceback. En app som dör direkt ger en annan kod än en som står kvar.
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

# --------------------------------------------------------------- frivilligt
# Inte installerat utan vidare: Ghostscript är stort, Java behövs bara för
# EPUB-validering, och faster-whisper hämtar en modell vid första användningen.
FRIVILLIGA=""
command -v gs   >/dev/null 2>&1 || FRIVILLIGA="$FRIVILLIGA ghostscript(PDF/X-1a)"
command -v java >/dev/null 2>&1 || FRIVILLIGA="$FRIVILLIGA java(EPUBCheck)"
[ -n "$FRIVILLIGA" ] && echo "Frivilligt, för fler funktioner:$FRIVILLIGA"

if [ "$MODE" = "check" ]; then
    [ "$START_OK" = "1" ] && { echo "Kontrollen är grön."; exit 0; }
    exit 1
fi

if [ "$START_OK" = "1" ]; then
    echo "Klart. Starta med 'scribentia' eller från menyn."
    echo "Uppdatera senare med ./update.sh"
else
    echo "Installationen ligger på plats men appen startar inte — se felet ovan." >&2
    exit 1
fi
