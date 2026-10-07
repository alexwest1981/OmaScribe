# AI-nativa författarverktyg

## Sammanfattning

- Romanverktyg gör berättelsekontext synlig och redigerbar: story bible/Codex, scener, scensammanfattningar och valda manusdelar används som underlag för AI:n. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://www.novelcrafter.com/help/docs/codex/the-codex]
- De mest användbara AI-flödena är avgränsade: arbeta på markerad text, valt kapitel eller hela projektet, och visa förslag som författaren kan granska. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://www.squibler.io/]
- NovelCrafter och Sudowrite har tydligast stöd för lång fiktion; Lex och Type visar mönster för stil, sparade prompts, feedback och redigering inne i dokumentet. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface] [belagt: https://lex.page/about] [belagt: https://blog.type.ai/post/type-ai-overview]
- Konsekvens och röst kan inte lämnas åt modellen ensam: forskning beskriver långdistansproblem, glömda berättelsefakta och begränsad stilåtergivning. [belagt: https://onlinelibrary.wiley.com/doi/full/10.1155/hbe2/8695447]
- För en ensam författare bör AI:n vara en redigerbar samtalspartner med tydlig kontext, historik och valbara ändringar; det minskar risken att en plausibel men felaktig generation tyst ersätter manus. [resonemang]

## Bordet: vad som är minimum i kategorin

- Ett projekt behöver hålla manus, instruktioner och referensmaterial ihop så AI-funktioner kan använda samma berättelsebakgrund. Claude Projects och ChatGPT Projects beskriver båda projektinstruktioner och uppladdade källor. [belagt: https://support.anthropic.com/en/articles/9517075-what-are-projects] [belagt: https://help.openai.com/en/articles/10169521-projects-in-chatgpt]
- För romaner är strukturerade berättelseposter och scener ett grundmönster: Sudowrite Story Bible och NovelCrafter Codex lagrar karaktärer, platser, objekt och andra berättelsedetaljer. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://www.novelcrafter.com/help/docs/codex/the-codex]
- Skrivhjälp måste omfatta både idéarbete, generering och revision. Sudowrite listar Write, Rewrite, Describe, Brainstorm, Expand och Feedback; Type listar generering, redigering och Reviews. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://blog.type.ai/post/type-ai-overview]
- Författaren behöver kunna välja kontext och modell; NovelCrafter låter användaren lägga till specifika scener och Codex-poster i chatten, och Lex dokumenterar modellval. [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes] [belagt: https://lex.page/about]
- Historik och acceptans är centrala skyddsräcken: Lex har Rewind och namngivna versioner; Squibler beskriver accept/reject/refine för förslag. [belagt: https://lex.page/about] [belagt: https://www.squibler.io/]

## Funktionskatalog

### 1. Story bible / Codex
- **Vad den gör:** Samlar kanoniska fakta om karaktärer, platser, objekt, fraktioner, värld och andra berättelseelement och gör dem möjliga att återanvända som AI-kontext. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://www.novelcrafter.com/help/docs/codex/the-codex]
- **Exakt arbetsflöde:** 1) Skapa projekt. 2) Lägg till posttyp och namn, exempelvis karaktär eller plats. 3) Fyll i fakta och relationer. 4) Koppla relevanta poster till scener eller välj dem som kontext när du frågar AI:n. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface] [resonemang]
- **Vem gör det bäst:** Sudowrite gör Story Bible till källa till sanning för både författare och AI; NovelCrafter har Codex-poster som kan kopplas till scener. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface]
- **Tekniskt i Python/Qt:** Modellera entiteter, typer, attribut, alias och relationer i SQLite; redigera dem i en dockad panel och bifoga explicita ID:n som kontext. [resonemang]
- **Prioritet för en ensam författare:** hög — förebygger att centrala fakta behöver jagas manuellt mellan kapitel. [resonemang]

