# OmaScribe 📝✨

<p align="center">
  <a href="#-english"><b>🇬🇧 English</b></a> &nbsp;•&nbsp; <a href="#-svenska"><b>🇸🇪 Svenska</b></a>
</p>

---

<a name="-english"></a>
## 🇬🇧 English

A powerful, intelligent **AI-Powered Rich Text Word-Like Editor** built with Python, Qt, and real-time DSP/Whisper dictation for Linux & Omarchy.

![OmaScribe workspace](docs/images/en/workspace.png)

*The binder, the A4 page and the inspector. More: [corkboard](docs/images/en/corkboard.png) · [publishing profile](docs/images/en/publish.png).*

Featuring A4 document canvas formatting, real-time AI review & style inspection, inline `Ctrl+K` rewriting, local Whisper speech-to-text dictation, and native `.docx`, `.pdf`, `.md`, and `.html` export!

### 🎛️ Key Features

* **📄 Full WYSIWYG Rich Text Editor:**
  * Clean A4 page layout with realistic margins, typography, headings (H1–H3), blockquotes, lists, colors, highlights, and alignment.
  * Undo/Redo history stack, Find & Replace, and autosave.

* **✨ Magic Co-Writer (`Ctrl + K`):**
  * Highlight any sentence or paragraph and press `Ctrl + K` to rewrite, make concise, expand, change tone (formal/casual), fix grammar, translate, or format.
  * Preview changes before accepting or inserting below.

* **⌨ Code Blocks and Markers:**
  * Write `[kodblock python]` … `[/kodblock]` and it becomes a real code block — monospace, shaded, and the language is remembered. `[citat]` … `[/citat]` becomes a quote.
  * The marker becomes a block the moment you close it. **Format → Format markers** (`Ctrl+Shift+M`) does the whole document at once.
  * Markers you left unclosed, or misspelled like `[kodblcok]`, are reported instead of being silently ignored.
  * Code blocks keep their language through `.md` export *and* import.

* **🔍 AI Code Review (`Ctrl+Shift+K`):**
  * Reads the code block at the cursor: what it does, what is wrong, and a correctly formatted version.
  * Apply it in place, or insert it below while keeping the original.

* **✎ Create Paragraph (`Ctrl+Shift+A`):**
  * Give an instruction ("summarise the counter-arguments") and get prose back in your own voice.

* **📑 AI Inspector Sidebar:**
  * **Review & Style:** Readability score (LIX), detected tone, and 1-click apply/dismiss suggestions.
  * **Outline:** Live document headings table of contents with 1-click jump to section.
  * **Metrics:** Real-time word count, character count, and estimated reading time.

* **🎙️ Voice Dictation (`F8`):**
  * Push-to-talk or continuous dictation powered by OpenAI's Whisper model running locally on your machine.

* **🌐 Full Bilingual Localization (i18n):**
  * Seamless instant language toggle between English and Swedish directly from the status bar, start page, or menu bar.

* **🎨 Themes & Google Fonts Catalog:**
  * Beautiful themes (Classic Paper, Dark Obsidian, Nord Arctic, Retro Amber CRT) and built-in Google Fonts downloader and manager.

* **📄 Pages, Numbering and Print Layout:**
  * Pages are separated on screen with real page breaks (`Ctrl+Enter`). Page
    numbers can sit centred, right, or alternating left/right (odd/even) — top
    or bottom — as `Page N of M`, `N`, `— N —` or `N / M`, with optional running
    header/footer text and a title page that skips the numbering.

* **🖼️ Images, Charts and Tables:**
  * Insert images (file, drag & drop, or paste) with scaling, alignment, and a
    caption. Build bar, horizontal bar, line, area, pie and donut charts from an
    editable data grid. Tab-separated data pasted from a spreadsheet becomes a
    formatted table.

* **🎨 Document Templates:**
  * Seven ready-made, print-clean templates — Report, Thesis, Minutes, Project
    Plan, Memo, Formal Letter, CV — in Swedish and English.

* **💾 Versatile Document Export & Import:**
  * Open & Save `.docx` (Microsoft Word), `.pdf` (print-quality vector PDF with preview), `.md` (Markdown), `.html`, and `.txt`.

* **⚪ Clean Documents by Default:**
  * What leaves the app is paper: white background, black text, grey rules — no
    tint from the app theme, from pasted content, or from imported files. A dark
    theme changes the application around the page, never the page itself. Charts
    are grayscale by default (colour palettes remain available for screen work),
    and embedded photos can be converted to grayscale on export. Toggle it under
    `File → Page Setup → Clean print & export`; `tools/print_purity_check.py`
    measures the contract page by page.

* **📚 Manuscript structure — the binder:**
  * A project is a folder: parts, chapters and scenes in a tree, a corkboard of scene cards, collections, and a scene inspector with synopsis, status, labels, POV and target. Word counts per scene and for the whole manuscript.
  * Research material (notes, research folders) lives in the project but outside the manuscript: it is never counted and never exported.

