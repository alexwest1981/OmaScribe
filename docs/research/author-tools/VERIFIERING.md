# Verifiering av de nio rapporterna

Agenters påståenden är självrapporter. Detta är min egen kontroll av de fyra nya
rapporterna (06–09), gjord 2026-10-08. Rapporterna 01–05 kontrollerades i det första
passet (`README.md`: 119 källänkar, 111 svarade 200, alla kodpåståenden mot fil och rad).

## Länkkontroll

95 unika URL:er i rapporterna 06–09, hämtade med webbläsar-UA och 20 s om timeout:

- **90 svarar 200.**
- **5 svarar 403** — samtliga `worldanvil.com` (botvägg, inte en död sida). Det betyder
  att World Anvils prisuppgifter i rapport 07 ($4,50 / $8,25 per månad) **inte är
  kontrollerade av mig** och inte får citeras som fakta. Artikel-/tidslinjebeskrivningarna
  kommer från samma domän och bär samma förbehåll.

## Punktkontroll av det jag tänker luta mig mot

Varje rad: påståendet i rapporten → vad jag själv fick ur källan.

| Påstående | Källa | Utfall |
|---|---|---|
| Fictionary: 38 story-element per scen | `fictionary.co/support/help-docs/evaluate/` | **Håller ordagrant:** "providing 38 Story Elements for Character, Plot, and Setting" |
| Papyrus: normseite = 30 rader × 60 tecken | `support.papyrus.de/wiki/…normseiten…` | **Håller ordagrant:** "30 Zeilen zu je (maximal) 60 Zeichen (ohne Silbentrennung)" |
| Vellum: PDF/X-1a:2003, ISO 15930-1, CMYK, SWOP v2, inbäddade teckensnitt | `vellum.pub/specs/` | **Håller.** Däremot hittade jag inte strängen "EPUB 3" på samma sida — rapportens "EPUB 2/3" är inte kontrollerad |
| NovelAI: Context Viewer med tokenbudget och trimning | `docs.novelai.net/en/text/editor/advancedsettings/` | **Håller:** "Context Viewer" + Context Settings "budgeted, positioned, and trimmed within your Context limit" |
| ProWritingAid: Chapter Critique, Plot Analysis, Character Analysis, Manuscript Analysis, Virtual Beta Reader, Marketability Analysis, Premium/Premium Pro, Lifetime | `prowritingaid.com/pricing` | **Håller** — samtliga namngivna funktioner står på prissidan |
| AutoCrit: Story Analyzer+, genrejämförelse, Grammar Checker, Book Formatting | `autocrit.com/pricing` | **Håller** i navigering/funktionslista. Rapporternas antal ("25+") kontrollerade jag inte siffra för siffra |
| Sudowrite: Story Bible med Braindump/Genre/Style/Synopsis/Characters/Worldbuilding/Outline/Scenes + Saliency Engine | `feedback.sudowrite.com/…what-is-story-bible`, `…saliency-engine` | **Håller** — båda artiklarna finns med de namnen |
| Scrivener: Corkboard, Collections, Compile till Word/PDF/Final Draft/e-bok | `literatureandlatte.com/scrivener/overview` | **Håller** för översikten. Listan över Compile-flikar kommer ur Mac-manualens PDF och är **inte** kontrollerad av mig rad för rad |

## Vad jag inte kontrollerade

- **Prisbelopp** i rapport 06 och 09 (ProWritingAid $30/$36, AutoCrit $30, Fictionary
  $19/$39, Sudowrite $10/$22/$44, Squibler $29,99, NovelAI $10/$15/$25). De står på
  prissidor jag hämtade, men en prissida är en kampanjyta: beloppen får inte bli kod
  eller löfte utan en ny kontroll vid köptillfället.
- **World Anvils priser** (403, se ovan).
- **Compile-flikarnas fullständiga lista** per OS (Scrivener-manualen, en PDF).
- **Fictionarys 38 elements exakta namn** — antalet håller, listan i rapporten är
  agentens läsning av Evaluate-sidorna, inte min.

## Korrigeringar

- Rapport 09:s rubrikrad är kvar från briefen ("Research-brief D: de AI-nativa
  betalverktygen") i stället för en egen titel. Innehållet är rätt; rubriken är kosmetisk
  och står kvar som spår av att den skrevs mot en brief.
