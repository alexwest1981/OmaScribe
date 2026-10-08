# Manusstruktur och binder

## Sammanfattning

- **Scrivener sätter ribban för manus som samling självständiga dokument:** Binder, Corkboard, Outliner, Scrivenings, metadata, snapshots och Collections samverkar i samma projekt. [belagt: https://www.literatureandlatte.com/blog/integrating-scriveners-binder-corkboard-and-outliner] [belagt: https://www.literatureandlatte.com/blog/use-snapshots-in-scrivener-to-save-versions-of-your-projects] [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly]
- **För Scribentia är det avgörande arkitekturbeslutet att gå från ett öppet dokument till ett projekt med ordnade textnoder och separat metadata.** Koden öppnar ett filnamn i den enda `self.editor.document`-instansen; statistiken analyserar det dokumentet. [belagt: ui/main_window.py:641-670] [belagt: core/document_stats.py:4-10]
- **Dabble visar en tydlig scenmodell för romanförfattare:** böcker och kapitel är behållare, varje scen är egen text, och scener kan flyttas mellan kapitel. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Minsta professionella paket:** hierarki, scener som enheter, kort-/översiktsvy, metadata, mål på projekt- och dokumentnivå, research som inte blandas in i manus samt säker versionshistorik. [resonemang]
- **Gör binder till navet:** välj dokument, flytta ordning, se status, synopsis och ordtal där; visa sedan samma data som kort, lista, filtrerad samling och sammanhängande läsvy. [resonemang]

## Bordet: vad som är minimum i kategorin

- **Manusobjekt måste kunna ordnas hierarkiskt** i exempelvis del → kapitel → scen, med möjlighet att flytta en scen utan att klippa och klistra i hela boken. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story] [resonemang]
- **Varje scen behöver vara ett självständigt redigerbart dokument** med synopsis, anteckningar och metadata; annars går det inte att planera och revidera lokalt. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story] [resonemang]
- **En författare måste kunna växla mellan detalj och helhet:** binder/lista, visuella indexkort och en vy som läser flera scener som ett manus. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard] [belagt: https://www.literatureandlatte.com/blog/scrivener-2-0-coming-soon-no-really]
- **Mål och arbetsläge ska följa dokumenten:** ordmål på scen/kapitel/projekt och status/etiketter för att se vad som saknas, behöver redigeras eller hör till en viss berättartråd. [belagt: https://help.ulysses.app/goals] [belagt: https://www.literatureandlatte.com/blog/three-ways-to-mark-the-status-of-items-in-your-scrivener-project] [resonemang]
- **Research, versioner och stödmaterial måste överleva manusredigering:** bilder/källor separeras från texten som ska exporteras; ändringar kan återställas per dokument. [belagt: https://www.literatureandlatte.com/blog/use-snapshots-in-scrivener-to-save-versions-of-your-projects] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story] [resonemang]

## Funktionskatalog

### 1. Binder: projektträd för delar, kapitel och scener
- **Vad den gör:** Visar manusets bestående ordning i ett träd, med mappar/behållare för delar och kapitel och skrivbara scendokument under dem. Scrivener beskriver Binder som projektets hierarkiska dokumentlista; Dabble skiljer behållare från scener. [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Exakt arbetsflöde:** 1. Skapa projekt. 2. Lägg till del eller kapitel som behållare. 3. Skapa scendokument i kapitel. 4. Välj scen i trädet för redigering. 5. Expandera eller fäll ihop grenar för att hitta rätt avsnitt. [resonemang]
- **Vem gör det bäst:** Scrivener, eftersom samma Binder-struktur används av Corkboard, Outliner, Scrivenings och Collections. [belagt: https://www.literatureandlatte.com/blog/integrating-scriveners-binder-corkboard-and-outliner]
- **Tekniskt i PyQt6/QTextDocument:** Lagra ett projektmanifest med stabilt `node_id`, `parent_id`, typ, position och sökväg till sceninnehåll. Visa det i `QTreeView` med `QAbstractItemModel`; skapa/ladda ett separat `QTextDocument` per scen. [resonemang]
- **Prioritet för en ensam författare:** hög – binder är den grund som allt annat organiseras kring. [resonemang]

### 2. En scen per textdokument
- **Vad den gör:** Scenen kan skrivas, flyttas, räknas, kommenteras och versionshanteras oberoende. Dabble anger uttryckligen att varje scen sparas och redigeras separat. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Exakt arbetsflöde:** 1. Skapa scen under kapitel. 2. Skriv scenens prosa i editorn. 3. Byt till annan scen utan att ändra de andra. 4. Flytta scenen vid behov. [resonemang]
- **Vem gör det bäst:** Dabble för enkel scenorienterad författarupplevelse; Scrivener för bredare dokumentmodell och flera parallella representationsvyer. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story] [belagt: https://www.literatureandlatte.com/blog/integrating-scriveners-binder-corkboard-and-outliner]
- **Tekniskt i PyQt6/QTextDocument:** Separera projektmodell från editor-widget. Ladda vald scen i en `QTextDocument` och spara innehåll som HTML eller ett eget format med schema-version; autospara med debounce och atomisk filersättning. [resonemang]
- **Prioritet för en ensam författare:** hög – utan scenen som självständig enhet blir 100 000 ord svårhanterligt. [resonemang]

### 3. Korktavla och indexkort
- **Vad den gör:** Gör scener till kort med titel och synopsis; kort kan ordnas visuellt. Scrivener-kort motsvarar samtidigt dokument i Binder och poster i Outliner. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard]
- **Exakt arbetsflöde:** 1. Öppna kapitel eller projekt i kortvy. 2. Skapa kort för idéer eller scener. 3. Skriv synopsis på kortet. 4. Dra kort till ny ordning. 5. Bekräfta ordningen så Binder och manus uppdateras. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard]
- **Vem gör det bäst:** Scrivener, genom att korten är samma projektobjekt som dokumenten och kan visas både linjärt och fritt. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard] [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-freeform-corkboard]
- **Tekniskt i PyQt6/QTextDocument:** Bygg `QGraphicsView`/`QGraphicsScene` för fri tavla eller `QListView` med `IconMode` för linjära kort. Kortet visar metadata från projektmodellen; drag/drop ändrar `position` och vid fri placering x/y. [resonemang]
- **Prioritet för en ensam författare:** hög – omordning och överblick är centrala i revision. [resonemang]

### 4. Synopsis och sammanfattning per dokument
- **Vad den gör:** Håller en kort beskrivning vid sidan av scenens brödtext, så författaren kan läsa berättelsens struktur utan att öppna varje scen. Scrivener använder synopsis i indexkort och Outliner. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard]
- **Exakt arbetsflöde:** 1. Markera scen. 2. Skriv/uppdatera synopsis i inspector eller direkt på kortet. 3. Granska synopses i kort-/listvy. 4. Använd dem för att se luckor och upprepningar. [resonemang]
- **Vem gör det bäst:** Scrivener, eftersom synopsis lever på dokumentet och återanvänds i flera planeringsvyer. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard]
- **Tekniskt i PyQt6/QTextDocument:** Lagra synopsis som metadata på scenobjektet, inte som rubrik eller dold text i `QTextDocument`; visa/redigera i `QPlainTextEdit` i inspector. [resonemang]
- **Prioritet för en ensam författare:** hög – synopsis gör ett långt manus skannbart. [resonemang]

