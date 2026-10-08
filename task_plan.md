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

Fas 5: utskriften. Sidhuvuden och sidfötter med jämn/udda sida (0.2 och 4.7 hör hit),
sidnumrering, marginaler per sida, formatmall för tryck och en förhandsvisning som
visar arket som det blir. Innan dess är fas 4 stängd: 4.8 (spalter och avstavning),
4.11 (teckentabell och tesaurus) och 4.13 (tabeller med formler) är de tre låga och
lämnades medvetet — de står kvar som val, inte som glömda.
(tidslinje och plot-tavla) som är nästa större punkt. Rutnätet i 2.9 bygger på
scenmodellen och på att scenens status redan finns.

## Current Phase

Fas 2 — Författarlagret (2.1–2.6 och 2.8–2.10 klara: skrivloggen, kvot, historik,
sprintar, skrivmaskinsläget, story biblen, plot-tavlan, samlingen som läsvy,
revisionsläget (2.12), övningarna (2.14), läsbarhetsmarkeringen (2.15),
projektinstruktionerna (2.17) och projektöversikten (2.16)).
Fas 0, 0b och 1 är klara. Sedan dess: appskalet följer v0-referensen, och
pappret delas i riktiga A4-ark (radbunden paginering, `core/pagination.py`).

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
- [x] **1.5** Status och etiketter per scen, redigerbara värdelistor, färg + text. R01.5
- [x] **1.6** Dra-och-släpp och omordning i träd och kortvy, atomiskt. R01.11
- [x] **1.7** Sammanhängande läsvy (Scrivenings): flera scener som ett manus. R01.9
- [x] **1.8** Ordräkningsmål per scen, kapitel och projekt, summerat i hierarkin. R01.10
- [x] **1.9** Samlingar: manuella grupper och sparade sökningar, utan att ändra binderordningen. R01.8
- [x] **1.10** Researchmapp: källor, länkar och bilder skilda från manuset, uteslutna ur export. R01.7
- [x] **1.11** Anteckningar och kommentarer per scen (knyter ihop med valvet). R01.12
- [x] **1.12** Projektmallar: Roman, Fackbok, novell — binderstruktur + statusvärden, separat från dokumentmallarna. R01.13, R03.8
- [x] **1.13** Scener och scenkopplingar: scen som enhet med sammanfattning, POV och kopplade entiteter. R04.2
- [x] **1.14** Manusvarianter och alternativa strukturer. R01.14 — *bara ordningen förgernas (namngiven ordning + lägg på manuset); innehållsligt grenade utkast väntar på snapshots per scen (3.1), som rapporten själv rekommenderar först*
- **Status:** klar — alla punkter 1.1–1.14 avslutade

### Fas 2: Författarlagret

