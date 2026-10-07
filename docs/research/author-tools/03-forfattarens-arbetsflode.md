# Författarens arbetsflöde
## Sammanfattning
- Deadline kopplad till ett konkret ordmål, med automatisk beräkning av dagskvot och vilodagar, ger en författare en handlingsbar väg från ambition till färdigt manus. [belagt: https://www.dabblewriter.com/l/d/j2] [belagt: https://help.ulysses.app/the-dashboard/goals]
- Arbetsmål per session, projektmål och omedelbar visuell återkoppling finns i Scrivener och Writing Analytics; den korta återkopplingsloopen är ett rimligt förstaval för att få skrivpass att faktiskt hända. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects] [belagt: https://support.writinganalytics.co/guides/setting-goals]
- Historik, aktivitetsdiagram och streaks gör vanan synlig över dagar och månader; Ulysses, Writing Analytics, 4thewords och FocusWriter visar olika varianter. [belagt: https://help.ulysses.app/the-dashboard/goals] [belagt: https://support.writinganalytics.co/guides/habit-tracker-and-streaks] [belagt: https://4thewords.com/] [belagt: https://gottcode.org/blog/new-focuswriter-release-3/]
- Romanförfattare behöver skrivytan och berättelsematerialet nära varandra: Scrivener, Dabble och Sudowrite kombinerar manus med scener, karaktärer, anteckningar eller plotverktyg. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- Distraktionsfritt läge ska gå att lämna direkt, medan stil- och läsbarhetskontroll bör kunna vänta till revision; FocusWriter och Hemingway skiljer skrivfokus från analys på tydliga sätt. [belagt: https://gottcode.org/focuswriter/?trk=organization-update_share-update_update-text] [belagt: https://hemingwayapp.com/help/docs/quick-start-guide]

## Bordet: vad som är minimum i kategorin
- Projekt- och sessionsmål med synlig aktuell status är en grundnivå: Scrivener har mål för hela projektet, dokument och session, och Ulysses har mål för texter, grupper och projekt. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects] [belagt: https://help.ulysses.app/the-dashboard/goals]
- Måldatum ska översättas till dagskvot och kunna hantera valda skrivdagar; både Dabble och Ulysses beskriver automatisk beräkning. [belagt: https://www.dabblewriter.com/l/d/j2] [belagt: https://help.ulysses.app/the-dashboard/goals]
- Skrivmiljön ska erbjuda fokus-/helskärmsläge och valfri centrerad markör; Scrivener har helskärmsläge och Ulysses Typewriter Mode. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://ulysses.app/releases/]
- En romanmall ska hjälpa till med struktur, scener och stödmaterial, men inte kräva att författaren planerar före skrivandet; Dabble tillåter omkastning av struktur och Sudowrite leder från synopsis mot scener. [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- Historik ska visa faktiska ord per dag snarare än bara totalsumma; Ulysses sparar sessionsdata och Writing Analytics sammanställer aktivitet och fokus. [belagt: https://help.ulysses.app/the-dashboard/goals] [belagt: https://www.writinganalytics.co/posts/new-stats-on-your-dashboard/]

## Funktionskatalog
### Mål för session och projekt
- **Vad den gör:** Visar ordmål för arbetspasset, enskild scen/text och hela manusprojektet; Scrivener visar målprogress visuellt och kan meddela när mål nås. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects]
- **Exakt arbetsflöde:** 1. Författaren väljer projekt eller text. 2. Anger slutmål. 3. Anger sessionsmål före skrivandet. 4. Skriver medan stapeln visar förlopp. 5. Avslutar när målet nås eller väljer att fortsätta. [belagt: https://www.literatureandlatte.com/docs/Scrivener_Manual-Mac.pdf]
- **Vem gör det bäst:** Scrivener för flera nivåer av mål och snabb status i verktygsfältet; Dabble för enkel daglig måluppföljning. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects] [belagt: https://www.dabblewriter.com/features-2/dabble-features]
- **Tekniskt i PyQt6/QTextDocument:** Spara mål och startvärde per projekt/scen/session i projektmetadata; räkna ord från dokumentets text efter debounce; bind statusfält och `QProgressBar` till samma progressmodell. [resonemang]
- **Prioritet för en ensam författare:** hög — gör en lång uppgift till ett konkret skrivpass. [resonemang]

### Deadline och dagskvot
- **Vad den gör:** Räknar fram hur många ord som behöver skrivas per skrivdag för att nå projektets målord på ett angivet datum. Dabble låter författaren markera lediga dagar; Ulysses har valbara skrivdagar. [belagt: https://www.dabblewriter.com/l/d/j2] [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Exakt arbetsflöde:** 1. Ange mål och slutdatum. 2. Välj veckans skrivdagar och eventuella lediga dagar. 3. Appen visar dagskvoten. 4. Efter skrivpass uppdateras återstående ord och kvot. 5. Ändra datum eller mål när planen ändras. [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Vem gör det bäst:** Ulysses beskriver både skrivdagar och exakt dagsbehov; Dabble stöder explicit frånräkning av dagar lediga. [belagt: https://help.ulysses.app/the-dashboard/goals] [belagt: https://www.dabblewriter.com/l/d/j2]
- **Tekniskt i PyQt6/QTextDocument:** Beräkna `ceil((mål - aktuell_progress) / återstående_skrivdagar)` med `QDate`; visa kvoten och datum i projektpanelen. Skydda mot noll dagar och mål under befintlig text. [resonemang]
- **Prioritet för en ensam författare:** hög — ger direkt svar på om planen är realistisk idag. [resonemang]

### Historik, diagram och streaks
- **Vad den gör:** Registrerar dagliga ordtal, sessioner, målträffar och sammanhängande skrivdagar. Writing Analytics skiljer skriv- och revisionsdagar och visar nuvarande/längsta streak; Ulysses visar historik och dagsmedel. [belagt: https://support.writinganalytics.co/guides/habit-tracker-and-streaks] [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Exakt arbetsflöde:** 1. Starta redigering. 2. Appen registrerar datum och förändring i ordantal. 3. Visa kalender-/stapeldiagram. 4. Klicka en dag för ord/sessioner. 5. Markera ledig dag om appens streakmodell stöder det. [belagt: https://support.writinganalytics.co/guides/habit-tracker-and-streaks]
- **Vem gör det bäst:** Writing Analytics för rutinöversikt och streaks; Ulysses för beständig sessionsexport och dagsstatistik. [belagt: https://support.writinganalytics.co/guides/habit-tracker-and-streaks] [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Tekniskt i PyQt6/QTextDocument:** Ta snapshots av ordantal med datum och sessionens start/slut i SQLite; rita dagliga värden med Qt Charts eller egen `QPainter`-grafik. Separera tillagda och borttagna ord så revision inte ser ut som noll aktivitet. [resonemang]
- **Prioritet för en ensam författare:** hög — synliggör framsteg när ett manus tar månader. [resonemang]

### Sessionshistorik och skrivlogg
- **Vad den gör:** Bevarar arbetspassens datum, längd och utfall. Ulysses börjar en session när författaren skriver och avslutar vid midnatt; data kan exporteras som CSV. [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Exakt arbetsflöde:** 1. Författaren börjar skriva i en målsatt text. 2. Appen öppnar dagens session. 3. Inaktivitet eller dygnsgräns avslutar/pausar den. 4. Historik visar skrivmängd per dag. 5. Författaren kan granska eller exportera historiken. [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Vem gör det bäst:** Ulysses för historik per dag och CSV-export; Writing Analytics för analys av ord tillagda/borttagna och tid i fokus. [belagt: https://help.ulysses.app/the-dashboard/goals] [belagt: https://www.writinganalytics.co/posts/new-stats-on-your-dashboard/]
- **Tekniskt i PyQt6/QTextDocument:** Lyssna på `QTextDocument.contentsChange`; spara sessionsrader separat från textfiler. En vilotimer bör avsluta pass först efter konfigurerbar inaktivitet. [resonemang]
- **Prioritet för en ensam författare:** medel — värdefullt för reflektion och planering men målen ger större omedelbar effekt. [resonemang]

### Skrivsprintar och timer
- **Vad den gör:** Begränsar skrivpasset till tidsmål eller gör skrivandet till en sprint/utmaning. Writing Analytics stöder tidsmål per session; 4thewords beskriver timed writing battles och sprints. [belagt: https://support.writinganalytics.co/guides/setting-goals] [belagt: https://4thewords.com/]
- **Exakt arbetsflöde:** 1. Välj exempelvis 25 minuter. 2. Starta nedräkning. 3. Skriv utan att avbryta. 4. Få signal vid slutet och spara ordtal för passet. 5. Välj om nästa sprint ska starta efter paus. [resonemang]
- **Vem gör det bäst:** 4thewords för spelifierade skrivsprintar och Writing Analytics för tidsmål integrerade med projektstatistik. [belagt: https://4thewords.com/] [belagt: https://support.writinganalytics.co/guides/setting-goals]
- **Tekniskt i PyQt6/QTextDocument:** En `QTimer` uppdaterar återstående tid; inställningar för ljud, diskret notis och paus mellan sprintar. Spara inte timerstatus i dokumentets text. [resonemang]
- **Prioritet för en ensam författare:** medel — enkelt att bygga och bra för tröskeln till ett arbetspass. [resonemang]

### Distraktionsfritt läge och skrivmaskinsläge
- **Vad den gör:** Gömmer gränssnittets sidopaneler eller håller aktuell textrad på en lugn, stabil plats. Scrivener har helskärmsläge; Ulysses har Typewriter Mode; FocusWriter döljer menyer tills pekaren når skärmkanten. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://ulysses.app/releases/] [belagt: https://gottcode.org/focuswriter/?trk=organization-update_share-update_update-text]
- **Exakt arbetsflöde:** 1. Tryck genväg för fokusläge. 2. Dölj verktygsfält och paneler. 3. Skriv med vald bredd, tema och markörposition. 4. Flytta pekaren eller tryck Escape för att visa kontrollerna igen. [resonemang]
- **Vem gör det bäst:** FocusWriter för helskärmsmiljö med gömda kontroller; Ulysses för justerbar fokusmarkering och centrerad markör. [belagt: https://gottcode.org/focuswriter/?trk=organization-update_share-update_update-text] [belagt: https://ulysses.app/releases/]
- **Tekniskt i PyQt6/QTextDocument:** OmaScribe har redan ett helskärmsläge som döljer verktygsfält och sidopanel (`ui/main_window.py:392-400`). Lägg till val för markörcentrering med `QTextEdit.ensureCursorVisible`, maxbredd och menyåterställning. [resonemang]
- **Prioritet för en ensam författare:** hög — låg kostnad och direkt hjälp mot gränssnittsstörningar. [resonemang]

### Pauspåminnelser och ergonomi
- **Vad den gör:** Påminner om kort paus efter lång skrivtid; av de granskade produkternas officiella källor kunde jag inte bekräfta en ergonomisk pausfunktion. Skrivpass med timer är belagda i Writing Analytics. [belagt: https://support.writinganalytics.co/guides/setting-goals]
- **Exakt arbetsflöde:** 1. Författaren anger arbets- och pauslängd. 2. Timer startas automatiskt eller manuellt. 3. En mild avisering föreslår paus. 4. Författaren skjuter upp, ignorerar eller startar paustimer. [resonemang]
- **Vem gör det bäst:** Ingen av de undersökta produkterna kan utses som belagd vinnare för ergonomiska pauspåminnelser. [resonemang]
- **Tekniskt i PyQt6/QTextDocument:** Kombinera `QTimer` med statusnotis och valbar systemnotis; räkna aktiv tid endast när redigeraren har fokus och textinmatning sker. [resonemang]
- **Prioritet för en ensam författare:** låg — bra som valbar hjälp, men mindre central än skrivmål och fokus. [resonemang]

### Romanmallar och onboarding
- **Vad den gör:** Ger en ny roman en startstruktur och introducerar var manus, scener, plot och anteckningar finns. Scrivener har projektdokumentmallar; Dabble samlar manus och plotmaterial i projekt; Sudowrite leder från synopsis via outline till scener. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- **Exakt arbetsflöde:** 1. Välj romanprojektmall eller tomt projekt. 2. Välj planeringsgrad. 3. Skapa kapitel/scener och stödanteckningar. 4. Börja skriva direkt eller fyll i valfria planeringsfält. [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble]
- **Vem gör det bäst:** Scrivener för anpassningsbara dokumentmallar; Dabble för lågfriktionsstart där planering kan ske före eller efter första texten. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble]
- **Tekniskt i PyQt6/QTextDocument:** Lägg till en projekttyp som skapar mappar/metadata för kapitel, scener, anteckningar och karaktärer; håll detta separat från standarddokumentmallar. [resonemang]
- **Prioritet för en ensam författare:** medel — särskilt värdefullt när ett romanprojekt startar, men inte för alla dokument. [resonemang]

### Karaktärsblad och story bible
- **Vad den gör:** Samlar karaktärers namn, roll, bakgrund, utseende och röst samt världsdetaljer. Sudowrite har strukturerade Character cards och Worldbuilding; Scrivener tillåter mallar för karaktärs- och platsblad; Dabble håller karaktärer och story notes i samma projekt. [belagt: https://feedback.sudowrite.com/en/help/articles/1726763-characters] [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble]
- **Exakt arbetsflöde:** 1. Skapa karaktär eller världspost. 2. Fyll i eller lämna tomma strukturerade fält. 3. Länka posten till scen eller manus. 4. Sök eller öppna bladet vid behov. [belagt: https://feedback.sudowrite.com/en/help/articles/1726763-characters]
- **Vem gör det bäst:** Sudowrite för tydligt strukturerade kort och världsposter; Scrivener för användarstyrda mallar. [belagt: https://feedback.sudowrite.com/en/help/articles/1726763-characters] [belagt: https://www.literatureandlatte.com/scrivener/overview]
- **Tekniskt i PyQt6/QTextDocument:** Modellera poster som egna textdokument med typmetadata och internlänkar; visa fält i `QDockWidget`/sidopanel utan att blanda fakta med manusbrödtext. [resonemang]
- **Prioritet för en ensam författare:** medel — starkt stöd för romaner med stor ensemble eller värld. [resonemang]

### Tidslinje, plot-tavla och scenöversikt
- **Vad den gör:** Visar händelser och scener i en ordningsbar visuell struktur. Scrivener Corkboard kopplar kort till manusdelar; Dabble Plot Grid visar huvudtråd och sidotrådar; Sudowrite Canvas är en fri yta med flyttbara kort. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/en/help/articles/2695461-canvas]
- **Exakt arbetsflöde:** 1. Skapa scenkort med synopsis. 2. Lägg kort i ordning eller gruppera efter tråd/karaktär. 3. Flytta kort för att ändra manusordning. 4. Öppna kortet för att skriva scenen. [belagt: https://www.literatureandlatte.com/scrivener/overview]
- **Vem gör det bäst:** Scrivener när omflyttning av kort samtidigt ska ändra manusordning; Dabble när parallella plottrådar ska jämföras. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble]
- **Tekniskt i PyQt6/QTextDocument:** Lagra stabilt scen-ID och sorteringsindex; använd `QGraphicsView` för kortvy och uppdatera projektordningen efter drag/drop. Tidslinje kräver dessutom händelsedatum som separat fält. [resonemang]
- **Prioritet för en ensam författare:** medel — stödjer strukturrevision men inte varje skrivpass. [resonemang]

### Taggar, samlingar och anteckningar knutna till scen
- **Vad den gör:** Låter författaren hitta scener efter POV, status eller tema och hålla scenkommentarer nära texten. Scrivener stöder nyckelord, metadata och samlingar; Dabble stöder story notes och scenetiketter. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/features-2/dabble-features]
- **Exakt arbetsflöde:** 1. Lägg tagg/status på scen. 2. Skriv scenanteckning. 3. Skapa samling, exempelvis “saknar redigering”. 4. Filtrera eller öppna samlingen för att arbeta igenom relaterade scener. [belagt: https://www.literatureandlatte.com/scrivener/overview]
- **Vem gör det bäst:** Scrivener för samlingar som kan gruppera dokument från olika delar av projektet; Dabble för anteckningar och etiketter direkt kopplade till scener. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/features-2/dabble-features]
- **Tekniskt i PyQt6/QTextDocument:** OmaScribe har redan en anteckningsvalvpanel med sökning och filter (`ui/notes_panel.py:86-107`). Lägg till scen-ID som backlink/metadata och bygg smarta samlingar som filtrerade vyer. [resonemang]
- **Prioritet för en ensam författare:** medel — minskar söktid när projektet växer. [resonemang]

### Namn- och ordförrådsgenerator
- **Vad den gör:** Ger förslag på namn, platser, föremål eller formuleringar när idéerna tar slut. Sudowrite Brainstorm har kategorier som namn, platser och världsbygge; ProWritingAid Sparks kan föreslå dialog, analogier och sensoriska detaljer. [belagt: https://feedback.sudowrite.com/help/articles/7767950-brainstorm] [belagt: https://help.prowritingaid.com/article/244-what-is-sparks]
- **Exakt arbetsflöde:** 1. Välj kategori. 2. Skriv kort seed/kontext. 3. Begär förslag. 4. Spara valda resultat i anteckning eller manus. [belagt: https://feedback.sudowrite.com/help/articles/7767950-brainstorm]
- **Vem gör det bäst:** Sudowrite för namngivning och berättelsematerial; ProWritingAid för att arbeta med markerad text och skapa konkreta skrivförslag. [belagt: https://feedback.sudowrite.com/help/articles/7767950-brainstorm] [belagt: https://help.prowritingaid.com/article/244-what-is-sparks]
- **Tekniskt i PyQt6/QTextDocument:** Anropa befintlig AI-tjänst från ett separat dialogfönster med valbar kategori; visa resultat som kopierbara förslag och kräv användarens uttryckliga infogning. [resonemang]
- **Prioritet för en ensam författare:** låg — hjälpsamt ibland men inte kärnan i att hålla skrivvanan. [resonemang]

### Revisionsläge och mål per utkast
- **Vad den gör:** Märker ändringar eller sparar separata ögonblicksbilder för första, andra och senare utkast. Scrivener har fem revisionsnivåer samt snapshots, och metadata kan markera revisionsstatus. [belagt: https://www.literatureandlatte.com/blog/how-to-use-revision-mode-to-edit-your-scrivener-projects] [belagt: https://www.literatureandlatte.com/scrivener/overview]
- **Exakt arbetsflöde:** 1. Slutför utkast 1 och spara snapshot. 2. Växla revisionsnivå. 3. Ändra text medan tillagda/borttagna delar markeras. 4. Jämför med tidigare version. 5. Rensa markeringar när passet är färdigt. [belagt: https://www.literatureandlatte.com/blog/how-to-revise-the-first-draft-of-your-novel-in-scrivener]
- **Vem gör det bäst:** Scrivener för synliga revisionsnivåer och versionsjämförelse i samma projekt. [belagt: https://www.literatureandlatte.com/blog/how-to-use-revision-mode-to-edit-your-scrivener-projects]
- **Tekniskt i PyQt6/QTextDocument:** Spara versionssnapshot per scen; använd character formats för revisionstaggar eller diffvy separat från huvudtexten. Ordprogress per utkast bör knytas till valda snapshot/versioner. [resonemang]
- **Prioritet för en ensam författare:** medel — viktig efter första utkastet, mindre relevant i den dagliga första skrivningen. [resonemang]

### Framstegsindikator i statusfältet
- **Vad den gör:** Håller mål och dagsprogress synliga i själva skrivvyn. Scrivener kan visa projekt- och sessionsstaplar i verktygsfältet; Ulysses visar indikatorer vid projekt/grupp/text. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects] [belagt: https://help.ulysses.app/the-dashboard/goals]
- **Exakt arbetsflöde:** 1. Ställ in mål. 2. Börja skriva. 3. Se ordtal och progress utan att lämna editorn. 4. Öppna detaljer bara när planering behövs. [belagt: https://www.literatureandlatte.com/blog/track-statistics-and-targets-in-your-scrivener-projects]
- **Vem gör det bäst:** Scrivener för parallell projekt- och sessionprogress i en kompakt verktygsrad. [belagt: https://www.literatureandlatte.com/docs/Scrivener_Manual-Mac.pdf]
- **Tekniskt i PyQt6/QTextDocument:** OmaScribe visar redan ord- och teckenantal i statusfältet (`ui/main_window.py:166-190`); utöka samalla widgeten med sessionstapeln och dagskvot. [resonemang]
- **Prioritet för en ensam författare:** hög — progress syns där skrivandet sker. [resonemang]

### Blurb och synopsis
- **Vad den gör:** Håller en kort pitch/sammanfattning nära projektets outline; Sudowrite Story Bible innehåller Synopsis och kan använda den i senare story-steg. [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- **Exakt arbetsflöde:** 1. Öppna projektets synopsisfält. 2. Skriv eller redigera kort sammanfattning. 3. Återanvänd den som referens vid plot- och scenarbete. 4. Skapa separat blurb när texten ska presenteras för läsare. Steg 4 är en rekommenderad modell, inte belagd som en separat funktion i de källor som granskats. [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible] [resonemang]
- **Vem gör det bäst:** Sudowrite för synopsis som sammanhållen del av Story Bible och berättelseplanering. [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- **Tekniskt i PyQt6/QTextDocument:** Separata projektfält för synopsis och blurb; räkna tecken och stöd export till metadata/omslagstext. [resonemang]
- **Prioritet för en ensam författare:** låg — viktigt för pitch och publicering, inte nödvändigt för första utkastet. [resonemang]

### Övningar mot skrivblock
- **Vad den gör:** Ger en konkret prompt eller ett alternativt nästa steg när författaren fastnar. ProWritingAid Sparks Inspire föreslår möjliga fortsättningar, dialog, handling och sinnesdetaljer; 4thewords erbjuder skrivutmaningar och quests. [belagt: https://help.prowritingaid.com/article/244-what-is-sparks] [belagt: https://4thewords.com/]
- **Exakt arbetsflöde:** 1. Markera text eller välj projekt. 2. Välj “What's next?” eller annan promptkategori. 3. Granska förslagen. 4. Välj, ändra eller ignorera och återgå till skrivandet. [belagt: https://help.prowritingaid.com/article/244-what-is-sparks]
- **Vem gör det bäst:** ProWritingAid för kontextuella förslag på vald text; 4thewords för externa utmaningar och spelifierat driv. [belagt: https://help.prowritingaid.com/article/244-what-is-sparks] [belagt: https://4thewords.com/]
- **Tekniskt i PyQt6/QTextDocument:** Skicka urval och valfri scenanteckning till befintlig AI-klient; visa förslag i popup med infogning som separat undo-steg. [resonemang]
- **Prioritet för en ensam författare:** medel — nyttigt när det låser sig, men ska vara frivilligt och diskret. [resonemang]

### Läsbarhetsanalys och stilråd
- **Vad den gör:** Synliggör långa/komplexa meningar, passiv form eller ordval och erbjuder råd. Hemingway visar läsbarhet, svårlästa meningar, passiv form och svagare ord; ProWritingAid erbjuder rapporter och Sparks-förslag. [belagt: https://hemingwayapp.com/help/docs/highlighted-issues] [belagt: https://prowritingaid.com/features/sparks]
- **Exakt arbetsflöde:** 1. Skriv utan markeringar i Write/fokusläge. 2. Växla till redigering/analys. 3. Gå igenom markerade meningar. 4. Acceptera, redigera eller avvisa varje råd. Hemingway rekommenderar uttryckligen att inte rensa varje markering mekaniskt. [belagt: https://hemingwayapp.com/help/docs/quick-start-guide] [belagt: https://hemingwayapp.com/help/docs/highlighted-issues]
- **Vem gör det bäst:** Hemingway för omedelbar, visuellt avgränsad läsbarhetsgenomgång; ProWritingAid för bredare stilrapporter och redigeringsförslag. [belagt: https://hemingwayapp.com/help/docs/highlighted-issues] [belagt: https://prowritingaid.com/features/sparks]
- **Tekniskt i PyQt6/QTextDocument:** OmaScribe har redan LIX, ordantal och lästid i `core/document_stats.py:17-18,38-73` och visar LIX i `ui/sidebar_inspector.py:176-183`. Visa markeringar som extra selections i `QTextEdit`, beräkna utanför varje tangenttryck och håll råtext oförändrad tills användaren väljer ett förslag. [resonemang]
- **Prioritet för en ensam författare:** medel — ger konkret revisionshjälp, men bör inte störa utkastfasen. [resonemang]

### Projektöversikt och onboardade anteckningar
- **Vad den gör:** Håller projektets anteckningar sökbara och strukturerade. Obsidian har tags, properties och Canvas; Canvas kan lägga ut och länka anteckningar, och tags kan filtreras. [belagt: https://obsidian.md/help/tags] [belagt: https://obsidian.md/help/Plugins/Canvas] [belagt: https://obsidian.md/help/properties]
- **Exakt arbetsflöde:** 1. Skapa anteckning eller scenblad. 2. Lägg till tagg/metadata. 3. Samla relaterade blad i Canvas eller sök på tagg. 4. Öppna länkat material från scenens arbetsyta. [belagt: https://obsidian.md/help/tags] [belagt: https://obsidian.md/help/Plugins/Canvas]
- **Vem gör det bäst:** Obsidian för blandningen av fria anteckningar, strukturerade properties, taggar och visuellt Canvas; Scrivener för att koppla detta närmare sammanhängande manusstruktur. [belagt: https://obsidian.md/help/Plugins/Canvas] [belagt: https://www.literatureandlatte.com/scrivener/overview]
- **Tekniskt i PyQt6/QTextDocument:** OmaScribe-valvet kan återanvändas som markdown-anteckningslager; använd YAML-liknande metadata eller sidecar-data för projekt-/scenrelationer. Valvets förekomst kan verifieras i `ui/notes_panel.py:86-107`. [resonemang]
- **Prioritet för en ensam författare:** medel — hjälper kontinuitet utan att kräva en tung plotmodell. [resonemang]

## Vad jag inte kunde belägga
- Jag kunde inte hitta tillräckligt stark officiell dokumentation för en specifik ergonomisk pauspåminnare i Scrivener, Ulysses, Dabble, 4thewords, Writing Analytics, ProWritingAid, Sudowrite, Obsidian/Logseq, FocusWriter eller Hemingway. [resonemang]
- Jag kunde inte verifiera ett tydligt dedikerat scenbaserat tidslinjeverktyg i alla produkter; källorna belägger främst plot-grid, kort/Canvas och ordning av manusdelar. [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/en/help/articles/2695461-canvas] [belagt: https://www.literatureandlatte.com/scrivener/overview]
- Jag kunde inte belägga att varje produkt i listan har romanmallar, karaktärsblad, blurbskrivning, revisionsmål per utkast eller dagskvotsberäkning. De funktionerna förekommer i olika kombinationer, inte som gemensam standard. [belagt: https://www.literatureandlatte.com/scrivener/overview] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble] [belagt: https://feedback.sudowrite.com/help/articles/1671191-what-is-story-bible]
- För OmaScribe har jag verifierat endast de citerade koddelarna: statusfält, helskärmsläge, LIX/statistik, mallkatalog och anteckningspanel. Andra här föreslagna funktioner är byggresonemang och ska inte läsas som befintligt stöd. [resonemang]
