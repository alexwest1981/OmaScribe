# Task Plan: OmaScribe → professionellt författarverktyg

## Goal

Allt som ett professionellt författarverktyg har skall in i OmaScribe — manusstruktur,
författarlagret, revision, sakprosa, publicering och AI — utan att något glöms mellan sessionerna.

Underlaget är `docs/research/author-tools/` (fem agentrapporter, 119 källor, alla
kodpåståenden verifierade mot fil och rad). Varje punkt nedan bär sin källa som
`R<xx>.<n>` = rapportens avsnittsnummer, så inget är påhittat här.

**Nuläge mätt:** 13 726 rader i `core/` + `ui/` + `main.py`, 38 moduler. Ett dokument i
taget (`ui/main_window.py:663`). Se `findings.md`.

## Next Step

Fas 1.7: sammanhängande läsvy — flera scener som ett manus i editorn, med
skiljelinjer och redigerbart innehåll. Därefter summerade ordmål i trädet (1.8).

## Current Phase

Fas 1 — Manusstruktur (fas 0 complete, 1.1–1.6 klara)

## Arbetsregler

- En agent = en git-worktree = ett område. Nya moduler framför ändringar i
  `ui/main_window.py` och `core/doc_manager.py`, som båda är flankerade.
- Grinden `tools/test_all.sh` skall vara grön före varje harvest, och är densamma i
  worktreen som i live-kassan.
- Ingen agent får `git push`, `git commit`, `systemctl` eller röra `~/Projects/OmaScribe`
  direkt. Diffen hämtas in för hand och granskas per fil.
- Punktlista: `[ ]` = inte gjord, `[~]` = pågår, `[x]` = klar och verifierad.

## Phases

### Fas 0: Fundament — buggar, grind, projektmodell

- [x] **0.1 Bugg:** DOCX-exporten skickade inte `page_settings` (`ui/main_window.py:807`) medan PDF-exporten gjorde det. Fixat med `_save_document()` som alla sju exportvägar går genom, och `ui_smoke` har nu ett prov som faller om det går sönder igen (falsifierat: felet återinfört → rött).
- [~] **0.2** `print_document_to_printer` sätter fyra fasta marginaler (`core/doc_manager.py:230-235`) och speglar dem aldrig efter jämn/udda sida. **Detta är ingen bugg utan en saknad funktion** — hör till 5.5, inte hit. Kräver sidvis layout (sidindex → inner/ytter), inte ett par rader.
- [x] **0.3 Bugg:** `_toggle_focus_mode` låg i två kopior (`ui/main_window.py:392` och `:544`) där den sista tyst tog över, så sidopanelen slutade gömmas. Slagna ihop till en.
- [x] **0.4 Grind:** `tools/test_all.sh` — importkontroll av alla 39 moduler, `core.project`, `core.epub`, `core.snapshots`, `core.spellcheck`, `tools/ui_smoke.py` (41 kontroller), `tools/print_purity_check.py` (54 kontroller). Grön.
- [x] **0.5 Projektmodellen `core/project.py`:** projekt = mapp med `project.json` + en HTML-fil per scen + `research/`. Noder (del/kapitel/scen), flytt, omordning, synopsis/status/etiketter/POV/mål, ordräkning per scen och totalt, deadline → dagkvot, `validate()` som rapporterar trasiga träd i stället för att kasta, atomär skrivning. 27 kontroller gröna. **Nyckeln: allt annat hänger på denna.** R01.1, R01.2, R04.2
- [x] **0.6 Projektvy `ui/binder_panel.py`:** `QTreeView` mot projektmodellen, skapa/döpa/flytta/ta bort noder, val avgör aktiv scen. Kopplad i `ui/main_window.py` (Arkiv → Nytt/Öppna/Stäng projekt), Spara och autosparning skriver scenen + manifestet, titeln visar bok och scen. `ui_smoke` avsnitt 9 kör hela vägen och läser filerna från disk. R01.1
- **Status:** complete

### Fas 0b: Moduler byggda parallellt (klara, ännu inte kopplade i gränssnittet)

