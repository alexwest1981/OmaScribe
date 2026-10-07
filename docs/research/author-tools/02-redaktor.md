# Redaktörskapet

## Sammanfattning

- **Spårade ändringar och beslut per ändring är kategorins redaktionella kärna:** Word och ONLYOFFICE dokumenterar navigering mellan revisioner och acceptera/avvisa enskilt; Google Docs har ett motsvarande föreslå-läge. [belagt: https://support.microsoft.com/en-us/word/training/track-changes-in-word] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/Review.aspx] [belagt: https://support.google.com/docs/answer/6033474?hl=en-8]
- **Långa verk behöver strukturell navigering och uppdaterbara register:** innehållsförteckning, rubriknavigator, korsreferenser, bildtexter och figurlistor bygger på semantiska stilar/fält snarare än manuellt skriven sidtext. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx] [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/references.html] [belagt: https://support.microsoft.com/en-gb/word/insert-a-table-of-figures]
- **Versionshistorik och jämförelse är särskilt värdefulla för den ensamme författaren:** de gör det möjligt att återställa ett manus och granska ändringar efter stora omskrivningar utan att lita på minnet. [belagt: https://support.google.com/docs/answer/190843?hl=en] [resonemang]
- **Fotnoter, slutnoter, sektioner, sidhuvud/sidfot, spalter och avstavning hör till den tryckfärdiga verktygslådan:** Typora har avsiktligt en annan tyngdpunkt som Markdown-redigerare, medan ordbehandlarna beskriver dessa layout- och referensfunktioner. [belagt: https://support.typora.io/Markdown-Reference/] [belagt: https://support.apple.com/guide/pages/welcome/mac]
- **OmaScribe bör börja med väl avgränsade funktioner som stöder manusets struktur och revision:** dokumenterad kod använder `QTextDocument`, `QTextEdit`, `QTextCursor` och egna roller för textblock; detta ger en rimlig grund men ersätter inte modellering av revisioner, fält och sidsektioner. [belagt: ../core/richtext.py:17] [belagt: ../core/richtext.py:53] [belagt: ../ui/editor_view.py:67] [resonemang]

## Bordet: vad som är minimum i kategorin

- **Redaktionell kontroll:** kunna visa ändringar och acceptera/avvisa enskilt, samt lämna kommentarer knutna till text och lösa trådar. Word och ONLYOFFICE visar dessa separata granskningsflöden. [belagt: https://support.microsoft.com/en-us/word/give-and-receive-feedback-in-word] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/Review.aspx]
- **Struktur för långa dokument:** rubrikstilar, snabbnavigering, uppdaterbar klickbar innehållsförteckning, fotnoter/slutnoter och korsreferenser. [belagt: https://support.google.com/a/users/answer/9299931?hl=en] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/ReferencesTab.aspx]
- **Pålitlig redigering över tid:** lokal versionshistorik eller namngivna ögonblicksbilder samt dokumentjämförelse som lämnar originalen intakta. [belagt: https://support.google.com/docs/answer/190843?hl=en] [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Manusberedskap:** automatiskt numrerade bildtexter och register, konsekvent typografi via stilar och sidlayout per avsnitt. [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/captions.html] [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c]
- **Språk- och korrekturverktyg:** språk per stycke/markering, stavning, egen ordlista, sök/ersätt med mönster och snabb åtkomst till rubriker/objekt. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/search_regexp.html] [resonemang]

## Funktionskatalog

### Spårade ändringar och acceptera/avvisa
- **Vad den gör:** Bevarar infogningar, borttagningar och eventuellt formateringsändringar som redaktionella förslag tills författaren godkänner eller avslår dem. Word och ONLYOFFICE stöder enskilt beslut och beslut i följd. [belagt: https://support.microsoft.com/en-us/word/training/track-changes-in-word] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/Review.aspx]
- **Exakt arbetsflöde:** 1. Slå på Spåra ändringar. 2. Redigera texten. 3. Gå till nästa/föregående markering. 4. Granska förslag och författare/tid. 5. Acceptera eller avvisa den valda ändringen; upprepa eller använd uttryckligt massbeslut. [belagt: https://support.microsoft.com/en-us/word/training/track-changes-in-word]
- **Vem gör det bäst:** **Word** — dokumenterar tydligt navigering, olika markup-vyer och beslut per ändring; **ONLYOFFICE** erbjuder motsvarande kortväg från ändringsballong och granskningsflik. [belagt: https://support.microsoft.com/en-us/word/training/track-changes-in-word] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/Review.aspx]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Lagra revisioner som stabila operationer (ankare/range, gammal och ny text, typ, tid, författare), inte enbart färgformat i `QTextDocument`. Rendera ändringsmarkeringar via extra format/highlight; vid accept/reject tillämpa operationen och uppdatera senare ankare. Använd `QTextCursor` för kontrollerad textändring, med undo-integrering och serialisering i dokumentformat.
- **Prioritet för en ensam författare:** hög — gör AI-förslag, självredigering och extern feedback granskningsbara.

### Kommentarer i marginalen med tråd och löst
- **Vad den gör:** Fäster en notering vid markerad text, låter svar samlas i en tråd och låter tråden markeras löst utan att raderas. Word beskriver svar och lösning; ONLYOFFICE visar kommentarer som marginalballonger/panelposter. [belagt: https://support.microsoft.com/en-us/word/give-and-receive-feedback-in-word] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/Commenting.aspx]
- **Exakt arbetsflöde:** 1. Markera text eller placera markören. 2. Välj Ny kommentar. 3. Skriv frågan/noteringen. 4. Lägg till svar i tråden. 5. Markera tråden som löst; återöppna vid behov. [belagt: https://support.microsoft.com/en-us/word/give-and-receive-feedback-in-word]
- **Vem gör det bäst:** **Word** — källan anger både anknytning till vald text, trådsvar och statusen löst. [belagt: https://support.microsoft.com/en-us/word/give-and-receive-feedback-in-word]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Lagra kommentar som separat objekt med stabila start/slutankare, citatkontext, tråd-ID, svar och status. Markera spann med extra selections och visa en dockad marginalpanel; ankare behöver återankras när text före dem ändras.
- **Prioritet för en ensam författare:** hög — användbart för självrevision, redaktörsfeedback och minnesanteckningar.

### Jämför dokument och slå ihop versioner
- **Vad den gör:** Jämför två manus och visar skillnader som revisioner i ett resultatdokument; sammanslagning importerar ändringar från en kopia. Word beskriver jämförelse i ett tredje dokument och LibreOffice har både Compare och Merge. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option] [belagt: https://help.libreoffice.org/latest/ug/text/swriter/track_changes_toolbar.html?DbPAR=BASE&System=WIN]
- **Exakt arbetsflöde:** 1. Välj originalfil. 2. Välj reviderad fil. 3. Välj om text och formatering ska jämföras och detaljnivå. 4. Skapa diff som nya spårade ändringar. 5. Granska och acceptera/avvisa i resultatet; originalen förblir oförändrade. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Vem gör det bäst:** **Word** — erbjuder explicit jämförelsedokument och alternativ för text, formatering samt tecken-/ordnivå. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Extrahera strukturerad text och objekt från båda dokumenten, kör sekvensdiff i block och därefter inom ändrade block, skapa revisioner i en ny kopia. Bevara originalformat och hantera tabeller/bilder separat; naiv HTML-diff riskerar falska ändringar.
- **Prioritet för en ensam författare:** hög — särskilt viktigt efter omskrivningar, säkerhetskopior eller redaktörsrundor.

### Versionshistorik och återställning
- **Vad den gör:** Sparar dokumenttillstånd över tid, visar datum/författare och låter användaren inspektera eller återställa en tidigare version. Google Docs stöder versionspanel och återställning; ONLYOFFICE visar versions-/revisionslistor och restore. [belagt: https://support.google.com/docs/answer/190843?hl=en] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/VersionHistory.aspx]
- **Exakt arbetsflöde:** 1. Öppna Versionshistorik. 2. Välj en ögonblicksbild. 3. Inspektera innehåll/ändringar. 4. Återställ den eller skapa kopia. 5. Fortsätt redigera från vald bas. [belagt: https://support.google.com/docs/answer/190843?hl=en]
- **Vem gör det bäst:** **Google Docs** — beskriver visning, namngivning, kopiering och återställning i ett samlat flöde. [belagt: https://support.google.com/docs/answer/190843?hl=en]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] För lokal författare räcker först atomiska snapshot-filer med tidsstämpel, hash och valfritt namn, plus diffvy och återställning som skapar ny aktuell version. Spara snapshots utanför det redigerade dokumentträdet eller i ett versionspaket.
- **Prioritet för en ensam författare:** hög — reducerar risken för förlorade kapitel och gör experiment mindre riskabla.

### Fotnoter och slutnoter
- **Vad den gör:** Kopplar en automatnumrerad hänvisningsmarkör i brödtext till nottext längst ned på sidan eller i slutet. [belagt: https://support.microsoft.com/en-au/word/training/insert-footnotes-and-endnotes-in-word] [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/footnote_usage.html?DbPAR=CALC&System=WIN]
- **Exakt arbetsflöde:** 1. Placera markören efter belägget. 2. Välj Infoga fotnot eller slutnot. 3. Skriv noten i notområdet. 4. Klicka/dubbelklicka markören för att hoppa mellan brödtext och not. [belagt: https://support.microsoft.com/en-au/word/training/insert-footnotes-and-endnotes-in-word]
- **Vem gör det bäst:** **ONLYOFFICE** — dokumenterar automatisk numrering, navigering och notinställningar, samt beroendet av avsnitt för olika format. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/InsertFootnotes.aspx]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] QTextDocument har fotnoter som objekt-/layoutproblem, inte vanlig superskriven text. Modellera not-ID och ankare separat, rendera via egen layout eller bygg stabilt DOCX/HTML-exportflöde; en enklare MVP kan visa noterna i separat panel men bör inte kalla det sidfotnot.
- **Prioritet för en ensam författare:** hög — grundläggande för sakprosa, akademiskt arbete och källhänvisningar.

### Korsreferenser till rubriker, figurer och tabeller
- **Vad den gör:** Infogar en uppdaterbar hänvisning till ett mål i samma dokument, exempelvis dess rubriktext, figurnummer eller sidnummer. LibreOffice beskriver fältbaserade korsreferenser till bokmärken och objekt med bildtext. [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/references.html]
- **Exakt arbetsflöde:** 1. Skapa rubrik eller bildtext som mål. 2. Placera markören där hänvisningen ska stå. 3. Välj måltyp och mål. 4. Välj visningsform, exempelvis etikett/text/sida. 5. Uppdatera fält efter omstrukturering. [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/references.html]
- **Vem gör det bäst:** **LibreOffice Writer** — ger separata mål, referenstyp och formatval; både text och sidnummer kan infogas. [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/references.html]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Ge rubriker och objekt stabila UUID och lagra hänvisningar som fält/markörer snarare än rå text. Vid export/uppdatering slå upp måltext och sidposition; klickbara ankare kan använda interna länkar.
- **Prioritet för en ensam författare:** hög — hindrar felaktiga ”se figur 4” efter redigering.

### Genererad innehållsförteckning och snabbnavigering
- **Vad den gör:** Samlar rubriker med nivåer från styckestilar, länkar poster till mål och kan uppdatera innehåll/sidnummer när manus ändras. Apple Pages uppdaterar automatiskt TOC; ONLYOFFICE har uttryckligt refresh och klickbar TOC. [belagt: https://support.apple.com/en-gu/guide/pages/tan5b8c588d6/mac] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx]
- **Exakt arbetsflöde:** 1. Tilldela rubrikstilar. 2. Placera markören. 3. Infoga TOC och välj nivåer/stilar. 4. Klicka en post för att hoppa. 5. Uppdatera hela TOC eller bara sidnummer efter ändringar. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx]
- **Vem gör det bäst:** **Apple Pages** — auto-uppdaterad sidopanel med klickbara rubriker och insättbar TOC; **ONLYOFFICE** dokumenterar manuell full uppdatering och endast sidnummer. [belagt: https://support.apple.com/en-gu/guide/pages/tan5b8c588d6/mac] [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Bygg rubrikträd från `QTextBlock`-format/outline-nivå och visa dockad navigator. Infogad TOC kan vara genererat spann med interna links, men behöver markering som fält för säker uppdatering. Paginationberoende kräver uppdatering efter layoutreflow.
- **Prioritet för en ensam författare:** hög — kapitelöverblick och navigering sparar tid i alla långa verk.

### Bildtexter, automatisk numrering och figur-/tabellregister
- **Vad den gör:** Kopplar etikett och sekvensnummer till bild/tabell; genererar sedan ett uppdaterbart register sorterat efter dokumentordning/sida. Word kräver bildtexter innan figurlista; Writer stöder löpande numrering och automatisk bildtext. [belagt: https://support.microsoft.com/en-gb/word/insert-a-table-of-figures] [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/captions.html]
- **Exakt arbetsflöde:** 1. Markera figur eller tabell. 2. Välj Infoga bildtext och kategori. 3. Skriv beskrivning; nummer tilldelas automatiskt. 4. Placera register och välj kategori. 5. Uppdatera registret efter flytt, ny bildtext eller sidändring. [belagt: https://support.microsoft.com/en-gb/word/insert-a-table-of-figures]
- **Vem gör det bäst:** **Word** — har ett uttryckligt registerflöde med uppdatering av enbart sidnummer eller hela listan; **Writer** ger automatisk löpnumrering och bildtext vid infogning. [belagt: https://support.microsoft.com/en-gb/word/insert-a-table-of-figures] [belagt: https://help.libreoffice.org/latest/ug/text/swriter/guide/captions.html]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Bildtext ska vara ett semantiskt objekt med typ, sekvens-ID och text; håll figur och bildtext ihop vid paginering. Generera register från objektlistan och sidlayoutens positioner, med uppdateringskommando.
- **Prioritet för en ensam författare:** medel — hög för illustrerad sakprosa, lägre för romanmanus.

### Stycke- och teckenstilar, stilinspektör och stilmallar
- **Vad den gör:** Namngivna återanvändbara regler för exempelvis brödtext, rubriker, citat och teckenbetoning. De ger konsekvent utseende och kan bära dokumenthierarki; ONLYOFFICE beskriver både stycke- och textstilar och stilmallar. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/formattingpresets.aspx]
- **Exakt arbetsflöde:** 1. Välj stycke/ord. 2. Applicera befintlig stil via stilpanelen. 3. Ändra stilens definition eller skapa ny. 4. Inspektera vilken stil och direkta formatering markeringen har. 5. Spara/återanvänd uppsättningen som dokumentmall. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/formattingpresets.aspx] [resonemang]
- **Vem gör det bäst:** **ONLYOFFICE** — dess dokumentation skiljer uttryckligen stycke- och textstilar och låter stilar bygga TOC/figurlista. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/formattingpresets.aspx]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Kartlägg namngivna paragraph/character styles till `QTextBlockFormat`/`QTextCharFormat`; låt en inspektör visa stilnamn plus lokala avvikelser. `QTextDocument` har stöd för format men ett Word-liknande stilsystem med arv och serialisering kräver egen modell.
- **Prioritet för en ensam författare:** hög — stilren struktur är förutsättning för TOC, exporter och global formatering.

### Avsnittsbrytningar och separata sidhuvuden/sidfötter
- **Vad den gör:** Delar ett dokument i sektioner vars sidlayout kan skilja sig, exempelvis romerska sidnummer i förordet och löpande sidhuvud i kapitel. Word beskriver sektioner med egna kolumner, sidhuvud och sidfot. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c]
- **Exakt arbetsflöde:** 1. Sätt markören vid gränsen. 2. Välj sektionsbrytningstyp (nästa sida/kontinuerlig/jämn/udda). 3. Öppna sidhuvud/sidfot i nya sektionen. 4. Bryt eventuell koppling till föregående. 5. Ställ layout och sidnumrering för sektionen. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c] [resonemang]
- **Vem gör det bäst:** **Word** — dokumenterar flera typer av sektionsbrytning och särskilt kontinuerlig brytning för spaltbyte utan ny sida. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] `QTextDocument` kan representera sidbrytningar och sidstorlek, men separata sidhuvuden/-fötter och sektionslayout kräver egen sidmodell och sannolikt exportanpassning. Lagra sektioner som dokumentstruktur som påverkar formattering från brytpunkt till nästa.
- **Prioritet för en ensam författare:** medel — centralt för bokframsida, förord och tryckmanus; mindre viktigt under första utkastet.

### Spalter och avstavning
- **Vad den gör:** Spalter låter text flöda i två eller fler spalter inom ett avsnitt; avstavning delar ord vid radslut efter språkregler för jämnare satsyta. Word beskriver kontinuerlig sektionsbrytning för spalter; Writer listar avstavning som sid-/styckeformatfunktion. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c] [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/footnote_usage.html?DbPAR=CALC&System=WIN]
- **Exakt arbetsflöde:** 1. Placera markören eller markera stycken. 2. Välj antal spalter och avstånd. 3. Lägg kontinuerlig sektionsbrytning före/efter vid lokal spaltlayout. 4. Ställ språk och automatisk/manuell avstavning. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c] [resonemang]
- **Vem gör det bäst:** **Word** — dokumenterar spalter som sektionslayout och möjligheten att byta mitt på sidan. [belagt: https://support.microsoft.com/en-us/office/insert-a-section-break-eef20fd8-e38c-4ba6-a027-e503bdf8375c]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Flera kolumner finns i textlayout-konceptet, men sidlayout över avsnittsgränser behöver noggrann paginering. Avstavning bör använda språkdata/motor och visuellt mjuka brytpunkter; exportformat måste behålla språk och inställning.
- **Prioritet för en ensam författare:** låg — behövs för layout och slutlig sats, sällan för romanens arbetsutkast.

### Autokorrigering och autotext
- **Vad den gör:** Autokorrigering ändrar vanliga felskrivningar eller typografiska mönster; autotext expanderar kortnamn till återanvända textstycken. [resonemang]
- **Exakt arbetsflöde:** 1. Aktivera regeluppsättning. 2. Skriv felstavning eller förkortning. 3. Acceptera automatisk ersättning eller expandering. 4. Lägg till/ändra egna poster i ordlistan. [resonemang]
- **Vem gör det bäst:** **LibreOffice Writer** — dokumenterar en konfigurerbar AutoCorrect-funktion och AutoText som centrala Writer-verktyg; exakt produktflöde kunde inte verifieras i källorna som användes här. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Lyssna på skrivhändelser vid ordgräns och tillämpa utbytbara regler på senaste ord/fras; håll egen ordlista och användarens undantag. Autotext bör öppna förslag efter prefix och sätta in formaterade fragment med undo.
- **Prioritet för en ensam författare:** medel — sparar tid och kan stödja konsekvent namn-/termbruk.

### Språk per textavsnitt samt stavning/grammatik och egen ordlista
- **Vad den gör:** Anger korrekturspråk för markerat spann eller stycke och flaggar stavnings-/grammatikproblem; egen ordlista undantar egennamn och facktermer. [resonemang]
- **Exakt arbetsflöde:** 1. Markera text eller stå i stycke. 2. Välj språk. 3. Kör korrektur eller granska understrykningar. 4. Välj förslag, ignorera eller lägg ord i egen ordlista. 5. Kör grammatikgranskning, exempelvis via LanguageTool. [resonemang]
- **Vem gör det bäst:** **LibreOffice Writer** — har språkbaserad korrekturarkitektur; LanguageTool-integration och ordlista behöver däremot verifieras mot aktuell produktversion och ingår inte i belagda påståenden här. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Spara språk som textformatmetadata per span/block. Stavning kan göras asynkront via highlighter under röd vågig markering; LanguageTool som separat valbar klient bör skicka endast behövda textspann och applicera förslag via cursorspann. Ordbok ska vara lokal och dokumentera språk.
- **Prioritet för en ensam författare:** hög — särskilt för svenskspråkiga långa texter, namn och flera språk.

### Tecken-/symboltabell och tesaurus
- **Vad den gör:** Symboltabellen hjälper användaren infoga tecken som inte finns lätt på tangentbordet; tesaurus visar synonymer/relaterade ord för valt uttryck. [resonemang]
- **Exakt arbetsflöde:** 1. Öppna symbolväljare eller markera ord. 2. Sök/bläddra tecken respektive synonymer. 3. Förhandsgranska tecken/ord. 4. Infoga eller ersätt uttrycket. [resonemang]
- **Vem gör det bäst:** **LibreOffice Writer** — denna jämförelse kunde inte belägga ett överlägset arbetsflöde från förstahandsdokumentation; behåll som etablerade hjälpfunktioner snarare än skiljande proffsfunktioner. [resonemang]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Symbolväljare kan använda Qt Unicode/character metadata och infoga via `QTextCursor`; tesaurus behöver lokala språklexikon eller en extern valbar tjänst, med tydlig språkväxling.
- **Prioritet för en ensam författare:** låg — användbart ibland, men inte kärna i långdokumentsredigering.

### Sök och ersätt med reguljära uttryck
- **Vad den gör:** Söker mönster, inte bara exakta ord, och kan ersätta grupper. LibreOffice Writer har reguljära uttryck; Typora stöder regex och grupper i ersättningssträng. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/search_regexp.html] [belagt: https://support.typora.io/Search/]
- **Exakt arbetsflöde:** 1. Öppna Sök/Ersätt. 2. Aktivera regex. 3. Skriv mönster och ersättning. 4. Förhandsgranska träffar. 5. Ersätt enskilt eller alla. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/search_regexp.html]
- **Vem gör det bäst:** **LibreOffice Writer** — har en komplett dokumenterad regex-sökning i den aktuella jämförelsen; **Typora** visar praktiskt stöd för capture groups i ersättningar. [belagt: https://help.libreoffice.org/latest/en-US/text/swriter/guide/search_regexp.html] [belagt: https://support.typora.io/Search/]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Kör regex mot dokumenttextens positioner, konvertera matchade offsetar till `QTextCursor` och visa träfflista/förhandsgranskning. Beakta blockgränser, formatering och att ersättning ändrar offsetar; ersätt bakifrån eller beräkna om.
- **Prioritet för en ensam författare:** medel — kraftfullt för konsekventa namn, termer och formatfixar.

### Snabbnavigering och rubriknavigator
- **Vad den gör:** Panel med rubrikträd/objekt som hoppar till texten och kan fälla ihop nivåer. ONLYOFFICE visar rubriker med nesting; Typora erbjuder Outline-funktionen. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx] [belagt: https://support.typora.io/TOC/]
- **Exakt arbetsflöde:** 1. Öppna Navigator/Outline. 2. Skanna eller sök rubrikträd. 3. Klicka rubrik för att hoppa. 4. Vik in/ut nivåer och fortsätt skriva. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx]
- **Vem gör det bäst:** **ONLYOFFICE** — dokumenterar panel med nivåer, hopp, expand/collapse och strukturhantering. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor/CreateTableOfContents.aspx]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Bygg `QTreeWidget` från blockens heading-roller/outline-level och behåll ankare/position till block. Uppdatera inkrementellt efter ändringar; synka aktuell markör med aktiv nod.
- **Prioritet för en ensam författare:** hög — daglig tidsbesparing i manus med många kapitel och underkapitel.

### Tabeller med formler och ekvationer
- **Vad den gör:** Tabellformler räknar cellvärden, summor och relationer; ekvationseditor skapar matematiska uttryck med korrekt layout. ONLYOFFICE dokumenterar formler i tabeller och symbol-/ekvationsnära funktioner i editorn. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor]
- **Exakt arbetsflöde:** 1. Skapa tabell eller placera markör. 2. Välj cell/formel eller Infoga ekvation. 3. Skriv/bygg uttryck. 4. Uppdatera resultat när källceller ändras. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor] [resonemang]
- **Vem gör det bäst:** **ONLYOFFICE** — användardokumentationen listar uttryckligen formler i tabeller och objektfunktioner; specifika formelgränser är inte belagda här. [belagt: https://helpcenter.onlyoffice.com/docs/userguides/document_editor]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Enkel MVP kan stödja `SUM(ABOVE)`-liknande formler i tabellceller med beroendegraf och uppdatering. Ekvationer bör vara inbäddade objekt (MathML/LaTeX-rendering) med separat redigeringsdialog och exportrepresentation; inte vanlig Unicode-text.
- **Prioritet för en ensam författare:** låg — hög för läroböcker och teknisk sakprosa, låg för de flesta skönlitterära manus.

### Jämförelse av formatering
- **Vad den gör:** Vid dokumentjämförelse visas även skillnader i formatering, inte bara ord. Word har jämförelseinställningar för formatering och text. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Exakt arbetsflöde:** 1. Välj två versioner. 2. Öppna jämförelsealternativ. 3. Slå på Formatering. 4. Välj diffens detaljnivå. 5. Granska markeringar i resultatdokumentet. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Vem gör det bäst:** **Word** — dokumenterar formateringsjämförelse som separat val i legal blackline-flödet. [belagt: https://support.microsoft.com/en-gb/word/compare-document-differences-using-the-legal-blackline-option]
- **Tekniskt i PyQt6/QTextDocument:** [resonemang] Jämför paragraph- och character-format separat från textdiff och rapportera typografiska ändringar (stil, storlek, fetstil, indrag, avstånd) per spann/block. Visa före/efter och undvik att generera många triviala revisioner från normaliserade interna format.
- **Prioritet för en ensam författare:** medel — viktig när man vill bevara manusets utseende genom externa redigeringsrundor.

## Vad jag inte kunde belägga

- Jag kunde inte belägga att varje namngiven produkt stöder samtliga uppräknade funktioner i alla utgåvor och operativsystem; produktfamiljerna har olika webb-, desktop- och abonnemangsversioner. [resonemang]
- För Apple Pages, Google Docs och Typora kunde jag inte verifiera hela matrisen av korsreferenser, formateringsjämförelse, tabellformler, språk per textavsnitt, avstavning och autotext från de primärkällor som hämtades. [resonemang]
- För LanguageTool kunde jag inte belägga den aktuella integrationsvägen, versionsbegränsningar eller fullständigt stöd för en egen ordlista i respektive produkt. [resonemang]
- PyQt6/QTextDocument-anteckningarna är tekniska förslag utifrån identifierade OmaScribe-kodstrukturer, inte verifierade implementeringslöften om Qt:s fulla pagination/exportbeteende. [resonemang]
- OmaScribe-kodkontext verifierad: [core/richtext.py:17](../core/richtext.py#L17) importerar textformat-, cursor- och dokumenttyper; [core/richtext.py:53](../core/richtext.py#L53) hanterar blockroller; [ui/editor_view.py:67](../ui/editor_view.py#L67) definierar en `QTextEdit`-canvas. Dessa rader styrker endast den arkitektoniska utgångspunkten, inte att uppräknade proffsfunktioner redan finns. [belagt: ../core/richtext.py#L17] [belagt: ../core/richtext.py#L53] [belagt: ../ui/editor_view.py#L67]