- [x] **2.1** Mål för session och projekt, med progress i statusfältet. `ui/writing_log_panel.py` äger loggen, får ordantalet efter varje ändring (`track()` räknar skillnaden mot förra mätningen — ett ändrat ord är inte ett skrivet ord) och visar dagens netto i panelen och i statusfältet. Projektets mål och andel kommer ur `project.progress()`. R03.1, R03.14
- [x] **2.2** Deadline och dagskvot: `project.daily_quota()` räknas redan i projektmodellen; panelen visar kvoten, hur många ord som är kvar och en stapel, och etiketten bär deadline i sin verktygstext. Utan projekt visas i stället andelen av manusets mål. R03.2
- [x] **2.3** Historik, diagram och svit över faktiska ord per dag: 14 dagar som stapeldiagram (`DayChart`, ritad i widgeten, inga nya beroenden), svit och längsta svit, snitt per skrivdag. R03.3
- [x] **2.4** Sessionshistorik och skrivlogg i SQLite via `core.writing_log` (som redan fanns och nu äntligen nås): dagens rader med added/removed separat, sessioner som startar vid första ändringen och stängs vid flush/stängning, CSV-export genom en filväljare. Loggen ligger i projektmappen när ett projekt är öppet — bokens dagar hör till boken. R03.4
- [x] **2.5** Skrivsprintar och timer: 15/25/45/60 minuter, nedräkning i panelen, avbryt, och vid slut en rad i statusfältet plus `QApplication.alert` (diskret — ingen modal). Antalet ord under sprinten räknas och rapporteras. R03.5
- [x] **2.6** Skrivmaskinsläge utöver befintligt helskärmsläge: `PagedPaper.center_cursor()` håller markörens rad mitt i fönstret medan man skriver, kopplat till markörens rörelse i `ui/editor_view.py`. Läget slås på i Visa-menyn och kommer ihåg sig i configen. Maxbredden var redan satt — arket är A4 (750 px) och texten kan inte bli bredare. Nära dokumentets slut kan ingen centrering ske (det finns ingen text att skrolla förbi), precis som i Word. R03.6
- [x] **2.8** Karaktärsblad och story bible i projektet: `ui/codex_panel.py` visar projektets codex (codex.sqlite i projektmappen) med sökning och typfilter, och ett blad per entitet — namn, alias, vem det är (sparas med kort fördröjning medan man skriver), relationer till andra i boken, scenerna den är kopplad till (klick öppnar scenen) och hur ofta namnet nämns i manuset. Ny/redigera/ta bort, koppla loss scen, lägg till och ta bort relation. `core.storybible` fick `remove_relation`; dialogrutan förifylls vid redigering. R03.9
- [x] **2.9** Tidslinje, plot-tavla och scenöversikt: `ui/plot_grid.py` visar manuset som en tabell — en rad per scen med del/kapitel, tråd (etiketter), POV, status, när i berättelsen den händer, ord och ordmål. Redigerbar direkt i tabellen (status genom en meny med projektets egna statusar), ett klick på titeln öppnar scenen, och sorteringen är poängen: manusordning, **tidslinje** (scenens egen tid, tom tid sist), POV eller status — Dabbles huvudtråd och sidotrådar sida vid sida, utan att lämna projektet. Modellen fick fältet `when` (sparas i manifestet). Tavlan är en egen sida i stacken och inte en flik i sidopanelen: åtta kolumner är ~790 px och panelen är 370. *Medvetet inte gjort:* en grafisk tidslinje (band med markörer) — texten i `when` sorterad i tid är tidslinjen en ensam författare läser, och en ritad tidslinje är en egen vy den dag någon saknar den. R03.10
- [x] **2.10** Taggar, samlingar och anteckningar knutna till scen. Mestadels färdigt sedan tidigare —fas 1.5 (statusfärg), 1.9 (samlingar), 1.11 (scenanteckning) och 2.9 (tråd/etiketter i tavlan) hade redan byggt bitarna. Det som saknades var sista steget i arbetsflödet: samlingen gick att filtrera fram men inte att *arbeta igenom*. Nu har samlingspanelen en läs-knapp som öppnar samlingens scener i läsvyn (`▶`, "Läs samlingen som en text") — och `_show_scrivenings` är utbruten så att hela manuset och en samling går samma väg. R03.11
- [x] **2.12** Revisionsläge och mål per utkast: plot-tavlan har en **Utkast**-kolumn (1–9, samma gränser som sceninspektören, redigerbar direkt i tabellen och skriven till manifestet) och ett **utkastfilter** — välj utkast 2 och tabellen visar bara de scener som nått dit, med räkningen "1 av 3 scener i utkast 2". Det är revisionsläget: arbetet blir en lista i stället för ett helt manus. *Målet per utkast* blev räkningen i stället för ett talfält per utkast — målet för ett utkast är att scenerna har nått det, och nio målfält som ingen fyller i är sämre än en siffra som stämmer. Vill du ha egna ordmål per utkast är det ett fält i projektdialogen; säg till. R03.13
- [x] **2.14** Övningar mot skrivblock ("vad händer nu?"): forskningens arbetsflöde satt rakt av — välj en fråga, få tre förslag, granska, välj eller ignorera, och återgå till skrivandet. Fyra kategorier (Vad händer nu? / Dialog / Handling / Sinnesintryck, efter Sparks), `core/exercises.py` bygger frågan och tolkar svaret (rent, eget självprov på 11 kontroller), och `ui/exercise_dialog.py` visar svaren. Det valda förslaget hamnar i **scenens egen anteckning**, inte i manuset: förslagen är vägar in, inte färdig prosa — och anteckningen är samma sammanhang som AI:n läser nästa gång. Anropet går genom den befintliga AI-klienten, så ingen ny nyckel eller leverantör behövs. R03.16
- [x] **2.15** Läsbarhetsanalys och stilråd i texten: LIX fanns i `core/document_stats.py` och visades i panelen, men ingenstans i texten. Nu finns `sentence_ranges(text, max_words=20)` (ren funktion, eget självprov) och `ReadabilityHighlighter` i editorn, som markerar tunga meningar med en **prickad understrykning** — formen bär betydelsen, färgen förstärker. Markeringen är en *vy*-format (som kommentarerna): texten rörs inte och inget hamnar i scenfilen. Slås på i Visa-menyn och kommer ihåg sig i configen. Valet av enhet är inte slumpat: meningen är det LIX drivs av, så markeringen visar precis det rådet gäller. R03.17
- [x] **2.16** Projektöversikt och anteckningar: **Arkiv → Projektöversikt** (Ctrl+Shift+O) visar
      var boken står på ett ställe — ord mot mål, dagskvot mot deadline, scener, status, utkast,
      trådar (etiketterna som faktiskt används), antalet anteckningar i valvet, **länkar som inte
      leder någonstans** (kontinuitetskollen som inte kräver en tung plotmodell) och projektets
      instruktioner i kortform. Allt räknas ur projektet och valvet som redan finns —
      `overview_rows()` är ren och provas mot oberoende räkningar. Valvet är projektets
      anteckningslager i vyn; **inga filer flyttas och valvet delas inte per bok** (hans
      anteckningar och länkarna mellan dem ligger kvar som de är — att splitta valvet per bok är
      ett eget beslut, säg till om du vill ha det). R03.18
