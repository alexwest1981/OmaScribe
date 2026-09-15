"""
core/templates.py — Inbyggda dokumentmallar för OmaScribe.

Mallarna är dokument, inte skärm. Därför använder de bara papperets färger:
vit botten, svart text och grå linjer — ingen kulör någonstans. Det gör att
en mall kan skrivas ut, PDF:as och kopieras till Word utan att något tappar
sin betydelse, och att `core/print_style.py` inte behöver rensa något som
redan är rent.

Tonerna som används:

    #000000  rubriker och brödtext
    #333333  dämpad text (metauppgifter, citat)
    #666666  sekundär text i tabeller
    #999999  ramar, avdelare
    #ededed  svag ton (tabellhuvud, informationsruta)
    #f5f5f5  svagare ton (formulärruta)

Mappningen till PDF/DOCX/HTML sköts av DocManager + print_style, så mallen
behöver aldrig känna till utdataformatet.

Mallar:
- Rapport (Teknisk / Företagsrapport)
- Avhandling / Akademisk uppsats
- Mötesprotokoll / Beslutsunderlag
- Projektplan & Tidslinje
- Promemoria (PM / Besluts-PM)
- Formellt brev / Ansökan
- CV / Meritförteckning
"""

TEMPLATES = [
    {
        "id": "report",
        "icon": "📊",
        "title_sv": "Rapport (Teknisk / Företagsrapport)",
        "title_en": "Report (Technical / Business Report)",
        "desc_sv": "Strukturerad rapport med sammanfattning, metodik, resultattabell och slutsatser.",
        "desc_en": "Structured report with executive summary, methodology, results table, and conclusions.",
        "category": "business",
        "html_sv": """
<h1 style="text-align: center; margin-bottom: 4px;">Teknisk Analysrapport</h1>
<p style="text-align: center; color: #333333; font-size: 11pt; margin-top: 0;">Dokument-ID: REP-2026-001 &bull; Författare: [Namn] &bull; Datum: [ÅÅÅÅ-MM-DD]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 16px 0;"/>

<h2>1. Sammanfattning (Executive Summary)</h2>
<p>Denna rapport redogör för nulägesanalysen, genomförda mätningar och rekommenderade åtgärder för det aktuella systemet. Resultaten visar på signifikanta effektivitetsvinster vid införande av föreslagen arkitektur.</p>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Viktig slutsats:</b> Preliminära tester indikerar en prestandaförbättring på upp till 35% efter optimering.
        </td>
    </tr>
</table>

<h2>2. Bakgrund &amp; Syfte</h2>
<p>Projektets målsättning är att utvärdera prestanda, robusthet och skalbarhet. Följande frågeställningar har adresserats under utredningens gång:</p>
<ul>
    <li>Identifiering av kritiska flaskhalsar i nuvarande arbetsflöde.</li>
    <li>Kvantitativ mätning av svarstider och resursanvändning.</li>
    <li>Framtagande av handlingsplan med prioriterade åtgärder.</li>
</ul>

<h2>3. Metod &amp; Datainsamling</h2>
<p>Undersökningen genomfördes genom automatiserade mättester över en sammanhängande period. Data sammanställdes och normaliserades enligt standardiserade mätmetoder.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 14px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="text-align: left; padding: 8px; border: 1px solid #999999;">Testscenario</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Baslinje (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Optimerat (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Förbättring</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Databasfrågor (Batch)</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">450 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">120 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+73%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Dokumentrendering</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">820 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">310 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+62%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Export till PDF</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">1 250 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">480 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+61%</td>
    </tr>
</table>

<h2>4. Slutsatser &amp; Rekommendationer</h2>
<p>Baserat på ovanstående resultat rekommenderas omedelbar implementering av den föreslagna arkitekturen i produktionsmiljön.</p>

<h3>4.1 Prioriterad åtgärdsordning</h3>
<ol>
    <li>Inför batchning av databasfrågor i produktionsmiljön.</li>
    <li>Genomför motsvarande mätning efter två veckor i drift.</li>
    <li>Utvärdera nästa optimeringssteg utifrån uppmätta värden, inte antaganden.</li>
</ol>
""",
        "html_en": """
<h1 style="text-align: center; margin-bottom: 4px;">Technical Analysis Report</h1>
<p style="text-align: center; color: #333333; font-size: 11pt; margin-top: 0;">Document ID: REP-2026-001 &bull; Author: [Name] &bull; Date: [YYYY-MM-DD]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 16px 0;"/>

<h2>1. Executive Summary</h2>
<p>This report details the baseline assessment, empirical measurements, and recommended interventions for the current system architecture. The results show significant efficiency gains across all tested workloads.</p>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Key finding:</b> Prototype benchmarks confirm latency reductions of up to 35% under peak load.
        </td>
    </tr>
</table>

<h2>2. Objectives &amp; Scope</h2>
<p>The primary objective is to evaluate latency, throughput, and system reliability. Key focal points include:</p>
<ul>
    <li>Bottleneck detection across execution pipelines.</li>
    <li>Empirical verification of memory and CPU footprints.</li>
    <li>Actionable roadmap for deployment and rollout.</li>
</ul>

<h2>3. Methodology &amp; Results</h2>
<p>Automated test suites were run continuously across isolated environments to collect telemetry data.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 14px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="text-align: left; padding: 8px; border: 1px solid #999999;">Benchmark Suite</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Baseline (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Optimized (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #999999;">Gain</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Batch Queries</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">450 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">120 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+73%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Document Rendering</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">820 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">310 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+62%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">PDF Generation</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">1,250 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999;">480 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #999999; font-weight: bold;">+61%</td>
    </tr>
</table>

<h2>4. Recommendations</h2>
<p>We recommend rolling out the architecture to the primary production pipeline immediately.</p>
""",
    },
    {
        "id": "thesis",
        "icon": "🎓",
        "title_sv": "Avhandling & Akademisk uppsats",
        "title_en": "Thesis & Academic Dissertation",
        "desc_sv": "Akademisk mall med abstract, teoriramverk, metod, diskussion och källhänvisningar.",
        "desc_en": "Academic template with abstract, theoretical framework, methodology, discussion, and bibliography.",
        "category": "academic",
        "html_sv": """
<p style="text-align: center; color: #333333; font-size: 12pt; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Institutionen för Informatik &amp; Systemvetenskap</p>
<h1 style="text-align: center; font-size: 24pt; margin-top: 0; margin-bottom: 12px;">Arkitektoniska mönster i moderna AI-assisterade skrivverktyg</h1>
<p style="text-align: center; font-size: 13pt; font-style: italic; color: #333333;">En empirisk studie av användarinteraktion och kontextuell modellstyrning</p>
<br/>
<p style="text-align: center; font-size: 11pt; color: #333333;">Författare: [Ditt Namn] &bull; Handledare: [Handledarens Namn] &bull; Magisteruppsats (30 hp)</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 24px 0;"/>

<h2>Abstract</h2>
<p>Denna uppsats undersöker hur lokalt integrerade AI-modeller kan samverka med moderna användargränssnitt för att förbättra skrivflöden och kognitiv avlastning hos författare. Genom en kombination av kvalitativa intervjuer och mätningar av revisionshastighet demonstreras att fokuserade mikrotjänster i editorn minskar kontextbyten avsevärt.</p>

<p><b>Nyckelord:</b> Textbehandling, AI-assistans, Människa-datorinteraktion, PyQt6, Dokumentarkitektur.</p>

<h2>1. Inledning</h2>
<p>Skrivprocessen ställer höga krav på kontinuerligt fokus. Traditionella ordbehandlare saknar ofta djup integration med intelligenta analysmodeller, vilket tvingar användare till externa webbgränssnitt.</p>

<h3>1.1 Problemformulering</h3>
<p>Hur kan en integrerad ordbehandlare tillhandahålla realtidsstöd utan att störa författarens kreativa tillstånd?</p>

<h3>1.2 Avgränsning</h3>
<p>Studien omfattar skrivverktyg för stationära miljöer och behandlar inte mobila applikationer eller helt molnbaserade tjänster.</p>

<h2>2. Teoretisk Referensram</h2>
<p>Tidigare forskning inom datorstödd textproduktion (se t.ex. Flower &amp; Hayes kognitiva skrivmodell) betonar vikten av friktionsfria övergångar mellan planering, formulering och granskning.</p>

<blockquote>"Att skriva är inte bara att registrera tankar, utan ett aktivt verktyg för själva tänkandet."</blockquote>

<h2>3. Metod</h2>
<p>Studien tillämpar en designvetenskaplig forskningsmetod (Design Science Research) där en fungerande prototyp iterativt utvecklats och utvärderats mot uppsatta kvalitetsmål.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 14px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="text-align: left; padding: 8px; border: 1px solid #999999;">Delstudie</th>
        <th style="text-align: left; padding: 8px; border: 1px solid #999999;">Datainsamling</th>
        <th style="text-align: center; padding: 8px; border: 1px solid #999999;">Urval</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Intervjuer</td>
        <td style="padding: 8px; border: 1px solid #999999;">Semistrukturerade samtal</td>
        <td style="text-align: center; padding: 8px; border: 1px solid #999999;">12 deltagare</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #999999;">Mätningar</td>
        <td style="padding: 8px; border: 1px solid #999999;">Loggad revisionstid</td>
        <td style="text-align: center; padding: 8px; border: 1px solid #999999;">[Antal sessioner]</td>
    </tr>
</table>

<h2>4. Resultat &amp; Analys</h2>
<p>De insamlade mätvärdena påvisar en markant reduktion av omskrivningstid när semantiska förslag tillhandahålls direkt i blockkontexten.</p>

<h2>5. Diskussion</h2>
<p>Resultaten bör tolkas med hänsyn till studiens begränsade urval. Förslag till fortsatt forskning inkluderar longitudinella studier över längre skrivprojekt.</p>

<h2>6. Källförteckning</h2>
<ul>
    <li>Hayes, J. R., &amp; Flower, L. S. (1980). <i>Identifying the organization of writing processes</i>. Cognitive processes in writing.</li>
    <li>Norman, D. A. (2013). <i>The Design of Everyday Things</i>. Basic Books.</li>
</ul>
""",
        "html_en": """
<p style="text-align: center; color: #333333; font-size: 12pt; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Department of Computer Science &amp; Information Systems</p>
<h1 style="text-align: center; font-size: 24pt; margin-top: 0; margin-bottom: 12px;">Architectural Paradigms in Modern AI-Assisted Authoring Environments</h1>
<p style="text-align: center; font-size: 13pt; font-style: italic; color: #333333;">An Empirical Study on Interaction Latency and Contextual Model Steering</p>
<br/>
<p style="text-align: center; font-size: 11pt; color: #333333;">Author: [Your Name] &bull; Supervisor: [Supervisor Name] &bull; Master Thesis (30 ECTS)</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 24px 0;"/>

<h2>Abstract</h2>
<p>This thesis investigates the interplay between native rich text editors and embedded machine learning copilots. By examining cognitive load and context-switching overhead across structured authoring tasks, we establish design patterns for seamless editor integration.</p>

<p><b>Keywords:</b> Text processing, Human-Computer Interaction, Local AI, Rich Text Architecture, Productivity.</p>

<h2>1. Introduction</h2>
<p>Authoring complex manuscripts demands sustained cognitive engagement. Disjointed web-based assistants introduce frequent context switching, fracturing the writer's concentration.</p>

<h3>1.1 Research Question</h3>
<p>How can an integrated word processor provide real-time assistance without disrupting the author's flow state?</p>

<h2>2. Literature Review &amp; Theory</h2>
<p>Cognitive process theories of writing emphasize the delicate balance between ideation, drafting, and reviewing phases.</p>

<blockquote>"Writing is not merely a recording medium for thoughts, but an epistemic engine for thought creation."</blockquote>

<h2>3. Methodology</h2>
<p>We employ Design Science Research (DSR), iteratively building and validating a native desktop artifact.</p>

<h2>4. Discussion &amp; Findings</h2>
<p>Telemetry indicates a measurable drop in editing cycle time when context-aware inline assistants are deployed.</p>

<h2>5. References</h2>
<ul>
    <li>Flower, L., &amp; Hayes, J. R. (1981). <i>A cognitive process theory of writing</i>. College Composition and Communication.</li>
    <li>Norman, D. A. (2013). <i>The Design of Everyday Things</i>. Basic Books.</li>
</ul>
""",
    },
    {
        "id": "minutes",
        "icon": "📝",
        "title_sv": "Mötesanteckningar & Protokoll",
        "title_en": "Meeting Minutes & Decisions",
        "desc_sv": "Mötesprotokoll med dagordning, närvarolista, formella beslut och åtgärdsmatris.",
        "desc_en": "Formal meeting minutes with agenda, attendee list, recorded decisions, and action matrix.",
        "category": "business",
        "html_sv": """
<h1>Mötesprotokoll — Projektavstämning</h1>
<table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0; background-color: #f5f5f5;">
    <tr>
        <td style="width: 25%; font-weight: bold; border: 1px solid #999999;">Datum &amp; Tid:</td>
        <td style="width: 25%; border: 1px solid #999999;">[ÅÅÅÅ-MM-DD kl. 10:00–11:30]</td>
        <td style="width: 25%; font-weight: bold; border: 1px solid #999999;">Plats:</td>
        <td style="width: 25%; border: 1px solid #999999;">[Konferensrum A / Digitalt]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #999999;">Mötesledare:</td>
        <td style="border: 1px solid #999999;">[Namn]</td>
        <td style="font-weight: bold; border: 1px solid #999999;">Protokollförare:</td>
        <td style="border: 1px solid #999999;">[Namn]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #999999;">Närvarande:</td>
        <td colspan="3" style="border: 1px solid #999999;">[Deltagare 1, Deltagare 2, Deltagare 3, Deltagare 4]</td>
    </tr>
</table>

<h2>Dagordning</h2>
<ol>
    <li>Mötets öppnande och val av justerare</li>
    <li>Genomgång av föregående protokoll</li>
    <li>Statusrapport för pågående delprojekt</li>
    <li>Beslutspunkter &amp; Resursallokering</li>
    <li>Övriga frågor &amp; Nästa möte</li>
</ol>

<h2>§ 1. Formalia</h2>
<p>Mötet öppnades av ordföranden. [Namn] utsågs till protokolljusterare.</p>

<h2>§ 2. Beslutspunkter</h2>
<p><b>Beslut 2.1:</b> Styrelsen/gruppen beslutade enhälligt att godkänna den uppdaterade tidsplanen för Q4.</p>
<p><b>Beslut 2.2:</b> Budgettillskott för infrastruktur och licenser godkändes enligt framlagt förslag.</p>

<h2>§ 3. Åtgärdslista (Action Items)</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left;">Uppgift / Åtgärd</th>
        <th style="border: 1px solid #999999; text-align: left; width: 140px;">Ansvarig</th>
        <th style="border: 1px solid #999999; text-align: center; width: 110px;">Deadline</th>
        <th style="border: 1px solid #999999; text-align: center; width: 100px;">Status</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Färdigställa rapportutkast och PDF-underlag</td>
        <td style="border: 1px solid #999999;">[Namn]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-01</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">Pågår</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Kvalitetssäkra diagram och mätdata</td>
        <td style="border: 1px solid #999999;">[Namn]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-05</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">Planerad</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Skicka ut inbjudan till nästa styrgruppsmöte</td>
        <td style="border: 1px solid #999999;">[Namn]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-09-25</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">Klar</td>
    </tr>
</table>

<h2>§ 4. Nästa möte</h2>
<p>Nästa avstämning äger rum [ÅÅÅÅ-MM-DD]. Protokollet justeras och publiceras senast två arbetsdagar efter mötet.</p>
""",
        "html_en": """
<h1>Meeting Minutes — Project Sync</h1>
<table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0; background-color: #f5f5f5;">
    <tr>
        <td style="width: 25%; font-weight: bold; border: 1px solid #999999;">Date &amp; Time:</td>
        <td style="width: 25%; border: 1px solid #999999;">[YYYY-MM-DD 10:00–11:30]</td>
        <td style="width: 25%; font-weight: bold; border: 1px solid #999999;">Location:</td>
        <td style="width: 25%; border: 1px solid #999999;">[Conference Room A / Virtual]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #999999;">Chair:</td>
        <td style="border: 1px solid #999999;">[Name]</td>
        <td style="font-weight: bold; border: 1px solid #999999;">Secretary:</td>
        <td style="border: 1px solid #999999;">[Name]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #999999;">Attendees:</td>
        <td colspan="3" style="border: 1px solid #999999;">[Attendee 1, Attendee 2, Attendee 3, Attendee 4]</td>
    </tr>
</table>

<h2>Agenda</h2>
<ol>
    <li>Opening and approval of agenda</li>
    <li>Review of previous action items</li>
    <li>Milestone status updates</li>
    <li>Key decision items</li>
    <li>AOB &amp; Next meeting</li>
</ol>

<h2>Key Decisions</h2>
<p><b>Decision 1:</b> The committee unanimously approved the updated milestone timeline for Q4.</p>
<p><b>Decision 2:</b> Budget allocation for toolchain modernization was ratified.</p>

<h2>Action Items</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left;">Action Item</th>
        <th style="border: 1px solid #999999; text-align: left; width: 140px;">Assignee</th>
        <th style="border: 1px solid #999999; text-align: center; width: 110px;">Due Date</th>
        <th style="border: 1px solid #999999; text-align: center; width: 100px;">Status</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Finalize report draft and PDF delivery</td>
        <td style="border: 1px solid #999999;">[Name]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-01</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">In Progress</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Verify chart figures and dataset integrity</td>
        <td style="border: 1px solid #999999;">[Name]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-05</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">Pending</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Dispatch invites for executive review</td>
        <td style="border: 1px solid #999999;">[Name]</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-09-25</td>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">Done</td>
    </tr>
</table>
""",
    },
    {
        "id": "project_plan",
        "icon": "📅",
        "title_sv": "Projektplan & Milstolpar",
        "title_en": "Project Plan & Milestones",
        "desc_sv": "Komplett projektplan med syfte, milstolpar, riskmatris och resursbudget.",
        "desc_en": "Comprehensive project charter with scope, milestone timeline, risk matrix, and budget.",
        "category": "management",
        "html_sv": """
<h1>Projektplan: [Projektnamn]</h1>
<p style="color: #333333; font-size: 11pt;">Projektägare: [Namn] &bull; Projektledare: [Namn] &bull; Version 1.0 &bull; Datum: [ÅÅÅÅ-MM-DD]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 16px 0;"/>

<h2>1. Mål &amp; Omfattning (Scope)</h2>
<p>Projektets huvudsakliga mål är att leverera en produktionsredo lösning som uppfyller verksamhetens krav på tillförlitlighet, användarvänlighet och prestanda.</p>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Effektmål:</b> 50% minskad handläggningstid och full spårbarhet i alla led.
        </td>
    </tr>
</table>

<h2>2. Milstolpar &amp; Tidslinje</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: center; width: 70px;">Fas</th>
        <th style="border: 1px solid #999999; text-align: left;">Milstolpe / Leverabel</th>
        <th style="border: 1px solid #999999; text-align: center; width: 120px;">Slutdatum</th>
        <th style="border: 1px solid #999999; text-align: center; width: 100px;">Ansvarig</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M1</td>
        <td style="border: 1px solid #999999;">Kravspecifikation &amp; Arkitekturdesign</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-15</td>
        <td style="border: 1px solid #999999; text-align: center;">Team Arkitektur</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M2</td>
        <td style="border: 1px solid #999999;">Prototypimplementering &amp; Verifiering</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-11-15</td>
        <td style="border: 1px solid #999999; text-align: center;">Utvecklingsteam</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M3</td>
        <td style="border: 1px solid #999999;">Acceptanstest (UAT) &amp; Dokumentation</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-12-05</td>
        <td style="border: 1px solid #999999; text-align: center;">QA &amp; Produktägare</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M4</td>
        <td style="border: 1px solid #999999;">Produktionsdriftsättning &amp; Överlämning</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-12-20</td>
        <td style="border: 1px solid #999999; text-align: center;">Drift / DevOps</td>
    </tr>
</table>

<h2>3. Riskanalys &amp; Åtgärder</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left;">Identifierad Risk</th>
        <th style="border: 1px solid #999999; text-align: center; width: 90px;">Sannolikhet</th>
        <th style="border: 1px solid #999999; text-align: center; width: 90px;">Påverkan</th>
        <th style="border: 1px solid #999999; text-align: left;">Förebyggande åtgärd</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Fördröjningar i extern API-integration</td>
        <td style="border: 1px solid #999999; text-align: center;">Medel</td>
        <td style="border: 1px solid #999999; text-align: center;">Hög</td>
        <td style="border: 1px solid #999999;">Mockade gränssnitt och tidig integrationstestning</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Resursbrist under semesterperiod</td>
        <td style="border: 1px solid #999999; text-align: center;">Låg</td>
        <td style="border: 1px solid #999999; text-align: center;">Medel</td>
        <td style="border: 1px solid #999999;">Tidig schemaläggning och korsutbildning i teamet</td>
    </tr>
</table>

<h2>4. Resurser &amp; Budget</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left;">Resurs</th>
        <th style="border: 1px solid #999999; text-align: right; width: 140px;">Budget</th>
        <th style="border: 1px solid #999999; text-align: right; width: 140px;">Utfall</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Utvecklingstimmar</td>
        <td style="border: 1px solid #999999; text-align: right;">[0] timmar</td>
        <td style="border: 1px solid #999999; text-align: right;">[0] timmar</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">Licenser &amp; infrastruktur</td>
        <td style="border: 1px solid #999999; text-align: right;">[0] kr</td>
        <td style="border: 1px solid #999999; text-align: right;">[0] kr</td>
    </tr>
</table>
""",
        "html_en": """
<h1>Project Charter: [Project Name]</h1>
<p style="color: #333333; font-size: 11pt;">Owner: [Name] &bull; Project Manager: [Name] &bull; Version 1.0 &bull; Date: [YYYY-MM-DD]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 16px 0;"/>

<h2>1. Scope &amp; Goals</h2>
<p>The project delivers a production-grade release fulfilling enterprise reliability, usability, and throughput requirements.</p>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Target Outcome:</b> 50% reduction in processing cycle time with complete auditability.
        </td>
    </tr>
</table>

<h2>2. Milestone Roadmap</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: center; width: 70px;">Phase</th>
        <th style="border: 1px solid #999999; text-align: left;">Milestone / Deliverable</th>
        <th style="border: 1px solid #999999; text-align: center; width: 120px;">Target Date</th>
        <th style="border: 1px solid #999999; text-align: center; width: 100px;">Owner</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M1</td>
        <td style="border: 1px solid #999999;">Specification &amp; System Architecture</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-10-15</td>
        <td style="border: 1px solid #999999; text-align: center;">Architecture Team</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M2</td>
        <td style="border: 1px solid #999999;">Core Implementation &amp; Testing</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-11-15</td>
        <td style="border: 1px solid #999999; text-align: center;">Engineering</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999; text-align: center; font-weight: bold;">M3</td>
        <td style="border: 1px solid #999999;">UAT Validation &amp; Documentation</td>
        <td style="border: 1px solid #999999; text-align: center;">2026-12-05</td>
        <td style="border: 1px solid #999999; text-align: center;">QA &amp; Product Owner</td>
    </tr>
</table>

<h2>3. Risk Matrix</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left;">Risk</th>
        <th style="border: 1px solid #999999; text-align: center; width: 90px;">Likelihood</th>
        <th style="border: 1px solid #999999; text-align: center; width: 90px;">Impact</th>
        <th style="border: 1px solid #999999; text-align: left;">Mitigation</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">External API integration delays</td>
        <td style="border: 1px solid #999999; text-align: center;">Medium</td>
        <td style="border: 1px solid #999999; text-align: center;">High</td>
        <td style="border: 1px solid #999999;">Mocked interfaces and early integration testing</td>
    </tr>
</table>
""",
    },
    {
        "id": "memo",
        "icon": "📄",
        "title_sv": "Promemoria (PM / Besluts-PM)",
        "title_en": "Memorandum (PM / Decision Memo)",
        "desc_sv": "Kortfattat och formellt beslutsunderlag med bakgrund, överväganden och förslag till beslut.",
        "desc_en": "Concise memorandum with context, alternatives considered, and recommendations.",
        "category": "business",
        "html_sv": """
<table width="100%" style="border-bottom: 2px solid #000000; margin-bottom: 20px;">
    <tr>
        <td style="font-size: 22pt; font-weight: bold; color: #000000;">PROMEMORIA</td>
        <td style="text-align: right; font-size: 11pt; color: #333333;">Datum: [ÅÅÅÅ-MM-DD]<br/>Dnr: PM-2026-042</td>
    </tr>
</table>

<table width="100%" style="margin-bottom: 18px; font-size: 11pt;">
    <tr>
        <td style="width: 100px; font-weight: bold;">TILL:</td>
        <td>[Mottagarens namn / Ledningsgrupp]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">FRÅN:</td>
        <td>[Ditt namn och titel]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">ÄRENDE:</td>
        <td><b>[Kort och tydlig ärendebeskrivning]</b></td>
    </tr>
</table>

<h2>1. Sammanfattning &amp; Förslag till beslut</h2>
<p>Detta PM föreslår att ledningen fattar beslut om att:</p>
<ol>
    <li>Godkänna införandet av den nya lösningen från och med nästkommande kvartal.</li>
    <li>Uppdra åt berörda avdelningar att påbörja förberedande implementering.</li>
</ol>

<h2>2. Bakgrund &amp; Nuläge</h2>
<p>Nuvarande process har identifierats som en begränsande faktor för tillväxt och operativ effektivitet. En översyn visar på tydliga möjligheter till automatisering.</p>

<h2>3. Överväganden &amp; Konsekvensanalys</h2>
<p>Införandet medför följande direkta fördelar samt identifierade risker:</p>
<ul>
    <li><b>Ekonomiska effekter:</b> Återbetalningstid beräknas till 8 månader.</li>
    <li><b>Verksamhetsnytta:</b> Högre datakvalitet och minskad administrativ belastning.</li>
</ul>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Observera:</b> En övergångsperiod om 2 veckor krävs för användarutbildning.
        </td>
    </tr>
</table>

<h2>4. Beslut</h2>
<p>Beslut fattas av [instans] senast [ÅÅÅÅ-MM-DD]. Vid uteblivet beslut kvarstår nuvarande process oförändrad.</p>
""",
        "html_en": """
<table width="100%" style="border-bottom: 2px solid #000000; margin-bottom: 20px;">
    <tr>
        <td style="font-size: 22pt; font-weight: bold; color: #000000;">MEMORANDUM</td>
        <td style="text-align: right; font-size: 11pt; color: #333333;">Date: [YYYY-MM-DD]<br/>Ref: MEMO-2026-042</td>
    </tr>
</table>

<table width="100%" style="margin-bottom: 18px; font-size: 11pt;">
    <tr>
        <td style="width: 100px; font-weight: bold;">TO:</td>
        <td>[Recipient / Executive Committee]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">FROM:</td>
        <td>[Your Name &amp; Title]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">SUBJECT:</td>
        <td><b>[Clear and concise subject line]</b></td>
    </tr>
</table>

<h2>1. Executive Summary &amp; Recommendation</h2>
<p>It is recommended that management approves the following actions:</p>
<ol>
    <li>Approve migration to the new platform starting next quarter.</li>
    <li>Authorize the cross-functional transition team to begin staging.</li>
</ol>

<h2>2. Context &amp; Background</h2>
<p>The current manual workflow presents scalability bottlenecks. An operational review confirms substantial opportunities for optimization.</p>

<h2>3. Considerations &amp; Impact</h2>
<ul>
    <li><b>Financial impact:</b> Estimated payback period of 8 months.</li>
    <li><b>Operational benefit:</b> Higher data quality and reduced administrative overhead.</li>
</ul>

<table width="100%" style="background-color: #ededed; border-left: 3px solid #000000; margin: 12px 0;">
    <tr>
        <td style="vertical-align: top; padding: 10px 14px; color: #000000; font-size: 11pt;">
            <b>Note:</b> A two-week transition period is required for user training.
        </td>
    </tr>
</table>
""",
    },
    {
        "id": "letter",
        "icon": "✉️",
        "title_sv": "Formellt brev & Ansökan",
        "title_en": "Formal Letter & Application",
        "desc_sv": "Brevmall med avsändarblock, datum, ämnesrad, brödtext och signatur.",
        "desc_en": "Letter template with sender block, date, subject line, body, and signature.",
        "category": "business",
        "html_sv": """
<p style="margin-bottom: 0;">[Ditt namn]</p>
<p style="margin: 0; color: #333333;">[Gatuadress] &bull; [Postnummer Ort]</p>
<p style="margin: 0; color: #333333;">[E-post] &bull; [Telefon]</p>

<hr style="border: 0; border-top: 1px solid #999999; margin: 18px 0;"/>

<table width="100%" style="margin-bottom: 18px; font-size: 11pt;">
    <tr>
        <td style="width: 130px; color: #333333;">Mottagare:</td>
        <td>[Organisation / Myndighet]<br/>[Handläggare]<br/>[Adress]</td>
        <td style="width: 90px; text-align: right; color: #333333;">Datum:</td>
        <td style="text-align: right;">[ÅÅÅÅ-MM-DD]</td>
    </tr>
</table>

<h2>Ansökan om [ärende]</h2>

<p>Härmed ansöker jag om [vad ansökan avser]. Ansökan avser [period eller omfattning] och grundar sig på [hänvisning till regelverk, avtal eller överenskommelse].</p>

<p>Sammanfattningsvis framförs följande skäl:</p>
<ol>
    <li>[Första skälet — konkret och verifierbart.]</li>
    <li>[Andra skälet — med hänvisning till bilaga.]</li>
    <li>[Tredje skälet.]</li>
</ol>

<h2>Bilagor</h2>
<ul>
    <li>Bilaga 1: [Namn på bilaga]</li>
    <li>Bilaga 2: [Namn på bilaga]</li>
</ul>

<p>Jag är tillgänglig för kompletterande uppgifter och svarar gärna på frågor via [e-post] eller [telefon].</p>

<p style="margin-top: 28px;">Med vänlig hälsning,</p>
<p style="margin-top: 24px;">_______________________<br/>[Namn]<br/>[Titel / Organisation]</p>
""",
        "html_en": """
<p style="margin-bottom: 0;">[Your Name]</p>
<p style="margin: 0; color: #333333;">[Street Address] &bull; [Postal Code City]</p>
<p style="margin: 0; color: #333333;">[Email] &bull; [Phone]</p>

<hr style="border: 0; border-top: 1px solid #999999; margin: 18px 0;"/>

<table width="100%" style="margin-bottom: 18px; font-size: 11pt;">
    <tr>
        <td style="width: 130px; color: #333333;">Recipient:</td>
        <td>[Organisation / Authority]<br/>[Case Officer]<br/>[Address]</td>
        <td style="width: 90px; text-align: right; color: #333333;">Date:</td>
        <td style="text-align: right;">[YYYY-MM-DD]</td>
    </tr>
</table>

<h2>Application regarding [matter]</h2>

<p>I hereby apply for [what the application concerns]. The application covers [period or scope] and is based on [reference to regulation, contract, or agreement].</p>

<p>The grounds are summarised as follows:</p>
<ol>
    <li>[First ground — concrete and verifiable.]</li>
    <li>[Second ground — with reference to an enclosure.]</li>
</ol>

<h2>Enclosures</h2>
<ul>
    <li>Enclosure 1: [Name of enclosure]</li>
    <li>Enclosure 2: [Name of enclosure]</li>
</ul>

<p>Yours faithfully,</p>
<p style="margin-top: 24px;">_______________________<br/>[Name]<br/>[Title / Organisation]</p>
""",
    },
    {
        "id": "cv",
        "icon": "🧾",
        "title_sv": "CV & Meritförteckning",
        "title_en": "CV & Résumé",
        "desc_sv": "Strukturerad meritförteckning med profil, erfarenhet, utbildning och kompetenser.",
        "desc_en": "Structured résumé with profile, experience, education, and skills.",
        "category": "personal",
        "html_sv": """
<h1 style="margin-bottom: 2px;">[För- och efternamn]</h1>
<p style="color: #333333; font-size: 11pt; margin-top: 0;">[Titel / Yrkesroll] &bull; [Ort] &bull; [E-post] &bull; [Telefon] &bull; [Länk]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 14px 0;"/>

<h2>Profil</h2>
<p>[Två till tre meningar som sammanfattar yrkesidentitet, inriktning och vad du tillför en arbetsgivare.]</p>

<h2>Arbetslivserfarenhet</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left; width: 130px;">Period</th>
        <th style="border: 1px solid #999999; text-align: left;">Roll &amp; arbetsgivare</th>
        <th style="border: 1px solid #999999; text-align: left;">Ansvar &amp; resultat</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">[2022–nu]</td>
        <td style="border: 1px solid #999999;"><b>[Titel]</b><br/>[Arbetsgivare]</td>
        <td style="border: 1px solid #999999;">[Ansvarområde och ett mätbart resultat.]</td>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">[2019–2022]</td>
        <td style="border: 1px solid #999999;"><b>[Titel]</b><br/>[Arbetsgivare]</td>
        <td style="border: 1px solid #999999;">[Ansvarområde och ett mätbart resultat.]</td>
    </tr>
</table>

<h2>Utbildning</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left; width: 130px;">Period</th>
        <th style="border: 1px solid #999999; text-align: left;">Utbildning</th>
        <th style="border: 1px solid #999999; text-align: left; width: 180px;">Lärosäte</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">[År–År]</td>
        <td style="border: 1px solid #999999;">[Program / kurs, omfattning]</td>
        <td style="border: 1px solid #999999;">[Lärosäte]</td>
    </tr>
</table>

<h2>Kompetenser</h2>
<ul>
    <li><b>Tekniska:</b> [Verktyg, språk, plattformar]</li>
    <li><b>Metodiska:</b> [Processer, ramverk, arbetssätt]</li>
    <li><b>Språk:</b> [Språk och nivå]</li>
</ul>

<h2>Referenser</h2>
<p>Referenser lämnas på begäran.</p>
""",
        "html_en": """
<h1 style="margin-bottom: 2px;">[First and Last Name]</h1>
<p style="color: #333333; font-size: 11pt; margin-top: 0;">[Title / Role] &bull; [City] &bull; [Email] &bull; [Phone] &bull; [Link]</p>
<hr style="border: 0; border-top: 1px solid #999999; margin: 14px 0;"/>

<h2>Profile</h2>
<p>[Two or three sentences summarising your professional identity, focus, and what you bring to an employer.]</p>

<h2>Professional Experience</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left; width: 130px;">Period</th>
        <th style="border: 1px solid #999999; text-align: left;">Role &amp; employer</th>
        <th style="border: 1px solid #999999; text-align: left;">Responsibility &amp; outcome</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">[2022–present]</td>
        <td style="border: 1px solid #999999;"><b>[Title]</b><br/>[Employer]</td>
        <td style="border: 1px solid #999999;">[Scope of responsibility and one measurable result.]</td>
    </tr>
</table>

<h2>Education</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #999999; margin: 12px 0;">
    <tr style="background-color: #ededed; font-weight: bold;">
        <th style="border: 1px solid #999999; text-align: left; width: 130px;">Period</th>
        <th style="border: 1px solid #999999; text-align: left;">Programme</th>
        <th style="border: 1px solid #999999; text-align: left; width: 180px;">Institution</th>
    </tr>
    <tr>
        <td style="border: 1px solid #999999;">[Year–Year]</td>
        <td style="border: 1px solid #999999;">[Degree / course, credits]</td>
        <td style="border: 1px solid #999999;">[Institution]</td>
    </tr>
</table>

<h2>Skills</h2>
<ul>
    <li><b>Technical:</b> [Tools, languages, platforms]</li>
    <li><b>Methodical:</b> [Processes, frameworks, ways of working]</li>
    <li><b>Languages:</b> [Languages and level]</li>
</ul>

<h2>References</h2>
<p>References available on request.</p>
""",
    },
]


