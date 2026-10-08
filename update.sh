#!/usr/bin/env bash
# update.sh — hämtar nyare version från GitHub och installerar om den.
#
#   ./update.sh           uppdatera
#   ./update.sh --check   bara tala om ifall det finns något nyare
#
# Skriptet vägrar hellre än gissar. En ocommittad ändring i ett spår*at* fil
# eller en lokal commit som inte finns på GitHub betyder att en uppdatering
# skulle skriva över något någon bryr sig om — då stannar det och säger vad det
# ser. Ospårade filer (anteckningar, utkast) stoppar inte en uppdatering.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="update"
[ "${1:-}" = "--check" ] && MODE="check"

command -v git >/dev/null 2>&1 || { echo "AVBRYTER: git finns inte på den här maskinen." >&2; exit 1; }
cd "$SCRIPT_DIR" || exit 1

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "AVBRYTER: $SCRIPT_DIR är ingen git-klon, så det finns inget att hämta." >&2
    echo "Är programmet installerat med pip: pip install --upgrade scribentia" >&2
    exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if ! git fetch --quiet origin "$BRANCH" 2>/dev/null; then
    echo "AVBRYTER: kunde inte nå GitHub (nätverk, eller grenen $BRANCH finns inte där)." >&2
    exit 1
fi

LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "origin/$BRANCH")"

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Redan senaste versionen: $(git log -1 --format='%h %s')"
    exit 0
fi

if ! git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
    echo "AVBRYTER: du har commits som inte finns på GitHub — de skulle skrivas över." >&2
    echo "  git log --oneline origin/$BRANCH..HEAD    (visar dem)" >&2
    exit 1
fi

echo "Ny version finns: $(git rev-list --count "$LOCAL..$REMOTE") commits"
git log --oneline "$LOCAL..$REMOTE" | head -10 | sed 's/^/  /'

if [ "$MODE" = "check" ]; then
    echo "Kör ./update.sh utan --check för att hämta den."
    exit 0
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "AVBRYTER: du har ändringar i spårade filer, och uppdateringen skulle skriva över dem:" >&2
    git status --short --untracked-files=no | head -10 >&2
    echo "Committa dem, eller spara undan dem med 'git stash', och kör om." >&2
    exit 1
fi

git pull --ff-only --quiet origin "$BRANCH" \
    || { echo "AVBRYTER: git pull misslyckades." >&2; exit 1; }
echo "Uppdaterat: $(git rev-parse --short "$LOCAL") → $(git rev-parse --short HEAD)"

# Samma installation som första gången: beroenden som tillkommit, startaren, och
# provstarten som säger ifall den nya versionen faktiskt startar.
bash "$SCRIPT_DIR/install.sh"
