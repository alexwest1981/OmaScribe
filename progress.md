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

### Fas 2.14: övningar mot skrivblock

- **Status:** complete, grindad (399 rökprov + 54 renhetsprov + övningarnas eget självprov).
- Forskningens arbetsflöde satt rakt av: markera text eller välj scen, välj en fråga, granska
  förslagen, välj eller ignorera, återgå till skrivandet. Fyra kategorier efter Sparks:
  Vad händer nu?, Dialog, Handling, Sinnesintryck.
- `core/exercises.py` bygger frågan (vald text om det finns en, annars scenens rad) och tolkar
  svaret (numrerade eller punktade rader, inledningsrader bort) — rent och provbart, 11 kontroller.
- `ui/exercise_dialog.py` visar de tre förslagen. Det valda förslaget hamnar i **scenens egen
  anteckning**, inte i manuset: förslagen är vägar in, inte färdig prosa, och anteckningen är
  samma sammanhang som AI:n läser nästa gång. Ingen ny nyckel eller leverantör — anropet går
  genom den befintliga AI-klienten.
- Mätt i provet: hela vägen genom menyvalet (med exec avbytt, den är modal), frågan och
  språket skickas vidare, markörens rad blir texten, förslaget hamnar i anteckningen med den
  gamla kvar före, manuset är tecken för tecken oförändrat, och utan förslag stängs vägen att spara.
- **Inte mätt:** själva AI-svaret. Grinden rör aldrig nätet — den kräver en nyckel och kostar
  pengar. Svaret från modellen går genom `parse_suggestions`, som är provad.

### Fas 2.17: projektets instruktioner till AI:n

- **Status:** complete, grindad (406 rökprov + 54 renhetsprov).
- Projektet har ett fält för sina egna instruktioner — ton, tempus, namn, allt som ska vara lika
  hela vägen — och texten läggs **sist** i systemprompten, närmast uppgiften. Ett tomt fält
  lämnar prompten orörd.
- Regeln bor på ett ställe: alla tre AI-vägarna (granskning, omskrivning, övningarna) går genom
  `AIClient._system_prompt`. Fönstret sätter en *funktion* som hämtar det öppna projektets
  instruktioner, i stället för att kopiera texten — byter man projekt följer reglerna med, och ett
  stängt projekt ger tom text. En trasig källa får inte stoppa ett AI-anrop.
- Menyväg: Arkiv → Projektinstruktioner (flerradigt fält).
- Mätt i provet, utan nät: instruktionerna finns i systemprompten och ligger sist, de följer med
  hela vägen ut i anropet (med `chat_completion` avbytt), uppgiften finns kvar i användarprompten,
  texten sparas trimmad, och ett tomt fält ger prompten tillbaka orörd.
- **Kvar av fas 2:** 2.16 projektöversikt, samt 2.7 (pauspåminnelser), 2.11 (namngenerator) och
  2.13 (blurb/synopsis) som är markerade låg. Synopsis finns redan per scen.

### Fas 2.16: projektöversikten — och en appvid knappbugg som skärmdumpen avslöjade

- **Status:** complete, grindad (423 rökprov + 54 renhetsprov, GRÖNT).
- **Arkiv → Projektöversikt** (Ctrl+Shift+O) visar var boken står på ett ställe: ord mot mål,
  dagskvot mot deadline, scener, status, utkast, trådar, antal anteckningar i valvet, länkar som
  inte leder någonstans, och projektets AI-instruktioner i kortform. Allt räknas ur projektet och
  valvet som redan finns; `overview_rows(project, vault)` är ren och provas mot oberoende räkningar.
- **Valvet som projektlager** i vyn, inte på disken: hans anteckningar ligger kvar i en samling och
  länkarna mellan dem fungerar som förut. Att dela valvet per bok är ett eget beslut — det rör hans
  egna filer, så det byggs inte utan att han säger till.
