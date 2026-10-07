# Publicering och export
## Sammanfattning

- [belagt: https://www.atticus.io/quick-start-guide/] En publiceringsprodukt behöver separera innehållet från två slutformat: reflowbar EPUB för läsare och sidbunden PDF för tryck; Atticus exporterar dessutom DOCX som redaktörs-/backupfil.
- [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] KDP:s tryckkrav beror på sidantal och blöd: inner-/guttermarginalen går från 0,375 tum för 24–150 sidor till 0,875 tum för 701–828 sidor.
- [belagt: https://www.w3.org/TR/epub-33/] EPUB 3 kräver en nav-dokumentstruktur med innehållsförteckning; teknisk validering är en egen del av publiceringsflödet och säger inte i sig att boken är tillgänglig.
- [belagt: https://www.w3.org/TR/epub-a11y/] EPUB Accessibility kräver tillgänglighetsmetadata och definierar krav för tillgänglig publikation; alt-texter, läsordning och semantiska rubriker måste därför vara redigerbara egenskaper, inte bara visuell styling.
- [belagt: https://help.vellum.pub/tutorial/] Vellum visar den starka bokformateringsmodellen: importera manus, granska identifierade kapitel, applicera en bokstil, koppla omslag och kontrollera utdata i förhandsvisning.

## Bordet: vad som är minimum i kategorin

- [belagt: https://www.atticus.io/quick-start-guide/] En och samma bok behöver exportvägar för EPUB, print-PDF och DOCX; DOCX behåller grundinnehåll och kapitelstruktur men inte nödvändigtvis specialdesign.
- [belagt: https://www.w3.org/TR/epub-33/] EPUB behöver giltigt paket, metadata och navigationsdokument med TOC.
- [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] Tryckexport behöver enkelsidiga sidor, inbäddade typsnitt, 300 DPI-bilder, trimformat, sidordning och marginalregler.
- [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] Omslag till paperback måste levereras som en sammanhängande PDF med baksida, rygg och framsida; ryggmåttet beror på sidantal och papper.
- [belagt: https://www.w3.org/TR/epub-a11y/] Metadata måste kunna ange accessMode, accessibilityFeature och accessibilityHazard; accessibilitySummary och accessModeSufficient rekommenderas.
- [belagt: https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf?t=1540849595582] Distributörsspecifika mallar/profiler behövs eftersom mått, bleed, omslagsmall och metadataregler inte är identiska.

## Funktionskatalog

### 1. Publiceringsprojekt och formatprofiler
- **Vad den gör:** [resonemang] Samlar manus, bokdata, omslagsdata och exportregler i ett publiceringsprojekt med separata profiler för KDP, IngramSpark, Lulu, Apple Books och Kobo. Varje profil ska visa vilka inställningar som ändras och vilka som är gemensamma.
- **Exakt arbetsflöde:** [resonemang] 1. Välj ny utgåva och språk. 2. Välj e-bok eller tryck. 3. Välj distributör och produktvariant. 4. Ange trim, papper/trycktyp och sidantal eller låt trycklayout beräkna sidantal. 5. Kontrollera profilens varningar. 6. Exportera profilens filer och en rapport.
- **Vem gör det bäst:** [belagt: https://www.atticus.io/quick-start-guide/] Atticus exporterar EPUB och PDF som den beskriver som publiceringsklara för stora tjänster inklusive KDP och IngramSpark; samma källa visar separat DOCX-export.
- **Tekniskt i Python/Qt:** [resonemang] Lagra FormatProfile som versionerade JSON-serialiserade inställningar med mm/in-konverterare och valideringsfunktioner. Bygg en QWizard för kanal, format, sidstorlek och förhandskontroll; låt exporteraren konsumera ett fryst profilobjekt.
- **Prioritet för en ensam författare:** hög — minskar fel och upprepade manuella inställningar mellan kanaler.

### 2. EPUB 3 med semantisk kapitelstruktur och TOC
- **Vad den gör:** [belagt: https://www.w3.org/TR/epub-33/] Skapar EPUB 3 med XHTML-innehåll, navigationsdokument och hierarkisk TOC. [resonemang] Dokumentmodellen bör skilja kapitel, avsnitt, scenbrytning, front matter och back matter från deras visuella utseende.
- **Exakt arbetsflöde:** [resonemang] 1. Markera dokumentets rubriker med namngivna nivåer. 2. Kontrollera ordning och kapitelindelning. 3. Välj vilka nivåer som ska visas i TOC. 4. Lägg till omslagsbild. 5. Exportera EPUB. 6. Öppna den i läsarförhandsvisning och klicka igenom varje TOC-post.
- **Vem gör det bäst:** [belagt: https://help.vellum.pub/tutorial/] Vellum importerar Word-manus, identifierar och listar kapitel i Navigator, låter användaren välja en stil och visar sid-/bokförhandsvisning. [belagt: https://help.apple.com/itc/booksassetguide/en.lproj/static.html] Apple anger att TOC krävs för alla böcker i Apple Books.
- **Tekniskt i Python/Qt:** [resonemang] Konvertera QTextDocument till intern semantisk AST: heading level, chapter, scene break, image, paragraph. Skriv EPUB ZIP-paket med OPF, XHTML, CSS, nav.xhtml och `mimetype` först; använd rubrik-UUID som stabila fragmentlänkar.
- **Prioritet för en ensam författare:** hög — EPUB är nödvändigt för bred e-boksdistribution och läsarnavigering.

### 3. Namngiven typografi och bokstilar
- **Vad den gör:** [belagt: https://help.vellum.pub/tutorial/] En bokstil appliceras över hela boken och kombinerar typografi, kapitelrubriker och dekorativa element. [resonemang] Exempel på namngivna roller: Body Text, Chapter Title, First Paragraph, Block Quote, Scene Break och Front Matter.
- **Exakt arbetsflöde:** [resonemang] 1. Välj en bokstil. 2. Justera brödtext, radavstånd, indrag och rubriker. 3. Välj kapitelornament/drop cap. 4. Växla mellan e-bok och tryckförhandsvisning. 5. Spara stilen som återanvändbar preset.
- **Vem gör det bäst:** [belagt: https://help.vellum.pub/tutorial/] Vellum applicerar en vald stil direkt på hela boken och visar både e-bok och print-spread. [belagt: https://intercom.help/atticus-5877e36564df/en/articles/12581876-how-to-format-your-book-with-atticus] Atticus erbjuder skilda inställningar för e-bok och print, inklusive marginaler, indrag, avstavning och keep-regler.
- **Tekniskt i Python/Qt:** [resonemang] Definiera semantiska stil-ID:n separerade från QTextCharFormat/QTextBlockFormat. EPUB får en CSS-mappning, PDF en typografisk layoutmappning och DOCX riktiga OOXML-stilar; undvik att härleda roll enbart från visuell fontstorlek.
- **Prioritet för en ensam författare:** hög — ger professionell konsekvens och gör samma manus återanvändbart i flera format.

### 4. Metadata, ISBN och front matter
- **Vad den gör:** [belagt: https://help.vellum.pub/title-info/] Titelinformation kan mata titelsida, print-headers och e-boksmetadata. [belagt: https://help.lulu.com/en/support/solutions/articles/64000255463] Lulu kräver bland annat titel, författare, copyrightdatum och e-boks-ISBN på copyright-sidan och matchande metadata.
- **Exakt arbetsflöde:** [resonemang] 1. Ange titel, undertitel, författare, medverkande, språk, serie, datum, förlag/imprint, beskrivning, nyckelord och ISBN per format. 2. Välj front-matter-element: halvtitel, titelsida, kolofon/copyright, dedikation, innehåll. 3. Välj back matter som tack, författarpresentation och nästa bok. 4. Kör en konsistenskontroll mellan metadata, titelblad och omslag.
- **Vem gör det bäst:** [belagt: https://help.vellum.pub/title-info/] Vellum återanvänder Title Info till titelblad, print-headers och EPUB-metadata. [belagt: https://help.vellum.pub/elements/] Vellum har elementtyper som Half Title, Title Page och Copyright.
- **Tekniskt i Python/Qt:** [resonemang] Skapa BookMetadata-modell med separata ISBN-fält per format/utgåva; generera frontmatter som dokumentblock och EPUB Dublin Core/Schema.org metadata från samma källa. Visa mismatch-varningar före export.
- **Prioritet för en ensam författare:** hög — metadatafel kan stoppa distribution och manuella upprepningar skapar inkonsekvenser.

### 5. Trycklayout: trim, spegelmarginaler, gutter och kapitelstart
- **Vad den gör:** [belagt: https://kdp.amazon.com/en_US/help/topic/G201834260] KDP beskriver spegelvända marginaler och inside/outside-marginaler; kapitel och paginering måste hållas inom den valda trycklayouten. [resonemang] Exporten behöver styra recto/verso, kapitelstart på höger sida eller valfri sida, blanka fyllnadssidor och olika frontmatter-paginering.
- **Exakt arbetsflöde:** [resonemang] 1. Välj trimstorlek. 2. Ange sidantal/trycktyp för minimum-gutter. 3. Sätt inner-, ytter-, topp- och bottenmarginal. 4. Aktivera spegelmarginaler och vid behov bleed. 5. Välj kapitelstart: ny sida eller höger sida. 6. Förhandsgranska uppslag, blanka sidor, folios och löpande huvuden.
- **Vem gör det bäst:** [belagt: https://intercom.help/atticus-5877e36564df/en/articles/12581876-how-to-format-your-book-with-atticus] Atticus erbjuder inner-/yttermarginal, indrag, avstavning, keep-regler och prioritering mellan änkor/horungar och sidbalans. [belagt: https://help.vellum.pub/elements/] Vellum kan ställa in när front/back-matter-element börjar i ett uppslag och när print-paginering börjar.
- **Tekniskt i Python/Qt:** [resonemang] Qt print layout kan rendera PDF men spegelmarginaler kräver sidindexbaserad växling left/right, inte en konstant QMarginsF. Implementera först layout i mm och rendera varje sida med margin-box; använd PDF-rendering för slutlig sidräkning eftersom sidantal påverkar gutter och rygg.
- **Prioritet för en ensam författare:** hög — tryckfilens sidantal, läsbarhet och godkännande beror på layouten.

### 6. Blödning, omslags-PDF och ryggbredd
- **Vad den gör:** [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] Skapar ett helt omslag med baksida, rygg, framsida och bleed. KDP:s ryggformel skiljer mellan vitt papper, crème och färgpapper.
- **Exakt arbetsflöde:** [resonemang] 1. Slutför inlaga och fastställ sidantal. 2. Välj distributör, trim, papper och färgtyp. 3. Beräkna rygg och totalmått eller hämta distributörens mall. 4. Placera omslagskonst, ryggtext och barcode i safe zones. 5. Exportera en enda PDF och kontrollera mått och utfallande bakgrund.
- **Vem gör det bäst:** [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] KDP:s Cover Calculator/template generator tar tryckval, trim och sidantal och ger layoutmått; KDP anger minsta sidantal för ryggtext. [belagt: https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf?t=1540849595582] IngramSpark rekommenderar att använda deras guide/mall och anger särskild bleed och säkerhetsmarginal.
- **Tekniskt i Python/Qt:** [resonemang] Bygg omslagscanvas som vektor-PDF med tre paneler och markeringar endast i redigeringsvyn; exportera utan crop marks om kanalprofilen kräver det. Hämta beräknade mått från kanalens regler och be användaren uppdatera efter varje ändring av sidantal/papper.
- **Prioritet för en ensam författare:** hög för tryckt bok — ryggbredd kan inte låsas innan slutlig paginering.

### 7. DOCX med redaktörsvänliga Word-stilar
- **Vad den gör:** [belagt: https://pandoc.org/MANUAL.html] Pandoc kan utgå från ett reference.docx vars namngivna stilar, dokumentegenskaper, marginaler, sidstorlek, header och footer appliceras på genererad DOCX.
- **Exakt arbetsflöde:** [resonemang] 1. Välj “redaktörsmanus” som exportprofil. 2. Exportera rubriker som Heading 1/2, brödtext som Normal/Body Text och specialstycken som namngivna stylar. 3. Bevara kapitelbrytningar och kommentarer/ändringsspår lämnas till Word. 4. Öppna exporten i Word/LibreOffice och kontrollera navigeringspanelen.
- **Vem gör det bäst:** [belagt: https://pandoc.org/MANUAL.html] Pandoc dokumenterar uttryckligen reference.docx och de stilar som används i genererad DOCX. [belagt: https://www.atticus.io/quick-start-guide/] Atticus DOCX-export behåller innehåll och kapitelindelning men inte dess specialdesign.
- **Tekniskt i Python/Qt:** [resonemang] python-docx kan skapa paragraphs/runs, namnge paragraph styles och page breaks; exportera strukturella roller i stället för direktformatering. Använd en kontrollerad DOCX-mall och testa att rubriker faktiskt har style IDs i OOXML.
- **Prioritet för en ensam författare:** medel — viktig vid extern redigering, men slutprodukten är EPUB/PDF.

### 8. EPUB-validering och tillgänglighet
- **Vad den gör:** [belagt: https://github.com/w3c/epubcheck] EPUBCheck är W3C:s officiella konformitetskontroll för EPUB 2/3 och kan köras som CLI eller Java-bibliotek. [belagt: https://www.w3.org/TR/epub-a11y/] Accessibility-kraven omfattar metadata för accessMode, accessibilityFeature och accessibilityHazard.
- **Exakt arbetsflöde:** [resonemang] 1. Exportera EPUB. 2. Kör EPUBCheck och visa fel som klickbara rader. 3. Reparera package/nav/XHTML-resurser och kör igen. 4. Kör separat accessibility-checklista för alt-text, rubrikordning, språk, kontrast och läsordning. 5. Spara rapport och status med exporten.
- **Vem gör det bäst:** [belagt: https://github.com/w3c/epubcheck] EPUBCheck är officiell validator; [belagt: https://www.w3.org/TR/epub-a11y/] W3C-specifikationen skiljer metadata/discoverability från att uppfylla tillgänglighetskraven.
- **Tekniskt i Python/Qt:** [resonemang] Kör Java-verktyget asynkront via QProcess mot temporär export, parsa severity/fil/rad och visa resultat i QAbstractItemModel. Validering av syntaktisk EPUB bör vara separat från a11y-granskning; låt aldrig “valid EPUB” betyda “tillgänglig EPUB”.
- **Prioritet för en ensam författare:** hög — fångar distributörsstopp och tillgänglighetsbrister innan uppladdning.

### 9. Efterbearbetning av EPUB i Sigil och Calibre
- **Vad den gör:** [belagt: https://github.com/Sigil-Ebook/Sigil] Sigil är en Qt6-baserad EPUB 2/3-editor som kan validera EPUB, CSS och XHTML. [belagt: https://manual.calibre-ebook.com/en/edit.html] Calibre Edit Book kan redigera TOC, generera den från rubriker/länkar/filer och låta användaren ändra destination för varje post.
- **Exakt arbetsflöde:** [resonemang] 1. Exportera EPUB från author tool. 2. Öppna i Sigil/Calibre för specialfall som internlänkar eller handbyggd TOC. 3. Kontrollera EPUBCheck efter ändring. 4. Importera inte manuella ändringar tillbaka genom destruktiv konvertering; behåll EPUB som separat publiceringsartefakt.
- **Vem gör det bäst:** [belagt: https://github.com/Sigil-Ebook/Sigil] Sigil passar direkt redigering av EPUB-källfiler; [belagt: https://manual.calibre-ebook.com/en/edit.html] Calibre har dedikerade verktyg för TOC och EPUB-redigering.
- **Tekniskt i Python/Qt:** [resonemang] Använd inte dessa som intern exporterare; bygg ren EPUB och låt externa verktyg vara valfri handpåläggning. Möjliggör “Öppna exportmapp” och rapportera checksumma så att ändrad EPUB kan granskas.
- **Prioritet för en ensam författare:** låg — värdefullt för avancerad kontroll, men ytterligare verktyg ökar arbetsbördan.

### 10. Distributörsuppladdning och slutkontroll
- **Vad den gör:** [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] KDP tar in manus och omslag som separata tryckfiler och har Print Previewer. [belagt: https://help.lulu.com/en/support/solutions/articles/64000255463] Lulu kräver EPUBCheck-validering, komplett TOC, korrekt metadata och rätt omslagsbild för e-boksdistribution.
- **Exakt arbetsflöde:** [resonemang] 1. Välj distributörsprofil. 2. Ladda upp EPUB/PDF och omslag. 3. Läs distributörens förhandsgranskning/fel. 4. Jämför titel, namn, ISBN, copyrightdatum, cover och inlaga. 5. Exportera om från källmanus efter ändringar. 6. Markera uppladdning som klar per utgåva.
- **Vem gör det bäst:** [belagt: https://kdp.amazon.com/en_US/help/topic/G201834190] KDP beskriver separata steg för trim/marginal, front/body/back matter, manus och omslag. [belagt: https://help.lulu.com/en/support/solutions/articles/64000255592-publishing-an-ebook-for-global-distribution] Lulu visar grön/röd status efter konvertering och rekommenderar att användaren provläser den konverterade EPUB-filen.
- **Tekniskt i Python/Qt:** [resonemang] Ingen automatisk uppladdning krävs för miniminivån; skapa exportpaket med tydliga filnamn, checksummor, profilens mått och en preflight-rapport. Länka till respektive distributörs inloggning/dokumentation.
- **Prioritet för en ensam författare:** hög — gör de sista felkontrollerna begripliga och spårbara.

### 11. Svensk och engelsk boksättning
- **Vad den gör:** [belagt: https://boktypografen.se/tecknen-som-skiljer/] Svensk typografi använder tankstreck (–) med mellanrum i paus/parentes och som replikinledning; engelska använder ofta em dash (—) för parentetiska inskott. [resonemang] Bokens trimstorlek är en marknads-/genreprofil, inte en enkel svensk kontra engelsk regel.
- **Exakt arbetsflöde:** [resonemang] 1. Välj språkvariant. 2. Välj citattecken/replikstil och språkets avstavningsordlista. 3. Kontrollera decimal-/tusentalsformat och typografiska ersättningar. 4. Välj trim baserat på målmarknad/genre och tryckalternativ. 5. Läs korrektur i den faktiska layouten.
- **Vem gör det bäst:** [belagt: https://internt.slu.se/en/support-services/administrative-support/communication/language-writing/language-tools/style-guide-english/] SLU:s engelska stilguide beskriver en dash/em dash-regler; [belagt: https://boktypografen.se/tecknen-som-skiljer/] Boktypografen beskriver svenska repliktankstreck, mellanrum och kontrast mot engelsk em dash.
- **Tekniskt i Python/Qt:** [resonemang] Låt språket styra spellcheck/avstavning och valbara typografiska förinställningar; gör aldrig globala ersättningar av bindestreck och tankstreck i brödtext utan förhandsvisning och ångra-stöd.
- **Prioritet för en ensam författare:** medel — viktigt för trovärdigt språk och flöde, men ska vara valbart och redigerbart.

## Siffertabell

| Parameter | Värde / regel | Källstöd |
|---|---|---|
| Vanligt KDP-trim | 6 × 9 tum = 152,4 × 228,6 mm; KDP anger detta som vanlig US-trimstorlek. | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| Vanliga format att erbjuda | 5 × 8 tum = 127 × 203,2 mm; 6 × 9 tum = 152,4 × 228,6 mm; A5 = 148 × 210 mm. [resonemang] Dessa bör finnas som presets, men faktisk tillgänglighet beror på distributör och tryckval. | 6×9 [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/]; 5×8/A5 [resonemang] |
| KDP inner/gutter, 24–150 sidor | minst 0,375 tum = 9,6 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP inner/gutter, 151–300 sidor | minst 0,5 tum = 12,7 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP inner/gutter, 301–500 sidor | minst 0,625 tum = 15,9 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP inner/gutter, 501–700 sidor | minst 0,75 tum = 19,1 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP inner/gutter, 701–828 sidor | minst 0,875 tum = 22,3 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP ytterkant utan blöd | minst 0,25 tum = 6,4 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP ytterkant med blöd | minst 0,375 tum = 9,6 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/] |
| KDP inlaga med blöd | lägg till 0,125 tum = 3,2 mm på ytterkant och 0,25 tum = 6,4 mm på höjden; 6×9 blir 6,125 × 9,25 tum. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] |
| Tryckbild | minst 300 DPI; KDP rekommenderar högst 600 DPI för att hålla filstorlek hanterbar. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] |
| KDP minsta trycktext | 7 pt | [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] |
| KDP minsta paperback-sidantal | 24 sidor; sidantal avrundas upp till jämnt tal. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201857950] |
| KDP omslagsbleed | 0,125 tum = 3,2 mm runt topp, botten och ytterkanter. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP ryggbredd, svartvitt/vitt papper | sidantal × 0,002252 tum = sidantal × 0,0572 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP ryggbredd, svartvitt/crème | sidantal × 0,0025 tum = sidantal × 0,0635 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP ryggbredd, premium color | sidantal × 0,002347 tum = sidantal × 0,0596 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP ryggbredd, standard color | sidantal × 0,002252 tum = sidantal × 0,0572 mm | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP total omslagsbredd | bleed + baksida + rygg + framsida + bleed; höjd = trimhöjd + bleed upptill och nedtill. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| KDP ryggtext | kräver minst 79 sidor för egen PDF-omslagsfil (Cover Creator anger 80 sidor); håll text minst 0,0625 tum = 1,6 mm från ryggkanten. | [belagt: https://kdp.amazon.com/en_US/help/topic/G201953020] |
| EPUB TOC | EPUB 3 navigation document och en `toc nav` krävs; Apple Books kräver TOC för alla böcker. | [belagt: https://www.w3.org/TR/epub-33/], [belagt: https://help.apple.com/itc/booksassetguide/en.lproj/static.html] |
| EPUB tillgänglighetsmetadata | `accessMode`, `accessibilityFeature`, `accessibilityHazard` är MUST; `accessibilitySummary`, `accessModeSufficient` SHOULD enligt EPUB Accessibility 1.1. | [belagt: https://www.w3.org/TR/epub-a11y/] |
| IngramSpark blödexempel | En 6×9-tums inlaga med bleed blir 6,125 × 9,25 tum; guiden rekommenderar 0,5 tum på tre trimkanter. | [belagt: https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf?t=1540849595582] |
| Lulu full bleed | Lulu anger 0,25 tum = 6,35 mm extra i både bredd och höjd för print-ready full-bleed-inlaga; deras bokguide anger 0,125 tum/3,175 mm bleed. | [belagt: https://help.lulu.com/en/support/solutions/articles/64000255584], [belagt: https://assets.lulu.com/media/guides/en/lulu-book-creation-guide.pdf] |

### Föreslaget minimum för OmaScribe

- [resonemang] Prioritera först publiceringsprojekt med metadata/front matter, exporterbar EPUB 3 med semantisk TOC, och DOCX med riktiga named styles.
- [resonemang] Bygg sedan trimstorlekar, spegelmarginaler, kapitelstart på höger/vänster sida, validering och distributörsprofiler; låt PDF-exporten visa slutligt sidantal innan omslagsrygg beräknas.
- [resonemang] Lägg omslagsdesigner som en separat, smal funktion efter inlaga; för KDP/IngramSpark/Lulu ska exporteraren använda aktuell mall-/kalkylatorinformation och tydligt visa att omslagsmåtten måste räknas om när sidantal eller papper ändras.
- [belagt: core/doc_manager.py#L39-L53] OmaScribe har redan A4/Letter, fasta marginalvärden, sidnumrering, “skip first page”, header/footer och clean-print-inställningar.
- [belagt: core/doc_manager.py#L219-L236] PDF-utskriften sätter QPageSize till A4 eller Letter och använder fyra fasta marginaler i mm; den spegelvänder inte marginalerna efter sidans jämna/udda position i detta avsnitt.
- [belagt: core/doc_manager.py#L429-L440] Den dokumenterade save_file-exporten hanterar DOCX, PDF, HTML, Markdown och text; EPUB-export finns inte i den här exportdispatchen.
- [belagt: ui/main_window.py#L734-L750] PDF-exporten anropar DocumentManager.save_file med sidinställningar.
- [belagt: ui/main_window.py#L797-L810] DOCX-exporten anropar DocumentManager.save_file utan att skicka page_settings.

## Vad jag inte kunde belägga

- [resonemang] Jag kunde inte belägga en enda gemensam officiell ryggbreddsformel för IngramSpark, Lulu och KDP; IngramSpark och Lulu hänvisar till produkt-/sidantalsspecifika mallar, så OmaScribe bör inte återanvända KDP:s koefficient mellan kanaler.
- [resonemang] Jag kunde inte belägga en generell regel att svenska böcker ska ha ett visst trimformat jämfört med engelska böcker; trim bör erbjudas som marknads- och kanalval.
- [resonemang] Jag kunde inte belägga exakt en universell dropp-cap-, ornaments- eller kapitelnumreringskonvention för alla genrer/marknader. Det bör vara valbara bokstilar.
- [resonemang] Jag kunde inte här fastställa hela KDP:s aktuella trimstorlekstabell, sidantalstak per alla format/trycktyper eller varje specialfall för hardcover; tabellen redovisar endast källbelagda mått som är direkt relevanta för minimum.
- [resonemang] Jag kunde inte styrka att en distributör accepterar varje tänkbar EPUB 3-funktion eller att en EPUBCheck-godkänd fil automatiskt godtas av varje butik; respektive kanal behöver slutlig uppladdning och egen förhandsgranskning.