- [x] **2.17** Projektinstruktioner till AI:n: projektet har ett fält (`settings["ai_instructions"]`)
      som författaren fyller i — ton, tempus, namn, allt som ska vara lika hela vägen — och som
      läggs **sist** i systemprompten, närmast uppgiften. Ett tomt fält lämnar prompten orörd, en
      trasig källa eller ett stängt projekt stoppar inte anropet, och fönstret pekar AI:n på det
      projekt som är öppet just nu i stället för att kopiera texten. Menyväg: Arkiv →
      Projektinstruktioner. Alla tre AI-vägarna (granskning, omskrivning, övningar) går genom samma
      `_system_prompt`, så regeln bor på ett ställe. R03.18
- **Status:** complete (två undantag flyttades till fas 4 som 4.14–4.16: pauspåminnelser, namn- och
  ordförrådsgenerator, blurb/synopsis — de hörde hemma med sakprosan)

### Fas 3: Revision och granskning

- [x] **3.1** Snapshots per scen: modellen fanns (oföränderlig kopia + tidsstämpel + etikett +
      `diff()` + `restore()`), men **ingen UI och ingen väg in** — lagret var byggt och oanvänt. Nu:
      Arkiv → Versionshistorik (Ctrl+Shift+H) visar scenens punkter, skillnaden mot texten som
      ligger på disk nu, och en väg tillbaka. En punkt tas automatiskt **när en scen öppnas** (så
      texten finns som den såg ut när man lämnade den), och bara om den skiljer sig från den
      senaste — annars fylls historiken av kopior av samma mening. R01.6, R02.4