- Rutan är så hög som innehållet (292 px, mätt i skärmdump) och knappen är svensk.
- **Bugg hittad och åtgärdad på vägen (appvid):** en svensk dialog visade engelska standardknappar
  ("Close", "Cancel") — Qt:s egna knapptexter kommer ur Qts översättningar, och appen installerade
  aldrig någon `QTranslator`. Nu laddas `qtbase_sv.qm` (systemets, med fallback till Qts egen
  sökväg) vid start och vid språkbyte, och översättaren hålls i fönstret så att den inte dör.
  Mätt: en ny knapprad ger Ok/Stäng/Avbryt på svenska, OK/Close/Cancel på engelska, och tillbaka.
  Samma mätning avslöjade att AI-övningarnas språk läste `i18n.language` som inte finns (föll
  tyst tillbaka på svenska) — rätt attribut är `i18n.current_lang`.

### Fas 3.1 + 3.6: versionshistorik per scen — och två buggar som bara syntes när den användes

- **Status:** complete, grindad (436 rökprov + 54 renhetsprov + snapshots egna 8, GRÖNT).
- `core/snapshots.py` fanns och var grindad, men **oanvänd**: ingen UI, ingen väg in, inga
  automatiska punkter. Nu är den inkopplad via projektet (`.snapshots/` i projektet, precis som
  `SNAPSHOT_DIR` var tänkt) och nås med Arkiv → Versionshistorik (Ctrl+Shift+H): punkterna till
  vänster, unified diff mot texten på disk till höger, och en väg tillbaka.
- En punkt tas automatiskt när en scen öppnas — "så såg den ut när jag lämnade den" — men bara om
  texten skiljer sig från den senaste punkten. En oförändrad scen ger ingen ny punkt (provat).
- En återställning sparar texten som låg där först som en egen punkt, så ingreppet går att ångra
  med samma knapp. Provat: texten är identisk med punkten efteråt, den ligger i editorn (inte bara
  på disk), och antalet punkter ökar med etiketten "före återställning".
- Skärmdumpen gav läsbara rubriker i stället för `snapshot/<uuid>` och full sökväg, och listan
  visar etikett och tid i stället för byte-storlek.
- **Två buggar hittade på vägen, båda i användning (inte i teorin):**
  1. En scenfil har inget radslut på sista raden, och `difflib` klistrade då ihop slutraden med
     motpartens första rad — ändringen såg ut som *en* rad med både minus och plus i sig. Fixat i
     `SnapshotStore.diff`: en saknad radbrytning läggs på innan jämförelsen. Det gällde varje scen.
  2. `QPlainTextEdit` har ingen `ExtraSelection` — den klassen hör till `QTextEdit`. Radtonerna
     kraschade rutan direkt; nu används rätt klass.
- **Medvetet val:** diffen jämför **filerna som de är**, alltså HTML. `<p>`-taggarna syns därför i
  vyn. Att skala bort dem skulle göra vyn snyggare men bryta garantin att det man ser är exakt det
  man återställer. Hellre taggar än en vänlig lögn.

### Fas 3.3: kommentarer med tråd

- **Status:** complete, grindad (449 rökprov + 54 renhetsprov, GRÖNT).
- Först mätt vad som fanns: kommentarerna, markeringarna i texten, hoppa-till-citatet och
  **löst** var redan färdiga i scenpanelen (`ui/scene_inspector.py`). Det som saknades var tråden.
- `core/project.py`: `add_reply()` — tråden hänger på kommentaren, som hänger på sitt citat, så ett
  svar behöver inget eget ankare och följer med när citatet flyttar sig. Nya kommentarer får
  `replies: []`, och `setdefault` ger gamla kommentarer sin tomma lista, så sparade projekt öppnas
  som förut.
- `ui/scene_inspector.py`: en ↳-knapp och svar som indragna rader direkt efter sin kommentar, med
  kommentarens id — ett klick på ett svar går till samma citat. Tråden hänger kvar under en löst
  kommentar, och allt går att öppna igen.
  `ponytail:` platt lista med ↳-rader i stället för ett QTreeWidget; byt till träd om trådarna blir
  långa nog att fällas ihop.
- En API-fälla på vägen: `QListWidgetItem` har ingen `addChild` (det är `QTreeWidgetItem`) — den
  första varianten kraschade direkt. Provet hade fångat det; nu är raden rätt från början.
