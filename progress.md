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

## Session: 2026-10-07 (pass 2 — fas 1 i mål)

### Fas 1: Manusstruktur (1.1–1.14)

- **Status:** complete — alla fjorton punkter avslutade, committade och pushade
- Byggt i detta pass: koppling scen ↔ researchmaterial, scenanteckning, valvpanelens uppslag på
  scenens rubrik (i stället för filnamnet `0001-scen-1`, som ingen skriver i en anteckning),
  statusfärg i träd och korttavla (statusen står som text också — färgen bär aldrig betydelsen själv),
  projektmallar roman/fackbok/novell/enkel i en egen dialog (ordmålet gick inte att nå förut),
  scenens entiteter mot projektets codex, skrivning i läsvyn (texten tillbaka till rätt scenfil via
  stycken märkta med sin scen), marginalkommentarer fästa på ett citat (ankaret är citatet, inte en
  position), och manusvarianter (namngiven ordning som kan läggas på manuset).
- Medvetna avgränsningar: innehållsligt grenade manusvarianter och trådade marginalkommentarer hör
  till fas 3 (snapshots 3.1, kommentartrådar 3.3). Rapportens egen slutsats är att snapshots kommer först.
- Files created: `ui/project_dialog.py`, `ui/entity_dialog.py`, `ui/variants_dialog.py`
- Files modified: `core/project.py` (135 kontroller), `ui/scene_inspector.py`, `ui/binder_panel.py`,
  `ui/corkboard.py`, `ui/scrivenings.py`, `ui/main_window.py`, `tools/test_all.sh`, `tools/ui_smoke.py`

## Test Results

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Grinden | `bash tools/test_all.sh` | allt grönt | importkontroll 39 moduler, 12 modulprov (project 135, scrivenings 31), ui_smoke 262, print_purity 54 | GRÖNT |
| Falsifiering: endast ändrade scener skrivs | `changed_content` returnerar allt | rött | 4 prov föll (en orörd läsning rör filerna) | bevisat |
| Falsifiering: kommentarens ankare | `doc.find(quote)` pinnat till position 0 | rött | 1 prov föll ("markeringen sitter på citatet") | bevisat |
| Grinden ostädad | `ui_smoke` via `test_all.sh` | grönt och avslutat | hängde på en modal ruta i `closeEvent` tills modalen togs bort | fann en riktig bugg |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| pass 1 | `numpy._core._multiarray_umath` saknas | 1 | Hermes-skalets `PYTHONPATH` mot python 3.14 skuggade projektets paket. `unset PYTHONPATH`; grinden gör det själv. |
| pass 1 | `move_node` dubblerade noden | 1 | `children()` räknade in noden före insättning. Filtreras bort först. Självprovet fann det. |
| pass 1 | EPUB: `lang` hårdkodad | 1 | Mitt oberoende prov fann det. Språket följer nu metadata. |
| pass 2 | Grinden öppnade riktiga fönster i sessionen och hängde | 1 | Skalets `QT_QPA_PLATFORM=wayland;xcb` ärvdes; `setdefault` i provet räcker inte. Grinden exporterar nu `QT_QPA_PLATFORM=offscreen`. |
| pass 2 | `ui_smoke` grönt men hängde i teardown | 1 | `closeEvent → _maybe_save_changes` visade en modal: att lämna projektet lämnade sista scenen som osparat dokument utan väg. `_deactivate_project` tömmer nu bufferten. |
| pass 2 | 13 orphaned ui_smoke-processer efter tool-timeouts | 1 | Konkurrerade om CPU och såg ut som nya hängningar. Döda med mönster som inte matchar egen kommandorad (`pkill -f "[u]i_smoke"`). |
| pass 2 | `mnemosyne_task_progress` / `mnemosyne_remember` | 1 | `ImportError: cannot import name 'write_policy_operation' from 'mnemosyne.core.filters'` — pluginets version matchar inte. Antecknat, inte åtgärdat (miljö, inte projektet). |

