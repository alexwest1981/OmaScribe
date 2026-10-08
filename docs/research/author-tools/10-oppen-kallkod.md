# Inventering av öppna författarverktyg

Denna rapport kartlägger open source-verktyg för skönlitterärt skrivande, deras teknikstack, licenser och livscykel, i syfte att identifiera luckor och återanvändbara mönster för projektet OmaScribe.

## 1. Vilka öppna författarverktyg finns det?

Sökningen omfattade kända verktyg såväl som GitHub-sökningar (topics: `novel-writing`, `writer`, `outliner`). 

*   **novelWriter** (Python/PyQt6): [belagt: https://github.com/saga-soft/novelWriter]. Ett textbaserat projektverktyg. Stödjer binder/scener, metadata per scen, plain text-editor (med egna markdown-liknande taggar). Kan kompilera projektet och exportera (DOCX/PDF via Pandoc), ser ut att sakna inbyggd AI, ren WYSIWYG, och native tryckfärdig sättning (förlitar sig på externa verktyg för PDF/tryck).
*   **Manuskript** (Python/PyQt5/6): [belagt: https://github.com/olivierkes/manuskript]. Stödjer scener, indexkort, metadata, versioner och the Snowflake method. Fokuserat på planering och outliner. Interfacet är mer komplicerat och exporterar via Pandoc. Saknar ljud/diktering och AI.
*   **Zettlr** (TypeScript/Electron): [belagt: https://github.com/Zettlr/Zettlr]. Främst en Markdown-editor inriktad på akademiskt skrivande och Zettelkasten i en filstruktur (folder-based). Stödjer inte renodlad romanskrivar-"binder" där scener flyttas fritt inom pärmar utan speglar diskens struktur.
*   **FocusWriter** (C++/Qt): [belagt: https://github.com/gottcode/focuswriter]. Distraction-free text-editor. Helfönster, målstatistik för ord/mål och text. Inget projektsystem eller binder.
*   **KIT Scenarist** (C++/Qt): [belagt: https://github.com/dimkanovikov/KITScenarist]. Inriktat på filmmanus, har kort, outline och statistik. Dess efterträdare (Story Architect) tycks inte publiceras aktivt med öppen källkod på GitHub i samma form.
*   **bibisco** (JavaScript/Java-backend): [belagt: https://github.com/andreafeccomandi/bibisco]. Bygger kring karaktärsintervjuer (Story Bible), outliner, tidslinjer och binder. Begränsat till lokalt (ingen molnsynk förutan via Dropbox-mapp) och är grafiskt tung. Har kommersiell Pro-version som låser upp en del av strukturen.
*   **Ghostwriter** (C++/Qt, numera KDE): [belagt: https://github.com/KDE/ghostwriter]. Distraction-free markdown editor (likt FocusWriter, men Markdown). Ingen pärm-funktionalitet.
*   **Calibre** (Python/PyQt) / **Sigil** (C++/Qt): [belagt: https://github.com/kovidgoyal/calibre, https://github.com/Sigil-Ebook/Sigil]. Bok-assemblers och paketeringsverktyg snarare än texteditorer, men i princip branschstandard öppen källkod för EPUB.
*   **Typst** (Rust) / **Pandoc** (Haskell): [belagt: https://github.com/typst/typst, https://github.com/jgm/pandoc]. Kraftfull konvertering och typsättning (PDF). Typst genererar absolut tryckfärdig PDF, men saknar dedikerat författar-GUI (kräver kod/markup).
*   **Obsidian + plugins**: Obsidian är stängd kod (Electron), men bygger på lokala Markdown-filer. Dess öppna plugin *Longform* implementerar scener och projektträd, men saknar tryckfärdig sättning och starka integrerade kort/tavlor direkt i core.

## 2. Livsläge

Följande livsläge har belagts från GitHubs API:

*   **novelWriter**: Aktivt. Senaste push 2026-10-07, senaste release `v26.2.1` 2026-09-26, 111 öppna issues. [belagt: GitHub API `saga-soft/novelWriter`]
*   **Zettlr**: Aktivt. Senaste push 2026-10-06, senaste release `v4.8.0` 2026-09-18, 548 öppna issues. [belagt: GitHub API `Zettlr/Zettlr`]
*   **Manuskript**: Aktivt, men långsammare. Senaste push 2026-09-01, senaste release `0.17.0` (2025-06-30), 588 öppna issues. [belagt: GitHub API `olivierkes/manuskript`]
*   **FocusWriter**: Aktivt. Senaste push 2026-10-08, senaste release `v1.9.1` 2026-07-23, 20 öppna issues. [belagt: GitHub API `gottcode/focuswriter`]
*   **KIT Scenarist**: Övergivet/Arkiverat. Senaste push 2023-08-01, release `0.7.2.rc12a` (2021-04-14), 87 öppna issues. [belagt: GitHub API `dimkanovikov/KITScenarist`]
*   **Ghostwriter**: Lågaktivt. Senaste push 2026-10-08 (mindre fixar), senaste release `2.1.6` 2022-09-14, 22 issues. [belagt: GitHub API `KDE/ghostwriter`]
*   **bibisco**: Lågaktivt m.h.a. öppna källkod-repots aktivitet. Senaste push i källan 2024-09-27, release `v2.2.0` (2020-08-23). 107 issues. [belagt: GitHub API `andreafeccomandi/bibisco`]
*   **Typst**: Extremt aktivt. Senaste push 2026-10-07, release `v0.15.1` (2026-07-17), över 1300 issues. [belagt: GitHub API `typst/typst`]

## 3. Licenser

Licenser hämtade via GitHubs API SPDX-kod för repofilen:

*   **novelWriter**: `GPL-3.0` (Copyleft)
*   **Manuskript**: `GPL-3.0` (Copyleft)
*   **Zettlr**: `GPL-3.0` (Copyleft)
*   **FocusWriter**: `GPL-3.0` (Copyleft)
*   **KIT Scenarist**: `GPL-3.0` (Copyleft)
*   **Ghostwriter**: `GPL-3.0` (Copyleft)
*   **bibisco**: `GPL-3.0` (Copyleft)
*   **Calibre / Sigil**: `GPL-3.0` (Copyleft)
*   **Pandoc**: `GPL-2.0` (Copyleft)
*   **Typst**: `Apache-2.0` (Tillåtande)

## 4. Verktyg som överlappar OmaScribe

**novelWriter** är projektet i öppen källkod som gör i stort sett exakt den grundläggande funktionen OmaScribe ämnar lösa (offline, scenbaserad text, QT-gränssnitt). [resonemang]
Det novelWriter *saknar* i relation till målbilden av ett modernt verktyg som Scrivener/Vellum/Sudowrite:
- **WYSIWYG och riktig formatering:** novelWriter tvingar användaren att skriva med Markdown-liknande syntax istället för att erbjuda en ordbehandlar-känsla (Rich Text). 
- **Modern publiceringskedja (Tryckfärdig PDF internt):** Exporten sker ofta till Pandoc för att sedan kompileras externt, vilket innebär att formatering av böcker för tryck inte kan dras/släppas och granskas direkt i programmet utan ett externt verktyg.
- **AI och assisterande teknik:** Avsaknad av inbyggd generation, formatering, grammatikkontroll eller diktering anpassat för kapitel.

Sökningen skedde via GitHub-topics (`novel-writing`, `writer`), vilket avslöjade novelWriter och Manuskript som de två största aktörerna för bokstruktureringsverktyg byggda för Linux/Windows. Ingen annan etablerad PyQt-applikation återfanns på dessa storleksnivåer (fler än 1000 stjärnor).

## 5. Konkurrensanalys: Mekaniker att låna eller rata

**Att låna:**
- **novelWriters filstruktur:** Filerna laglas externt som enkla `.nw` filer med ren text (id-baserade metadata). Detta gör programmet extremt versionshanterings-vänligt. Skrivs data till rena filer kan git ligga bakom och hantera versioner utan komplexa proprietära binärformat. [resonemang]
- **Markdown i botten:** Att låta GUI vara rich-text WYSIWYG men spara till Markdown-underlag gör konvertering till Pandoc/HTML smärtofri.

**Vad de löser sämre än betalda (Scrivener, Vellum, NovelCrafter):**
- **Sättning (Typesetting):** Manuskript och novelWriter överlämnar boksättningen till användaren (export till ODT/DOCX). Betalda verktyg som Vellum (macOS) eller Atticus löser hela publiceringen "ready-to-upload", vilket är en extrem edge.
- **Gränssnittet:** QT-gränssnitten i både Manuskript och novelWriter tenderar att kännas daterade ("programmerarverktyg") jämfört med Scriveners eleganta pärm och tavla.
- **Ingen inbyggd AI:** AI-assistans, som Sudowrite och NovelCrafter bygger sina användarbaser på, existerar inte native i i princip någon av dessa FOSS-lösningar.

## 6. Qt/PyQt-projekt och licensiering

De projekt som delar eventuell teknisk mark (PyQt / C++ Qt) med OmaScribe är:
*   **novelWriter** (Python/PyQt6) - `GPL-3.0`
*   **Manuskript** (Python/PyQt5/6) - `GPL-3.0`
*   **FocusWriter** (C++/Qt) - `GPL-3.0`
*   **Calibre** (Python/PyQt) - `GPL-3.0`
*   **Ghostwriter** (C++/Qt) - `GPL-3.0`

Dessa bär alla `GPL-3.0`-licensiering. [belagt] Detta innebär full licensförenlighet med en egen `GPL-3.0` bas för OmaScribe, vilket betyder att interna parser-moduler eller träd-widgets från dessa rent licensmässigt får inlånas förutsatt tillskrivning och identisk licens.

## 7. Luckor och rangordning 

Följande rangordnas utifrån hur mycket en oberoende författare bryr sig kontra vad det kostar att utveckla lokalt i PyQt.

1.  **Print-ready PDF / Modern Typesetting:**
    *Skäl:* Författare är oerhört betalningsvilliga (se Vellum) för verktyg som magiskt formaterar boken redo för lanseringsplattformarna (Amazon KDP, Ingram). Att integrera **Typst** som lokal binär backend i PyQt kostar relativt lite (generera Typst-markup och kör CMD), men ger ofantligt stort värde.
2.  **AI Revision & Chat (Story Bible AI):**
    *Skäl:* Mycket svårt och kostsamt att hosta externt, men att bygga PyQt-klient mot lokala Ollama eller OpenAI API (där användaren har egen nyckel) kostar lite logik att bygga in men sparar författaren från kontext-byten ut till webbläsaren. NovelCrafter gör detta via webben, lokalt är det ovanligt.
3.  **Ren, avskalad WYSIWYG Editor:**
    *Skäl:* Manuskript och novelWriter saknar riktigt njutbara skrivytor. Ett Qt WebEngine-baserat edit-block eller starkt stylad QTextEdit som känns responsiv (distraction free) löser detta. Relativt billigt att åtgärda per kod.

**Vad som inte bör byggas:**
OmaScribe bör inte försöka skriva en *egen* konverteringsmotor från start för DOCX eller EPUB; sådana filformat är extremt komplicerade och svåra att rendera korrekt. [resonemang] Pandoc, Calibre och Typst bör anropas under huven, då en författare inte bryr sig om ifall filkonverteringen utfördes av en intern modul eller en körbar tredjepartsfil, så länge gränssnittet döljer det väl och det fungerar offline. Detsamma gäller ett eget versionshanteringssystem (använd lokal git-backend eller diff för revisioner istället för att bygga hjulet).

## Vad jag inte kunde belägga

*   **Story Architects / KIT Scenarist öde:** Dimkanovikovs `KITScenarist`-repo är arkiverat, men nästa generation "Story Architect" uppfattas distribueras som binärer via stängda nät eller egna hemsidor; inget klart FOSS-repo med mätbar stjärnstatus hittades på Github under namnet `Story Architect`. UNVERIFIED.
*   **OStorybook:** Projektet verkar existera på Sourceforge snarare än aktivt main-tained på Github; en gammal version från `favdb/oStorybook` hittades men ingen daterbar modern FOSS-utveckling kunde exakt bekräftas via Github API. UNVERIFIED.
*   Ändamålsenligheten hos Quarto: Även om det är GPL-licensierat används verktyget sällan i romankrivningssammanhang. UNVERIFIED om det används av vanliga författare alls.