- Mätt: tom tråd på nya kommentarer, svar hamnar i tråden, svar på okänd kommentar och tomma svar
  avvisas, svar hamnar indraget under rätt kommentar med rätt id, löst/öppna-igen fungerar med
  tråden kvar, och svarsknappen lägger till i samma tråd.

- **Tråden avslöjade en egen regression:** kommentarsrutan hade 96 px som tak, vilket räckte för
  en enda kommentar men klippte tråden. Taket följer nu antalet rader (28 + 22 per rad, kapat vid
  260 px) — sett i skärmdump: 5 rader ger 138 px och inget klipps. Två gamla trångmål i panelen
  (flikraden och etikettraden vid ~390 px) står i listan över det som skall åtgärdas senare.

### Fas 3.2 (del 1 av 2): revisioner som operationer

- **Status:** kärnan byggd, grindad (`revisions: 28 kontroller gröna`, plus 452 rökprov och 54
  renhetsprov). Rutan och menyvägen är kvar.
- `core/revisions.py`: en ändring är en **operation** — typ (added/removed/changed), gammal och ny
  text, ett ankare (slutet av stycket före) och vilket stycke den hör till. Det är formen
  forskningen pekar ut, och den enda som går att besluta om stycke för stycke.
- **Jämförelsen läser text, inte HTML.** Två stycken som ser olika ut i källkoden men läser
  likadant är oförändrade — provat: `<p style="...">` mot `<p>` ger **noll** ändringar. Det är
  hela poängen: Qt skriver om attributen varje gång dokumentet sparas, och en naiv HTML-diff skulle
  kalla det en ändring varenda gång. Forskningen varnar uttryckligen för falska ändringar i en naiv
  HTML-diff.
- **Delningen är en fullständig partition av källtexten**, och varje bit är ett komplett element:
  ett `<ul>` med sina `<li>` är en enhet. Därför kan inget beslut lämna halv HTML — provat med
  `"".join(blocks(...)) == html` och med en lista där ett beslut avvisas.
- Provat: tillägg, borttagning, omskrivning, blandade beslut i rätt ordning (behåll första/avvisa
  andra och tvärtom), två omskrivna stycken blir **två** beslut (inte en klump), okänt beslut
  behåller, och ingen ändring ger ingen ändring.
- **Medvetet:** ett oförändrat stycke behåller filens bytes (jämförelsen är text, filen är källan);
  garantin är att läsningen blir densamma, och det står i docstringen.
- **Kvar i 3.2:** rutan med Behåll/Ångra per stycke och menyvägen (senaste punkten mot texten nu),
  samt textdiff inom ett ändrat stycke.

### Fas 3.2 (del 2 av 2): granskningsrutan

- **Status:** complete, grindad (466 rökprov + 54 renhetsprov + revisionernas 30 egna, GRÖNT).
- `ui/review_dialog.py`: en rad per ändring med tecknet först (`+` tillagt, `−` borttaget,
  `~` omskrivet), **kryssad rad = behåll**, och en förhandsvisning längst ner som räknas om för
  varje kryss — den är exakt den text som skrivs, ur samma funktion som skriver den.
- Menyväg: Arkiv → Granska ändringar sedan senaste punkten (Ctrl+Alt+R). Ändringarna räknas ur
  samma jämförelse som historiken visar (nyaste punkten mot texten på disk nu). Finns inget att
  granska sägs det i statusfältet i stället för att öppna en tom ruta.
- Texten före granskningen sparas som egen punkt, så ingreppet går att ångra med samma knapp som
  allt annat i historiken.
- **Finare parning:** ett stycke som blivit två paras i tur och ordning (det första blir en
  omskrivning, resten egna tillägg) i stället för att slås ihop till en klump — närmare en läsares
  uppfattning, och det syns i provet.
- **En PyQt6-fälla som kostade mest tid i hela passet:** `clicked.connect(self._verkställ)`
  kraschade med signal 11, i kopplingen, innan rutan ens fanns. Minimalt prov: lambda ok, ASCII-namn
  ok, svenskt metodnamn = segfault. Svensk text i strängar och gränssnitt är ofarlig — det är
  *metodnamn* som kopplas till signaler som måste vara ASCII. Regeln är skriven i Qt-skillen, och
  `python -X faulthandler` pekade ut raden på ett försök.