## 5-Question Reboot Check

| Question | Answer |
|----------|--------|
| Where am I? | Fas 1 klar (1.1–1.14, commit `fae80aa`), grinden grön (12 modulprov, ui_smoke 262, print_purity 54) |
| Where am I going? | Fas 2 (författarlagret) eller fas 3.1 (snapshots per scen) enligt `task_plan.md` |
| What's the goal? | Allt ett professionellt författarverktyg har, in i OmaScribe |
| What have I learned? | Se `findings.md` |
| What have I done? | Se ovan — fas 0 (fundament, grind, projektmodell) och fas 1 (manusstruktur 1.1–1.14) |

## Session: 2026-10-07 (pass 5 — pappret blir ark, författarlagret börjar)

### Pappret: ett ark per sida

- **Status:** complete, pushat (`8a26fde`). Alex: "DELA bladet, så det blir 2 ark, eller fler,
  när man når slutet" — det gamla försöket (ett grått band över texten) revs.
- `core/pagination.py` (ny): radbunden paginering — varje ark börjar vid en *rads* överkant,
  tabeller och bilder flyttas hela, en inlagd sidbrytning börjar ett nytt ark. Eget självprov
  som kontrollerar att ingen rad korsar en arkgräns.
- `ui/paged_paper.py` (ny): ark-kolumnen. Det ark markören står i bär den riktiga editorn
  (flyttas dit, klipps till arkets egen texthöjd); övriga ark ritas statiskt ur dokumentets
  layout. Klick i ett annat ark sätter markören dit. Sidnumret ligger i arkets fot, där det
  nu finns tom plats.
- Mätt: två ark med 26 px mellanrum (`#f4f5f7` mellan, `#ffffff` på arket), ingen rad klippt,
  hjul över texten skrollar pappret (0 → 120), inlagd sidbrytning ger nytt ark (3 → 4).
- Kvar, sagt rakt ut: musmarkering kan inte spänna över två ark, och änke/föräldralöst-skydd saknas.

### Fas 2.1–2.5: författarlagret

- **Status:** complete, grindad (344 rökprov + 54 renhetsprov, GRÖNT).
- `ui/writing_log_panel.py` (ny): skrivloggen i sidopanelen och i statusfältet. Dagens netto,
  dagskvot mot deadline (ur projektmodellen), 14 dagar som stapeldiagram, svit och snitt,
  skrivsprintar med nedräkning och diskret notis, CSV-export.
- `core/writing_log.py` fanns färdig sedan fas 0b men nåddes inte från gränssnittet — nu gör den
  det, med ett prov per inkoppling (7 nya kontroller i `ui_smoke`).
- Loggen ligger i projektmappen när ett projekt är öppet, annars i `~/.local/share/omascribe`.
  Grinden och rökprovet pekar om den med `OMASCRIBE_DATA_DIR` till en temp-mapp, så att deras
  skrivande inte hamnar i Alex riktiga logg.
- Grinden kör nu även `core.pagination`.

### Fas 2.6: skrivmaskinsläge

- **Status:** complete, grindad (348 rökprov + 54 renhetsprov, GRÖNT).
- `PagedPaper.center_cursor()` håller markörens rad mitt i fönstret; läget slås på i
  Visa-menyn och kommer ihåg sig i configen. Maxbredden var redan satt (arket är A4).
- Mätt: 0 px från mitten både mitt i texten och en bit ned, oavsett vilket ark markören
  står i. Vid dokumentets slut kan ingen centrering ske — det finns ingen text att skrolla
  förbi, precis som i Word.
- Rökprovet fick lära sig visa fönstret för den mätningen (skrollfältet är 22 px högt utan
  utläggning) och sedan städa efter sig: dolt fönster och orört dokument, annars stannar
  provets egen stängning i en fråga om att spara — 25 minuter utan ett ord på skärmen.

### Fas 2.8: story biblen