- [~] **0b.1 `core/epub.py`** — EPUB 3 med nav, TOC per kapitel, bilder med alt-text, tillgänglighetsmetadata, atomär skrivning. 10 egna kontroller + 13 i mitt oberoende prov (XML-välformighet med `&` i titel och text, manifest/spine-konsistens). R05.2
- [~] **0b.2 `core/snapshots.py`** — ögonblicksbilder per fil: skapa, lista, läs, återställ, diff, prune; index som återskapas ur innehållet om det är trasigt. 8 egna kontroller + 7 i mitt prov (restore ger exakt samma byte). R01.6, R02.4
- [~] **0b.3 `core/spellcheck.py`** — LanguageTool-klient med styckedelning och UTF-16-korrekta offset. Verifierad mot riktiga tjänsten: felet `teskt` i en text med emoji före fick offset 14:19 — rätt ord. Degraderar ärligt (nätfel → `available()=False`, tom lista). R02.13
- [~] **0b.4 `core/writing_log.py`** — skrivlogg i SQLite: added/removed separat, sessionsrader, historik med nollor utfyllda, sviter med vilodagar, netto per skrivdag, CSV. 9 egna + 10 i mitt prov (månadsskifte, hål i sviten, session över midnatt). R03.3–R03.5
- [~] **0b.5 `core/storybible.py`** — codex: entiteter med alias/fält, relationer, koppling till scen-id, `mentions()` som hittar namn i en text. 11 egna + 13 i mitt prov. **Mitt prov hittade att LIKE-jokertecken escapas** (`%` som sökord gav inga träffar i stället för allt). R04.1, R04.13
- [~] **0b.6 `core/find_replace.py`** — regex-sök och ersättning över ett `QTextDocument`, bakåtreferenser, ett ångra-steg per `replace_all`. 10 egna + 12 i mitt prov (50 ersättningar utan att offsetarna glider). R02.16
- [~] **0b.7 `core/autocorrect.py`** — autokorrigering och autotext: hela ord, skiftläge bevaras, webbadresser och sökvägar rörs inte, regler mot sitt eget svar avvisas, trasig regelfil degraderar. 14 egna + 14 i mitt prov. R02.12
- **Status:** modulerna är klara och grindade, men ingen av dem nås ännu från gränssnittet. Nästa steg är att koppla dem, ett i taget, med ett prov per inkoppling.



### Fas 1: Manusstruktur

- [x] **1.1** Binder: projektträd för delar → kapitel → scener. R01.1
- [x] **1.2** En scen per textdokument, laddas i editorn vid val i trädet. R01.2
- [x] **1.3** Korktavla och indexkort (`QListView` IconMode, titel + status + synopsis). R01.3
- [x] **1.4** Synopsis och sammanfattning per scen, i inspector och på kortet. R01.4
- [~] **1.5** Status och etiketter per scen, redigerbara värdelistor, färg + text. R01.5 — *text klar, färg kvar (statusar är fria strängar i projektet, färgen hör ihop med kortdelegaten)*
- [x] **1.6** Dra-och-släpp och omordning i träd och kortvy, atomiskt. R01.11
- [ ] **1.7** Sammanhängande läsvy (Scrivenings): flera scener som ett manus. R01.9
- [~] **1.8** Ordräkningsmål per scen, kapitel och projekt, summerat i hierarkin. R01.10 — *mål och framsteg per scen klart, summeringen i trädet kvar*
- [ ] **1.9** Samlingar: manuella grupper och sparade sökningar, utan att ändra binderordningen. R01.8
- [ ] **1.10** Researchmapp: källor, länkar och bilder skilda från manuset, uteslutna ur export. R01.7
- [ ] **1.11** Anteckningar och kommentarer per scen (knyter ihop med valvet). R01.12
- [ ] **1.12** Projektmallar: Roman, Fackbok, novell — binderstruktur + statusvärden, separat från dokumentmallarna. R01.13, R03.8
- [ ] **1.13** Scener och scenkopplingar: scen som enhet med sammanfattning, POV och kopplade entiteter. R04.2
- [ ] **1.14** Manusvarianter och alternativa strukturer. R01.14 — *låg*
- **Status:** pending

### Fas 2: Författarlagret

