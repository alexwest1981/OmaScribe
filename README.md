# OmaScribe 📝✨

<p align="center">
  <a href="#-english"><b>🇬🇧 English</b></a> &nbsp;•&nbsp; <a href="#-svenska"><b>🇸🇪 Svenska</b></a>
</p>

---

<a name="-english"></a>
## 🇬🇧 English

A powerful, intelligent **AI-Powered Rich Text Word-Like Editor** built with Python, Qt, and real-time DSP/Whisper dictation for Linux & Omarchy.

![OmaScribe Screenshot](screenshot.png)

Featuring A4 document canvas formatting, real-time AI review & style inspection, inline `Ctrl+K` rewriting, local Whisper speech-to-text dictation, and native `.docx`, `.pdf`, `.md`, and `.html` export!

### 🎛️ Key Features

* **📄 Full WYSIWYG Rich Text Editor:**
  * Clean A4 page layout with realistic margins, typography, headings (H1–H3), blockquotes, lists, colors, highlights, and alignment.
  * Undo/Redo history stack, Find & Replace, and autosave.

* **✨ Magic Co-Writer (`Ctrl + K`):**
  * Highlight any sentence or paragraph and press `Ctrl + K` to rewrite, make concise, expand, change tone (formal/casual), fix grammar, translate, or format.
  * Preview changes before accepting or inserting below.

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

* **💾 Versatile Document Export & Import:**
  * Open & Save `.docx` (Microsoft Word), `.pdf` (print-quality vector PDF with preview), `.md` (Markdown), `.html`, and `.txt`.

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

![OmaScribe Skärmdump](screenshot.png)

Med realistisk A4-sidlayout, AI-granskning och stilanalys i realtid, snabb omskrivning via `Ctrl+K`, lokal röst-diktering och direkt export till `.docx`, `.pdf`, `.md` och `.html`!

### 🎛️ Huvudfunktioner

* **📄 Fullfjädrad WYSIWYG-textredigerare:**
  * Tydlig A4-sidlayout med marginaler, rubriknivåer (H1–H3), citatblock, punkt- och numrerade listor, text- och överstrykningsfärger samt justering.
  * Full ångra/gör om-historik, Sök & Ersätt samt autosparning.

* **✨ Magisk Co-Writer (`Ctrl + K`):**
  * Markera valfri mening eller stycke och tryck `Ctrl + K` för att skriva om, förkorta, utveckla, ändra tonläge (formellt/avslappnat), rätta grammatik eller översätta.
  * Förhandsgranska AI-förslaget innan du godkänner eller infogar det.

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

* **💾 Flexibel dokumenthantering & Export:**
  * Öppna och spara direkt som `.docx` (Microsoft Word), utskriftsklar `.pdf` (med förhandsgranskning), `.md` (Markdown), `.html` och `.txt`.

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

## 📄 License
MIT License © 2026 [Alex Weström](https://github.com/alexwest1981)