- **Status:** complete, grindad (359 rökprov + 54 renhetsprov, GRÖNT).
- `ui/codex_panel.py` (ny): projektets codex i sidopanelen — sökning, typfilter, lista,
  och ett blad per entitet: namn, typ, alias, vem det är, relationer, scenerna den är
  kopplad till (klick öppnar scenen) och antalet omnämnanden i manuset (alias inräknade).
  Ny/redigera/ta bort, koppla loss scen, lägg till och ta bort relation.
- `core.storybible` fanns färdig sedan fas 1.13 och fick bara `remove_relation` — en
  relation skall gå att ångra. Entiteter, scenkopplingar och relationer städas av
  `ON DELETE CASCADE` när en entitet tas bort (kontrollerat i schemat, inte antaget).
- `ui/entity_dialog.py` förifylls vid redigering, så samma dialog skapar och ändrar.
- Mätt: 2 entiteter i listan, bladet visar rätt scen och relation, omnämnandena räknas
  till 3 med alias ("Anna gick … Anka tittade upp. Anna log."), typfiltret visar bara
  platser, sökningen hittar "Anka" som alias, klick på scenen öppnar rätt nod, och både
  relation och entitet går att ta bort utan att scenen rörs.
- Ingen cache för manuset: en cachad siffra som ljuger när man just ändrat en scen är
  värre än att läsa om boken (millisekunder).

### Teckensnittsmenyn: från skärmhög popup till vanlig meny

- **Status:** complete, grindad (362 rökprov + 54 renhetsprov, GRÖNT).
- Orsak (mätt, inte gissad): stilmallens regler för `QComboBox QAbstractItemView` får Qt att svara
  ja på `SH_ComboBox_Popup`. Menyn fyller då hela den lediga höjden med skrollpilar och listen
  läggs mitt i — 800 px meny, listen 390 px på y=133. Samma regler stänger av menyvyns egen
  skrollist, så bara elva av 37 typsnitt gick att nå.
- Fix: reglerna bort (färgerna kommer från appens palett, som redan sätts ur temat; radhöjden från
  `FontItemDelegate.sizeHint`), och `use_dropdown()` svarar nej på menyläget för teckensnitts- och
  storleksmenyn. Mätt efteråt: 366 px för 14 rader à 26 px, listen från y=0, skrollist med 23 rader
  kvar, läsbar även i temat dark.
- Två fällor på vägen, båda värda att minnas: en `QProxyStyle` som bara hålls i en Python-variabel
  dör före sina widgetar och ger signal 11 i städningen (appen får äga den), och rökprovet får inte
  öppna menyn — offscreen-plattformen kraschar ibland i städningen efter en visad popup, så provet
  mäter mekanismen (stilfrågan, skrollisten, radhöjden) i stället.

### Fas 2.9: plot-tavlan

- **Status:** complete, grindad (371 rökprov + 54 renhetsprov, GRÖNT).
- `ui/plot_grid.py` (ny): manuset som tabell — en rad per scen med del/kapitel, tråd
  (etiketter), POV, status, när i berättelsen, ord och ordmål. Redigerbar direkt i
  tabellen; status genom en meny med projektets egna statusar. Klick på titeln öppnar
  scenen (dubbelklick i de andra kolumnerna ändrar dem — titeln är därför inte redigerbar,
  ett klick skall inte kunna bli både öppna och ändra).
- Sorteringen är hela poängen: manusordning, tidslinje (scenens egen tid, tom tid sist),
  POV eller status. Modellen fick fältet `when`.
- Tavlan ligger som en egen sida i stacken, inte som flik i sidopanelen: åtta kolumner är
  ~790 px och panelen är 370 (mätt: tabellen blir 1184 px bred i ett 1250 px fönster, alla
  kolumner synliga). Vägen dit och tillbaka går genom Visa-menyn; verktygsraden göms medan
  tavlan är uppe och kommer tillbaka med manuset (den vägen var låst först — `show_editor_screen`
  visar raden men låser inte upp den, så `_sync_reading_mode(False)` måste med).