### 2. Scener och scenkopplingar
- **Vad den gör:** Delar upp manusets plan i scener, med sammanfattning, POV och kopplade Codex-poster. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface]
- **Exakt arbetsflöde:** 1) Skapa kapitel/scener i planvyn. 2) Lägg till scensammanfattning och POV. 3) Tilldela entiteter som förekommer. 4) Skriv eller öppna scenen och skicka scenen med dess metadata till AI:n. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface] [resonemang]
- **Vem gör det bäst:** NovelCrafter visar scenåtgärder, sammanfattning, POV, ordantal och tilldelade Codex-poster i skrivgränssnittet. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface]
- **Tekniskt i Python/Qt:** Lagra scener som dokumentankare med ordningspositioner och metadata; visa scenlista i QDockWidget och använd QTextCursor/positionsintervall för koppling till dokumentet. [resonemang]
- **Prioritet för en ensam författare:** hög — är gränssnittet mellan plan, manus och projektminne. [resonemang]

### 3. Manusfrågor och RAG
- **Vad den gör:** Svarar på frågor med stöd av manus och referensmaterial, gärna med träffar som visar var svaret finns. NovelCrafter låter användaren välja scener, kapitel, akter och snippets som chattkontext; Claude Projects använder projektkunskap och RAG när kunskapsbasen blir stor. [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes] [belagt: https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects]
- **Exakt arbetsflöde:** 1) Välj hela projektet eller ett avgränsat kapitel/scener. 2) Fråga exempelvis ”Vem avslöjade hemligheten och var?”. 3) Visa svar tillsammans med källstycken och kapitelrubriker. 4) Öppna källstället för kontroll. [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes] [resonemang]
- **Vem gör det bäst:** NovelCrafter har synligt val av kapitel/scener i chattkontext; Anthropic dokumenterar automatisk RAG för projektkunskap över kontextgränsen. [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes] [belagt: https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects]
- **Tekniskt i Python/Qt:** Chunk:a per scen och stycke, skapa lokal sökindexering och returnera citat med dokumentposition. Håll retrieval separat från sammanfattad kontext så användaren kan kontrollera träffarna. [resonemang]
- **Prioritet för en ensam författare:** hög — besvarar ”var hände det?” och ”vad bestämde vi?” utan att läsa hela manuset. [resonemang]

### 4. Chatta med helt manus eller valt kapitel
- **Vad den gör:** Ger ett samtalsgränssnitt för feedback, idéer och ändringar baserat på valt textomfång. Sudowrite Chat beskrivs som berättelsemedveten och projektövergripande; NovelCrafter stöder selektiv kontext. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes]
- **Exakt arbetsflöde:** 1) Öppna chattpanelen. 2) Välj hela dokumentet, kapitel eller markerade scener. 3) Fråga eller be om analys. 4) Läs svar och följ källhänvisningarna tillbaka till manus. [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes] [resonemang]
- **Vem gör det bäst:** Sudowrite täcker hela projektet från en konversation; NovelCrafter dokumenterar precis urval av kapitel, scener, akter och snippets. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes]
- **Tekniskt i Python/Qt:** Bygg en panel med kontextchip (projekt/kapitel/urval), historik per projekt och möjlighet att hoppa till källpositioner. [resonemang]
- **Prioritet för en ensam författare:** hög — samma panel kan hantera både manusfrågor och redaktörsdialog. [resonemang]