* **📖 Reading view:** `Ctrl+Shift+L` merges the scenes into one continuous scroll — read-only on purpose, so formatting can never land on a hidden scene.

* **🕘 Revision and review:**
  * Snapshots per scene, tracked changes you accept or reject one by one, margin comments with threads and *resolved*, compare-and-merge against any earlier point, and formatting compared separately from the text.
  * An AI suggestion is filed as a margin comment on its own quote: the manuscript stays byte-identical until you accept, and accepting costs exactly one undo step.

* **🔤 Non-fiction:** footnotes with automatic numbering, cross-references to headings, a generated table of contents, figure and table captions with lists, paragraph and character styles, autocorrect and autotext, spell and grammar check per language section, regex find & replace, blurb and synopsis fields, a story bible with a plot board, a writing log, and a name/word generator for when you're stuck.

* **📕 Publishing:**
  * A channel profile carrying the channel's own numbers — trim size, paper, margins and gutter, spine width, cover size (Amazon KDP and others) — each with its source.
  * EPUB 3 with semantic chapter structure, navigation and accessibility metadata; DOCX with named Word styles; print PDF with mirrored margins, hyphenation and dialogue dashes; a cover sheet drawn in the channel's exact measurements.
  * A release folder with checksums and a pre-flight report, and EPUBCheck offered as an option rather than a requirement.

### 🚀 Installation & Launch

```bash
git clone https://github.com/alexwest1981/OmaScribe.git
cd OmaScribe
./install.sh
```

Or run directly with `uv`:
```bash
uv run python main.py
```

---

<a name="-svenska"></a>
## 🇸🇪 Svenska

En kraftfull, intelligent **AI-driven textredigerare och ordbehandlare** byggd med Python, Qt och lokal Whisper-röstdiktering för Linux & Omarchy.

![OmaScribe arbetsyta](docs/images/sv/workspace.png)

*Projektvyn, A4-sidan och sidopanelen. Mer: [korttavlan](docs/images/sv/corkboard.png) · [publiceringsprofilen](docs/images/sv/publish.png).*

Med realistisk A4-sidlayout, AI-granskning och stilanalys i realtid, snabb omskrivning via `Ctrl+K`, lokal röst-diktering och direkt export till `.docx`, `.pdf`, `.md` och `.html`!

### 🎛️ Huvudfunktioner

* **📄 Fullfjädrad WYSIWYG-textredigerare:**
  * Tydlig A4-sidlayout med marginaler, rubriknivåer (H1–H3), citatblock, punkt- och numrerade listor, text- och överstrykningsfärger samt justering.
  * Full ångra/gör om-historik, Sök & Ersätt samt autosparning.

* **✨ Magisk Co-Writer (`Ctrl + K`):**
  * Markera valfri mening eller stycke och tryck `Ctrl + K` för att skriva om, förkorta, utveckla, ändra tonläge (formellt/avslappnat), rätta grammatik eller översätta.
  * Förhandsgranska AI-förslaget innan du godkänner eller infogar det.

* **⌨ Kodblock och markeringar:**
  * Skriv `[kodblock python]` … `[/kodblock]` och det blir ett riktigt kodblock — monospace, skuggad bakgrund, och språket sparas. `[citat]` … `[/citat]` blir ett citat.
  * Markeringen blir ett block i samma stund du stänger den. **Format → Formatera markeringar** (`Ctrl+Shift+M`) tar hela dokumentet på en gång.
  * Markeringar du lämnat öppna, eller stavat fel som `[kodblcok]`, rapporteras i stället för att tyst ignoreras.
  * Kodblock behåller sitt språk genom både export *och* import av `.md`.

* **🔍 AI-kodgranskning (`Ctrl+Shift+K`):**
  * Läser kodblocket vid markören: vad det gör, vad som är fel, och en korrekt formaterad version.
  * Applicera på plats, eller infoga under det gamla och behåll originalet.

* **✎ Skapa stycke (`Ctrl+Shift+A`):**
  * Ge en instruktion ("sammanfatta motargumenten") och få text tillbaka i din egen röst.

* **📑 AI-Granskare & Inspektör i sidopanelen:**
  * **Granskning & Stil:** Läsbarhetsbetyg (LIX), identifierat tonläge och förbättringsförslag som tillämpas med ett enda klick.
  * **Disposition:** Automatisk innehållsförteckning över dokumentets rubriker med direktnavigering.
  * **Statistik:** Ordantal, teckenantal och beräknad lästid i realtid.

* **🎙️ Röst-diktering (`F8`):**
  * Tala in text med automatisk transkribering via Whisper lokalt på din dator.

* **🌐 Tvåspråkigt gränssnitt (i18n):**
  * Direkt växling mellan svenska och engelska via statusfältet, startsidan eller menyraden.

* **🎨 Teman & Google Fonts-bibliotek:**
  * Fyra anpassade designteman (Klassiskt Papper, Mörk Obsidian, Nord Arctic, Retro Bärnsten CRT) samt inbyggd Google Fonts-katalog.

