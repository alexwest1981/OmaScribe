# Findings & Decisions

## Requirements

Alex vill att OmaScribe skall ha **allt** ett professionellt författarverktyg har.
Underlaget är fem agentrapporter i `docs/research/author-tools/` (119 källor, kontrollerade).
Hela listan med status ligger i `task_plan.md` — den är den enda sanningskällan för vad som är kvar.

## Research Findings

- **Bordet i kategorin** (vad som krävs för att kallas professionellt, ur R01–R05): hierarkisk
  manusstruktur med scener som egna dokument och metadata; redaktionell kontroll (spårade
  ändringar, kommentarer med tråd, acceptera/avvisa enskilt); uppdaterbar innehållsförteckning
  och korsreferenser; versionshistorik och dokumentjämförelse; mål per session och projekt med
  dagskvot; EPUB + tryck-PDF + DOCX ur samma manus; tillgänglighetsmetadata.
- **Mätt mot koden** (`docs/research/author-tools/narvaromatris.txt`): noll träffar på
  spårade ändringar, fotnoter, korsreferenser, infogad TOC, namngivna stilar, snapshots,
  stavning/grammatik, EPUB, tryckfärdig PDF, skrivmål, story bible. Nyckelordsträffar är
  pekare, inte fynd — "spalt" var tabellkod och "mål" var valvets wikilänkar.
- **AI-fallgropar** (R04, designkrav i planen): hallucinationer och röstförlust i långa verk
  är dokumenterade, inte lösta. Därför: visa källor, gör AI-förslag granskningsbara, låt aldrig
  genererad fakta bli kanon automatiskt.
- **KDP-siffrorna** i R05 (marginaler per sidantal, ryggkoefficienter per papperstyp) är
  Amazons egna uppgifter och bör läsas in som data, inte hårdkodas i logik.

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Projekt = mapp med `project.json` + en HTML-fil per scen | Människoläsbart, git-vänligt, ingen databas att korrumpera; varje scen får egen versionshistorik per fil |
| `core/project.py` är Qt-fritt | Självprovet körs utan skärm; modellen kan läsas av kommandoradsverktyg |
| Ordningstal i syskonlistan, omnumreras vid flytt | Kapitel räknas i tiotal, inte tusental — gles ordning vore överkonstruktion |
| Ord i HTML räknas med `\w+` i projektmodulen | Modulen slipper Qt; skiljer sig möjligen från statusfältets räknare — byt till en delad räknare om siffrorna måste stämma exakt |
| Grinden använder live-kassans `.venv` | En fräsch worktree har ingen egen `.venv` (gitignorerad), och nya beroenden får då inte smyga in |
| Nya moduler skrivs på engelska | Alex regel 23/9; de äldre modulerna lämnas i fred |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `import numpy` dog i `.venv` | Hermes-skalet exporterar `PYTHONPATH` mot sin egen python 3.14, som skuggade projektets 3.12-paket. `unset PYTHONPATH` löste det; grinden gör det själv. Ominstallation hjälpte inte. |
| Agenternas självprov var gröna men EPUB saknade bokens språk | Oberoende prov (skrivet av mig) hittade det. Agentens eget prov testade aldrig `lang`-attributet. |

## Resources

- `docs/research/author-tools/` — fem rapporter + `narvaromatris.txt`
- `tools/test_all.sh` — grinden: importkontroll, fyra modulprov, `ui_smoke` (41), `print_purity_check` (54)
- `core/project.py`, `core/epub.py`, `core/snapshots.py`, `core/spellcheck.py` — körbara med `python -m core.<modul>`

## Visual/Browser Findings

- `ui_smoke.py` exporterar sina filer till en temp-katalog och skriver ut sökvägen — PDF/DOCX/HTML
  kan granskas där när något ser fel ut i en export.
