# Vad ett professionellt författarverktyg har — och var OmaScribe står

Underlag för att lyfta OmaScribe från ordbehandlare till författarverktyg.
Fem externa rapporter (under denna mapp) + en mätning av vad som redan finns i koden.

## Metod, och hur mycket du bör lita på det

Fem parallella agenter (codex, en per område, en git-worktree var) researchade
webben mot förstahandskällor: Scrivener, Ulysses, Dabble, Atticus, Vellum,
NovelCrafter, Sudowrite, Word, LibreOffice, Google Docs, Pages, Typora,
ONLYOFFICE, KDP, IngramSpark, W3C med flera. Varje påstående är märkt
`[belagt: <url>]` (källa finns) eller `[resonemang]` (slutsats utan källa —
vanligtvis "så här byggs det i Qt").

Kontrollerat efteråt, av mig:

- **119 unika källänkar** — 111 svarar 200. Åtta gav 403 (botvägg hos OpenAI,
  Wiley, Atticus, CapRadio) eller tillfällig timeout hos literatureandlatte.com;
  de fyra timeouterna svarar 200 vid omkörning. Inga döda länkar.
- **Varje kodpåstående om OmaScribe** är kontrollerat mot fil och rad. Alla höll,
  utom en radhänvisning (LIX ligger på `core/document_stats.py:38-73`, inte 17-18).
- Siffertabellen i rapport 5 (KDP-marginaler, blöd, ryggbredd) är hämtad från
  Amazons egna hjälpsidor och är den enda delen som bör dubbelkollas mot KDP
  innan den blir kod — leverantörer ändrar krav.

## Var OmaScribe står i dag (mätt, inte läst ur README)

13 726 rader i `core/` + `ui/` + `main.py`, 38 moduler. Ett **dokument i taget**
öppnas i `self.editor.document` (`ui/main_window.py:663`). Två språk, sju
dokumentmallar.

Finns och fungerar: WYSIWYG, A4/Letter-sidlayout med marginaler, sidnumrering
och löpande sidhuvud/sidfot, tabeller, diagram, bilder, dokumentmallar, import
och export av `.docx`/`.md`/`.html`/`.txt`, PDF, sök & ersätt, autosparning,
ångra, anteckningsvalv med wikilänkar, AI (Ctrl+K, kodgranskning, skapa stycke,
ghostwriter), Whisper-diktering, teman, LIX-statistik, outline-panel,
helskärmsläge.

## Gapet — bordet i kategorin, och vad som saknas

Mätt med nyckelordssökning över `core/`, `ui/`, `main.py` (råutskrift i
`narvaromatris.txt`). Noll träffar betyder att funktionen inte finns; varje
träff är handgranskad, för en nyckelordsträff är en pekare och inte ett fynd
(t.ex. gav "spalt" träffar i tabellkoden och "mål" träffar i valvets wikilänkar —
ingendera är den funktion som efterfrågades).

**Saknas helt (0 träffar):**

| Område | Vad som fattas |
|---|---|
| Manusstruktur | Projektmodell: binder, kapitel, scener, synopsis, status/etiketter, samlingar |
| Revision | Spårade ändringar, snapshots/versionshistorik, dokumentjämförelse |
| Granskning | Kommentarer i marginalen med tråd och "löst" |
| Sakprosa | Fotnoter/slutnoter, korsreferenser, genererad innehållsförteckning i dokumentet, figur-/tabellregister |
| Typografi | Namngivna stycke-/teckenstilar, stilinspektör, stilmallar, avstavning, avsnittsbrytningar, spalter |
| Korrektur | Stavning/grammatik (LanguageTool), egen ordlista, tesaurus, autokorrigering/autotext |
| Skrivprocess | Mål per session/scen/projekt, deadline och dagskvot, statistik över tid, streaks, skrivmaskinsläge |
| Publicering | EPUB 3 + validering, tryckfärdig PDF (trim, blöd, ryggbredd, spegelmarginaler), DOCX med namngivna stilar, metadata/ISBN/försättssidor |
| AI-kontext | Story bible/codex som entitetsdatabas, RAG/chatt med manuset, recap per scen, stilprofil, promptbibliotek |

**Finns delvis:** helskärmsläge (`ui/main_window.py:392`) men inget
skrivmaskinsläge; outline-panel (`ui/sidebar_inspector.py:176`) men ingen
infogad innehållsförteckning; LIX/lästid men ingen stilanalys i texten;
anteckningsvalv men inget kopplat till en scen; sidhuvud/sidfot men bara ett
avsnitt, ingen spegling; sex AI-funktioner men ingen gemensam projektkontext.

**Två fel som hittades på vägen:**

- DOCX-exporten skickar inte med `page_settings` (`ui/main_window.py:807`)
  medan PDF-exporten gör det (`:747`) — en Word-fil får alltså inte samma
  sidinställningar som PDF:en.
- PDF-utskriften sätter fyra fasta marginaler (`core/doc_manager.py:230-235`)
  och speglar dem aldrig efter jämn/udda sida — vilket är precis vad en tryckt
  bok kräver.

## Förslag: sex steg, i den ordning beroenden tillåter

Stegen är min bedömning, inte agenternas. Principen är att **projektmodellen är
förutsättningen för nästan allt annat**: mål, status, snapshots, research,
story bible och kompilering hänger alla på att en scen är ett eget objekt.