* **📄 Sidor, sidnummer och utskriftslayout:**
  * Sidorna separeras på skärmen med riktiga sidbrytningar (`Ctrl+Enter`).
    Sidnummer kan stå centrerat, till höger eller växelvis vänster/höger (udda
    och jämna sidor) — upptill eller nedtill — som `Sida N av M`, `N`, `— N —`
    eller `N / M`, med valfri löpande sidhuvuds- och sidfotstext och en titelsida
    som hoppar över numreringen.

* **🖼️ Bilder, diagram och tabeller:**
  * Infoga bilder (fil, dra-och-släpp eller inklistrat) med skalning, justering
    och bildtext. Bygg stapel-, liggande stapel-, linje-, områdes-, cirkel- och
    donutdiagram från ett redigerbart datarutnät. Tabbsepararerad data som
    klistras in från ett kalkylark blir en formaterad tabell.

* **🎨 Dokumentmallar:**
  * Sju färdiga, utskriftsrena mallar — Rapport, Avhandling, Mötesprotokoll,
    Projektplan, PM, Formellt brev och CV — på svenska och engelska.

* **💾 Flexibel dokumenthantering & Export:**
  * Öppna och spara direkt som `.docx` (Microsoft Word), utskriftsklar `.pdf` (med förhandsgranskning), `.md` (Markdown), `.html` och `.txt`.

* **⚪ Rena dokument som standard:**
  * Det som lämnar programmet är papper: vit botten, svart text, grå linjer —
    ingen ton från programmets tema, från inklistrat innehåll eller från
    importerade filer. Ett mörkt tema ändrar applikationen runt sidan, aldrig
    sidan själv. Diagram är i gråskala som standard (färgpaletterna finns kvar
    för skärmarbete) och inbäddade foton kan göras gråskaliga vid export.
    Stängs av och på under `Arkiv → Sidinställningar → Ren utskrift & export`;
    `tools/print_purity_check.py` mäter kontraktet sida för sida.

* **📚 Manusstruktur — projektvyn:**
  * Ett projekt är en mapp: delar, kapitel och scener i ett träd, en korttavla med sceneskort, samlingar och en sceninspektör med synopsis, status, etiketter, POV och mål. Ordantal per scen och för hela manuset.
  * Researchmaterial (anteckningar, researchmappar) ligger i projektet men utanför manuset: det räknas aldrig in och exporteras aldrig.

* **📖 Läsvyn:** `Ctrl+Shift+L` fogar ihop scenerna till en sammanhängande rulle — avsiktligt skrivskyddad, så att formatering aldrig kan landa i en dold scen.

* **🕘 Revision och granskning:**
  * Ögonblicksbilder per scen, spårade ändringar som du accepterar eller avvisar en i taget, marginalkommentarer med tråd och *löst*, jämför-och-slå-ihop mot vilken tidigare punkt som helst, och formateringen jämförd separat från texten.
  * Ett AI-förslag läggs som en marginalkommentar på sitt eget citat: manuset står byte-identiskt tills du accepterar, och ett accepterat förslag kostar exakt ett ångra-steg.

* **🔤 Sakprosan:** fotnoter med automatisk numrering, korsreferenser till rubriker, genererad innehållsförteckning, bild- och tabelltexter med register, stycke- och teckenstilar, autokorrigering och autotext, stavnings- och grammatikkontroll per språkavsnitt, sök och ersätt med reguljära uttryck, fält för blurb och synopsis, en story bible med plot-tavla, skrivlogg och en namn- och ordförrådsgenerator när det tar stopp.

* **📕 Publiceringen:**
  * En kanalprofil med kanalens egna siffror — trim, papper, marginaler och innermarginal, ryggbredd, omslagsmått (Amazon KDP med flera) — var och en med sin källa.
  * EPUB 3 med semantisk kapitelstruktur, navigering och tillgänglighetsmetadata; DOCX med namngivna Word-stilar; tryck-PDF med speglade marginaler, avstavning och repliktankstreck; ett omslagsark ritat i kanalens exakta mått.
  * En släppmapp med checksummor och en förhandskontroll, och EPUBCheck som ett val i stället för ett krav.

### 🚀 Installation och start

```bash
git clone https://github.com/alexwest1981/OmaScribe.git
cd OmaScribe
./install.sh
```

Eller starta direkt via `uv`:
```bash
uv run python main.py
```

---

## 🔒 Your keys, your provider

OmaScribe ships with **no API keys**. Enter your own provider and key under
`AI-Assistent → Settings` (Ollama, OpenAI, OpenRouter, Gemini, DeepSeek, a local
server, or any OpenAI-compatible endpoint).

Keys are stored in your local config, never in the code. Two rules the
installer enforces for you:

- **Never put document files in the project folder.** API keys end up in
  `.docx`/`.pdf` files people save next to their code. `install.sh` aborts if it
  finds one, and git, the wheel and the sdist all exclude them.
- **Never commit your config or `.env`.** Both are ignored.

## 📄 License
MIT License © 2026 [Alex Weström](https://github.com/alexwest1981)