- [ ] **2.1** Mål för session och projekt, med progress i statusfältet. R03.1, R03.14
- [ ] **2.2** Deadline och dagskvot: valda skrivdagar → `ceil((mål − nu) / dagar)`. R03.2
- [ ] **2.3** Historik, diagram och streaks över faktiska ord per dag. R03.3
- [ ] **2.4** Sessionshistorik och skrivlogg, sessionsrader i SQLite, CSV-export. R03.4
- [ ] **2.5** Skrivsprintar och timer (`QTimer`, diskret notis, paus). R03.5
- [ ] **2.6** Skrivmaskinsläge utöver befintligt helskärmsläge: centrerad markör, maxbredd. R03.6
- [ ] **2.7** Pauspåminnelser och ergonomi, valbart. R03.7 — *låg*
- [ ] **2.8** Karaktärsblad och story bible i projektet. R03.9
- [ ] **2.9** Tidslinje, plot-tavla och scenöversikt (Plot Grid-modellen). R03.10
- [ ] **2.10** Taggar, samlingar och anteckningar knutna till scen. R03.11
- [ ] **2.11** Namn- och ordförrådsgenerator. R03.12 — *låg*
- [ ] **2.12** Revisionsläge och mål per utkast (utkast 1/2/3). R03.13
- [ ] **2.13** Blurb och synopsis som projektfält. R03.15 — *låg*
- [ ] **2.14** Övningar mot skrivblock ("vad händer nu?"). R03.16
- [ ] **2.15** Läsbarhetsanalys och stilråd i texten (LIX finns, markeringar saknas). R03.17
- [ ] **2.16** Projektöversikt och anteckningar (valvet som projektlager, taggar/properties). R03.18
- [ ] **2.17** Projektinstruktioner: per-projekt kontext för AI:n. R04.18
- **Status:** pending

### Fas 3: Revision och granskning

- [ ] **3.1** Snapshots per scen: oföränderlig kopia + tidsstämpel + etikett, jämför och återställ. R01.6, R02.4
- [ ] **3.2** Spårade ändringar: revisioner som operationer (ankare, gammal/ny text, typ, författare, tid), acceptera/avvisa enskilt. R02.1
- [ ] **3.3** Kommentarer i marginalen med tråd och "löst". R02.2
- [ ] **3.4** Jämför dokument och slå ihop versioner. R02.3
- [ ] **3.5** Jämförelse av formatering, separat från textdiff. R02.15
- [ ] **3.6** Versionshistorik och återställning i ett samlat flöde. R02.4
- [ ] **3.7** AI-kommentarer i marginalen i stället för överskrivning. R04.14
- [ ] **3.8** Acceptans per stycke för AI-förslag, som egna undo-steg. R04.15
- **Status:** pending

### Fas 4: Sakprosan

- [ ] **4.1** Fotnoter och slutnoter med automatisk numrering och navigering. R02.5
- [ ] **4.2** Korsreferenser till rubriker, figurer och tabeller (fält, inte rå text). R02.6
- [ ] **4.3** Genererad innehållsförteckning i dokumentet, uppdaterbar och klickbar. R02.7
- [ ] **4.4** Snabbnavigering och rubriknavigator (utöka befintlig outline-panel). R02.17
- [ ] **4.5** Bildtexter med automatisk numrering + figur-/tabellregister. R02.8
- [ ] **4.6** Stycke- och teckenstilar, stilinspektör och stilmallar. R02.9
- [ ] **4.7** Avsnittsbrytningar med separata sidhuvuden/sidfötter. R02.10
- [ ] **4.8** Spalter och avstavning. R02.11 — *låg*
- [ ] **4.9** Autokorrigering och autotext. R02.12
- [ ] **4.10** Språk per textavsnitt, stavning/grammatik (LanguageTool) och egen ordlista. R02.13
- [ ] **4.11** Tecken-/symboltabell och tesaurus. R02.14 — *låg*
- [ ] **4.12** Sök och ersätt med reguljära uttryck. R02.16
- [ ] **4.13** Tabeller med formler och ekvationer. R02.18 — *låg*
- **Status:** pending

### Fas 5: Publiceringen