- **Kvar i 3.2:** textdiff *inom* ett ändrat stycke (ett omskrivet stycke visas som en helhet).

- **Radens tecken bär beslutet:** skärmdumpen visade att en okryssad rad kunde se tom ut — kryssrutan
  ritas svagt i den här stilen. Raden inleds nu med ✓ (behålls) eller ↩ (ångras) före ändringstecknet,
  så beslutet syns även om formen inte gör det. Sett i skärmdump: rad 1 `✓ ~`, rad 2 `↩ +`, och
  förhandsvisningen stämmer med raderna.

### Fas 3.4 och 3.5: granska mot vilken punkt som helst, och formateringen för sig

- **Status:** complete, grindade (476 rökprov + 54 renhetsprov + revisionernas 38 egna, GRÖNT).
- **3.4:** historiken har knappen "Granska mot texten nu". Fönstret kör samma väg som för den
  senaste punkten, så originalvalet är det enda som skiljer — forskningens blackline-arbetsflöde:
  originalet förblir orört, och ingenting skrivs förrän granskningen är verkställd. Provat: mot den
  äldsta punkten syns ändringen sedan dess, mot den senaste färre och utan den äldre ändringen.
- **3.5:** `formatting_changes()` räknar de stycken där texten är oförändrad men markupen inte, och
  rutan säger det i en rad i stället för att göra dem till ändringar. Provat: kursiv text ger noll
  textändringar och en formateringsnot.
- **Två falska ändringar hittade i användning** (samma familj som attribut-fällan i 3.2):
  1. Qt lägger sin stilmall i `<style>`, och texten där lästes som ett stycke — en ändrad
     standardstil blev en "ändring" att ta ställning till. `plain()` hoppar nu över dokumentets
     huvud, och stycken utan läsbar text är varken ändringar eller formateringsnoter.
  2. `<body>` räknades som ett block, så **inga** stycken hittades i ett Qt-dokument: hela texten
     blev en enda enhet och styckesgranskningen tappade sin upplösning. Behållare (`html`, `body`)
     räknas inte i djupet längre. Båda har egna prov nu.
- **Känd kant, märkt i koden:** parningen följer `difflib`, så ett omskrivet stycke kan visas som
  borttaget + tillagt när grannstycket också ändrats. En läsare ser det som en omskrivning. Räcker
  för granskning; skärps med en egen kostnad för parningen om det blir störande.

### Fas 3.7 och 3.8: AI-förslaget i marginalen, och ett ångra-steg — fas 3 komplett

- **Status:** complete, grindade (489 rökprov + 54 renhetsprov + revisionernas 42 egna, GRÖNT).
- **3.7:** varje förslagskort i AI-panelen har en 💬-knapp som lägger förslaget som kommentar på sitt
  citat i stället för att skriva över texten. Förslaget hamnar där författaren läser sina egna
  kommentarer, texten står kvar orörd, och `comment_by_quote()` gör att samma förslag två gånger
  blir en kommentar — inte två. Provat hela vägen från kortets knapp.
- **3.8:** `+`-knappen skriver in ett förslag i taget som ett enskilt `insertText` över markeringen
  = ett steg i ångra-historiken. Provat: förslaget in, **ett** ångra ut, och ett förslag vars citat
  inte längre finns skriver ingenting utan säger det i statusfältet.
- **Detaljnivån i granskningen (resten av 3.2):** `word_diff()` visar vilka ord som gick och kom i
  ett omskrivet stycke — i radens verktygstips. Besluten är kvar per stycke: en läsare får
  ordningen, men tar ställning till stycket. Provat: `Nyckeln låg [+kvar+] på bordet.`
- **Fas 3 är därmed komplett:** 3.1 snapshots, 3.2 spårade ändringar, 3.3 kommentarer med tråd,
  3.4/3.5 jämförelse och formatering, 3.6 historik, 3.7/3.8 AI-förslag granskningsbara.

### Fas 4: sök, autokorrigering och fältlagret (4.9, 4.12, 4.1–4.3, 4.5)

