"""Stilvarningar ur ordlistor: fyllnadsord, klichéer, dialogtaggar och adverb.

De här är de klasser som går att **lista** — och därför de vi listar. Ordklasser
och passiv form kräver taggning av texten; LanguageTool (4.10) äger grammatiken,
och en gissning som pekar fel i författarens text är värre än ingen varning alls.
Adverben täcker bara de entydiga ändelserna (-ligen, -ly): svenska -t-adverb
(snabbt, gärna, ofta) går inte att skilja från adjektiv utan taggning, så de
lämnas åt grammatiken i stället för att fylla rapporten med falska träffar.

Båda språkens listor körs alltid. En svensk lista träffar inte engelsk text och
tvärtom, så ingen språkdetektering behövs — och en författare som skriver på
engelska får samma rapport som en som skriver på svenska.

Ett fynd per ord och manus, inte per scen: en lista med "liksom" tio gånger i
tio scener är tio rader som säger samma sak. Raden pekar i stället på den scen
där ordet är tätast, för det är där författaren har något att göra.

Ett ord som står i flera listor hamnar i den första: fyllnadsorden går före
adverben, så "egentligen" blir ett fyllnadsord och inte ett adverb. Ordningen är
fast, inte slumpad, så samma text ger samma rapport varje gång.

    python -m core.style_rules      kör självprovet
"""

from __future__ import annotations

import re
import tempfile
import shutil
from collections import defaultdict

from core.analysis import Finding, scenes_in_order, _tokens   # samma tokenisering som upprepningarna
from core.i18n import _

# Ord som sällan gör något för meningen. Listan är stramad efter en mätning på
# tre riktiga svenska romaner (Dan Andersson, Almqvist, "Noveller och skizzer"):
# med vanliga räkningsord och förbehåll som mycket, nästan, kanske, helt och
# plötsligt i listan toppades rapporten av dem (mycket 104 gånger i en bok), och
# en varning som pekar på vanligt språk lär författaren att strunta i rapporten.
# Kvar är de ord svensk och engelsk skrivrådgivning faktiskt namnger.
#
# "just" är medvetet borta: det är ett engelskt fyllnadsord men betyder "nyss"
# på svenska, och appen är svensk först. Homografer är priset för att båda
# språkens listor körs samtidigt utan språkdetektering.
FILLERS = frozenset("""
    liksom typ egentligen faktiskt väldigt ganska riktigt verkligen alltså
    tydligen uppenbarligen självklart naturligtvis
    very really quite rather actually basically literally simply totally
    definitely somewhat completely utterly extremely incredibly obviously
    clearly
""".split())

# Fras-fyllnadsord: de sitter ihop och fångas som fraser.
PHRASE_FILLERS = ("i princip", "på något sätt", "i alla fall", "på sätt och vis",
                  "en aning", "lite grand",
                  "pretty much", "in order to", "the fact that", "as a matter of fact",
                  "sort of", "kind of")

# Klichéer: en enda förekomst är en för många, så de kräver inget antal.
CLICHES = ("kallt som is", "kall som is", "tyst som graven", "hjärtat slog en volt",
           "en blixt från klar himmel", "tidens tand", "i sista stund",
           "tårarna brände", "hjärtat av guld", "som en våt filt",
           "mörkret sänkte sig", "en lättnadens suck", "blodet frös till is",
           "öronbedövande tystnad", "sist men inte minst", "vid det här laget",
           "at the end of the day", "cold as ice", "heart of gold",
           "avoid like the plague", "dead as a doornail", "calm before the storm",
           "needle in a haystack", "a sigh of relief", "blood ran cold",
           "deafening silence", "last but not least", "darkness descended")

# Dialogtaggar utöver sade/sa/said/asked. Det är de färgade taggarna som drar
# uppmärksamheten från repliken — prosa rådgivare brukar säga: behåll "sade".
DIALOGUE_TAGS = frozenset("""
    viskade skrek ropade mumlade muttrade suckade stönade väste fräste flinade
    fnissade skrattade utbrast invände stammade vrålade morrade kvittrade log
    whispered shouted screamed murmured muttered sighed groaned hissed snarled
    chuckled laughed giggled exclaimed retorted stammered bellowed yelled
    growled smiled cooed
""".split())

# Adverb: bara de entydiga ändelserna. Se modulens inledning om varför.
ADVERB_SUFFIXES = ("ligen", "ly")
ADVERB_MIN_LENGTH = 7

_STYLE_MIN_COUNT = 3

_fold = str.casefold
_CLICHE_KEYS = frozenset(_fold(k) for k in CLICHES)
_PHRASE_FILLERS_FOLDED = tuple(" ".join(map(_fold, p.split())) for p in PHRASE_FILLERS)
_PHRASE_FIRST_WORDS = frozenset(p.split()[0] for p in _PHRASE_FILLERS_FOLDED)


def _phrase_here(tokens, index: int) -> str | None:
    """Den fras som börjar på den här token, eller inget."""
    for phrase in _PHRASE_FILLERS_FOLDED:
        delar = phrase.split()
        if [token[0] for token in tokens[index:index + len(delar)]] == delar:
            return phrase
    return None


_CLICHE_RE = re.compile("|".join(re.escape(k) for k in CLICHES), re.IGNORECASE)


def _is_style_word(word: str) -> bool:
    return (word in FILLERS or word in DIALOGUE_TAGS
            or len(word) >= ADVERB_MIN_LENGTH and word.endswith(ADVERB_SUFFIXES))


