"""
core/templates.py — Inbyggda dokumentmallar för OmaScribe.

Innehåller fördefinierade mallar med rik typografi, rubrikstrukturer,
formaterade tabeller, infoboxar och platshållare:
- Rapport (Teknisk / Företagsrapport)
- Avhandling / Akademisk uppsats
- Mötesprotokoll / Beslutsunderlag
- Projektplan & Tidslinje
- Promemoria (PM / Besluts-PM)
"""

from core.i18n import _

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
<p style="text-align: center; color: #64748b; font-size: 11pt; margin-top: 0;">Dokument-ID: REP-2026-001 • Författare: [Namn] • Datum: [ÅÅÅÅ-MM-DD]</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 16px 0;"/>

<h2>1. Sammanfattning (Executive Summary)</h2>
<p>Denna rapport redogör för nulägesanalysen, genomförda mätningar och rekommenderade åtgärder för det aktuella systemet. Resultaten visar på signifikanta effektivitetsvinster vid införande av föreslagen arkitektur.</p>

<table width="100%" style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
    <tr>
        <td style="vertical-align: top; width: 24px; font-size: 16px;">ℹ️</td>
        <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
            <b>Viktig slutsats:</b> Preliminära tester indikerar en prestandaförbättring på upp till 35% efter optimering.
        </td>
    </tr>
</table>

<h2>2. Bakgrund & Syfte</h2>
<p>Projektets målsättning är att utvärdera prestanda, robusthet och skalbarhet. Följande frågeställningar har adresserats under utredningens gång:</p>
<ul>
    <li>Identifiering av kritiska flaskhalsar i nuvarande arbetsflöde.</li>
    <li>Kvantitativ mätning av svarstider och resursanvändning.</li>
    <li>Framtagande av handlingsplan med prioriterade åtgärder.</li>
</ul>

