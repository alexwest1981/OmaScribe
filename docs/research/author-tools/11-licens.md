# Rapport: Licensval för OmaScribe

Denna rapport utreder vilken licens som är möjlig och lämplig för skrivbordsprogrammet OmaScribe (PyQt6). Syftet är att säkerställa att upphovsmannen ("du") behåller erkännandet (attribution) och att källkoden, samt all vidareutveckling av den, förblir öppen och fri.

## 1. PyQt6 och dess licensvillkor

När du bygger ett program med PyQt6 och inte har köpt en kommersiell licens från Riverbank Computing, är biblioteket licensierat under GNU General Public License v3 (GPL-3.0). Riverbanks egen dokumentation fastslår: "PyQt is dual licensed on all supported platforms under the GNU GPL v3 and the Riverbank Commercial License." [belagt: https://www.riverbankcomputing.com/software/pyqt/]

GPL är en starkt "smittande" (copyleft) licens. Det innebär att all mjukvara som länkar till eller distribueras tillsammans med PyQt6 måste göras tillgänglig under GPL-kompatibla villkor. Du tvingas därmed släppa det kombinerade OmaScribe-programmet under GPL-3.0.

När det gäller `GPL-3.0-only` vs `GPL-3.0-or-later`: Om ett beroende, som PyQt6, uttryckligen distribueras som "GPL-3.0-only" betyder det att programmet som helhet inte kan ta del av hypotetiska framtida villkor i en GPL-4.0. Din egen kod *får* licensieras som `GPL-3.0-or-later`, men när paketet distribueras i kombinerad, exekverbar form med PyQt6 är det `GPL-3.0-only` som sätter det praktiska taket för distributionen. Det säkraste och mest transparenta för ett PyQt6-projekt är därför att använda SPDX-identifieraren `GPL-3.0-only` för helheten.

## 2. Skillnaden mellan GPL, AGPL, LGPL, MPL och tillåtande licenser

När man vill undvika att andra tar koden och "gör den till sin egen" i stängda produkter, faller tillåtande licenser omedelbart bort:
- **MIT / Apache-2.0:** Vem som helst får ta din kod, stänga källkoden, bygga om den till en kommersiell och proprietär produkt, så länge de behåller en copyright-text gömd i en meny.
- **LGPL-3.0:** Svag copyleft. Tillåter att någon bakar in din kod som ett bibliotek i ett stängt program. (I OmaScribes fall stänger PyQt6 redan denna dörr).
- **MPL-2.0:** Copyleft på filnivå. Någon kan lägga till stängd kod i nya filer och sälja helheten.
- **GPL-3.0:** Stark copyleft. Detta är standarden för skrivbordsprogram i C++ och Python (särskilt med PyQt). Om någon vill bygga vidare på, eller distribuera systemet, måste hela det resulterande programmet släppas fritt med öppen källkod under samma villkor.
- **AGPL-3.0:** Adderar en extremt stark klausul för nätverkstjänster. Den stänger "SaaS-kryphålet" (se fråga 3).

Ett typiskt PyQt6-skrivbordsprogram väljer GPL-3.0, dels för att Riverbank tvingar dem, och dels för att det exakt skyddar koden mot stängd appropriering.

## 3. Vad GPL-3.0 hindrar och tillåter

GPL-3.0 reglerar distribution och modifiering, men lägger inga hinder för försäljning eller användning.
- **Får någon sälja programmet?** Ja. GPL tillåter vem som helst att sälja kopior av den öppna programvaran (och ta betalt för tjänsten att ladda ned/hjälpa till), men de måste samtidigt erbjuda källkoden till köparen [belagt: GNU FAQ].
- **Får någon stänga källkoden i en bearbetning?** Nej. Om de distribuerar en bearbetning, måste den vara öppen och licensieras under GPL-3.0 [belagt: GNU GPL v3 Section 5c].
- **Får någon ta bort mitt namn?** Nej. Upphovsrättsnotiser ("Appropriate Legal Notices") måste bevaras i källkoden och i användargränssnittet [belagt: GNU GPL v3 Section 5a & 7b].
- **SaaS och nätverkstjänster:** Om någon tar OmaScribe och driver det exklusivt som en molntjänst (SaaS) där användare loggar in via webben, och de inte distribuerar binären, *behöver de inte* släppa sina kodändringar under GPL-3.0. Detta är SaaS-kryphålet. Om du väljer **AGPL-3.0**, tvingas de släppa källkoden även till nätverksanvändare. Eftersom OmaScribe länkar PyQt6 (GPL) kan du licensiera *din egen originella kod* som AGPL, men det komplicerar saken. För ett rent skrivbordsprogram är GPL-3.0 fullt tillräckligt.
- **Dual licensing:** Så länge *du* är 100 % ägare till all din skrivna kod, kan du sälja undantag till företag. Men eftersom OmaScribe *måste köras tillsammans med PyQt6*, kan du inte sälja en kommersiell helhet såvida du inte också köper en kommersiell licens från Riverbank för PyQt6.

## 4. Krav vid paketering av en binär

För att du och de som förmedlar programmet skall uppfylla GPL-3.0 och skydda projektet, måste följande finnas med:
1. **Licenstexten:** En fil med namnet `LICENSE` eller `COPYING` i repots rot som innehåller hela GPL-3.0-texten.
2. **Copyright-raden:** Texten "Copyright (C) 2026 OmaScribe Authors" (eller ditt namn) högst upp i centrala källkodsfiler.
3. **Ansvarsfriskrivning (No Warranty):** Måste synas.
4. **Källkodserbjudande:** Ett sätt att få källkoden (oftast länk till Git-repot).

I ett modernt Python-projekt:
- Filen `LICENSE.txt` eller `LICENSE` ligger bredvid `pyproject.toml`.
- I `pyproject.toml` läggs följande fält: `license = { text = "GPL-3.0-only" }` (eller fil-länk) och i `classifiers` listan: `"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"`.
- I programmets gränssnitt läggs en om-meny ("Hjälp -> Om OmaScribe") som innehåller copyrightraden, programmets namn och en notis att det distribueras under GPL-3.0, samt länk till källkoden. [belagt: gnu.org/licenses/gpl-3.0.html "How to Apply These Terms"].

## 5. Vad gör jämförbara projekt?

När vi tittar på etablerade skriv- och författarverktyg ser vi en tydlig uppdelning mellan proprietary- och copyleft-modeller:
- **Manuskript:** GNU GPL v3 (`GPL-3.0-or-later`) [belagt: github.com/milotype/manuskript/blob/master/LICENSE].
- **Zettlr:** GNU GPL v3 (`GPL-3.0-only`) [belagt: github.com/Zettlr/Zettlr/blob/develop/LICENSE].
- **novelWriter:** Bygger precis som du på Python och PyQt, och är licensierat under GPL-3.0, "Permissions of this strong copyleft license are conditioned on making available complete source code..." [belagt: github.com/vkbo/novelWriter/blob/main/LICENSE.md].
- **Sigil / Calibre:** Båda använder GPL-3.0.
- **LibreOffice:** Dual-licensierat historiskt, bygger på MPL 2.0 idag för att de behövde mer flexibilitet än LGPL för webbversioner, men behåller stark copyleft-skydd för kärnan.
- **Scrivener / Vellum / Atticus:** Proprietär mjukvara (Stängd, "All Rights Reserved", EULA). Ingen insyn, du får inte kopiera eller studera koden överhuvudtaget.

## 6. Distribution på PyPI, Flathub och Linux/AUR

- **PyPI:** Inga problem alls. Du laddar upp ett wheel. Beroenden definieras i din metadata, och pip hämtar PyQt6. GPL styr distributionen perfekt.
- **App-butiker och Flathub:** Flathub (Linux primära app-butik idag) bygger i grunden kring öppen källkod och lutar sig starkt på GPL. Att distribuera som en Flatpak på Flathub kräver att `spdx` taggen i din manifest är korrekt, och GPL-3.0 är den vanligaste där.
- **Linux / Debian / AUR:** Paketerare (maintainers) för pacman (Arch) och apt (Debian/Ubuntu) älskar GPL. Program under GPL paketar sig ofta själva genom gemenskapen. Det ställs inga negativa krav – licensen tillåter uttryckligen att de redistribuerar binärer och kod. Däremot stöter GPL-3.0 ibland på problem i Mac App Store och iOS (där Apples DRM och terms of service historiskt krockat med GPL:s krav på att få ersätta programvaran på enheten), men för distribution som `.dmg` eller via Homebrew/Flathub/PyPI uppstår ingen friktion.

## 7. Avgränsningar: Vad licensen de facto ger, och vad den inte kan hindra

Om det centrala målet är *"ingen tar åt sig äran för mina grejer"*, ger mekaniken bakom GPL exakt det:
- **Upphovsrättsligt skydd (Copyright):** Detta får du automatiskt när du skriver koden. Licensen är *ditt* tillstånd att andra får röra den, givet vissa krav. All kod förblir din egendom.
- **Erkännande:** GPL sektion 5(a) kräver att alla bearbetningar bär en tydlig notis om att de ändrat i orginalet, och från vem.

Men du måste vara ärlig och beredd på gränserna för vad en programvarulicens *inte* kan göra [resonemang]:
1. **Forks (förgreningar):** Licensen kan *inte* hindra någon från att klicka på "Fork" på GitHub, modifiera utseendet på OmaScribe och släppa det som sitt eget öppna projekt (så länge de är tydliga med källan och behåller orginalupphovsmannens copyright-texter inom projektet).
2. **Komersialisering:** Licensen kan *inte* hindra någon från att bygga din kod och sälja binären på en CD eller via en webbplats. Men om de gör det, måste de också lämna över all källkod, vilket kraftigt begränsar vinstincitamentet för klonare som vill slå mynt av andras arbete.
3. **Användaranpassning:** Vem som helst får ladda ned programmet, ändra det för sitt eget syfte och hålla den versionen privat (så länge de inte distribuerar den vidare).

**Ett separat men kraftfullt skydd: Varumärket.**
Programvarulicensen täcker koden (copyright). Den täcker *inte* identiteten. Om någon gör en egen förgrening av ditt arbete har de automatisk licens till koden, men de har *ingen* licens att kalla sin version "OmaScribe". Bara du har rätt till namnet OmaScribe genom varumärkeslagstiftning (även som oregistrerat inarbetat varumärke är skyddet starkt). Det är därför Debian döpte om Firefox till Iceweasel, de fick koden (via MPL) men inte varumärket. Detta är ditt absolut starkaste skydd mot att någon utnyttjar programmets "ära" eller namn.

---

## Vad jag inte kunde belägga
- Om du i framtiden skulle vilja sälja OmaScribe i iOS App Store kan GPL-3.0 innebära licenskonflikter med Apples publiceringsvillkor, men detta är inte belagt via Apples nuvarande officiella guidelines utan baseras historiskt på hur t.ex. VLC hanterats.

## Rekommendation

**Exakt SPDX-identifierare:** `GPL-3.0-only`

**Varför:** PyQt6:s egna beroendekrets tvingar i praktiken fram GPL-3.0, och det tillgodoser till fullo ditt krav att koden hålls öppen, stänger dörren för proprietär inbakning (MIT/Apache tillåter detta) och tvingar fram attribution.

**Vad som måste läggas till i repot:**
1. En fil namngiven `LICENSE` i projektets rotmapp med texten för GNU General Public License v3.0.
2. I `pyproject.toml` (eller motsvarande konfigurationsfil), fältet:
   `license = { text = "GPL-3.0-only" }`
3. I instansieringen/OM-dialogrutan i PyQt-koden: Ett kort block text som anger `"Copyright (C) 2026 [Ditt namn]"` följt av `"Dela och modifiera under GNU GPLv3."`
