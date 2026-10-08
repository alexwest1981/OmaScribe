# Verifiering av de nio rapporterna

Agenters påståenden är självrapporter. Detta är min egen kontroll av de fyra nya
rapporterna (06–09), gjord 2026-10-08. Rapporterna 01–05 kontrollerades i det första
passet (`README.md`: 119 källänkar, 111 svarade 200, alla kodpåståenden mot fil och rad).

## Länkkontroll

95 unika URL:er i rapporterna 06–09, hämtade med webbläsar-UA och 20 s om timeout:

- **90 svarar 200.**
- **5 svarar 403** — samtliga `worldanvil.com` (botvägg, inte en död sida). Det betyder
  att World Anvils prisuppgifter i rapport 07 ($4,50 / $8,25 per månad) **inte är
  kontrollerade av mig** och inte får citeras som fakta. Artikel-/tidslinjebeskrivningarna
  kommer från samma domän och bär samma förbehåll.

## Punktkontroll av det jag tänker luta mig mot

Varje rad: påståendet i rapporten → vad jag själv fick ur källan.

| Påstående | Källa | Utfall |
|---|---|---|
| Fictionary: 38 story-element per scen | `fictionary.co/support/help-docs/evaluate/` | **Håller ordagrant:** "providing 38 Story Elements for Character, Plot, and Setting" |
| Papyrus: normseite = 30 rader × 60 tecken | `support.papyrus.de/wiki/…normseiten…` | **Håller ordagrant:** "30 Zeilen zu je (maximal) 60 Zeichen (ohne Silbentrennung)" |
| Vellum: PDF/X-1a:2003, ISO 15930-1, CMYK, SWOP v2, inbäddade teckensnitt | `vellum.pub/specs/` | **Håller.** Däremot hittade jag inte strängen "EPUB 3" på samma sida — rapportens "EPUB 2/3" är inte kontrollerad |
| NovelAI: Context Viewer med tokenbudget och trimning | `docs.novelai.net/en/text/editor/advancedsettings/` | **Håller:** "Context Viewer" + Context Settings "budgeted, positioned, and trimmed within your Context limit" |
| ProWritingAid: Chapter Critique, Plot Analysis, Character Analysis, Manuscript Analysis, Virtual Beta Reader, Marketability Analysis, Premium/Premium Pro, Lifetime | `prowritingaid.com/pricing` | **Håller** — samtliga namngivna funktioner står på prissidan |
| AutoCrit: Story Analyzer+, genrejämförelse, Grammar Checker, Book Formatting | `autocrit.com/pricing` | **Håller** i navigering/funktionslista. Rapporternas antal ("25+") kontrollerade jag inte siffra för siffra |
| Sudowrite: Story Bible med Braindump/Genre/Style/Synopsis/Characters/Worldbuilding/Outline/Scenes + Saliency Engine | `feedback.sudowrite.com/…what-is-story-bible`, `…saliency-engine` | **Håller** — båda artiklarna finns med de namnen |
| Scrivener: Corkboard, Collections, Compile till Word/PDF/Final Draft/e-bok | `literatureandlatte.com/scrivener/overview` | **Håller** för översikten. Listan över Compile-flikar kommer ur Mac-manualens PDF och är **inte** kontrollerad av mig rad för rad |

## Vad jag inte kontrollerade

- **Prisbelopp** i rapport 06 och 09 (ProWritingAid $30/$36, AutoCrit $30, Fictionary
  $19/$39, Sudowrite $10/$22/$44, Squibler $29,99, NovelAI $10/$15/$25). De står på
  prissidor jag hämtade, men en prissida är en kampanjyta: beloppen får inte bli kod
  eller löfte utan en ny kontroll vid köptillfället.
- **World Anvils priser** (403, se ovan).
- **Compile-flikarnas fullständiga lista** per OS (Scrivener-manualen, en PDF).
- **Fictionarys 38 elements exakta namn** — antalet håller, listan i rapporten är
  agentens läsning av Evaluate-sidorna, inte min.

## Korrigeringar

- Rapport 09:s rubrikrad är kvar från briefen ("Research-brief D: de AI-nativa
  betalverktygen") i stället för en egen titel. Innehållet är rätt; rubriken är kosmetisk
  och står kvar som spår av att den skrevs mot en brief.

## Rapport 10 och 11 (det öppna och juridiska) — kontrollerade 2026-10-08

Rapport 10 bygger på GitHub-API:et. Jag körde om varje rad själv (`gh api` för 12 repon):

| Påstående | Utfall |
|---|---|
| novelWriter: GPL-3.0, pushad 2026-10-07, release v26.2.1 2026-09-26, 111 issues | **Håller exakt**, och repot ligger verkligen på `saga-soft/novelWriter` (`vkbo/novelWriter` svarar "Moved Permanently" dit) |
| Manuskript: GPL-3.0, pushed 2026-09-01, 588 issues | **Håller** |
| Zettlr: GPL-3.0, pushed 2026-10-06, 548 issues | **Håller** |
| FocusWriter 2026-10-08 / 20 issues, KDE/ghostwriter 2026-10-08 / 22 issues | **Håller** |
| KIT Scenarist: **arkiverat**, senaste push 2023-08-01 | **Håller** (`archived=true`, 350 stjärnor) |
| bibisco: senaste push i öppna repot 2024-09-27, 107 issues | **Håller** |
| Calibre, Sigil: GPL-3.0. Pandoc: GPL-2.0. Typst: Apache-2.0 | **Håller** |
| oStorybook: "UNVERIFIED" i rapporten | **Nu mätt:** repot finns (`favdb/oStorybook`), GPL-3.0, senaste push 2023-10-24, 7 stjärnor — i praktiken vilande |

Två fel i rapporten som jag rättar i stället för att låta stå:

- **Felaktig källhänvisning:** Manuskripts licens anges som
  `github.com/milotype/manuskript/blob/master/LICENSE` — den URL:en svarar **404**, och
  filen heter `COPYING` (inte `LICENSE`). Rätt källa är
  `github.com/olivierkes/manuskript/blob/master/COPYING`, och den innehåller GPL v3:s
  text. Om det är `-only` eller `-or-later` går inte att se ur filen; GitHub-API:et svarar
  bara `GPL-3.0` för båda. **Därför står `or-later` som obelagt.**
- **Ett citat som inte finns i källan:** novelWriters licenscitat ("Permissions of this
  strong copyleft license are conditioned on making available complete source code…")
  finns **inte** i repots `LICENSE.md` (0 träffar) — det är GitHubs egen sammanfattning av
  GPL-3.0. Projektets egen rad är "novelWriter is licenced under GPLv3" i README. Licensen
  håller alltså; citatet var fel attribuerat.

Rapport 11:s bärande citat håller ordagrant mot Riverbanks egen sida:

> "PyQt is dual licensed on all supported platforms under the GNU GPL v3 and the
> Riverbank Commercial License. Unlike Qt, PyQt is not available under the LGPL."

Det är första hand, från leverantören, och det är hela grunden för att GPL-3.0-only är
tvingad — inte vald. Två rättelser till rapport 11:

- Den föreslår `license = { text = "GPL-3.0-only" }` i `pyproject.toml`. Det är den gamla
  tabellformen; PEP 639 ersatte den med `license = "GPL-3.0-only"` +
  `license-files = ["LICENSE"]`. Det är den formen som är byggd, och den är **verifierad i
  det byggda hjulet** (`License-Expression: GPL-3.0-only`, LICENSE i `dist-info/licenses/`).
- Licensfilen i repot är hela GPL v3:s text (674 rader ur gnu.org), inte ett utdrag.
