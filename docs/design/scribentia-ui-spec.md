# Scribentia — UI-spec från v0-referensen

Referens: `scribentia-ui-design.zip` (v0-export, Next.js + Tailwind-skal men all formgivning i
`app/globals.css` som ren CSS med egna klassnamn). Markup: `app/page.tsx`.

**Referensens värden är specen.** Allt nedan är läst ur `globals.css`, rad för rad. Där ett värde
inte står här är det inte mätt och får inte hittas på. Avvikelser från referensen listas sist som
medvetna val, med skäl.

## 1. Färger (referensens `:root`)

| Namn | Värde | Var den används |
|------|-------|-----------------|
| `--ink` | `#1d2630` | brödtext i appen, "Lägg på manuset"-knappen, brand-mark-bakgrund `#1e2937` |
| `--muted-ink` | `#87909b` | dämpad text |
| `--line` | `#e7e9ed` | **alla** avdelare i appskalet: topbar, rail, toolbar, statusbar, inspector |
| `--canvas` | `#f4f5f7` | ytan runt papperet |
| `--blue` | `#3366ff` | accent: aktiv rail-ikon, kicker, h1-em, sektionsnummer, blockquote-kant, aktiv flik, ring |
| `--lavender` | `#7966ed` | aktiv "Inspector"-knapp (`#f0efff` bakgrund, `#6253db` text), tonchip |

Sidofärger utanför tokens: papper `#ffffff`, papperstext `#29323c`, sparat-punkt `#3eb68a`,
avatar `#dce6ff`/`#4a68b7`, hover-yta `#f2f4f7`, chip-grön `#5b8d79`/`#eff8f3`,
varnings-chip `#e5a23b`/`#fff5e5`, blå chip `#6a8bdc`/`#edf2ff`, kort-yta `#f7f8fb`,
"listening" `#ed6a68`.

## 2. Mått och rytm

| Del | Mått |
|-----|------|
| topbar | höjd **64**, `padding 0 22px 0 20px`, vit, `border-bottom 1px --line` |
| brand-mark | **31×31**, radie **10**, Georgia 19px, skugga `0 2px 5px #1e293744` |
| brand-name | 15px/700, `letter-spacing -.02em` |
| avdelare i topbar | 22×1px, `margin 0 8px` |
| vänsterrail | bredd **66**, `padding 18px 12px`, kolumn, `gap 10` |
| rail-knapp | **40×40**, radie **11**; aktiv: bakgrund `#eef2ff`, text `--blue` |
| editortoolbar | `min-height 58`, `padding 0 23px`, `gap 3` i gruppen |
| toolbar-knapp | höjd **34**, `min-width 32`, radie **7**, `padding 0 8`; aktiv/hover `#f1f3f6` |
| toolbar-avdelare | 20×1px, `margin 0 6px` |
| dokumentyta | `padding 28px 34px 54px` |
| papper | `max-width 750`, `min-height 900`, `padding 70px 88px 62px`, skugga `0 5px 22px #26354d0d` |
| metarad | `max-width 750`, `margin 0 auto 13px`, 10px, `letter-spacing .12em` |
| statusbar | höjd **43**, `padding 0 25px`, `gap 19` |
| inspector | bredd **312**, `padding 28px 22px 21px` i huvudet, `20px 22px` i innehållet |
| kort | radie **12**, `padding 15`, bakgrund `#f7f8fb` |
| ring | 52×52, `border 4px #cdd8ff`, `border-right-color --blue` |
| chip | radie 99, `padding 5px 8px` |
| kbd | `padding 2px 5px`, radie 4 |
| brytpunkter | 1000px (inspector 280, papper 58px marginal), 760px (inspector bort, rail 52) |

## 3. Typskala

| Roll | Typsnitt | Storlek | Radhöjd | Spärr |
|------|----------|---------|---------|-------|
| appskal | Arial/Helvetica | – | – | – |
| brödtext (papper) | Georgia, 'Times New Roman' | 15px | 1.7 | – |
| h1 (papper) | Georgia | `clamp(48,6vw,68)` | .94 | −.06em, vikt 400 |
| dek | – | 18px | 1.45 | max-bredd 445 |
| lead | – | 17px | 1.65 | – |
| sektionsrubrik | – | 23px | – | −.03em, vikt 500 |
| sektionsnummer | Arial | 11px | – | vikt 700, `--blue` |
| kicker | Arial | 10px | – | .2em, vikt 700, `--blue` |
| citat | Georgia | 18px | – | kursiv, vänsterkant 2px `--blue` |
| metarad/eyebrow | Arial | 10px | – | .12em / .15em |
| inspector-h2 | – | 21px | – | −.04em |
| metrik-tal | – | 22px | – | −.05em |
| knappar | – | 10–13px | – | – |

