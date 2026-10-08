# Har OmaScribe allt de betalda har? — mätt, inte gissat

Frågan: *"har vi allt som de andra textredigerarna/författarverktygen har, och vad
saknas i så fall?"* Detta är svaret, byggt av mig (inte av agenterna) genom att ställa
den samlade funktionslistan från de **nio** rapporterna i denna mapp mot planen
(`task_plan.md`) och mot koden (`grep` över `core/`, `ui/`, `main.py` — noll träffar
betyder att ingen kod bär funktionen, och varje träff är handgranskad: "sätts" gav 18
träffar på TTS, "pacing" 110 på `spacing`, ingen av dem ett fynd).

Kolumnen **Vår status** är det som avgör: `kod` = finns och fungerar, `plan [~]` =
modul finns men är inte kopplad, `plan [ ]` = planerad men inte byggd, `SAKNAS` = ingen
post i planen och ingen kod.

Rapporterna: `01`–`05` (första passet: Scrivener, Ulysses, Dabble, Atticus, Vellum,
NovelCrafter, Sudowrite, Word, Docs, KDP m.fl.), `06` korrektur, `07` planering,
`08` betalda sviter, `09` AI-nativt.

## 1. Publicering och utskrift

| Funktion | Vem har den | Vår status |
|---|---|---|
| Formatprofiler per kanal (trim, blöd, gutter) | KDP/Vellum/Atticus | `plan [~]` 5.1 — `core/publishing.py` finns, inte kopplad |
| **Kompilera ett URVAL** (draft/grupp/aktiv markering/sökträff/samling → platt lista) | Scrivener (belagt i manualen) | **SAKNAS** — 5.9 släpper hela boken, inget urval |
| **Flera sparade utskriftsprofiler per bok** (olika mål per kanal) | Scrivener Compile | **SAKNAS** — 5.1 är "kvar: ett sparat publiceringsprojekt per bok" |
| Kapitelnumrering, prefix/suffix, filnamnsmall per kapitel, **separata filer per kapitel** | Scrivener Compile | **SAKNAS** |
| Front matter som genererade sidor | Scrivener, Vellum | `plan [~]` 5.4 — titel + kolofon i EPUB; dedikation/tack kvar |
| **Scenbrytning som ornament, versblock, meddelandeblock, inline-bild** som textelement | Vellum | **SAKNAS** (koden har bara `***` vid DOCX-konvertering) |
| **widow/orphan-kontroll** | Vellum | **SAKNAS** |
| **PDF/X-1a:2003, CMYK, SWOP v2, inbäddade teckensnitt** (tryckerikrav) | Vellum (`vellum.pub/specs`) | **SAKNAS** — PDF utan X-1a/CMYK |
| **Normseite: 30 rader × max 60 tecken** för förlagsinlämning | Papyrus 12 | **SAKNAS** — ordagrant belagt hos Papyrus |
| Large print-utgåva | Atticus | **SAKNAS** |
| Tillgänglighetskontroll med Ace by DAISY | Vellum | `plan [x]` 5.8 — EPUBCheck finns; Ace är en annan kontroll |
| Direktpublicering till WordPress/Ghost/Medium | Ulysses | **SAKNAS** — medvetet: nätverksskrivning med credentials |

## 2. Korrektur, stil och granskning

| Funktion | Vem har den | Vår status |
|---|---|---|
| Stavning/grammatik | Grammarly, PWA, LanguageTool | `kod` 0b.3/4.10 |
| Läsbarhet (LIX) + markering av tunga meningar | Papyrus, PWA, Hemingway | `kod` 2.15 |
| **Repetitionsanalys över hela boken** ("All Repeats"/"Echoes") | ProWritingAid, AutoCrit | **SAKNAS** (0 träffar) |
| **Konsistenskontroll: namn/stavning/versalisering/bindestreck genom boken** | ProWritingAid, AutoCrit | **SAKNAS** (0 träffar) — codexet har redan namnen |
| **Fyllnadsord, adverb, passiv form, klichéer, dialogtaggar** | PWA, AutoCrit, Papyrus | **SAKNAS** (0 träffar) |
| **Showing-vs-telling, pacing, POV/tempus-drift** | AutoCrit (Story Analyzer+) | **SAKNAS** |
| **Klickbar rapport med länkar tillbaka till stället i texten, per kapitel** | PWA, AutoCrit, Fictionary | **SAKNAS** |
| Kapitelkritik och helmanusanalys | PWA (Chapter Critique, Manuscript Analysis), AutoCrit | `plan [ ]` 6.9 (prosakritik/redaktörspass) |
| Genrejämförelse, marketability, beta reader-perspektiv | PWA, AutoCrit | **SAKNAS** — förkastas nedan |
| Uppläsning för korrekturläsning ("read-to-me") | Dabble (Author), AutoCrit, NovelAI TTS | **SAKNAS** (Whisper är tal→text, inte omvänt) |

