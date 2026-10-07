# Progress Log

## Session: 2026-10-07 (pass 1 — research + fundament)

### Research: fem agentrapporter

- **Status:** complete
- Fem codex-agenter via Orca, en worktree var, en fråga var: manusstruktur, redaktörskap,
  författarens arbetsflöde, AI-nativa verktyg, publicering/export.
- Leverans i `docs/research/author-tools/` + `README.md` med gapet. Committad och pushad (`8477b3f`).
- Verifierat av mig: alla kodpåståenden mot fil och rad (en radhänvisning avvek), 111 av 119
  källänkar svarar 200 — de åtta andra är botväggar eller transienta timeouts.
- Worktrees och grenar städade efteråt.

### Fas 0: buggar, grind, projektmodell

- **Status:** complete (0.2 flyttad till 5.5 — den är en saknad funktion, inte en bugg)
- **Started:** 2026-10-07
- Actions taken:
  - Mätte baslinjen: `ui_smoke` 40 gröna, `print_purity_check` 54 gröna.
  - Byggde `tools/test_all.sh` (importkontroll + modulprov + smoke + renhet).
  - Fixade DOCX-exporten som tappade `page_settings` — alla sju exportvägar går nu genom
    `MainWindow._save_document()`.
  - Lade in ett prov i `ui_smoke` som **falsifierades**: med felet återinfört föll det.
  - Slagna ihop de två kopiorna av `_toggle_focus_mode` till en.
  - Skrev `core/project.py` (27 kontroller) — noder, flytt, metadata, ordmål, dagkvot, `validate()`.
  - Satte tre agenter på oberoende nya moduler parallellt: `core/epub.py`, `core/snapshots.py`,
    `core/spellcheck.py`.
- Files created/modified:
  - `tools/test_all.sh` (ny), `tools/ui_smoke.py` (+1 prov), `ui/main_window.py` (buggfixar),
    `core/project.py` (ny), `core/epub.py` (ny), `core/snapshots.py` (ny), `core/spellcheck.py` (ny),
    `task_plan.md`, `findings.md`, `progress.md`

### Fas 0b: de tre parallella modulerna

- **Status:** complete (modulerna), ej inkopplade i gränssnittet
- Verifierat av mig, inte av agenterna:
  - EPUB: egenbyggd EPUB av ett dokument med `&`, `<`, emoji och tabell. Alla XML-filer välformade,
    manifest och spine hänger ihop, `lang` följer bokens språk. **Ett riktigt fel hittades**:
    kapitlens `lang` var hårdkodad till engelska. Fixat, med kontroll i modulens självprov.
  - snapshots: restore ger exakt samma byte (sha256), unicode och `&` överlever, dubbel skada
    (trasigt index + saknad innehållsfil) återhämtas utan krasch, prune behåller de nyaste.
  - spellcheck: körd mot **riktiga** LanguageTool-tjänsten. `teskt` i en text med emoji före gav
    offset 14:19 — rätt ord. Det var den verkliga risken (UTF-16 mot tecken).

## Test Results

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Grinden | `bash tools/test_all.sh` | allt grönt | importkontroll 39 moduler, project 27, epub 10, snapshots 8, spellcheck 8, ui_smoke 41, print_purity 54 | GRÖNT |
| Falsifiering av DOCX-provet | `_save_document` utan `page_settings` | rött | 1 av 41 föll, just det nya provet | bevisat |
| Oberoende prov vecka 1 | `verify_w1.py` mot live-kassan | 20 gröna | 20 gröna, 0 röda | GRÖNT |
| Språkkontroll live | text med emoji + `teskt` | offset på rätt ord | `[14:19] 'teskt' -> ['test', 'stekt', 'beskt', 'tyskt']` | GRÖNT |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| pass 1 | `numpy._core._multiarray_umath` saknas | 1 | Hermes-skalets `PYTHONPATH` mot python 3.14 skuggade projektets paket. `unset PYTHONPATH`; grinden gör det själv. |
| pass 1 | `move_node` dubblerade noden | 1 | `children()` räknade in noden före insättning. Filtreras bort först. Självprovet fann det. |
| pass 1 | EPUB: `lang` hårdkodad | 1 | Mitt oberoende prov fann det. Språket följer nu metadata. |

## 5-Question Reboot Check

| Question | Answer |
|----------|--------|
| Where am I? | Fas 0, punkt 0.6 (projektvyn i gränssnittet) |
| Where am I going? | Fas 1–6 enligt `task_plan.md` |
| What's the goal? | Allt ett professionellt författarverktyg har, in i OmaScribe |
| What have I learned? | Se `findings.md` |
| What have I done? | Se ovan — fundament, grind, projektmodell, tre moduler |