### 5. Status och etiketter
- **Vad den gör:** Status anger arbetsfas (idé, utkast, revidering, klart); etikett kan ange POV, plats, tråd eller annan kategorisering. Scrivener visar status och label i Binder, Corkboard och Outliner. [belagt: https://www.literatureandlatte.com/blog/three-ways-to-mark-the-status-of-items-in-your-scrivener-project] [belagt: https://www.literatureandlatte.com/blog/structuring-with-label-view]
- **Exakt arbetsflöde:** 1. Välj en eller flera scener. 2. Sätt status från en redigerbar lista. 3. Sätt etikett/POV. 4. Visa värden som badge, färg eller kortstämpel. 5. Filtrera eller gruppera efter värde. [resonemang]
- **Vem gör det bäst:** Scrivener, med både statusfält och visuella labels, samt stöd för att visa dem på flera vyer. [belagt: https://www.literatureandlatte.com/blog/three-ways-to-mark-the-status-of-items-in-your-scrivener-project] [belagt: https://www.literatureandlatte.com/blog/structuring-with-label-view]
- **Tekniskt i PyQt6/QTextDocument:** Typade metadatafält i projektmodellen med användarens egna värdelistor; Qt proxy-model filtrerar och sorterar. Färg är presentation, statusvärde bör även läsas som text. [resonemang]
- **Prioritet för en ensam författare:** hög – visar vad som är ofärdigt och möjliggör POV-/trådkontroll. [resonemang]

### 6. Snapshots och dokumentversioner
- **Vad den gör:** Fryser en version av en enskild scen före större ändring; användaren kan jämföra eller återställa text. Scrivener skiljer snapshots från fullständig projektbackup. [belagt: https://www.literatureandlatte.com/blog/use-snapshots-in-scrivener-to-save-versions-of-your-projects] [belagt: https://www.literatureandlatte.com/blog/how-to-manage-compare-and-restore-snapshots-in-your-scrivener-projects]
- **Exakt arbetsflöde:** 1. Öppna scen. 2. Skapa snapshot med datum och valfri etikett, exempelvis ”före POV-byte”. 3. Fortsätt skriva. 4. Öppna snapshot och jämför med aktuell text. 5. Återställ hela texten eller kopiera utvalda stycken. [belagt: https://www.literatureandlatte.com/blog/use-snapshots-in-scrivener-to-save-versions-of-your-projects] [belagt: https://www.literatureandlatte.com/blog/how-to-manage-compare-and-restore-snapshots-in-your-scrivener-projects]
- **Vem gör det bäst:** Scrivener, med dokumentvisa snapshots som går att hantera, jämföra och återställa. [belagt: https://www.literatureandlatte.com/blog/how-to-manage-compare-and-restore-snapshots-in-your-scrivener-projects]
- **Tekniskt i PyQt6/QTextDocument:** Spara snapshot som oföränderlig kopia av serialiserad scen plus tidsstämpel/etikett; jämför plain text med diff-widget och gör återställning som ett explicit undo-säkert innehållsbyte. [resonemang]
- **Prioritet för en ensam författare:** hög – scenvis revision innebär ofta stora strykningar som författaren vill kunna ångra senare. [resonemang]

### 7. Researchmapp och referensmaterial
- **Vad den gör:** Håller research, länkar, anteckningar och bilder i projektet men skilt från texten som ska bli bok. Scrivener har Research-mapp; Dabble håller Characters och Notebook vid sidan av manus. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Exakt arbetsflöde:** 1. Skapa researchanteckning eller importera bild/källa. 2. Lägg i mapp och märk med ämne. 3. Länka anteckningen till scen via relation eller tagg. 4. Öppna materialet från scenens inspector. 5. Uteslut researchmaterial från manusvy och export. [resonemang]
- **Vem gör det bäst:** Scrivener för en direkt projektmapp avsedd för research; Dabble för tydligt separerade stödsektioner och anteckningar knutna till scener. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Tekniskt i PyQt6/QTextDocument:** Använd `node_type=research` med filbilagor och länkar; bygg en separat attachment-panel. Håll exporturval explicit och inkludera endast manusnoder. [resonemang]
- **Prioritet för en ensam författare:** medel – särskilt värdefullt för fackbok och researchintensiv roman. [resonemang]

### 8. Samlingar och sökbaserade vyer
- **Vad den gör:** Visar en tillfällig eller sparad grupp dokument utan att ändra deras plats i binder. Scrivener har vanliga Collections och sökbaserade Saved Search Collections; Ulysses Filters visar ark som matchar kriterier. [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly] [belagt: https://help.ulysses.app/en_US/getting-started/first-steps-library-editor]
- **Exakt arbetsflöde:** 1. Sök efter text eller välj metadatafilter. 2. Granska träffar. 3. Spara sökningen som vy eller lägg dokument i manuell samling. 4. Öppna träff från samlingen; binderordningen lämnas intakt. [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly] [resonemang]
- **Vem gör det bäst:** Scrivener, eftersom det stöder både manuellt kuraterade grupper och sökresultat som återanvändbara samlingar. [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly]
- **Tekniskt i PyQt6/QTextDocument:** Separat `QSortFilterProxyModel` för snabb filtrering i trädet; spara sökfråga/metadatafilter som vyobjekt. Vanlig samling sparar en lista `node_id`, inte kopior av scener. [resonemang]
- **Prioritet för en ensam författare:** medel – nyttigt när projektet växer och man vill samla alla scener med en person, plats eller arbetsstatus. [resonemang]

### 9. Sammanhängande läsvy (Scrivenings)
- **Vad den gör:** Visar flera separata dokument som ett sammanhängande manus för läsning och redigering utan att förstöra deras individuella identitet. [belagt: https://www.literatureandlatte.com/blog/scrivener-2-0-coming-soon-no-really]
- **Exakt arbetsflöde:** 1. Markera kapitel eller flera scener. 2. Välj sammanhängande manusvy. 3. Läs/redigera som en följd. 4. Ändringar routas tillbaka till respektive scen. [resonemang]
- **Vem gör det bäst:** Scrivener, som har en särskild Edit Scrivenings-vy för flera valda dokument. [belagt: https://www.literatureandlatte.com/blog/scrivener-2-0-coming-soon-no-really]
- **Tekniskt i PyQt6/QTextDocument:** För visning kan skapa ett tillfälligt sammanfogat dokument med markörer som mappar blockintervall till `node_id`. För redigering är säkrare att använda en sammansatt editor med separata underdokument eller en transaktionslogg som översätter ändringar till källdokument. [resonemang]
- **Prioritet för en ensam författare:** hög – nödvändigt för kapitelgenomläsning och kontinuitetsredigering. [resonemang]

### 10. Ordräkningsmål per scen och projekt
- **Vad den gör:** Sätter mål på dokument, grupp/kapitel eller projekt och visar framsteg. Ulysses dokumenterar mål på sheet-, group- och project-nivå; Dabble lyfter project- och daily-goals. [belagt: https://help.ulysses.app/goals] [belagt: https://www.dabblewriter.com/docs/getting-started/what-is-dabble]
- **Exakt arbetsflöde:** 1. Välj scen eller projekt. 2. Ange ordmål och eventuell gräns/deadline. 3. Följ aktuellt antal och procent. 4. Låt kapitel/projekt summera relevanta scener. 5. Uteslut synopsis, research och trash från totalsiffran. [belagt: https://help.ulysses.app/goals] [resonemang]
- **Vem gör det bäst:** Ulysses, för att samma målmodell kan kopplas till enskilt ark, grupp och projekt med progressvisning. [belagt: https://help.ulysses.app/goals]
- **Tekniskt i PyQt6/QTextDocument:** Räkna ord per scen vid textändring och cachelagra resultat; summera enligt projekthierarkin. Lagra mål som metadata och låt användaren välja om dialog, synopses eller frontmatter ingår. [resonemang]
- **Prioritet för en ensam författare:** hög – ett 100 000-ordsprojekt behöver både totalmålet och delmål som styr veckans arbete. [resonemang]

### 11. Dra-och-släpp och omordning
- **Vad den gör:** Ändrar manusordningen genom att flytta kort eller trädnoder. Scrivener flyttar dokument mellan Corkboard och Binder; Dabble kan flytta scener inom och mellan kapitel. [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Exakt arbetsflöde:** 1. Dra scen till ny plats i kortvy eller träd. 2. Visa tydlig insättningsmarkör. 3. Släpp för att uppdatera ordningsindex och eventuell förälder. 4. Ångra med vanlig undo eller återställ tidigare ordning. [resonemang]
- **Vem gör det bäst:** Dabble för uttryckligen att scener kan flyttas inom och mellan kapitel; Scrivener för att samma flytt syns i både binder och korktavla. [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story] [belagt: https://www.literatureandlatte.com/blog/organize-your-scrivener-project-with-the-corkboard]
- **Tekniskt i PyQt6/QTextDocument:** Implementera `mimeData`, `dropMimeData` och `flags` i `QAbstractItemModel`, med validering mot cykler och behållartyper. En drag/drop-transaktion uppdaterar ordning och parent atomiskt. [resonemang]
- **Prioritet för en ensam författare:** hög – omstrukturering ska vara lättare än att manuellt klippa och klistra. [resonemang]

### 12. Anteckningar och kommentarer per dokument
- **Vad den gör:** Fäster författarens noteringar eller marginalkommentarer till en scen eller ett textstycke. Ulysses stöder kommentarer, annotations och sheet-anteckningar; Dabble har anteckningar knutna till scen. [belagt: https://help.ulysses.app/en_US/the-library/567894-sheets-groups] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Exakt arbetsflöde:** 1. Öppna scen. 2. Lägg till generell scenanteckning eller markera text och kommentera. 3. Navigera kommentarerna från sidopanel. 4. Markera som löst eller behåll som arbetsnot. [resonemang]
- **Vem gör det bäst:** Ulysses, där dashboard samlar textannotationer och bifogade notes för arket; Dabble för att snabbt lägga till scenanknutna kortanteckningar. [belagt: https://help.ulysses.app/en_US/the-library/567894-sheets-groups] [belagt: https://www.dabblewriter.com/docs/planning-story-notes/how-dabble-organizes-your-story]
- **Tekniskt i PyQt6/QTextDocument:** Scenanteckning som metadata i projektmodellen; inline-kommentar som `QTextCharFormat`-markering med stabila ankare eller lagrade textpositioner som uppdateras vid edit. [resonemang]
- **Prioritet för en ensam författare:** medel – håller reda på avsikt och revisionsarbete utan att förorena prosan. [resonemang]

### 13. Projektmallar för romaner
- **Vad den gör:** Skapar projekt med färdig manusmapp, exempelkapitel, researchutrymme och förvalda statusvärden. Scrivener erbjuder projektmallar, inklusive fiktion; Dabble marknadsför manusmallar. [belagt: https://www.literatureandlatte.com/blog/how-to-write-short-story-or-essay-collections-in-scrivener] [belagt: https://www.dabblewriter.com/features-2/dabble-features]
- **Exakt arbetsflöde:** 1. Välj ”Roman” eller ”Fackbok”. 2. Ange projektnamn och eventuellt mål. 3. Skapa binderstruktur och förvalda status/etiketter. 4. Börja skriva i första scenen eller ersätt exempelstruktur. [resonemang]
- **Vem gör det bäst:** Scrivener, genom projektmallar för olika skrivprojekt och en etablerad Binder-struktur. [belagt: https://www.literatureandlatte.com/blog/how-to-write-short-story-or-essay-collections-in-scrivener]
- **Tekniskt i PyQt6/QTextDocument:** En mall är ett manifest plus valfria tomma RichText-dokument; instansiera stabila noder och standardmetadata vid nytt projekt. Scribentia har dokumentmallar, men källan beskriver dem som dokumentmallar snarare än projekt/binder-mallar. [belagt: core/templates.py:1-8] [resonemang]
- **Prioritet för en ensam författare:** medel – minskar startfriktion och visar användaren hur projektet kan struktureras. [resonemang]

### 14. Manusvarianter och alternativa strukturer
- **Vad den gör:** Låter författaren prova alternativ ordning, POV eller utkast utan att behöva duplicera allt manuellt. Scrivener dokumenterar Collections som listor av länkar till samma projektfiler, men det belägger inte i sig separata divergerande manusversioner. [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly]
- **Exakt arbetsflöde:** 1. Skapa variant från manusets struktur eller utvalda scener. 2. Flytta/ersätt scener i varianten. 3. Jämför med huvudversion. 4. Välj om ändringar ska återföras. [resonemang]
- **Vem gör det bäst:** Det går inte att belägga en tydlig variantfunktion hos de undersökta verktygen från de granskade officiella sidorna; Scrivener snapshots skyddar enstaka dokument och Collections grupperar dokument, men det är inte samma sak som grenad manusvariant. [belagt: https://www.literatureandlatte.com/blog/use-snapshots-in-scrivener-to-save-versions-of-your-projects] [belagt: https://www.literatureandlatte.com/blog/how-to-use-scriveners-collections-to-access-groups-of-files-or-search-results-quickly] [resonemang]
- **Tekniskt i PyQt6/QTextDocument:** En säker variantmodell kräver att ordningsstruktur och sceninnehåll kan förgrenas separat, exempelvis med copy-on-write scenrevisioner och variantens egen lista av `node_id`/revisioner. Det är mer omfattande än snapshots. [resonemang]
- **Prioritet för en ensam författare:** låg – värdefullt vid alternativa slut eller stora omarbetningar, men snapshots räcker i första versionen. [resonemang]

## Vad jag inte kunde belägga

- **NovelCrafter** belägger akter, kapitel och scener, scensammanfattningar, grid-/matrix-/outline-vyer, etiketter, Codex för karaktärer/platser och historik för sceninnehåll och sammanfattningar. [belagt: https://www.novelcrafter.com/help/docs/plan/plan-views] [belagt: https://www.novelcrafter.com/help/docs/codex/the-codex] [belagt: https://docs.novelcrafter.com/en/articles/8677729-revision-history/]
- **Manuskript**s officiella projekt-README belägger Linux-stöd, outline/indexkort, redigering och omordning av kapitel/scener samt fiction- och nonfiction-mallar; detaljer om scenvisa snapshots och sökbaserade vyer kunde jag inte belägga där. [belagt: https://github.com/olivierkes/manuskript/blob/develop/README.md] [resonemang]
- Jag kunde inte belägga att **Atticus** erbjuder en binder med scener, korkkort, statusflöde eller scenvisa snapshots; den officiella Quick Start-sidan visar skriv-/formateringsflöde, kapitel och anteckningar men inte dessa specifika funktioner. [belagt: https://www.atticus.io/quick-start-guide/] [resonemang]
- **Vellum**-källan belägger struktur med delar och kapitel för bokproduktion, men inte en scenbaserad binder eller planeringstavla. [belagt: https://help.vellum.pub/elements/parts/] [resonemang]
- Jag kunde inte belägga en komplett, versionsmärkt jämförelse av alla sju produkters nuvarande stöd för snapshots, sökbaserade vyer, researchbilagor och parallella manusvarianter. Produktdokumentation kan skilja mellan plattformar och abonnemang. [resonemang]
- Scribentia-läsningen visar redigering av ett dokument i taget, rubrikbaserad outline, dokumentordräkning, dokumentmallar och ett separat anteckningsvalv; den visar inte ett projektträd, scenobjekt, Scrivenings eller dokumentvisa snapshots. [belagt: ui/main_window.py:641-670] [belagt: core/document_stats.py:20-34] [belagt: ui/sidebar_inspector.py:176-194] [belagt: core/vault.py:104-116] [resonemang]