- [x] **3.2** Spårade ändringar som operationer, acceptera/avvisa enskilt: `core/revisions.py` gör
      ändringar till operationer (typ, gammal och ny text, ankare, stycke) och beslutar per stycke;
      `ui/review_dialog.py` visar dem med **kryssad rad = behåll**, förhandsvisar exakt den text som
      skrivs, och Arkiv → Granska ändringar sedan senaste punkten (Ctrl+Alt+R) är vägen dit. Texten
      före granskningen sparas som egen punkt, så ingreppet går att ångra. **Jämförelsen läser text,
      inte HTML** — annars vore varje sparning en ändring, eftersom Qt skriver om attributen (det är
      fällan forskningen varnar för). Ett `<ul>` med sina `<li>` är en enhet, så inget beslut kan
      lämna halv HTML. Detaljnivån finns nu också: `word_diff()` visar vilka **ord** som gick och kom
      i ett omskrivet stycke, i radens verktygstips. Besluten är kvar per stycke — en läsare får
      ordningen, men tar ställning till stycket. R02.1
- [x] **3.3** Kommentarer i marginalen med tråd och "löst": kommentarerna, markeringarna i
      texten, hoppa-till-citatet och **löst** fanns redan färdiga i scenpanelen (kontrollerat, inte
      antaget). Det som saknades var **tråden**: `add_reply()` i projektet, en ↳-knapp i panelen och
      svar som indragna rader direkt efter sin kommentar — med kommentarens id, så ett klick på ett
      svar går till samma citat. Kommentarer som sparades innan trådar fanns får sin tomma lista av
      `setdefault`, så gamla projekt öppnas som förut. Tråden hänger kvar under en löst kommentar.
      R02.2
- [x] **3.4** Jämför dokument och slå ihop versioner: granskningen kan nu köras mot **vilken punkt
      som helst**, inte bara den senaste — historiken har knappen "Granska mot texten nu", och
      fönstret kör samma väg som för senaste punkten. Originalet förblir orört: punkten läses,
      texten jämförs, och ingenting skrivs förrän granskningen är verkställd (forskningens
      blackline-arbetsflöde). Provat: mot den äldsta punkten syns ändringen sedan dess, mot den
      senaste färre och utan den äldre ändringen — det är skillnaden mellan att välja original.
      Själva sammanslagningen är densamma som acceptans per stycke gav i 3.2. R02.3
- [x] **3.5** Jämförelse av formatering, separat från textdiff: formateringen hålls utanför
      ändringarna. `formatting_changes()` räknar de stycken där **texten är oförändrad men
      markupen inte** (kursiv, indragning, rader) och rutan säger det i en rad ovanför listan i
      stället för att göra dem till ändringar man ska ta ställning till. Provat: kursiv text ger
      noll textändringar men en formateringsnot. R02.15
- [x] **3.6** Versionshistorik och återställning i ett samlat flöde: historiken öppnas med
      osparade ändringar, och de sparas först — annars jämförs punkterna mot en text på disk som är
      äldre än den man ser. En återställning sparar texten som låg där **först** som en egen punkt
      ("före återställning"), så ingreppet går att ångra med samma knapp som allt annat. R02.4
- [x] **3.7** AI-kommentarer i marginalen i stället för överskrivning: varje förslagskort i
      AI-panelen har nu en 💬-knapp som lägger förslaget som **kommentar på sitt citat** i stället
      för att skriva över texten. Texten står kvar orörd, författaren läser förslaget där hon läser
      sina egna kommentarer, och samma förslag två gånger blir en kommentar — inte två. Provat hela
      vägen: kortets knapp → signalen → kommentaren på citatet med förslaget i sig → syns i
      marginalen, och manuset tecken för tecken oförändrat. R04.14
- [x] **3.8** Acceptans per förslag, som eget undo-steg: `+`-knappen skriver in **ett** förslag i
      taget som ett enskilt `insertText` över markeringen — alltså ett steg i ångra-historiken, och
      ett ångra tar tillbaka hela förslaget. Provat: förslaget in, ett ångra ut, och ett förslag som
      inte går att hitta i texten (citatet kan ha ändrats) skriver ingenting utan säger det i
      statusfältet. R04.15
- **Status:** pending

### Fas 4: Sakprosan