def style_findings(scenes, min_count: int = _STYLE_MIN_COUNT) -> list[Finding]:
    """Fyllnadsord, klichéer, dialogtaggar och adverb över hela manuset.

    Ett fynd per ord (eller fras) och manus — tio scener med "liksom" är tio
    rader som säger samma sak, inte tio fynd. Fyndet bär den stavning som står i
    texten (versalt "Liksom" hittas av markören) och den scen där ordet är
    tätast, för det är där arbetet finns. Klichén kräver ingen tröskel: en
    förekomst är en för mycket, och det är just vad en kliché betyder.
    """
    findings: list[Finding] = []
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    # ord -> {scen: (stavning i texten, förekomst i scenen)}
    places: dict[str, dict[str, tuple[str, int]]] = defaultdict(dict)
    titles: dict[str, str] = {}

    for node_id, title, text in scenes:
        titles[node_id] = title
        for match in _CLICHE_RE.finditer(text):
            key = _fold(match.group(0))
            counts[key][node_id] += 1
            if node_id not in places[key]:           # första träffen i scenen bär platsen
                places[key][node_id] = (match.group(0),
                                        _fold(text[:match.start()]).count(key))

        tokens = [(_fold(w), w, start) for w, start, _end in _tokens(text)]
        for index, (folded, original, start) in enumerate(tokens):
            phrase = _phrase_here(tokens, index) if folded in _PHRASE_FIRST_WORDS else None
            if phrase:
                key = phrase
                original = " ".join(t[1] for t in tokens[index:index + len(phrase.split())])
            elif _is_style_word(folded):
                key = folded
            else:
                continue
            counts[key][node_id] += 1
            if node_id not in places[key]:
                places[key][node_id] = (original, _fold(text[:start]).count(key))

    for key, per_scene in counts.items():
        total = sum(per_scene.values())
        tröskel = 1 if key in _CLICHE_KEYS else min_count
        if total < tröskel:
            continue
        densest = max(per_scene, key=lambda scen: per_scene[scen])
        quote, occurrence = places[key][densest]
        if key in _CLICHE_KEYS:
            kind = "cliche"
        elif key in FILLERS or key in _PHRASE_FILLERS_FOLDED:
            kind = "filler"
        elif key in DIALOGUE_TAGS:
            kind = "dialogue_tag"
        else:
            kind = "adverb"
        note = _("style_note_scenes", total=total, scenes=len(per_scene), title=titles[densest])
        if kind == "dialogue_tag":
            note += _("style_note_consider_said")
        findings.append(Finding(kind=kind, label=quote, quote=quote, occurrence=occurrence,
                                node_id=densest, node_title=titles[densest], count=total,
                                note=note))

    findings.sort(key=lambda f: (-f.count, f.label))
    return findings


def _self_check() -> int:
    from core.project import Project

    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    root = tempfile.mkdtemp(prefix="style-check-")
    try:
        project = Project.create(root, "Stilprov", template="enkel")
        ett = project.manuscript()[0]
        project.write(ett.id, "<p>Han var liksom trött, liksom. Hon nickade liksom. "
                              "Han suckade, och suckade, och suckade igen. Det var "
                              "kallt som is. Egentligen, egentligen, egentligen.</p>")
        två = project.add_node("scene", "Andra")
        project.write(två.id, "<p>Liksom, liksom.</p>")
        tre = project.add_node("scene", "Tredje")
        project.write(tre.id, "<p>Han såg henne. the fact that det regnade, "
                              "the fact that hon teg, the fact that han gick. "
                              "Slutligen, slutligen, slutligen kom hon.</p>")
        scenes = scenes_in_order(project)
        findings = style_findings(scenes)
        kinds = defaultdict(list)
        for f in findings:
            kinds[f.kind].append(f)

        liksom = next((f for f in kinds["filler"] if f.label == "liksom"), None)
        kolla(liksom is not None and liksom.count == 5,
              f"fyllnadsordet räknas över hela manuset ({liksom.count if liksom else None})")
        kolla(liksom is not None and liksom.node_title == ett.title,
              f"och pekar i den scen där det är tätast ({liksom.node_title if liksom else None})")
        kolla(liksom is not None and liksom.occurrence >= 0
              and liksom.quote == liksom.label, "och bär ett textställe att markera")

        kolla(any(f.label == "kallt som is" for f in kinds["cliche"]),
              "klichéen hittas vid en enda förekomst")
        kolla(len(kinds["cliche"]) == 1, f"och bara den ena ({len(kinds['cliche'])})")
        kolla(any(f.label == "suckade" for f in kinds["dialogue_tag"]),
              "den färgade dialogtaggen hittas")
        kolla(not any(f.label in ("sade", "sa", "said") for f in findings),
              "medan 'sade' lämnas i fred")
        kolla(any(f.label.casefold() == "slutligen" for f in kinds["adverb"]),
              f"adverbet på -ligen hittas ({[f.label for f in kinds['adverb']]})")
        kolla(not any(f.label.endswith("t") and len(f.label) < ADVERB_MIN_LENGTH
                      for f in findings), "och inga korta -t-ord slinker med")
        kolla(any(f.label.replace("\u00a0", " ") == "the fact that" for f in kinds["filler"]),
              "fras-fyllnadsordet hittas")
        kolla(len([f for f in findings if f.kind == "filler" and f.count < _STYLE_MIN_COUNT]) == 0,
              "ett enstaka fyllnadsord blir inget fynd")
        kolla(all(f.node_id in {n.id for n in project.manuscript()} for f in findings),
              "varje fynd pekar på en riktig scen")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"style_rules: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
