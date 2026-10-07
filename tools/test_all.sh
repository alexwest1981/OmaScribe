#!/usr/bin/env bash
# tools/test_all.sh — grinden. Samma kommando i en worktree som i live-kassan.
#
#   bash tools/test_all.sh
#
# Kör tre kontroller: att varje modul i core/ och ui/ går att importera, att
# appen startar och fungerar (ui_smoke), och att exporterade filer är rena
# (print_purity_check). Avslutar RÖTT om någon faller.
#
# Interpretern är den utvecklade .venv i live-kassan, eftersom en fräsch
# worktree inte har någon egen .venv (den är gitignorerad). Nya beroenden kan
# därför inte smygas in — vilket är avsiktligt. Sätt OMASCRIBE_PY för att peka
# på en annan tolk.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
unset PYTHONPATH   # Hermes-skalet läcker sin egen python 3.14 hit annars

PY="${OMASCRIBE_PY:-$HOME/Projects/OmaScribe/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "GRINDEN KAN INTE KÖRA: $PY saknas (sätt OMASCRIBE_PY)"
  exit 2
fi

LOG="$(mktemp)"
fail=0

run() {
  local name="$1"; shift
  printf '\n### %s\n' "$name"
  if "$@" >"$LOG" 2>&1; then
    grep -E "RESULTAT|GRÖNT|ren|ok|OK" "$LOG" | tail -2
    tail -1 "$LOG"
  else
    echo "RÖTT: $name"
    tail -25 "$LOG"
    fail=1
  fi
}

run "importkontroll" "$PY" - <<'PYEOF'
import glob, importlib, os, sys
sys.path.insert(0, os.getcwd())
bad = []
for path in sorted(glob.glob("core/*.py") + glob.glob("ui/*.py")):
    name = os.path.basename(path)[:-3]
    if name.startswith("__"):
        continue
    try:
        importlib.import_module(("core." if path.startswith("core") else "ui.") + name)
    except Exception as exc:  # noqa: BLE001 — grinden skall se allt
        bad.append(f"{path}: {type(exc).__name__}: {exc}")
print(f"importerade {len(glob.glob('core/*.py')) + len(glob.glob('ui/*.py'))} moduler")
if bad:
    print("\n".join(bad))
    raise SystemExit(1)
PYEOF

run "projektmodellen" "$PY" -m core.project
run "epub-exporten" "$PY" -m core.epub
run "snapshots" "$PY" -m core.snapshots
run "stavningskontrollen" "$PY" -m core.spellcheck
run "skrivloggen" "$PY" -m core.writing_log
run "storybible" "$PY" -m core.storybible
run "sök och ersätt" "$PY" -m core.find_replace
run "autokorrigeringen" "$PY" -m core.autocorrect
run "korktavlan" "$PY" -m ui.corkboard
run "läsvyn" "$PY" -m ui.scrivenings
run "samlingarna" "$PY" -m core.collections
run "samlingspanelen" "$PY" -m ui.collections_panel
run "ui_smoke" "$PY" tools/ui_smoke.py
run "print_purity" "$PY" tools/print_purity_check.py

rm -f "$LOG"
printf '\n==============================================\n'
if [ "$fail" -eq 0 ]; then echo "GRINDEN: GRÖNT"; else echo "GRINDEN: RÖTT"; fi
exit "$fail"