### 5. Recap per scen och kapitel
- **Vad den gör:** Lagrar kompakta sammanfattningar av scener/kapitel för planering och som mindre kontext än fulltext. NovelCrafter visar redigering av scenens summary; NovelAI erbjuder Memory och Author’s Note som kontextfält. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface] [belagt: https://docs.novelai.net/en/text/lorebook/]
- **Exakt arbetsflöde:** 1) När scenen är klar, generera en sammanfattning. 2) Granska och rätta namn, händelser och öppna trådar. 3) Spara sammanfattningen på scenen. 4) Välj recaps vid senare planering eller AI-frågor. [resonemang]
- **Vem gör det bäst:** NovelCrafter har sammanfattningar direkt i scenens planeringsdata; NovelAI låter användaren styra vilken memory och nylig story-text som följer med i generering. [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface] [belagt: https://docs.novelai.net/en/text/lorebook/]
- **Tekniskt i Python/Qt:** Kör sammanfattning först på scenen, spara som redigerbar metadata med versionsdatum; undvik automatisk uppdatering utan att visa diff eftersom summering kan utelämna fakta. [resonemang]
- **Prioritet för en ensam författare:** hög — ger billigare och mer styrbar kontext för långt manus. [resonemang]

### 6. Kapitelplan, disposition och synopsis
- **Vad den gör:** Hjälper till att skapa och omstrukturera berättelsens plan och synopsis. Squibler erbjuder outline generation och beskriver den som en flexibel blueprint; Sudowrite Story Bible innehåller synopsis och outline-steg. [belagt: https://www.squibler.io/] [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC]
- **Exakt arbetsflöde:** 1) Ange premiss, genre, längd och begränsningar. 2) Be om synopsis eller kapitelplan. 3) Redigera ordning och beats. 4) Expandera valda planpunkter till scener. [belagt: https://www.squibler.io/] [resonemang]
- **Vem gör det bäst:** Squibler beskriver genererad outline som möjlig att expandera, omorganisera och omforma; Sudowrite binder outline till Story Bible och scener. [belagt: https://www.squibler.io/] [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC]
- **Tekniskt i Python/Qt:** Be modellen lämna strukturerad JSON med kapitel, syfte, konflikt, vändpunkt och resultat; visa i trädvy och låt författaren flytta och redigera noder. [resonemang]
- **Prioritet för en ensam författare:** medel — användbart vid start och omstrukturering, men planens värde beror på författarens kontroll. [resonemang]

### 7. Brainstorm: konflikt, twist, karaktärsbåge
- **Vad den gör:** Tar fram alternativa storyidéer eller utvecklingsvägar. Sudowrite listar Brainstorm; Lex lyfter idébrainstorming; Squibler marknadsför outline- och berättelseutveckling. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://lex.page/] [belagt: https://www.squibler.io/]
- **Exakt arbetsflöde:** 1) Markera scen, karaktär eller konflikt. 2) Välj frågetyp som twist, hinder eller båge. 3) Ange vad som inte får ändras. 4) Jämför flera alternativ och spara valda idéer i plan eller Codex. [resonemang]
- **Vem gör det bäst:** Sudowrite har en namngiven Brainstorm-funktion; NovelCrafter kan ge chatten specifik Codex- och scenkontext. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://www.novelcrafter.com/help/faq/chat/chat-multiple-scenes]
- **Tekniskt i Python/Qt:** Fördefinierade prompts med kontextvariabler och resultat i separata kort; spara valt alternativ som anteckning utan att ändra manus. [resonemang]
- **Prioritet för en ensam författare:** medel — värdefullt vid låsning och planering, mindre viktigt i daglig redigering. [resonemang]