- [x] **4.1** Fotnoter med automatisk numrering och navigering: markeringen `[not: …]` står i texten
      och **numret räknas fram ur ordningen**, så att flytta ett stycke är att numrera om. Panelen har
      fliken *Noter och figurer* — registret — där varje not står med sitt nummer, och ett klick sätter
      markören vid markeringen. Exporten gör markeringen till en riktig upphöjd notlänk och samlar
      noterna under "Noter" i filen. Provat: infogning, numrering i ordning, registret, klicket och
      exporten. R02.5
- [x] **4.2** Korsreferenser till rubriker (fält, inte rå text): `[ref: Rubrikens text]` blir
      "se kapitel 2" — man väljer rubrik i en lista med kapitelnumren, i stället för att skriva dess
      text och hoppas. Rubriken slås upp utan hänsyn till skiftläge och inledande nummer, och en
      hänvisning som inte hittar sin rubrik **står kvar orörd** i stället för att bli en tyst felaktig
      siffra. Provat: vägran utan rubriker, uppslagningen, och den färdiga texten i exporten. R02.6
- [x] **4.3** Genererad innehållsförteckning, uppdaterbar: rubrikerna läses ur dokumentets
      rubriknivåer, får kapitelnummer (`number_headings`: 1, 1.1, 1.2, 2 — och en överhoppad nivå blir
      1.1, inte 1.0.1), och listan står mellan `[innehåll]` och `[/innehåll]`. Trycker man en gång till
      **uppdateras listan i stället för att en ny läggs till** — provat (en förekomst, inte två).
      Klickbarheten ligger i panelens rubriklista, som hoppar till rubriken i texten. R02.7
- [x] **4.4** Rubriknavigatorn: panelens Kapitel-flik har fyllts ur dokumentets rubriknivåer sedan
      tidigare, och ett klick hoppar till rubriken. **Verifierat** i rökprovet hela vägen: en rubrik
      sätts med verktygsradens stilsättning → den hamnar i navigatorn (med indrag efter nivå, ▪ för
      nivå 2) → ett klick sätter markören exakt på rubriken (16 mot 16) → och ett vanligt stycke
      hamnar inte där. Det som saknades var provet, inte funktionen. R02.17
- [x] **4.5** Bildtexter med automatisk numrering + register: `[figur: …]` och `[tabell: …]` får
      egna serier (Figur 1, Tabell 1) och blir "Figur 1. Trappan från hallen." i filen. Registret är
      samma panelflik som noterna — figurerna och tabellerna med sina nummer, i textens ordning.
      Provat både i registret och i den exporterade texten. R02.8
- [x] **4.6** Stycke- och teckenstilar och stilmallar: styckeformaten är blockroller (rubrik 1–3,
      citat, kod) och sätts i verktygsraden; teckenformaten (fet, kursiv, understruken, genomstryken,
      upphöjd, nedsänkt) likaså; och **stilmallarna** (`core/templates.py`: roman, novell, fackbok …)
      ger ett nytt projekt sina statusar och sitt ordmål — rökprovet arbetar i ett projekt skapat med
      mallen "roman" genom hela körningen. **Provat** rubriknivån (2) och teckenformatet (vikt 700).
      *Medvetet inte gjort:* en stilinspektör som listar dokumentets stilar med räknare — ingen
      författare har saknat den, och en förteckning över sina egna rubriker finns i navigatorn. R02.9
- [~] **4.7** Avsnittsbrytningar med separata sidhuvuden/sidfötter — **flyttad till fas 5 (5.5)**.
      Detta hör till utskriften, inte till skrivandet: det kräver sidvis layout (sidindex → inner/
      ytter) i utskriftsvägen, samma sak som den befintliga anteckningen i 0.2 pekar på. En författare
      märker det först när boken ska tryckas, och då är 5.5 rätt plats. Att bygga det nu hade varit
      att bygga sidnumrering två gånger. R02.10
- [ ] **4.8** Spalter och avstavning. R02.11 — *låg*
- [x] **4.9** Autokorrigering och autotext: `core/autocorrect.py` har funnits sedan 0b men **nådde
      aldrig gränssnittet**. Nu ligger den i Redigera-menyn (Ctrl+Shift+K) och kör över scenen.
      Provat: `teh` → `the`, `"hej"` → `”hej”`, `...` → `…`, fler fel i samma scen, **fetstilen runt
      ordet står kvar** (vikt 700) och en gång till hittar ingenting. Bara de områden som faktiskt
      skiljer skrivs om, och allt sker i ett edit block — ett ångra tar tillbaka hela körningen.
      R02.12