<h2>3. Metod & Datainsamling</h2>
<p>Undersökningen genomfördes genom automatiserade mättester över en sammanhängande period. Data sammanställdes och normaliserades enligt standardiserade mätmetoder.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 14px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="text-align: left; padding: 8px; border: 1px solid #cbd5e1;">Testscenario</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Baslinje (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Optimerat (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Förbättring</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">Databasfrågor (Batch)</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">450 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">120 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+73%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">Dokumentrendering</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">820 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">310 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+62%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">Export till PDF</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">1 250 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">480 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+61%</td>
    </tr>
</table>

<h2>4. Slutsatser & Rekommendationer</h2>
<p>Baserat på ovanstående resultat rekommenderas omedelbar implementering av den föreslagna arkitekturen i produktionsmiljön.</p>
""",
        "html_en": """
<h1 style="text-align: center; margin-bottom: 4px;">Technical Analysis Report</h1>
<p style="text-align: center; color: #64748b; font-size: 11pt; margin-top: 0;">Document ID: REP-2026-001 • Author: [Name] • Date: [YYYY-MM-DD]</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 16px 0;"/>

<h2>1. Executive Summary</h2>
<p>This report details the baseline assessment, empirical measurements, and recommended interventions for the current system architecture. The results show significant efficiency gains across all tested workloads.</p>

<table width="100%" style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
    <tr>
        <td style="vertical-align: top; width: 24px; font-size: 16px;">ℹ️</td>
        <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
            <b>Key finding:</b> Prototype benchmarks confirm latency reductions of up to 35% under peak load.
        </td>
    </tr>
</table>

<h2>2. Objectives & Scope</h2>
<p>The primary objective is to evaluate latency, throughput, and system reliability. Key focal points include:</p>
<ul>
    <li>Bottleneck detection across execution pipelines.</li>
    <li>Empirical verification of memory and CPU footprints.</li>
    <li>Actionable roadmap for deployment and rollout.</li>
</ul>

<h2>3. Methodology & Results</h2>
<p>Automated test suites were run continuously across isolated environments to collect telemetry data.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 14px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="text-align: left; padding: 8px; border: 1px solid #cbd5e1;">Benchmark Suite</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Baseline (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Optimized (ms)</th>
        <th style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">Gain</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">Batch Queries</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">450 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">120 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+73%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">Document Rendering</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">820 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">310 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+62%</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #cbd5e1;">PDF Generation</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">1,250 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1;">480 ms</td>
        <td style="text-align: right; padding: 8px; border: 1px solid #cbd5e1; color: #16a34a; font-weight: bold;">+61%</td>
    </tr>
</table>

<h2>4. Recommendations</h2>
<p>We recommend rolling out the architecture to the primary production pipeline immediately.</p>
"""
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
<p style="text-align: center; color: #64748b; font-size: 12pt; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Institutionen för Informatik & Systemvetenskap</p>
<h1 style="text-align: center; font-size: 24pt; margin-top: 0; margin-bottom: 12px;">Arkitektoniska mönster i moderna AI-assisterade skrivverktyg</h1>
<p style="text-align: center; font-size: 13pt; font-style: italic; color: #475569;">En empirisk studie av användarinteraktion och kontextuell modellstyrning</p>
<br/>
<p style="text-align: center; font-size: 11pt; color: #64748b;">Författare: [Ditt Namn] • Handledare: [Handledarens Namn] • Magisteruppsats (30 hp)</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 24px 0;"/>

<h2>Abstract</h2>
<p>Denna uppsats undersöker hur lokalt integrerade AI-modeller kan samverka med moderna användargränssnitt för att förbättra skrivflöden och kognitiv avlastning hos författare. Genom en kombination av kvalitativa intervjuer och mätningar av revisionshastighet demonstreras att fokuserade mikrotjänster i editorn minskar kontextbyten avsevärt.</p>

<p><b>Nyckelord:</b> Textbehandling, AI-assistans, Människa-datorinteraktion, PyQt6, Dokumentarkitektur.</p>

<h2>1. Inledning</h2>
<p>Skrivprocessen ställer höga krav på kontinuerligt fokus. Traditionella ordbehandlare saknar ofta djup integration med intelligenta analysmodeller, vilket tvingar användare till externa webbgränssnitt.</p>

<h3>1.1 Problemformulering</h3>
<p>Hur kan en integrerad ordbehandlare tillhandahålla realtidsstöd utan att störa författarens kreativa tillstånd?</p>

<h2>2. Teoretisk Referensram</h2>
<p>Tidigare forskning inom datorstödd textproduktion (se t.ex. Flower & Hayes kognitiva skrivmodell) betonar vikten av friktionsfria övergångar mellan planering, formulering och granskning.</p>

<blockquote>"Att skriva är inte bara att registrera tankar, utan ett aktivt verktyg för själva tänkandet."</blockquote>

<h2>3. Metod</h2>
<p>Studien tillämpar en designvetenskaplig forskningsmetod (Design Science Research) där en fungerande prototyp iterativt utvecklats och utvärderats mot uppsatta kvalitetsmål.</p>

<h2>4. Resultat & Analys</h2>
<p>De insamlade mätvärdena påvisar en markant reduktion av omskrivningstid när semantiska förslag tillhandahålls direkt i blockkontexten.</p>

<h2>5. Källförteckning</h2>
<ul>
    <li>Hayes, J. R., & Flower, L. S. (1980). <i>Identifying the organization of writing processes</i>. Cognitive processes in writing.</li>
    <li>Norman, D. A. (2013). <i>The Design of Everyday Things</i>. Basic Books.</li>
</ul>
""",
        "html_en": """
<p style="text-align: center; color: #64748b; font-size: 12pt; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Department of Computer Science & Information Systems</p>
<h1 style="text-align: center; font-size: 24pt; margin-top: 0; margin-bottom: 12px;">Architectural Paradigms in Modern AI-Assisted Authoring Environments</h1>
<p style="text-align: center; font-size: 13pt; font-style: italic; color: #475569;">An Empirical Study on Interaction Latency and Contextual Model Steering</p>
<br/>
<p style="text-align: center; font-size: 11pt; color: #64748b;">Author: [Your Name] • Supervisor: [Supervisor Name] • Master Thesis (30 ECTS)</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 24px 0;"/>

<h2>Abstract</h2>
<p>This thesis investigates the interplay between native rich text editors and embedded machine learning copilots. By examining cognitive load and context-switching overhead across structured authoring tasks, we establish design patterns for seamless editor integration.</p>

<p><b>Keywords:</b> Text processing, Human-Computer Interaction, Local AI, Rich Text Architecture, Productivity.</p>

<h2>1. Introduction</h2>
<p>Authoring complex manuscripts demands sustained cognitive engagement. Disjointed web-based assistants introduce frequent context switching, fracturing the writer's concentration.</p>

<h2>2. Literature Review & Theory</h2>
<p>Cognitive process theories of writing emphasize the delicate balance between ideation, drafting, and reviewing phases.</p>

<blockquote>"Writing is not merely a recording medium for thoughts, but an epistemic engine for thought creation."</blockquote>

<h2>3. Methodology</h2>
<p>We employ Design Science Research (DSR), iteratively building and validating a native desktop artifact.</p>

<h2>4. Discussion & Findings</h2>
<p>Telemetry indicates a measurable drop in editing cycle time when context-aware inline assistants are deployed.</p>

<h2>5. References</h2>
<ul>
    <li>Flower, L., & Hayes, J. R. (1981). <i>A cognitive process theory of writing</i>. College Composition and Communication.</li>
    <li>Norman, D. A. (2013). <i>The Design of Everyday Things</i>. Basic Books.</li>
</ul>
"""
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
<table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0; background-color: #f8fafc;">
    <tr>
        <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1;">Datum & Tid:</td>
        <td style="width: 25%; border: 1px solid #cbd5e1;">[ÅÅÅÅ-MM-DD kl. 10:00–11:30]</td>
        <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1;">Plats:</td>
        <td style="width: 25%; border: 1px solid #cbd5e1;">[Konferensrum A / Digitalt]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Mötesledare:</td>
        <td style="border: 1px solid #cbd5e1;">[Namn]</td>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Protokollförare:</td>
        <td style="border: 1px solid #cbd5e1;">[Namn]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Närvarande:</td>
        <td colspan="3" style="border: 1px solid #cbd5e1;">[Deltagare 1, Deltagare 2, Deltagare 3, Deltagare 4]</td>
    </tr>
</table>

<h2>Dagordning</h2>
<ol>
    <li>Mötets öppnande och val av justerare</li>
    <li>Genomgång av föregående protokoll</li>
    <li>Statusrapport för pågående delprojekt</li>
    <li>Beslutspunkter & Resursallokering</li>
    <li>Övriga frågor & Nästa möte</li>
</ol>

<h2>§ 1. Formalia</h2>
<p>Mötet öppnades av ordföranden. [Namn] utsågs till protokolljusterare.</p>

<h2>§ 2. Beslutspunkter</h2>
<p><b>Beslut 2.1:</b> Styrelsen/gruppen beslutade enhälligt att godkänna den uppdaterade tidsplanen för Q4.</p>
<p><b>Beslut 2.2:</b> Budgettillskott för infrastruktur och licenser godkändes enligt framlagt förslag.</p>

<h2>§ 3. Åtgärdslista (Action Items)</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="border: 1px solid #cbd5e1; text-align: left;">Uppgift / Åtgärd</th>
        <th style="border: 1px solid #cbd5e1; text-align: left; width: 140px;">Ansvarig</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 110px;">Deadline</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 100px;">Status</th>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Färdigställa rapportutkast och PDF-underlag</td>
        <td style="border: 1px solid #cbd5e1;">[Namn]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-01</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #2563eb; font-weight: bold;">Pågår</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Kvalitetssäkra diagram och mätdata</td>
        <td style="border: 1px solid #cbd5e1;">[Namn]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-05</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #d97706; font-weight: bold;">Planerad</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Skicka ut inbjudan till nästa styrgruppsmöte</td>
        <td style="border: 1px solid #cbd5e1;">[Namn]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-09-25</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #16a34a; font-weight: bold;">Klar</td>
    </tr>
</table>
""",
        "html_en": """
<h1>Meeting Minutes — Project Sync</h1>
<table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0; background-color: #f8fafc;">
    <tr>
        <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1;">Date & Time:</td>
        <td style="width: 25%; border: 1px solid #cbd5e1;">[YYYY-MM-DD 10:00–11:30]</td>
        <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1;">Location:</td>
        <td style="width: 25%; border: 1px solid #cbd5e1;">[Conference Room A / Virtual]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Chair:</td>
        <td style="border: 1px solid #cbd5e1;">[Name]</td>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Secretary:</td>
        <td style="border: 1px solid #cbd5e1;">[Name]</td>
    </tr>
    <tr>
        <td style="font-weight: bold; border: 1px solid #cbd5e1;">Attendees:</td>
        <td colspan="3" style="border: 1px solid #cbd5e1;">[Attendee 1, Attendee 2, Attendee 3, Attendee 4]</td>
    </tr>
</table>

<h2>Agenda</h2>
<ol>
    <li>Opening and approval of agenda</li>
    <li>Review of previous action items</li>
    <li>Milestone status updates</li>
    <li>Key decision items</li>
    <li>AOB & Next meeting</li>
</ol>

<h2>Key Decisions</h2>
<p><b>Decision 1:</b> The committee unanimously approved the updated milestone timeline for Q4.</p>
<p><b>Decision 2:</b> Budget allocation for toolchain modernization was ratified.</p>

<h2>Action Items</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="border: 1px solid #cbd5e1; text-align: left;">Action Item</th>
        <th style="border: 1px solid #cbd5e1; text-align: left; width: 140px;">Assignee</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 110px;">Due Date</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 100px;">Status</th>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Finalize report draft and PDF delivery</td>
        <td style="border: 1px solid #cbd5e1;">[Name]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-01</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #2563eb; font-weight: bold;">In Progress</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Verify chart figures and dataset integrity</td>
        <td style="border: 1px solid #cbd5e1;">[Name]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-05</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #d97706; font-weight: bold;">Pending</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Dispatch invites for executive review</td>
        <td style="border: 1px solid #cbd5e1;">[Name]</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-09-25</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #16a34a; font-weight: bold;">Done</td>
    </tr>
</table>
"""
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
<p style="color: #64748b; font-size: 11pt;">Projektägare: [Namn] • Projektledare: [Namn] • Version 1.0 • Datum: [ÅÅÅÅ-MM-DD]</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 16px 0;"/>

<h2>1. Mål & Omfattning (Scope)</h2>
<p>Projektets huvudsakliga mål är att leverera en produktionsredo lösning som uppfyller verksamhetens krav på tillförlitlighet, användarvänlighet och prestanda.</p>

<table width="100%" style="background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
    <tr>
        <td style="vertical-align: top; width: 24px; font-size: 16px;">🎯</td>
        <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
            <b>Effektmål:</b> 50% minskad handläggningstid och full spårbarhet i alla led.
        </td>
    </tr>
</table>

<h2>2. Milstolpar & Tidslinje</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 70px;">Fas</th>
        <th style="border: 1px solid #cbd5e1; text-align: left;">Milstolpe / Leverabel</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 120px;">Slutdatum</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 100px;">Ansvarig</th>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M1</td>
        <td style="border: 1px solid #cbd5e1;">Kravspecifikation & Arkitekturdesign</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-15</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">Team Arkitektur</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M2</td>
        <td style="border: 1px solid #cbd5e1;">Prototypimplementering & Verifiering</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-11-15</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">Utvecklingsteam</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M3</td>
        <td style="border: 1px solid #cbd5e1;">Acceptanstest (UAT) & Dokumentation</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-12-05</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">QA & Produktägare</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M4</td>
        <td style="border: 1px solid #cbd5e1;">Produktionsdriftsättning & Överlämning</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-12-20</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">Drift / DevOps</td>
    </tr>
</table>

<h2>3. Riskanalys & Åtgärder</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="border: 1px solid #cbd5e1; text-align: left;">Identifierad Risk</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 90px;">Sannolikhet</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 90px;">Påverkan</th>
        <th style="border: 1px solid #cbd5e1; text-align: left;">Förebyggande åtgärd</th>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Fördröjningar i extern API-integration</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #d97706;">Medel</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #dc2626;">Hög</td>
        <td style="border: 1px solid #cbd5e1;">Mockade gränssnitt och tidig integrationstestning</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1;">Resursbrist under semesterperiod</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #16a34a;">Låg</td>
        <td style="border: 1px solid #cbd5e1; text-align: center; color: #d97706;">Medel</td>
        <td style="border: 1px solid #cbd5e1;">Tidig schemaläggning och korsutbildning i teamet</td>
    </tr>
</table>
""",
        "html_en": """
<h1>Project Charter: [Project Name]</h1>
<p style="color: #64748b; font-size: 11pt;">Owner: [Name] • Project Manager: [Name] • Version 1.0 • Date: [YYYY-MM-DD]</p>
<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 16px 0;"/>

<h2>1. Scope & Goals</h2>
<p>The project delivers a production-grade release fulfilling enterprise reliability, usability, and throughput requirements.</p>

<table width="100%" style="background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
    <tr>
        <td style="vertical-align: top; width: 24px; font-size: 16px;">🎯</td>
        <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
            <b>Target Outcome:</b> 50% reduction in processing cycle time with complete auditability.
        </td>
    </tr>
</table>

<h2>2. Milestone Roadmap</h2>
<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; border: 1px solid #cbd5e1; margin: 12px 0;">
    <tr style="background-color: #f1f5f9; font-weight: bold;">
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 70px;">Phase</th>
        <th style="border: 1px solid #cbd5e1; text-align: left;">Milestone / Deliverable</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 120px;">Target Date</th>
        <th style="border: 1px solid #cbd5e1; text-align: center; width: 100px;">Owner</th>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M1</td>
        <td style="border: 1px solid #cbd5e1;">Specification & System Architecture</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-10-15</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">Architecture Team</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M2</td>
        <td style="border: 1px solid #cbd5e1;">Core Implementation & Testing</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-11-15</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">Engineering</td>
    </tr>
    <tr>
        <td style="border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">M3</td>
        <td style="border: 1px solid #cbd5e1;">UAT Validation & Documentation</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">2026-12-05</td>
        <td style="border: 1px solid #cbd5e1; text-align: center;">QA & Product Owner</td>
    </tr>
</table>
"""
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
<table width="100%" style="border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 20px;">
    <tr>
        <td style="font-size: 22pt; font-weight: bold; color: #0f172a;">PROMEMORIA</td>
        <td style="text-align: right; font-size: 11pt; color: #64748b;">Datum: [ÅÅÅÅ-MM-DD]<br/>Dnr: PM-2026-042</td>
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

<h2>1. Sammanfattning & Förslag till beslut</h2>
<p>Detta PM föreslår att ledningen fattar beslut om att:</p>
<ol>
    <li>Godkänna införandet av den nya lösningen från och med nästkommande kvartal.</li>
    <li>Uppdra åt berörda avdelningar att påbörja förberedande implementering.</li>
</ol>

<h2>2. Bakgrund & Nuläge</h2>
<p>Nuvarande process har identifierats som en begränsande faktor för tillväxt och operativ effektivitet. En översyn visar på tydliga möjligheter till automatisering.</p>

<h2>3. Överväganden & Konsekvensanalys</h2>
<p>Införandet medför följande direkta fördelar samt identifierade risker:</p>
<ul>
    <li><b>Ekonomiska effekter:</b> Återbetalningstid beräknas till 8 månader.</li>
    <li><b>Verksamhetsnytta:</b> Högre datakvalitet och minskad administrativ belastning.</li>
</ul>

<table width="100%" style="background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
    <tr>
        <td style="vertical-align: top; width: 24px; font-size: 16px;">⚠️</td>
        <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
            <b>Observera:</b> En övergångsperiod om 2 veckor krävs för användarutbildning.
        </td>
    </tr>
</table>
""",
        "html_en": """
<table width="100%" style="border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 20px;">
    <tr>
        <td style="font-size: 22pt; font-weight: bold; color: #0f172a;">MEMORANDUM</td>
        <td style="text-align: right; font-size: 11pt; color: #64748b;">Date: [YYYY-MM-DD]<br/>Ref: MEMO-2026-042</td>
    </tr>
</table>

<table width="100%" style="margin-bottom: 18px; font-size: 11pt;">
    <tr>
        <td style="width: 100px; font-weight: bold;">TO:</td>
        <td>[Recipient / Executive Committee]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">FROM:</td>
        <td>[Your Name & Title]</td>
    </tr>
    <tr>
        <td style="font-weight: bold;">SUBJECT:</td>
        <td><b>[Clear and concise subject line]</b></td>
    </tr>
</table>

<h2>1. Executive Summary & Recommendation</h2>
<p>It is recommended that management approves the following actions:</p>
<ol>
    <li>Approve migration to the new platform starting next quarter.</li>
    <li>Authorize the cross-functional transition team to begin staging.</li>
</ol>

<h2>2. Context & Background</h2>
<p>The current manual workflow presents scalability bottlenecks. An operational review confirms substantial opportunities for optimization.</p>
"""
    }
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