### 8. Skrivhjälp på markerad text
- **Vad den gör:** Utför fokuserade operationer som beskriva, skriva om, expandera, korta eller fortsätta text. Sudowrite listar dessa lägen och Type beskriver bland annat Continue och Shorten. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://blog.type.ai/post/type-ai-overview]
- **Exakt arbetsflöde:** 1) Markera passage. 2) Välj operation och skriv eventuell instruktion. 3) Granska genererad variant. 4) Ersätt, infoga efter eller kopiera; behåll originalet i historiken. [belagt: https://docs.novelai.net/en/text/editor/] [resonemang]
- **Vem gör det bäst:** Sudowrite täcker flera prosaspecifika lägen (Describe, Rewrite, Expand); Type placerar AI-redigering och generering inne i blockbaserat dokument. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://blog.type.ai/post/type-ai-overview]
- **Tekniskt i Python/Qt:** Skicka markerad text separat från omkringliggande kontext; rendera förslag i en dialog med diff och knappar för ersätt/infoga/avbryt. [resonemang]
- **Prioritet för en ensam författare:** hög — tydlig nytta med begränsad risk när ändringar är förhandsgranskade. [resonemang]

### 9. Prosakritik och redaktörspass
- **Vad den gör:** Ger reaktioner, feedback eller linjeförslag på befintlig text. Sudowrite har Feedback; Lex erbjuder AI Feedback och Checks; Type har Reviews för hela dokumentet. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://lex.page/] [belagt: https://blog.type.ai/post/type-ai-overview]
- **Exakt arbetsflöde:** 1) Välj textomfång och granskningsmål, exempelvis rytm eller begriplighet. 2) Kör granskning. 3) Läs varje kommentar med hänvisning till passage. 4) Acceptera, avvisa eller be om alternativ. [belagt: https://www.squibler.io/] [resonemang]
- **Vem gör det bäst:** Lex Checks visar linjeförslag markerade i dokumentet; Sudowrite erbjuder Feedback specifikt för berättande prosa. [belagt: https://lex.page/about] [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features]
- **Tekniskt i Python/Qt:** Be om strukturerad lista med ankare, problem, motivering och förslag; använd QTextEdit extra selections eller separat kommentarspanel och kräv manuellt godkännande. [resonemang]
- **Prioritet för en ensam författare:** hög — extern redaktörsrespons på begäran utan att ersätta författarens kontroll. [resonemang]

### 10. Röstbevarande och stilprofil
- **Vad den gör:** Försöker vägleda AI-utkast och redigering så de följer exempel eller en uttrycklig stilguide. Sudowrite har Match My Style; Lex har Style Guides; Type kan använda tidigare text som mall. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://lex.page/about] [belagt: https://blog.type.ai/post/type-ai-overview]
- **Exakt arbetsflöde:** 1) Välj egna provtexter. 2) Skapa redigerbar stilprofil med exempel och preferenser. 3) Välj profilen för ett skriv- eller redigeringspass. 4) Jämför resultat med original och justera profilen. [resonemang]
- **Vem gör det bäst:** Lex dokumenterar stilguider för att träna assistenten på användarens röst; Sudowrite erbjuder Match My Style i Story Bible. [belagt: https://lex.page/about] [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC]
- **Tekniskt i Python/Qt:** Bygg profilen av användarredigerade regler plus valda exempelstycken, som valbar promptkontext; undvik påståendet att systemet exakt kan återskapa en röst. [resonemang]
- **Prioritet för en ensam författare:** medel — hjälper vid redigering men kan inte garantera trogen stil. [resonemang]

### 11. Promptbibliotek och återanvändbara instruktioner
- **Vad den gör:** Sparar arbetsinstruktioner och granskningsmallar för upprepad användning. Lex har sparade prompts, prompt library och prompt builder; NovelCrafter stöder egna prompts och chatassistenter. [belagt: https://lex.page/about] [belagt: https://www.novelcrafter.com/help/docs/prompts/prompt-types]
- **Exakt arbetsflöde:** 1) Skapa prompt med namn och instruktion. 2) Lägg in platshållare för markerad text, kapitel och genre. 3) Kör mot valt underlag. 4) Ändra och spara en ny version när arbetsflödet förbättras. [belagt: https://www.novelcrafter.com/help/docs/prompts/prompt-types] [resonemang]
- **Vem gör det bäst:** NovelCrafter stöder skräddarsydda prompts och assistenter som använder tillförd Codex-kontext; Lex kombinerar promptbibliotek med egna sparade prompts. [belagt: https://www.novelcrafter.com/help/docs/prompts/prompt-types] [belagt: https://lex.page/about]
- **Tekniskt i Python/Qt:** Lagra promptmallar lokalt i projekt/global config, med versionsfält och tydlig visning av expanderad prompt före sändning. [resonemang]
- **Prioritet för en ensam författare:** medel — ger konsekventa arbetslägen och minskar repetitiv promptskrivning. [resonemang]

### 12. Modellval och kostnad per uppgift
- **Vad den gör:** Låter användaren välja modell för vissa uppgifter och se användning eller kostnadsestimat. Lex dokumenterar guide för modellval; Sudowrite listar prose modes och models och visar uppskattningar för generering. [belagt: https://lex.page/about] [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://feedback.sudowrite.com/changelog/features-and-fixes]
- **Exakt arbetsflöde:** 1) Välj uppgift, exempelvis brainstorming eller språkgranskning. 2) Välj konfigurerad modell. 3) Visa uppskattad token-/kostnadsåtgång före körning. 4) Visa faktisk användning efter anrop om leverantören ger data. [resonemang]
- **Vem gör det bäst:** Sudowrite dokumenterar modell/prosa-lägen och kredituppskattningar; Lex har en särskild modellvalsresurs. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://lex.page/about]
- **Tekniskt i Python/Qt:** Separera modellinställning per uppgiftsprofil, logga prompt-/completion-token när API tillhandahåller dem och visa osäker uppskattning där prisdata saknas. [resonemang]
- **Prioritet för en ensam författare:** medel — viktigt vid API-nyckel och varierande modellpriser, men sekundärt mot kontext och granskningsflöde. [resonemang]