- [x] **4.10** Språk per textavsnitt, stavning och grammatik: `core/spellcheck.py` har funnits
      sedan 0b (verifierad mot riktiga tjänsten, UTF-16-korrekta offset) men **nådde aldrig
      gränssnittet** — samma mönster som sök och autokorrigering. Nu i Redigera-menyn (Ctrl+Shift+G)
      och i panelens Språk-flik. **Ett språk per avsnitt:** stycken med egen språkmärkning skickas för
      sig, resten med scenens språk — provat att ett stycke märkt engelskt kontrolleras som engelskt.
      Träffarna står i panelen med ordet, meddelandet och förslagen; ett klick markerar ordet i
      texten, ett dubbelklick tar första förslaget (**ett** ångra-steg). Adressen står i panelen —
      texten lämnar datorn, det ska man veta om — och en tjänst som inte svarar säger *varför* i
      stället för att visa en tom lista. Egen server ställs in med `spellcheck_endpoint`. R02.13
- [ ] **4.11** Tecken-/symboltabell och tesaurus. R02.14 — *låg*
- [x] **4.12** Sök och ersätt med reguljära uttryck: `core/find_replace.py` har också funnits utan
      att nås. Nu i Redigera-menyn (Ctrl+F och Ctrl+H), icke-modal (man ska kunna skriva vidare) med
      räknare, mönster, skiftläge och hela ord. Provat: räknaren, sök nästa markerar träffen, Ersätt
      alla byter alla och **ett** ångra tar tillbaka hela ersättningen, mönster med bakåtreferens
      (`(skriv)en` → `\1et`). R02.16
- [ ] **4.13** Tabeller med formler och ekvationer. R02.18 — *låg*
- [x] **4.14** Pauspåminnelser, valbart: en klocka (50 minuter, `pause_minutes` i inställningarna)
      som säger till i **statusfältet** och blinkar i aktivitetsfältet — ingen modal ruta som avbryter
      mitt i en mening, samma diskreta form som sprintens slut. Valet kommer ihåg sig. Provat:
      på/av, att valet sparas, och att påminnelsen syns. *Flyttad från fas 2 (2.7).* R03.7
- [x] **4.15** Namn- och ordförrådsgenerator: två nya kategorier i "Fastnat?"-rutan — **Namn** och
      **Ord och uttryck** — som ber om tolv alternativ i stället för tre (antalet står per kategori,
      och tolkningen följer kategorin, inte ett tak i koden). Ett valt **namn läggs i codexet** med
      noten som sammanfattning — ett namn hör till boken, inte till scenen — medan en väg vidare
      fortfarande hamnar i scenens anteckning. Provat: antalen, tolkningen, codexet och att scenens
      anteckning inte rörs av ett namn. *Flyttad från fas 2 (2.11).* R03.12
- [x] **4.16** Blurb och synopsis som projektfält: baksidestext och sammanfattning ligger i
      projektöversikten (Ctrl+Shift+O) och sparas i projektfilen när rutan stängs. De hör till
      **projektet**, inte till scenen — de beskriver boken. Provat: att båda sparas och att de står i
      `project.json` på disk. *Flyttad från fas 2 (2.13).* R03.15
- **Status:** complete (556 rökprov + 54 renhetsprov + modulernas egna, GRÖNT)

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

## Att åtgärda senare (rapporterat av Alex, ej gjort)

- [ ] **Flikraden och etiketterna i sidopanelen klipps vid ~390 px bredd.** Sett i skärmdumpar
      2026-10-07 (samma familj som flikklippningen): de fyra flikarna i panelen ("Anteckningar",
      "Scen", "Skrivlogg", "Story bib") ryms inte, och etiketten för antalet öppna kommentarer
      klipps till "1 kva…". Panelens bredd är satt för fyra flikar och etiketten ligger i en
      formkolumn som är för smal. En egen layoutvända: kortare fliknamn eller ikoner med tooltip,
      och etiketten på egen rad. Inget av detta hindrar arbetet — det ser bara trångt ut.