## 3. Författarlagret: scener, struktur, analys

| Funktion | Vem har den | Vår status |
|---|---|---|
| Projektmodell, binder, korktavla, synopsis, status, etiketter, samlingar, ordmål, snapshots | Scrivener | `kod` fas 0–1, 3 |
| **Scenens story-element-checklista** (Fictionary: 38 element — POV+mål, scenfunktion, hook, tension, revelation, action/sequel, läsarens vetande, plats/tid, sinnen, emotion, väder) + Story Map | Fictionary StoryTeller | **SAKNAS** |
| **Scenstatistik: scener per karaktär, karaktärernas inträde/utträde, POV-fördelning, ord per scen** | Fictionary, bibisco | **SAKNAS** — men allt underlag finns i modellen |
| **Beat sheet-mallar som data** (Save the Cat, Hero's Journey, mysteriemallar) | Plottr (20+), Campfire | **SAKNAS** — 1.12 har projektmallar (struktur), inte beats |
| **Tidslinje som ritad vy med återanvändbara händelser kopplade till scener** | bibisco, World Anvil, Plottr | `plan [ ]` medvetet avstod i 2.9 — återöppnas nedan |
| Spår/plotlines med kort i skärningspunkter | Plottr | `plan [x]` 2.9 som *kolumn* (tråd), ingen dra-och-släpp-yta |
| Filter på flera axlar (karaktär/plats/tagg/färg/egna attribut) | Plottr, Scrivener Collections | `plan [x]` 1.9/2.9 delvis |
| **Karaktärsintervju** (frågeformulär per karaktär) | bibisco | **SAKNAS** |
| Revisionsläge, utkast, spårade ändringar, kommentarer, dokumentjämförelse | Word, Scrivener, Dabble | `kod` fas 3 |
| Fri canvas / mindmap | Scapple, bibisco | **SAKNAS** — låg prioritet |

## 4. Codex, värld och kontinuitet

| Funktion | Vem har den | Vår status |
|---|---|---|
| Entitetsdatabas med alias, fält, relationer, koppling till scen | Scrivener, NovelCrafter, Campfire | `kod` 0b.5 + 2.8 |
| **Relationsgraf / familjeträd som ritad vy** | Campfire, World Anvil | **SAKNAS** — men `ui/graph_dialog.py` ritar redan valvets graf, så skalet finns |
| Fler entitetstyper: kulturer, religioner, arter, föremål, system | Campfire (moduler), World Anvil | `plan [x]` 0b.5 som generiska typer (fälten är fria) |
| **Kalender/era och parallella tidslinjer** | World Anvil, Campfire Calendar | **SAKNAS** |
| Kartor med markörer och lager | World Anvil, Campfire | **SAKNAS** — förkastas nedan |
| Wiki-artiklar med korslänkar och mallar per typ | World Anvil | `kod` delvis (valvet med wikilänkar, codex-poster) |
| Seriebibel över flera böcker | Plottr (Series), NovelCrafter | `plan [ ]` 6.13 |

## 5. AI

| Funktion | Vem har den | Vår status |
|---|---|---|
| Skriv om/utöka/korta/beskriva på markerad text | Sudowrite, NovelAI, Squibler | `kod` (Ctrl+K, ghostwriter, "Fastnat?") |
| **Kontextvisaren: visa exakt vilken text och vilka bibelposter som skickas, med tokenräkning och varför** | NovelAI (färgkodad Context Viewer) | **SAKNAS** — men det är redan ett *Designkrav* i planen ("Visa vilka textdelar som faktiskt skickas") |
| **Valbar kontext per anrop**: bocka i scener/kapitel/akter/snippets; codex per post alltid / vid omnämning / aldrig | NovelCrafter (+Context, AI Context per post) | **SAKNAS** — fördjupar 6.3/6.4 |
| **Automatiskt relevant urval av bibelposter** | Sudowrite (Saliency Engine), NovelAI (nyckelmatchning/cascading) | **SAKNAS** |
| **Story Bible-generering som flöde** (braindump → genre → stil → synopsis → karaktärer → värld → outline → scener) | Sudowrite | **SAKNAS** — 6.1/6.6 täcker delarna, inte flödet |
| Scenbeats → prosa | NovelCrafter (Scene Beat Completion) | `plan [ ]` 6.5/6.6 |
| Förslag i granskningskö med accept per stycke, aldrig direkt i manuset | NovelCrafter, Sudowrite | `kod` 3.7/3.8 — vi ligger före |
| Samtalshistorik per projekt | NovelCrafter, Squibler | `plan [ ]` medvetet uppskjutet (4.18) |
| Promptbibliotek, modellval, kostnad per uppgift | NovelCrafter, Sudowrite, Squibler | `plan [ ]` 6.11/6.12; egen API-nyckel finns redan (`kod`) |
| AI-bildgenerering | NovelAI, LivingWriter | **SAKNAS** — förkastas nedan |

## Vad som bör byggas, i ordning

Billigt och avgörande (dagar, inte veckor):

1. **Normsidan (30 × 60)** — `core/pagination.py` finns redan, det är en sidmall.
2. **Scenbrytning, versblock och meddelandeblock** som textelement i alla tre kanaler.
3. **Repetitions- och konsistensanalys över hela boken, med klickbara träffar.** Ren
   lokal kod: scenerna indexeras, codexets namn ger konsistensen. Detta är den största
   enskilda funktionsluckan mot ProWritingAid/AutoCrit.
4. **Scenstatistik ur befintlig modell** — scener per karaktär, POV-fördelning, ord per
   scen, karaktärernas inträde/utträde.
5. **Beat sheet-mallar som data** i `core/templates.py`-mönstret (Save the Cat, tre
   akter, mysterieformeln).
6. **Kontextvisaren** — Designkravet vi redan lovat, och NovelAI visar hur litet det är.
7. **Uppläsning** för korrekturläsning med örat (Alex har redan TTS-leverantörer).
8. **Karaktärsintervjun** — frågor, svar i codexposten, via befintlig AI-klient.

Medelstora, efter ovanstående:

9. **Kompilera ett urval + flera utskriftsprofiler** (Scrivener Compile) — hör till 5.1/5.9.
10. **Scenens story-element-checklista + Story Map** (Fictionary) — datamodellen finns.
11. **Valbar kontext per anrop + relevansurval** (NovelCrafter/Sudowrite) — 6.3/6.4.
12. **Relationsgraf/familjeträd i codexet** — återanvänd `ui/graph_dialog.py`.
13. **Utkastkritik per kapitel som klickbar rapport** (6.9).
14. **widow/orphan + PDF/X-1a + large print** — hör till tryckkedjan i fas 5.

## Vad som inte bör byggas

- **Molnsynk, realtidssamarbete, iOS-app** (Dabble, Ulysses, Campfire): kräver drift och
  backend; hela poängen med OmaScribe är att boken är en lokal mapp.
- **Kartredigerare med lager** (World Anvil, Campfire): dyrt, nischat.
- **Marknadsplats, community, kursakademi, läsarprenumerationer** (World Anvil, AutoCrit).
- **Kreditvaluta och egen grundmodell** (Sudowrite, NovelAI): dubblar leverantörens
  infrastruktur. Vi använder användarens egen nyckel.
- **Plagiatdatabas och AI-textdetektion** (PWA, Grammarly): kräver extern databas, och
  detektorns utfall är inte säkert bevis (AutoCrit/HelloWriter-klassen är omstridd).
- **Genrepoäng och "marketability"** (PWA, AutoCrit): ett betyg som inte går att belägga
  lokalt, och AutoCrit säger själv att 100 % inte är målet.
- **Direktpublicering till WordPress/Medium** (Ulysses): nätverksskrivning med
  användarens credentials i ett program som lovar offline.
- **AI-bildgenerering, screenplay-konvertering, butiksuppladdning**: integrationskostnad
  utanför kärnan. (Omslagsarket är geometri och stannar.)

## Två beslut till Alex

- 🟠 **Tidslinjen**: planen avstod medvetet från en ritad tidslinje (2.9: "texten i
  `when` sorterad i tid är tidslinjen"). Tre betalda verktyg har den (bibisco, Plottr,
  World Anvil) och rapporten rankar "tidslinje med händelser kopplade till scener" högt.
  Den är medelstor, inte liten: en händelsetabell kopplad till scen-id kan byggas utan
  ny ritad vy, och vyn ovanpå den är ett eget steg. Säg till om händelsetabellen skall in.
- 🟠 **Licensen är avgjord och byggd** — `GPL-3.0-only`, tvingad av PyQt6 (Riverbanks egen
  rad: "PyQt is dual licensed on all supported platforms under the GNU GPL v3 and the
  Riverbank Commercial License. Unlike Qt, PyQt is not available under the LGPL.").
  `LICENSE`, `pyproject.toml` och `Hjälp → Om OmaScribe` bär den, och hjulet är byggt och
  kontrollerat. Andra åsikten (`11-licens.md`) landar i samma identifierare. Det som
  återstår är inte tekniskt: vill du skydda **namnet** OmaScribe är varumärket det enda
  som gör det — licensen täcker koden, inte identiteten.

## Den öppna sidan (R10) — vad de andra öppna verktygen gör

Alla relevanta öppna skrivverktyg bär **GPL-3.0** (novelWriter, Manuskript, Zettlr,
FocusWriter, Ghostwriter, KIT Scenarist, bibisco, Calibre, Sigil) — alltså samma licens som
OmaScribe nu tvingas till, och därför förenliga att läsa och låna mönster från, förutsatt
tillskrivning. Typst är Apache-2.0, Pandoc GPL-2.0.

Den närmaste grannen är **novelWriter** (PyQt6, GPL-3.0, aktivt: pushad 2026-10-07,
v26.2.1 2026-09-26, 3 172 stjärnor). Det gör offline, scenbaserat, med metadata per scen.
Det som saknas där är exakt det vi har: WYSIWYG i stället för markup, egen tryckfärdig
sättning i stället för Pandoc, och AI/diktering. **Manuskript** (2 446 stjärnor) har
indexkort, versioner och Snowflake-metoden men exporterar via Pandoc och är daterat i
gränssnittet. **KIT Scenarist är arkiverat** (senaste push 2023-08-01) och **bibiscos
öppna repo är vilande** (2024-09-27) — de är inte alternativ någon väljer i dag.
**oStorybook**: mätt nu, 7 stjärnor, senaste push 2023-10-24. Det finns alltså **ingen
öppen konkurrent som gör publiceringskedjan**: de öppna verktygen slutar där de betalda
börjar (Vellum/Atticus).

### Utvärderat och avvisat: anropa Pandoc/Typst/Calibre under huven

Rapport 10 föreslår att lägga Typst eller Pandoc som lokal backend i stället för att
underhålla egen konvertering, och kallar det "relativt lite" arbete. Det är inte byggt och
blir ingen planpost, av tre skäl som är mätta, inte tyckta:

1. **Kedjan finns och är provad.** `core/epub.py`, `core/doc_manager.py` och
   `ui/main_window.py` skriver EPUB 3, DOCX med namngivna Word-stilar och PDF, och grinden
   läser tillbaka filerna (EPUB:en packas upp och OPF:en kontrolleras i rökprovet). En
   extern binär hade bytt en verifierad väg mot en oprövad.
2. **Ett externt program är ett nytt krav på användarens maskin.** Paketering, uppdatering
   och felmeddelanden när binären saknas är arbete som inte syns i en jämförelsetabell.
3. **Det löser inget vi saknar i dag** — luckorna i publiceringen är normsidan,
   widow/orphan, PDF/X-1a och urvalskompilering, och ingen av dem kräver Typst.

Där står det kvar som ett *val*: vill du ha PDF/X-1a ur en färdig typsättningsmotor är
Typst den billigaste vägen dit (5.16), men det är i så fall ett medvetet nytt beroende, inte
en omskrivning av det som fungerar.

Det öppna projektet bekräftar också vårt filformat: novelWriter sparar scener som enkla
textfiler med id-baserad metadata "vilket gör programmet extremt versionshanteringsvänligt"
— samma val OmaScribe gjorde med `project.json` + en HTML-fil per scen.

## Vad den här sammanställningen inte är

De elva rapporterna är webresearch mot leverantörernas egna sidor och mot GitHub-API:et —
inget av det säger något om hur svårt något är att bygga här, och kostnadsuppskattningarna i
"i ordning" är mina, inte agenternas. Siffertabeller hos leverantörer ändras; se
`VERIFIERING.md` för vilka belopp och påståenden som är kontrollerade av mig och vilka som
inte är det.