### 13. Kontinuitet och aktiverat berättelseminne
- **Vad den gör:** För in relevanta fakta när texten nämner nyckelord eller när användaren väljer berättelseposter. NovelAI Lorebook aktiverar poster via nycklar i nylig text; NovelCrafter låter scener använda tilldelade Codex-poster. [belagt: https://docs.novelai.net/en/text/lorebook/] [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface]
- **Exakt arbetsflöde:** 1) Skapa fakta/post med namn och nyckelord. 2) Ange om den alltid ska gälla eller aktiveras vid omnämnande. 3) Skriv scenen. 4) Granska vilken kontext som skickades när generering avviker. [belagt: https://docs.novelai.net/en/text/lorebook/] [resonemang]
- **Vem gör det bäst:** NovelAI har detaljerade nyckel-, sökintervall- och placeringsregler; NovelCrafter använder scenkopplade Codex-poster. [belagt: https://docs.novelai.net/en/text/lorebook/] [belagt: https://www.novelcrafter.com/help/docs/write/the-write-interface]
- **Tekniskt i Python/Qt:** Börja med explicit scenkoppling och indexsökning; visa aktiverade poster i en ”AI-kontext”-inspektör. Regex och automatisk cascading kan vänta. [resonemang]
- **Prioritet för en ensam författare:** hög — konsekvensdata hjälper bara om de faktiskt når rätt anrop. [resonemang]

### 14. AI-kommentarer i marginalen
- **Vad den gör:** Lägger förslag på en plats i dokumentet så författaren kan utvärdera dem utan att den ursprungliga prosan omedelbart byts ut. Lex Checks markerar linjeförslag i dokumentet; Type Reviews visas i sidopanel. [belagt: https://lex.page/about] [belagt: https://blog.type.ai/post/type-ai-overview]
- **Exakt arbetsflöde:** 1) Kör kontroll på dokument eller urval. 2) Visa markering och kommentar kopplad till text. 3) Acceptera/avvisa eller öppna omskrivningsdialog. 4) Behåll original om inget accepteras. [belagt: https://www.squibler.io/] [resonemang]
- **Vem gör det bäst:** Lex Checks ger linjenära markeringar; Squibler beskriver accept, reject och refine för AI-förslag. [belagt: https://lex.page/about] [belagt: https://www.squibler.io/]
- **Tekniskt i Python/Qt:** Använd QTextEdit extra selections för markeringar och en separat lista med stabila textankare; skapa undo-kommandon för varje godkänd ändring. [resonemang]
- **Prioritet för en ensam författare:** hög — granskningsbarhet är viktigare än att AI ändrar snabbt. [resonemang]

### 15. Versionshistorik och acceptans per stycke
- **Vad den gör:** Gör det möjligt att återställa tidigare text och att godkänna AI-förslag selektivt. Lex erbjuder Rewind och namngivna versioner; Squibler anger accept/reject/refine. [belagt: https://lex.page/about] [belagt: https://www.squibler.io/]
- **Exakt arbetsflöde:** 1) Spara automatiskt före AI-ändring. 2) Visa ändringsförslag per stycke. 3) Acceptera eller avvisa individuellt. 4) Återställ hela dokumentet till namngiven punkt vid behov. [resonemang]
- **Vem gör det bäst:** Lex dokumenterar både versionspunkter och Rewind; Squibler beskriver explicit författarens godkännandekontroll över förslag. [belagt: https://lex.page/about] [belagt: https://www.squibler.io/]
- **Tekniskt i Python/Qt:** Spara dokument-snapshots och diffs lokalt; utför accepterade ändringar som separata undo-stack-kommandon så Qt-redo fungerar förutsägbart. [resonemang]
- **Prioritet för en ensam författare:** hög — ger trygghet att prova större AI-redigeringar. [resonemang]

### 16. Flerboks-seriebibel och återanvändning
- **Vad den gör:** Återanvänder värld och berättelsefakta mellan böcker i samma serie. Sudowrite listar Series Support; dess Story Bible är projektanknuten och fungerar som källa till sanning. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features] [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC]
- **Exakt arbetsflöde:** 1) Skapa serie. 2) Lägg gemensamma entiteter i seriebibeln. 3) Skapa bokprojekt kopplat till serien. 4) Lägg bokspecifika fakta lokalt och ange vilka serieposter som gäller. [resonemang]
- **Vem gör det bäst:** Sudowrite är den granskade produkten i urvalet som explicit listar Series Support. [belagt: https://feedback.sudowrite.com/en/help/collections/5442133-features]
- **Tekniskt i Python/Qt:** Lägg till valfri serierot med delade entiteter och bokprojektspecifika överlagringar; visa källa och skrivskydda gemensamma poster om de ändras från en bok. [resonemang]
- **Prioritet för en ensam författare:** låg till medel — stor nytta för serier, liten för en fristående bok. [resonemang]

### 17. Genre, åldersgräns, röst och innehållsgränser
- **Vad den gör:** Låter användaren ange stil och berättelsekrav så generering håller sig inom önskad genre eller ton. Sudowrite har Genre och Style-fält i Story Bible; NovelAI har Memory/Author’s Note för kontext. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://docs.novelai.net/en/text/lorebook/]
- **Exakt arbetsflöde:** 1) Ange genre, målgrupp/åldersnivå och önskad röst. 2) Lägg till uttryckliga ”måste” och ”undvik”. 3) Inkludera profilen för relevant AI-uppgift. 4) Granska resultatet mot reglerna. [resonemang]
- **Vem gör det bäst:** Sudowrite integrerar genre och stil i sin Story Bible; NovelAI exponerar author’s note och memory som separat styrbar kontext. [belagt: https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC] [belagt: https://docs.novelai.net/en/text/lorebook/]
- **Tekniskt i Python/Qt:** En enkel projektprofil med valbara fält, alltid synlig och redigerbar promptförhandsvisning; behandla regler som vägledning, inte garanti. [resonemang]
- **Prioritet för en ensam författare:** medel — särskilt användbart vid genrearbete och återkommande tonalitetskrav. [resonemang]

### 18. Projektinstruktioner i generella assistenter
- **Vad den gör:** Claude Projects och ChatGPT Projects binder ihop konversationer, filer och instruktioner som delas inom ett projekt. [belagt: https://support.anthropic.com/en/articles/9517075-what-are-projects] [belagt: https://help.openai.com/en/articles/10169521-projects-in-chatgpt]
- **Exakt arbetsflöde:** 1) Skapa projekt. 2) Lägg till instruktioner och referensfiler. 3) Samla relaterade chattar i projektet. 4) Fråga om uppladdat material. ChatGPT Projects kan även använda projektkällor och chattar som kontext. [belagt: https://support.anthropic.com/en/articles/9517075-what-are-projects] [belagt: https://help.openai.com/en/articles/10169521-projects-in-chatgpt]
- **Vem gör det bäst:** Claude dokumenterar kunskapsbas plus projektinstruktioner och RAG; ChatGPT Projects samlar instruktioner, filer och projektchattar. [belagt: https://support.anthropic.com/en/articles/9517075-what-are-projects] [belagt: https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects] [belagt: https://help.openai.com/en/articles/10169521-projects-in-chatgpt]
- **Tekniskt i Python/Qt:** Samma princip går att implementera lokalt: per-projekt instruktioner, referensmaterial och chatthistorik, med valbar retrieval och transparent kontext. [resonemang]
- **Prioritet för en ensam författare:** hög — praktisk bas även innan full romanplanering finns. [resonemang]

### 19. Inworld och Storyteller-verktyg
- **Vad den gör:** Inworlds primära utvecklardokumentation beskriver TTS, STT, realtime tal och en LLM-router. Den dokumenterar inte i sig ett komplett manusverktyg med story bible. [belagt: https://docs.inworld.ai/introduction]
- **Exakt arbetsflöde:** För den dokumenterade Inworld-produkten: 1) Integrera API för vald tal- eller modellfunktion. 2) Skicka text/ljud enligt respektive API. 3) Ta emot genererad output. Något särskilt arbetsflöde för författare kunde inte verifieras. [belagt: https://docs.inworld.ai/introduction] [resonemang]
- **Vem gör det bäst:** Inworld är belagt som infrastruktur för röst och modellrouting; Storyteller som forskningsramverk beskriver en storyline-modul och narrative entity knowledge graph, men är en forskningsartikel och inte belägg för en kommersiell författarprodukt. [belagt: https://docs.inworld.ai/introduction] [belagt: https://arxiv.org/abs/2506.02347]
- **Tekniskt i Python/Qt:** Behandla tal som ett separat gränssnitt till samma projektkontext; koppla transkription till anteckningar eller dialogutkast och kräv redigering innan manusinfogning. [resonemang]
- **Prioritet för en ensam författare:** låg — röst kan stödja idéfångst, men ger inte de kärnfunktioner för kontinuitet och revision som långprosa kräver. [resonemang]

## Kända fallgropar

- **Hallucinerade eller bortglömda detaljer:** En litteraturöversikt rapporterar hallucinationer, missade viktiga detaljer, svag sammanfattningstrohet och att små inkonsekvenser kan ackumuleras i långa berättelser. Designval: visa källpassager, låt författaren korrigera recap och gör inte AI-genererade fakta till kanon automatiskt. [belagt: https://onlinelibrary.wiley.com/doi/full/10.1155/hbe2/8695447] [resonemang]
- **Röstförlust:** Samma översikt tar upp begränsad förmåga att återge författares stil. En stilprofil bör därför vara stöd och jämförelseunderlag, inte ett löfte om att AI:n ”skriver som du”. [belagt: https://onlinelibrary.wiley.com/doi/full/10.1155/hbe2/8695447] [resonemang]
- **Överskrivning och svårgranskade ändringar:** AI-funktioner som ersätter text direkt gör det svårt att se var förslag börjar och original slutar. Linjemarkeringar, diff, undo och versionshistorik är konkreta designskydd som återfinns i Lex och NovelAI. [belagt: https://lex.page/about] [belagt: https://docs.novelai.net/en/text/editor/]
- **Träningsdata och juridisk osäkerhet:** Authors Guild och författare har drivit upphovsrättstalan mot OpenAI och Microsoft och hävdar otillåten kopiering av böcker för träning; det är partsanklagelser och pågående process, inte i sig en slutlig dom i sak. [belagt: https://authorsguild.org/news/plaintiffs-file-motion-for-summary-judgment-v-openai-and-microsoft/] En Anthropic-målsättning resulterade i förlikning, och en domstol skilde mellan träning på lagligt inköpta böcker och kopior hämtade från piratbibliotek. [belagt: https://www.capradio.org/news/npr/story?storyid=nx-s1-5529404]
- **Kopiera inte en levande författares stil som marknadsfunktion:** Röstprofil bör baseras på användarens egna texter eller uttryckliga tillstånd; Authors Guild förespråkar uttryckligt samtycke för AI-användning av författares verk. [belagt: https://authorsguild.org/advocacy/artificial-intelligence/faq/] [resonemang]
- **För mycket kontext ger inte automatiskt bättre minne:** RAG och selektiv kontext är etablerade produktmönster, men retrieval kan missa eller välja fel avsnitt. Visa därför vilka delar som faktiskt skickas med varje anrop. [belagt: https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects] [resonemang]

## Vad jag inte kunde belägga

- Jag kunde inte verifiera en aktuell, officiell Inworld-produkt som är ett komplett AI-nativt romanverktyg med manus, story bible och kapitelplan; den officiella dokumentationen jag hittade handlar om utvecklar-API:er för tal och LLM-routing. [belagt: https://docs.inworld.ai/introduction]
- ”Storyteller” förekommer som forskningsnamn på narrativa system och generella produktbegrepp; det gick inte att knyta användarens formulering till en specifik kommersiell produkt utan att gissa. [belagt: https://arxiv.org/abs/2506.02347] [resonemang]
- Jag kunde inte belägga att någon produkt automatiskt upptäcker alla namn-, tidslinje- och faktamotsägelser med hög tillförlitlighet; produktbeskrivningar om kontinuitet är leverantörspåståenden och forskningsöversikten anger kvarstående långdistansproblem. [belagt: https://www.squibler.io/] [belagt: https://onlinelibrary.wiley.com/doi/full/10.1155/hbe2/8695447]
- Jag kunde inte styrka att någon ”skriv som jag”-funktion bevarar en individuell litterär röst pålitligt över en hel roman. [belagt: https://onlinelibrary.wiley.com/doi/full/10.1155/hbe2/8695447]
- Jag kunde inte verifiera exakta kostnader per anrop för samtliga jämförda produkter; modellutbud, krediter och priser ändras och flera funktioner kräver konto. [resonemang]