def get_template(template_id: str):
    """Hämtar en specifik mall efter id."""
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return None


def get_template_html(template_id: str, lang: str = "sv") -> str:
    """Returnerar HTML för en mall på angivet språk."""
    t = get_template(template_id)
    if not t:
        return ""
    if lang == "sv":
        return t.get("html_sv") or t.get("html_en", "")
    return t.get("html_en") or t.get("html_sv", "")


def template_title(template: dict, lang: str = "sv") -> str:
    """Mallens visningsnamn på valt språk (används av mallväljaren)."""
    if not template:
        return ""
    if lang == "sv":
        return template.get("title_sv") or template.get("title_en", "")
    return template.get("title_en") or template.get("title_sv", "")


def template_description(template: dict, lang: str = "sv") -> str:
    """Mallens beskrivning på valt språk."""
    if not template:
        return ""
    if lang == "sv":
        return template.get("desc_sv") or template.get("desc_en", "")
    return template.get("desc_en") or template.get("desc_sv", "")


def template_catalog(lang: str = "sv") -> list[dict]:
    """Mallkatalogen som (id, ikon, titel, beskrivning, kategori)."""
    return [
        {
            "id": t["id"],
            "icon": t.get("icon", ""),
            "title": template_title(t, lang),
            "description": template_description(t, lang),
            "category": t.get("category", ""),
        }
        for t in TEMPLATES
    ]