- [ ] **5.1** Publiceringsprojekt och formatprofiler (KDP, IngramSpark, Lulu, Apple, Kobo). R05.1
- [ ] **5.2** EPUB 3 med semantisk kapitelstruktur och TOC. R05.2
- [ ] **5.3** Namngiven typografi och bokstilar, samma roller till EPUB-CSS, PDF och DOCX. R05.3
- [ ] **5.4** Metadata, ISBN och front matter (halvtitel, titelsida, kolofon, dedikation, tack). R05.4
- [ ] **5.5** Trycklayout: trim, spegelmarginaler, gutter, kapitelstart på rätt sida. R05.5 (+ 0.2)
- [ ] **5.6** Blödning, omslags-PDF och ryggbredd enligt kanalens formel. R05.6
- [ ] **5.7** DOCX med redaktörsvänliga Word-stilar (namngivna stilar). R05.7
- [ ] **5.8** EPUB-validering (EPUBCheck) och tillgänglighetsmetadata. R05.8
- [ ] **5.9** Distributörsuppladdning och slutkontroll: exportpaket, checksummor, preflight-rapport. R05.10
- [ ] **5.10** Svensk och engelsk boksättning: repliktankstreck, citattecken, avstavning. R05.11
- [ ] **5.11** Efterbearbetning i Sigil/Calibre: "öppna exportmapp", checksumma. R05.9 — *låg*
- [ ] **5.12** Siffertabellen ur R05 (KDP-marginaler, blöd, ryggkoefficienter) in som data med källa, ej hårdkodad i logik.
- **Status:** pending

### Fas 6: AI som författarverktyg

- [ ] **6.1** Story bible / Codex: entiteter, typer, attribut, alias, relationer i SQLite. R04.1
- [ ] **6.2** Kontinuitet och aktiverat berättelseminne: scenkopplade poster + visad AI-kontext. R04.13
- [ ] **6.3** Manusfrågor och RAG: chunka per scen/stycke, svara med källhänvisning. R04.3
- [ ] **6.4** Chatta med helt manus eller valt kapitel, med kontextchip och historik. R04.4
- [ ] **6.5** Recap per scen och kapitel, redigerbar, aldrig automatisk kanon. R04.5
- [ ] **6.6** Kapitelplan, disposition och synopsis genererad som strukturerad data. R04.6
- [ ] **6.7** Brainstorm: konflikt, twist, karaktärsbåge, med "får inte ändras". R04.7
- [ ] **6.8** Skrivhjälp på markerad text (beskriv, skriv om, utöka, korta) — utöka befintlig Ctrl+K. R04.8
- [ ] **6.9** Prosakritik och redaktörspass med ankare, motivering och förslag. R04.9
- [ ] **6.10** Röstbevarande och stilprofil, ärligt formulerad som stöd. R04.10
- [ ] **6.11** Promptbibliotek och återanvändbara instruktioner. R04.11
- [ ] **6.12** Modellval och kostnad per uppgift. R04.12
- [ ] **6.13** Flerboks-seriebibel och återanvändning. R04.16 — *låg till medel*
- [ ] **6.14** Genre, åldersgräns, röst och innehållsgränser som projektprofil. R04.17
- [ ] **6.15** Diktering in i rätt scen/anteckning (befintlig Whisper kopplas till projektmodellen). R04.19
- **Status:** pending

## Bordet — kategorins minimikrav (acceptanskriterier)

Varje rapport listar vad som krävs för att verktyget skall kallas professionellt. Detta är
kontrollistan när faserna är klara.