- [ ] **Teckensnittsväljaren visar menyrubriken i stället för typsnittet.** Sett i skärmdump
      2026-10-07: rutan visar "—— ⭐ Popular Writing Fonts ——" tills man väljer ett typsnitt.
      `populate_fonts` lägger rubrikerna först i listan, och ingen väljer den aktuella skriften
      vid start — index står kvar på rubriken. Fixen är att ställa in den aktuella familjen
      efter `populate_fonts` (eller att göra rubrikerna ovalbara).


- [ ] **Rökprovet kraschar ibland i städningen (signal 11) efter grön resultatrad.** Sett 2 gånger
      2026-10-07 (gate35 och gate39), aldrig tidigare i någon gate-logg. Alla 376 kontroller är
      gröna och krashen kommer *efter* sammanfattningen. Det troliga var stilen som lades på
      widgeten (`use_dropdown`) — den ägs nu av applikationen (`install_dropdown_style()`) i stället
      för av en widget, och 10 körningar i rad är gröna. Om det kommer tillbaka: kör rökprovet i en
      slinga och läs sista raden, och misstänk Qt-objekt som dör före sina användare.


- [x] **Teckensnittsväljarens meny sprängde hela fönstret.** Fixat 2026-10-07. Orsaken var
      stilmallens fyra regler för `QComboBox QAbstractItemView` (i `ui/theme_manager.py`): de får
      Qt att svara ja på `SH_ComboBox_Popup`, och då fyller menyn hela den lediga höjden med
      skrollpilar och listan läggs mitt i — mätt 800 px meny med listen 390 px på y=133, alltså
      de två tomma fälten i skärmdumpen. Reglerna stängde dessutom av menyvyns egen skrollist, så
      bara de första elva av 37 typsnitt gick att nå. Reglerna är borta (färgerna kommer från
      appens palett, som redan sätts ur temat, och radhöjden från `FontItemDelegate.sizeHint`),
      och `core.font_manager.use_dropdown` svarar nej på menyläget för teckensnitts- och
      storleksmenyn. Mätt efteråt: 366 px meny för 14 rader à 26 px, listen från y=0, skrollist
      med 23 rader kvar — och läsbar även i temat dark (#1e222b bakgrund, #f8fafc text). Tre
      kontroller i rökprovet vaktar mekanismen (bit-testade: utan fixen blir de röda).
- [ ] **Inspektörens första flik klipps.** Sett i skärmdumpar 2026-10-07: flikraden visar "…ingar"
      längst till vänster — det är `sidebar_tab_notes` ("Anteckningar", `ui/main_window.py:150`) som
      skjutits ut när den aktiva fliken är den sista. Raden har `setUsesScrollButtons(True)` och
      pilarna är 10 px men osynliga: stilmallen tar bort plattformens pilar, så det finns ingen synlig
      väg tillbaka till första fliken. Fixen: stila `QTabBar::scroller` och dess
      `QToolButton::left-arrow/right-arrow` (samma fallgrop som tidigare, se Designkrav), eller visa
      flikarna i två rader när de inte får plats.
- [ ] **Verktygsradens emoji blir svarta fyrkanter.** Sett i skärmdumpar 2026-10-07: rutor i stället
      för ikon där emoji används — `ui/toolbar.py`: `🌐` (`act_gfonts`), `🎨 Color`, `🖍️ Highlight`,
      `🧹 Tx`, `📊` (`btn_table`). Vanliga glyfer (`𝐁`, `𝐼`, `≡`, `⇤`) ritas korrekt, så det är
      emojin och typsnittet, inte knapparna. `ui/icons.py` med Lucide-SVG:er finns redan och används
      i toppbaren och vänsterrail sedan `6e44ecb` — byt emojin mot dem (eller mot ren text).

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