1. **Projektmodellen** — ett projekt är en mapp med manifest + en fil per scen.
   Binder-träd, skapa/ordna/ta bort, spara per scen. Inget annat fungerar utan.
2. **Författarlagret** — synopsis, status och etiketter per scen, ordmål per
   scen/kapitel/projekt, deadline → dagskvot, skrivstatistik över tid, board-
   och textvy (Scrivener/Ulysses-modellen).
3. **Revisionen** — snapshot per scen, spårade ändringar, kommentarer i
   marginalen, dokumentjämförelse. Gör AI-förslag granskningsbara i stället för
   överskrivande.
4. **Sakprosan** — fotnoter, korsreferenser, genererad innehållsförteckning,
   namngivna stilar, stavning/grammatik via LanguageTool, regex-sök.
5. **Publiceringen** — EPUB 3 med validering, tryckfärdig PDF (trim, blöd,
   spegelmarginaler, ryggbredd), DOCX med riktiga Word-stilar, metadata,
   ISBN och försättssidor.
6. **AI som författarverktyg** — story bible/codex kopplad till scener, RAG och
   frågor mot manuset, recap per scen, stilprofil, promptbibliotek.

Rapporterna prioriterar internt: steg 1–3 är "hög" nästan överallt, medan
spalter, ekvationer, tesaurus, seriebibel och omslagsdesigner hamnar på "låg"
för en ensam författare och kan vänta.

## Rapporterna

| Fil | Område | Källa till |
|---|---|---|
| `01-manusstruktur-och-binder.md` | binder, scener, kort, snapshots, samlingar | Scrivener, Ulysses, Dabble, NovelCrafter, Manuskript, Vellum, Atticus |
| `02-redaktor.md` | spårade ändringar, kommentarer, noter, stilar, TOC, korrektur | Word, LibreOffice, Google Docs, Pages, Typora, ONLYOFFICE |
| `03-forfattarens-arbetsflode.md` | mål, deadlines, statistik, fokusläge, story bible, plot | Scrivener, Ulysses, Dabble, 4thewords, Writing Analytics, ProWritingAid, Sudowrite, FocusWriter, Hemingway, Obsidian |
| `04-ai-nativa-verktyg.md` | codex, RAG, recap, stilprofil, promptbibliotek, fallgropar | Sudowrite, NovelCrafter, Squibler, Lex, Type, NovelAI, Claude/ChatGPT Projects |
| `05-publicering-och-export.md` | EPUB 3, tryck-PDF, KDP-mått, DOCX-stilar, metadata | Vellum, Atticus, Scrivener, pandoc, KDP, IngramSpark, Lulu, W3C, Sigil/Calibre |
| `narvaromatris.txt` | rå mätning av OmaScribes kod mot 26 nyckelord | denna kodbas |

## Andra passet (2026-10-08): produkt för produkt, och vad som saknades

Det första passet var **tematiskt** ("hur gör de X") och täckte därför de kända
verktygen men missade de betalda specialistverktygen. Frågan den här gången var
"har vi allt de betalda har?" — alltså en funktionslista per *produkt*, uppifrån och
ned på leverantörens egen sida. Fyra agenter (codex, en git-worktree var) mot de
produkter som det första passet inte hade inventerat, plus två agenter på det öppna
och juridiska: vad de öppna verktygen gör och vilken licens som gäller.

| Fil | Område | Källa till |
|---|---|---|
| `06-betald-korrektur.md` | korrektur, stilgranskning, strukturkritik | ProWritingAid, AutoCrit, Fictionary, Grammarly Pro |
| `07-betald-planering.md` | planering, tidslinje, världsbygge | Plottr, Campfire, World Anvil, bibisco, Scapple |
| `08-betalda-sviter.md` | hela sviten, funktion för funktion | Scrivener (inkl. Compile), Vellum, Atticus, Ulysses, Dabble, Papyrus |
| `09-ai-nativa-betalda.md` | AI-verktygen och deras mekanik | Sudowrite, NovelCrafter, Squibler, NovelAI, NovelPad, LivingWriter, Novlr |
| `10-oppen-kallkod.md` | de öppna verktygen: licens, livsläge, vad de gör | Manuskript, bibisco, Zettlr, novelWriter m.fl. + sökning utanför de namnen |
| `11-licens.md` | vilken licens som gäller och vad varje alternativ betyder | PyQt6:s villkor, GNU, SPDX, jämförbara projekt |
| `luckor.md` | **sammanställningen**: vad de betalda har, vad vi har, vad som saknas | min jämförelse av 01–09 mot planen och koden |
| `VERIFIERING.md` | vilka källor och belopp jag kontrollerade själv, och vad jag inte gjorde | 95 URL:er, 9 punktkontroller |

Kort: **29 funktionsluckor** är mätta och sammanställda i `luckor.md` — 17 av dem står
nu som poster i planen (2.18–2.23, 4.17, 4.19–4.21, 5.13–5.16, 6.16–6.18), och nio
funktionsområden är förkastade med skäl. Det vi har som de betalda inte har —
projektmodellen, snapshots per scen, förslag i marginalen med accept som ett
ångra-steg, publiceringskedjan hela vägen till EPUB-validering — behålls; inget av det
byts bort mot deras funktionslistor.