- **Status:** delvis klar och grindad (524 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **Det genomgående fyndet:** `core/find_replace.py`, `core/autocorrect.py` och `core/spellcheck.py`
  var **skrivna men oanvända** — ingen meny, ingen ruta, ingen väg in. Samma mönster som
  plot-tavlan i fas 3 och snapshots i 3.1. Först kopplas de, sedan byggs det som saknas.
- **4.12 sök och ersätt** i Redigera-menyn (Ctrl+F, Ctrl+H), icke-modal med räknare (ental rättat:
  "1 träff", inte "1 träffar"), mönster, skiftläge, hela ord och bakåtreferenser. Ersätt alla går i
  ett edit block = **ett** ångra-steg.
- **4.9 autokorrigering** (Ctrl+Shift+K) över scenen: `changed_spans()` ger varje sammanhangande
  ändring ur en teckendiff, så bara det som skiljer skrivs om — fetstilen i resten av stycket står
  kvar (mätt: vikten 700 om ordet). Ett edit block. Rättelserna samlas först och skrivs bakifrån,
  eftersom ett `QTextBlock` blir ogiltigt så snart dokumentet ändras.
- **core/fields.py** — fältlagret för sakprosan: 27 egna kontroller. `[not: …]`, `[figur: …]`,
  `[tabell: …]`, `[ref: Rubrik]`, numrering ur textens ordning, kapitelnummer ur rubriknivåerna och
  `resolve()` för export. Språkoberoende (orden kommer från gränssnittet).
- **4.1/4.5 registret:** ny panelflik *Noter och figurer* med nummer och text; klick sätter markören
  vid markeringen (samma väg som rubriklistan).
- **4.2/4.3:** hänvisningar till rubriker (med en lista att välja ur), och en innehållsförteckning
  mellan `[innehåll]` och `[/innehåll]` som **uppdateras på plats**. En hänvisning som inte hittar
  sin rubrik står kvar orörd — hellre synligt fel än tyst felaktigt.
- **Exporten** löser upp fälten i `_save_document()`, den enda vägen alla sju exporterna går genom:
  en kopia byggs bara när texten innehåller en markering.
- **Kvar i fas 4:** 4.4 (verifiera rubriknavigatorn), 4.6 (roller/stilmallar), 4.7 (avsnittsbrytningar
  — medvetet inte gjord: hör till utskriften), 4.8 och 4.13 (låga), 4.10 (språk per avsnitt och
  LanguageTool), 4.11 (låg), samt de flyttade 4.14–4.16.

### Fas 4 stängd: språk, generatorer, projektets fält och de två låga som flyttades

- **Status:** complete, grindade (556 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **4.10 språk och grammatik:** `core/spellcheck.py` kopplades in (Redigera → Kontrollera språket,
  Ctrl+Shift+G, och panelens Språk-flik). **Ett språk per avsnitt** — `check(text, language)` tar
  språket per anrop, och ett stycke märkt engelskt kontrolleras som engelskt (provat). Träffen
  står med ordet och meddelandet; klick markerar i texten, dubbelklick tar första förslaget som
  **ett** ångra-steg. Adressen står i panelen — texten lämnar datorn — och en tjänst som inte
  svarar säger varför i stället för att visa en tom lista.
- **4.14 pauspåminnelse:** en klocka (50 min, inställningsbar) som säger till i statusfältet och
  blinkar i aktivitetsfältet. Ingen modal ruta. Kommer ihåg sig. *(Flyttad från 2.7.)*
- **4.15 namn och ord:** två nya kategorier i "Fastnat?"-rutan som ber om tolv alternativ i stället
  för tre — antalet står **per kategori**, och tolkningen följer kategorin, inte ett tak i koden.
  Ett valt namn läggs i **codexet** med noten som sammanfattning; en väg vidare hamnar fortfarande i
  scenens anteckning. *(Flyttad från 2.11.)*
- **4.16 blurb och synopsis:** projektets egna fält i projektöversikten, sparade i `project.json`.
  *(Flyttad från 2.13.)*
- **4.4 och 4.6 kontrollerade mot koden, inte mot minnet:** rubriknavigatorn var redan byggd — provet
  visar hela vägen (stilsättning → navigatorn med indrag → klick sätter markören exakt på rubriken
  → och ett vanligt stycke hamnar inte där). Stilarna likaså: rubriknivån och teckenformatet (vikt
  700) mätta. Det som saknades var bevisen.
- **Två riktiga fel hittade i arbetet:**
  1. `namn, _, noten = ...partition("—")` **skuggade i18n-funktionen `_`** i samma metod, och
     `_insert_exercise` kraschade på nästa rad (`UnboundLocalError`). Rökprovet fångade det —
     en tyst bugg i en menyväg ingen annan kontroll rör.
  2. Kategori-tupeln fick ett fjärde fält, och `ui/exercise_dialog.py` packade upp tre — sedan
     kolliderade `rad` (layouten) med `rad` (kategorin). Båda rättade.
- **Medvetet inte gjort:** 4.8 (spalter och avstavning), 4.11 (teckentabell och tesaurus) och 4.13
  (tabeller med formler) — de tre som var markerade låga, och en författare skriver inte formler.
  4.7 (avsnittsbrytningar med egna sidhuvuden) flyttad till **5.5**: den kräver sidvis layout i
  utskriftsvägen, samma sak som 0.2 pekar på, och hör till tryckningen.

### Fas 5 påbörjad: publiceringsprofilen och en isolerad provning

- **Status:** delvis klar och grindad (577 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **`core/publishing.py`** (34 egna kontroller): kanalernas siffror som **data med källa** — KDP:s
  gutter-trappa (9,6 → 22,3 mm i fem steg), ryggbredden per papper (0,0572/0,0635/0,0596 mm per sida),
  omslaget som bleed + baksida + rygg + framsida + bleed, och trim som presets. **Ingen kanal lånar
  en annans koefficient:** forskningen kunde inte belägga en gemensam ryggformel för IngramSpark och
  Lulu, så där står det "använd kanalens mall" i stället för ett påhittat tal. Provat: trappans
  gränser steg för steg, ryggbredden per papper, och att Lulu får `None`.
- **Arkiv → Publicering…** räknar fram siffrorna ur kanal, format, trim, papper, sidantal och blöd,
  visar **källan** de kommer ifrån, varnar för det kanalen skulle klaga på (under 24 sidor, udda
  sidantal, under 79 sidor blir det ingen ryggtext, blöd utanför KDP) och skriver trim, gutter och
  spegelmarginaler in i sidinställningarna. Måtten visas med svenska decimaler (12,7 — inte 12.7).
- **Två riktiga fel hittade på vägen:**
  1. **`_on_page_settings_applied` bytte ut hela inställningen i stället för att slå samman den.**
     En profil som bara känner till några nycklar tappade `clean_print` och de andra valen — den som
     bytte tryckmått hade tyst tappat sin rena export. Nu slås de samman, med det nya värdet vinnande.
  2. **`ui/variants_dialog.py` anropade `item.setEnabled(False)`** — `QListWidgetItem` har ingen
     sådan metod, så raden kastade varje gång en scen tagits bort ur manuset men låg kvar i en variant.
     Latent sedan tidigare; rökprovet nådde den först nu. Rättat med flaggan (`~ItemIsEnabled`).
- **Rökprovningen skrev i Alex riktiga inställningsfil** (`~/.config/omascribe/config.json`):
  `CONFIG_PATH` var hårdkodad, så provet sparade sina egna sidinställningar (6×9, spegelmarginaler)
  i hans app. Åtgärdat i tre steg — `OMASCRIBE_CONFIG_PATH` respekteras nu, provet pekar om till sin
  egen fil, och provet läser sparade val **ur filen** i stället för ur ett objekt i minnet (två prov
  visade sig ha levt på värden ur hans config: skrivmaskinsläget och läsbarhetsmarkeringen, som nu
  prövas genom menyvägen i stället). Hans sidinställningar är återställda till appens standard, med
  säkerhetskopia i `config.json.bak-fore-provsid` — han hade inte satt egna, men det gick inte att
  veta förrän filen var läst.
- **Ny vakt i grinden:** `tools/i18n_shadow_check.py` — i18n-funktionen heter `_`, och den som
  skriver `for _, x in …` i en metod som anropar `_()` får ett heltal i stället för en funktion.
  Felet har dykt upp **tre gånger** i fas 4 och 5 (variants_dialog, _insert_exercise, publish_dialog).
  Vakten är falsifierad: den larmar på det buggiga fallet och tiger om det ofarliga.

### Fas 5: EPUB-exporten in i menyn, och bokens metadata

- **Status:** delvis klar och grindad (590 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **Samma mönster igen:** `core/epub.py` har exporterat EPUB 3 sedan 0b — kapitel vid rubrikerna,
  navigation document, bilder med alt-text, tillgänglighetsmetadata — men `export_epub` nåddes
  **inte från exportmenyn**. Ingen meny, ingen filväg, ingen väg in. Nu: Arkiv → Exportera EPUB….
- **Bokens metadata (5.4):** författare, förlag och ISBN blev projektfält i projektöversikten, och
  `book_metadata()` för dem till EPUB:en: `dc:creator`, `dc:publisher`, `dc:identifier` och
  **baksidestexten som `dc:description`** — den text en läsare läser först. Titeln kommer ur projektet,
  inte ur filnamnet.
- **Provat ända in i filen:** EPUB:en packas upp med `zipfile`, OPF:en läses, och titel, författare,
  språk, ISBN, tillgänglighetsmärkning, nav och de två kapitelfilerna kontrolleras. 2 386 byte, två
  kapitel, `accessMode`/`accessibilityFeature`/`accessibilityHazard` på plats (5.8:s MUST-krav).
- **Kvar i fas 5:** utskriftsvägen ska verkställa spegelmarginalerna och kapitelstarten (5.5), rita
  omslagsarket (5.6), front matter som sidor (5.4), DOCX med namngivna Word-stilar (5.7), EPUBCheck
  som val (5.8), exportpaket med checksummor och preflight (5.9), svensk/engelsk sättning (5.10) och
  samma roller till EPUB-CSS/PDF/DOCX (5.3).

### Fas 5: spegelvändningen verkställs i utskriften (5.5, och 0.2)

- **Status:** grindad (596 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **Problemet:** `page_settings_for` ger en tryckprofil *asymmetriska* marginaler — ytterkant till
  vänster, gutter till höger — men utskriftsvägen satte dem rakt av på **varje** sida. I en färdig bok
  hamnar då innermarginalen på utsidan varannan sida. Det är felet 0.2 pekade på och som forskningen
  varnar för.
- **Lösningen:** regeln ligger som en ren funktion, `publishing.mirrored_margins()`, och utskriften
  använder den. Är spegling på sätts **samma marginal på båda sidor, lika med den inre**: rätt i tryck
  (innermarginalen blir aldrig för liten), priset en något generös ytterkant. Utan spegling står
  marginalerna som de är.
- **Kanten är märkt i koden** (`ponytail:`): den riktiga växlingen mellan udda och jämn sida kräver en
  paginerad målare, inte en konstant margin-box. Den byggs när någon faktiskt ska trycka; tills dess är
  den symmetriska marginalen aldrig *fel*, bara frikostig. **Ett medvetet val, inte en glömd rad.**
- **Provat på skrivarens egen sidlayout:** speglad profil → (12,7; 12,7; 15,0), ospeglad → (6,4; 12,7;
  15,0), toppmarginalen orörd i båda fallen, och en PDF skriven (8 745 byte). Kontrollen är således
  falsifierbar i båda riktningarna.
- **Tredje gången samma familj av fel:** en **funktionslokal bindning skuggar namnet för hela
  funktionen.** I rökprovets `main()` gjorde en sen `from core.doc_manager import DocumentManager` att
  exportkontrollerna *tidigare* i samma funktion fick `UnboundLocalError` — samma sak som `_`-skuggan
  i fas 4 och 5. Rättat med ett eget namn i avsnittet.

### Fas 5: bokens första sidor genereras (5.4)

- **Status:** grindad (602 rökprov + 54 renhetsprov + modulernas egna, GRÖNT).
- **Vad som blev gjort:** EPUB:en får nu **titelsida och kolofon** som genererade XHTML-sidor ur
  bokens egna uppgifter — titel, författare, förlag, ISBN, året och en rättighetsrad. Poängen är att
  bokens första sidor inte är text man skriver utan uppgifter man *har*: skrivna för hand ska de
  hållas i minne och uppdateras manuellt när förlaget eller ISBN:t ändras.
- **Läsordningen är rätt:** de står först i ryggraden (4 poster: två framsidor + två kapitel) och
  listar sig **inte** i innehållsförteckningen — en titelsida listar sig inte själv.
- **Provat i filen:** två frontmateria-filer, titel och författare på titelsidan, ISBN, förlag och år
  i kolofonen, och nav.xhtml utan `front-`.
- **Kvar:** samma sidor i utskriften (där skriver författaren dem i dag, och det är rimligt — en
  utskrift kommer från ett dokument, en EPUB från ett projekt), samt dedikation och tack som fält.

### Fas 5: släppet — paketet med checksummor och förhandskontroll (5.9, 5.11)

- **Vad som blev gjort:** **Arkiv → Släpp boken…** samlar EPUB:en, tryck-PDF:en och en rapport i en
  mapp. PDF:en ritas ur samma sidinställningar som utskriften, så tryckprofilens trim, gutter och
  spegling följer med ända in i filen.
- **Rapporten är medvetet tråkig:** `RAPPORT.md` (läsbar text, den ska gå att skicka till ett
  tryckeri) och `release.json` (för program). Titel, författare, förlag, ISBN, byggtid, varje fils
  storlek och **SHA-256**. Utan summorna går frågan "är det här samma fil som jag skickade i går?"
  inte att svara på — och den frågan kommer alltid, först när något gått fel.
- **Förhandskontrollen** säger vad kanalen skulle klaga på innan filen skickas: kanalens egna
  varningskoder översatta (`warn_*`, samma nycklar som publiceringsrutan), tom baksidestext, saknat
  ISBN, udda sidantal, ingen vald tryckprofil. En fil som inte kunde skrivas **namnges i rapporten**
  i stället för att tyst försvinna — en saknad fil är exakt vad rapporten är till för.
- **En väg till sidantalet:** `_page_count()` — publiceringsrutan och släppet läser samma källa
  (`editor.canvas.pages`), i stället för två kopior som kan glida ifrån varandra.
- **Provat:** fyra filer i mappen, EPUB 2 386 byte, PDF 9 109 byte, checksumman omräknad i provet och
  jämförd, rapporten bär titeln **ur projektet** (inte ur filnamnet), och menyposten finns.
- **Kvar:** uppladdningen till distributören (KDP:s API — kräver kontouppgifter, eget beslut) och
  "öppna exportmappen" (`xdg-open`, en rad, låg prioritet).

### Fas 5: rollerna når alla tre kanaler (5.3, 5.7)

- **Vad som blev gjort:** rollerna (citat, kod) ur `core/richtext.py` — som editorn sätter och Markdown
  redan följde — når nu **Word** (namngivna stilar) och **EPUB-CSS:en** (citatet ser ut som ett citat).
  Utskriften får rollernas formatering genom dokumentet: rollen sätter både semantik *och* utseende när
  den läggs på, så papperet visar samma sak som skärmen.
- **Word:** citat → `Quote` (finns i Words standardmall), kod → `Code Block`, och stilen **skapas i
  filen** när mallen inte har den. Det är hela poängen med 5.7: en redaktör ska kunna restyla bokens
  kodblock i ett svep i stället för att jaga direkt formatering. Stilnamnen är språkoberoende i filen.
- **EPUB:** `blockquote` och `pre` stajlas i `book.css` i stället för att ärva allt från läsarens app.
- **Mätningarna tog tre varv, och två av dem var mina egna fel:**
  1. `HTML Preformatted` finns **inte** i python-docx standardmall — antagandet föll direkt, och
     lösningen blev att *skapa* stilen. (Hade jag inte läst tillbaka filen hade det sett ut att funka.)
  2. `apply_role` med en markör *mitt* i ett block vidgar rollen till hela det sammanhängande stycket —
     rätt i editorn (där man markerar det man menar) men fel i ett prov, som i stället markerar blocket
     och använder samma väg som användaren.
- **En tredje gång samma familj:** `export_epub46` fanns inte — avsnitt 43 importerar sin EPUB-export
  *inuti* `main()`, så namnet var inte synligt i avsnitt 46. Funktionslokal bindning, igen.