- [ ] Manusobjekt ordnas hierarkiskt, flyttbara utan klipp-och-klistra. R01
- [ ] Varje scen är ett självständigt redigerbart dokument med metadata. R01
- [ ] Växla mellan detalj och helhet: träd, kort, sammanhängande läsvy. R01
- [ ] Mål och arbetsläge följer dokumenten (ordmål, status, etiketter). R01
- [ ] Research och versioner överlever manusredigering, separerade från texten. R01
- [ ] Redaktionell kontroll: ändringar och acceptera/avvisa enskilt, kommentarer med tråd. R02
- [ ] Struktur för långa dokument: rubrikstilar, navigator, uppdaterbar TOC, noter, korsreferenser. R02
- [ ] Pålitlig redigering över tid: versionshistorik och dokumentjämförelse. R02
- [ ] Manusberedskap: automatiska bildtexter, register, konsekvent typografi, sidlayout per avsnitt. R02
- [ ] Språkverktyg: språk per stycke, stavning, egen ordlista, mönstersök. R02
- [ ] Mål per session och projekt med synlig status. R03
- [ ] Måldatum → dagskvot med valda skrivdagar. R03
- [ ] Fokus-/helskärmsläge och centrerad markör. R03
- [ ] Romanmall som inte kräver planering före skrivandet. R03
- [ ] Historik över faktiska ord per dag, inte bara totalsumma. R03
- [ ] Manus, instruktioner och referensmaterial hålls ihop för AI:n. R04
- [ ] Strukturerade berättelseposter och scener som grundmönster. R04
- [ ] Skrivhjälp täcker idéarbete, generering och revision. R04
- [ ] Användaren väljer kontext och modell. R04
- [ ] Historik och acceptans som skyddsräcken mot överskrivning. R04
- [ ] En och samma bok exporteras till EPUB, print-PDF och DOCX. R05
- [ ] EPUB har giltigt paket, metadata och navigation. R05
- [ ] Tryckexport: enkelsidiga sidor, inbäddade typsnitt, 300 DPI, trim, sidordning, marginalregler. R05
- [ ] Omslag som sammanhängande PDF med baksida, rygg och framsida. R05
- [ ] Tillgänglighetsmetadata kan anges (accessMode, accessibilityFeature, accessibilityHazard). R05
- [ ] Kanalprofiler, eftersom mått, blöd och metadataregler skiljer sig. R05

## Designkrav (fallgropar som styr bygget)

- [ ] Visa källpassager; låt aldrig AI-genererade fakta bli kanon automatiskt. R04
- [ ] Stilprofilen är stöd och jämförelseunderlag — inte ett löfte om "skriver som du". R04
- [ ] Inga AI-ändringar som ersätter text direkt: linjemarkering, diff, undo, versionshistorik. R04
- [ ] Stilprofilen byggs av användarens egna texter, aldrig av en levande författares verk. R04
- [ ] Visa vilka textdelar som faktiskt skickas med varje AI-anrop. R04
- [ ] "Giltig EPUB" betyder inte "tillgänglig EPUB" — två separata kontroller. R05

## Avfört

- **Inworld/Storyteller som författarprodukt** (R04.19): rapporten kunde inte belägga att det
  är ett manusverktyg — det är tal- och modell-API:er. Det användbara i punkten (röst → text i
  rätt sammanhang) ligger i 6.15.

## Key Questions

1. Hur mycket av `ui/main_window.py` (1216 rader) skall projektmodellen ta över? Besvaras i fas 0.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Projektmodellen först, allt annat efter | Mål, status, snapshots, story bible och kompilering hänger alla på att scenen är ett eget objekt (R01) |
| Nya moduler framför ändringar i `main_window.py` / `doc_manager.py` | Två flankerade filer; fem agenter som redigerar samma fil ger en oläsbar harvest |
| En worktree per agent, diffen hämtas in för hand | Mätt: agenters egen självrapport är inte verifiering, och worktreen är isolerad från live-kassan |
| `core/project.py` utan Qt | Självprovet skall kunna köras utan skärm, och modellen skall kunna läsas av kommandoradsverktyg senare |
| Nya moduler får engelska kommentarer | Alex regel 23/9 är kod på engelska; äldre moduler lämnas i fred (ingen storskalig omskrivning) |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| `numpy._core._multiarray_umath` saknas | 1 | Hermes-skalet läcker `PYTHONPATH` mot sin egen python 3.14, som skuggade projektets 3.12-paket. `unset PYTHONPATH` (och i grinden) löste det. Ominstallation av numpy gjorde ingen skillnad. |
| `python -m core.project` dör i `validate()` | 1 | Cirkelkontrollen anropade `by_id()` på en okänd förälder och kastade i stället för att rapportera. Vandringen bryter nu på okänd förälder. |
| `move_node` dubblerar noden | 1 | `children()` räknade redan in noden med sin gamla ordning, och den sattes in en gång till. Filtreras bort före insättning. Hittades av självprovet. |
| EPUB: kapitlens `lang` hårdkodad till engelska | 1 | Hittades av mitt oberoende prov, inte av agentens. Språket följer nu metadata; en kontroll i modulens självprov hindrar återfall. |

## Notes

- Uppdatera fasstatus när arbetet fortskrider: `pending` → `in_progress` → `complete`.
- Läs om Goal och Next Step före varje större beslut.
- Logga fel direkt så att en misslyckad väg inte upprepas.