## 4. Anatomi (referensens ordning uppifrån)

1. **topbar** — brand-mark + "Scribentia" + avdelare + dokumentknapp (filnamn + fäll) · till höger:
   sparat-läge med grön punkt, Ångra, Gör om, Hjälp, avatar.
2. **vänsterrail** (66px) — fyra ikoner: aktuellt dokument (aktiv), öppna filer, mallar; skjuts ned,
   Inställningar.
3. **editortoolbar** — typsnitt, storlek, B/I/U, överstrykning, justering v/h/centrerat, punktlista,
   numrerad lista, bild, tabell, kod; längst till höger "Inspector"-växlaren.
4. **dokumentyta** — metarad över papperet (vänster: dokumenttitel i versaler, höger: "Last edited
   today · 10:42"), papperet (kicker, h1 med kursiv accent i `--blue`, dek, linje, lead,
   sektionsrubriker med nummer, citat med vänsterkant, punktlista, sidfot), sidnummer "01 / 04".
5. **statusbar** — vänster: ordantal, lästid, språk; höger: Diktera med `F8`, "Page 1 of 4".
6. **inspector** (312px) — eyebrow "AI INSPECTOR", rubrik, stäng; flikar **Review / Outline /
   Metrics**; Review: betygskort med ring, tonchips, förslagslistor med åtgärdsknapp,
   "Rewrite selection ⌘K"; Outline: numrerade punkter med aktiv markering; Metrics: 2×2 rutnät med
   stora tal.

## 5. Mappning mot Scribentia (allt referensen visar finns redan)

| Referens | Scribentia |
|----------|-----------|
| inspector-flikarna Review/Outline/Metrics | `ui/sidebar_inspector.py` har **exakt** dessa tre flikar (`tab_review`, `tab_outline`, `tab_metrics`) |
| betygskort + förslag + åtgärdsknapp | `tab_review` (`apply_suggestion_requested`) |
| Outline-listan | `tab_outline` (`outline_item_clicked`) |
| Metrics-rutnätet | `tab_metrics` + `core/document_stats.py` |
| editortoolbaren | `ui/toolbar.py` (`FormattingToolBar`) |
| papperet + sidfot + sidnummer | `ui/editor_view.py` (sidvis vy, sidmärken, sidfot) |
| statusbaren | `QStatusBar` med `lbl_stats`, ai, diktering, markör, språkväxlare |
| Diktera `F8` | `core/dictation_engine.py` (`toolbar.dictation_clicked`) |
| sparat-läge | `is_modified` + autosparande |

## 6. Medvetna avvikelser från referensen

| Avvikelse | Skäl |
|-----------|------|
| Menyraden behålls, inuti topbaren | Referensen är en webbsida och kan inte visa en menyrad; appens ~100 kommandon nås där. Formges med samma tokens. |
| Avataren ("AW") tas bort | En privat användare — en avatar är dekoration utan funktion. Referensens *innehåll* är inte dess designsystem. |
| "Project Northstar", "1,248 words", betyg 82, "English (UK)" | v0:s påhittade innehåll. Ersätts med appens verkliga data. |
| Dokumentets egen typografi (Georgia-h1 m.m.) blir en **mall**, inte tvingad stil | Appens regel: temat ändrar applikationen runt sidan, aldrig sidan själv. Referensens papperstypografi läggs i `core/templates.py` så användaren kan välja den. |
| Papperets ram (750px, vit, centrerad på canvas) följer referensen | Det är skal, inte dokumentinnehåll. |
| **Skuggan under papperet är utelämnad** | `QGraphicsDropShadowEffect` renderar om hela editorn till en pixmap vid varje tangenttryckning — för dyrt i ett skrivverktyg för en nyans på 5 % alfa (`0 5px 22px #26354d0d`). |
| **Ikoner är emoji, inte lucide-linjeikoner** | Appen har inga SVG-tillgångar (`resources/icons` är tom). 35 ikoner skulle behöva vendas in som filer; egen omgång om det ska bli exakt. |
| **Flikraden i panelen skrollar** | Panelen är 312 som referensen, men appen har fem flikar mot referensens tre. Skrollpilar visas i stället för att texten klipps. |
| **A4-höjd i stället för referensens `min-height: 900`** | 900 är ett skärmvärde i mocken; appens papper följer användarens sidinställning (750 × 1,414 ≈ 1060). |
| **Sidans textspalt har appens dokumentmarginal kvar** | Referensens 88px inre marginal nås via ramens 52px + dokumentets egen 36px marginal, så spaltbredden blir densamma (574px) utan att röra dokumentets egen layout. |