- Mätt i provet: 3 rader × 8 kolumner, tidslinjen ger dag 1, dag 3, tom sist, en ändring i
  tabellen skriver till modellen och till manifestet, klick öppnar rätt scen, och vägen
  tillbaka ger manuset och formateringsraden tillbaka. Två kontroller bit-testade.
- Medvetet inte gjort: en grafisk tidslinje. Texten i `when` sorterad i tid är tidslinjen
  en ensam författare läser; en ritad tidslinje är en egen vy den dag någon saknar den.

### Fas 2.10: taggar, samlingar och anteckningar på scen

- **Status:** complete, grindad (376 rökprov + 54 renhetsprov, GRÖNT).
- Mätt först, byggt sedan: nästan allt fanns redan. Sceninspektören redigerar taggar
  (`input_labels`), anteckning (`input_note`, med fördröjning) och status; `core/collections.py`
  har frågespråket `status:`, `etikett:`, `pov:`, `text:`; statusfärgen sitter i trädet och
  korktavlan. Det som saknades var sista steget i arbetsflödet ur forskningen — samlingen gick
  att filtrera fram men inte att *arbeta igenom*.
- Därför: en läs-knapp i samlingspanelen (`▶`) som öppnar samlingens scener i läsvyn, och
  `_show_scrivenings(noder, rubrik)` utbruten så att hela manuset och en samling går samma väg.
- Mätt i provet: en sparad sökning på `status:Utkast` ger 2 av 3 scener, scenens anteckning
  ligger kvar, läsvyn visar exakt samlingens scener i manusets ordning, och vägen tillbaka går
  till manuset.

### Fas 2.12: revisionsläget

- **Status:** complete, grindad (381 rökprov + 54 renhetsprov, GRÖNT).
- Plot-tavlan fick en **Utkast**-kolumn (1–9, samma gränser som sceninspektören — redigerbar
  i tabellen, skriven till manifestet) och ett **utkastfilter**: välj utkast 2 och bara de
  scener som nått dit visas, med räkningen "1 av 3 scener i utkast 2". Revisionsläget blir
  en lista att arbeta igenom i stället för ett helt manus.
- "Mål per utkast" blev räkningen i stället för ett talfält per utkast: målet för ett utkast
  är att scenerna har nått det. Nio målfält som ingen fyller i är sämre än en siffra som
  stämmer — egna ordmål per utkast är ett fält i projektdialogen den dag de saknas.
- Mätt i provet: filtret ger 1 rad av 3 och rätt räkning, alla utkast visar dem igen,
  utkastnumret skrivs till modellen, och ett skrivet 99 stannar på 9.

### Fas 2.15: tunga meningar markeras i texten

- **Status:** complete, grindad (386 rökprov + 54 renhetsprov, plus läsbarhetens eget självprov).
- LIX fanns i `core/document_stats.py` och visades som en siffra i panelen, men ingenstans i
  texten — rådet gick inte att agera på. Nu markerar `ReadabilityHighlighter` tunga meningar
  med en prickad understrykning. Formen bär betydelsen (en färgblind författare ser den), och
  markeringen är en *vy*-format som kommentarerna: texten rörs inte och inget hamnar i filen.
- Enheten är meningen, inte ordet: det är orden per mening LIX drivs av, så markeringen visar
  precis det rådet gäller. Tröskeln är 20 ord.
- `sentence_ranges(text, max_words)` är ren och har eget självprov (5 kontroller), och grinden
  kör `core.document_stats`.
- Mätt i provet: noll format när läget är av, ett när det är på, noll igen när det slås av —
  och texten är tecken för tecken oförändrad. Sett i skärmdump: de två långa meningarna bär
  den prickade linjen, de korta gör det inte.
- Skärmdumpen avslöjade en gammal skönhetsfläck som nu står i listan: teckensnittsväljaren visar
  menyrubriken "—— ⭐ Popular Writing Fonts ——" i stället för typsnittet tills man väljer ett.
