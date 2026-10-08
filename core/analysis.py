"""Deterministic repetition and name consistency analysis for a manuscript."""

from __future__ import annotations

import re
import tempfile
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass

from core.project import Project, html_to_text


@dataclass
class Finding:
    kind: str
    label: str
    quote: str
    occurrence: int
    node_id: str
    node_title: str
    count: int
    note: str = ""


# Python's Unicode-aware \w includes Swedish letters; apostrophes and hyphens
# are explicitly kept inside tokens so names such as Anna-Lisa remain whole.
_TOKEN_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
_STOP = frozenset("a an and att av de dem den denna deras dess det detta dig du då efter eller en ett för från få genom ha hade han hans har här henne hennes hit hon honom hur i inte jag kan kanske komma kunde man med men mig min mitt mot mycket när ni nu och om oss på så sig sin sitt skulle som sådan sådant sådana till under upp ur vad var vara varit varje vem vi vid vilka vilken vilket vill än är även ö över the a an and are as at be been but by for from had has have he her hers him his i if in into is it its me my no not of on or our she that the their them then there they this to was we were what when where which who will with you your in och att det den de en ett är som på för med till av inte om jag du han hon vi de som från vid för att som och the a an an and or is was were to of in on for with his her it this that you i".split())
_WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)


def scenes_in_order(project) -> list[tuple[str, str, str]]:
    """Return (node_id, title, plain_text) for writable manuscript scenes."""
    return [(node.id, node.title, html_to_text(project.read(node.id)))
            for node in project.manuscript()]


def _tokens(text: str):
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def _occurrence(text: str, quote: str, offset: int) -> int:
    return text.count(quote, 0, offset)


TIGHT_REPEATS = 2      # minsta antal *täta* förekomster för ett fynd
WINDOW = 20            # ord; en fras av n ord får n * WINDOW


def repeats(scenes, min_count: int = TIGHT_REPEATS, max_words: int = 4, min_chars: int = 4,
            window: int = WINDOW) -> list[Finding]:
    """Ord och fraser som upprepas *tätt* — en författares tics.

    Ett fynd kräver `min_count` täta förekomster, inte att ordet står många
    gånger i boken. Mätt på tre riktiga svenska romaner (37 000–54 000 ord):

    * ren förekomst-räkning över hela boken gav 10 336 fynd på 120 000 ord, och
      på en riktig roman **552–892** — toppen var "bara (189 gånger)": vanligt
      språk som råkar ha ett närbeläget par någonstans i boken;
    * krav på två täta förekomster inom `window` ord gav **82–154 fynd per bok**,
      och toppen är namn och ord som faktiskt klumpar sig ("david", "nilenius",
      "älskar", "aldrig"), alltså precis det en författare vill se.

    En fras som börjar eller slutar i ett funktionsord räknas inte: "att gå" och
    "såg han" står tätt i varenda bok. Mätt: 316 fraser blev 31 på en roman.
    Markören pekar på den tätaste förekomsten — det är den som är ticen.
    """
    scenes = list(scenes)
    tight: dict = Counter()        # täta förekomster per fynd
    totals: dict = Counter()       # förekomster i hela manuset
    closest: dict = {}
    last_at: dict = {}
    scene_counts: dict = defaultdict(set)
    place: dict = {}               # tätaste träffen: (node_id, title, text, quote, start)
    at = 0
    for node_id, title, text in scenes:
        toks = _tokens(text)
        folded = [t.casefold() for t, _start, _end in toks]
        for n in range(1, max(1, max_words) + 1):
            for i in range(len(toks) - n + 1):
                words = folded[i:i + n]
                if sum(map(len, words)) < min_chars:
                    continue
                if words[0] in _STOP or (n > 1 and words[-1] in _STOP):
                    continue
                key = (n, tuple(words))
                totals[key] += 1
                scene_counts[key].add(node_id)
                previous = last_at.get(key)
                if previous is not None:
                    gap = at + i - previous
                    if gap <= window * n:
                        tight[key] += 1
                        if gap <= closest.get(key, 1 << 30):
                            closest[key] = gap
                            place[key] = (node_id, title, text,
                                          " ".join(t[0] for t in toks[i:i + n]), toks[i][1])
                last_at[key] = at + i
        at += len(toks)

    out = []
    for key, täta in tight.items():
        if täta < min_count:
            continue
        n = key[0]
        node_id, title, text, quote, start = place[key]
        note = (f"{täta} gånger tätt, {totals[key]} i boken, "
                f"tätast {closest[key]} ord isär")
        out.append((closest[key], Finding(
            "repeat" if n == 1 else "phrase",
            " ".join(key[1]) if n > 1 else quote, quote,
            _occurrence(text, quote, start), node_id, title, täta, note)))
    # Tätaste upprepningen först — det är den författaren skall åtgärda.
    out.sort(key=lambda par: (par[0], par[1].label.casefold()))
    return [finding for _gap, finding in out]


def _edit_distance_one(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > 1:
        return False
    i = j = edits = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1; j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            if len(a) >= len(b): i += 1
            if len(b) >= len(a): j += 1
    return edits + int(i < len(a) or j < len(b)) == 1


def name_consistency(scenes, entities) -> list[Finding]:
    scenes = list(scenes)
    entities = list(entities or [])
    counts = Counter()
    forms = defaultdict(Counter)
    first = {}
    corpus_names = set()
    for node_id, title, text in scenes:
        for m in _WORD_RE.finditer(text):
            word = m.group()
            counts[word.casefold()] += 1
            forms[word.casefold()][word] += 1
            first.setdefault((word.casefold(), word), (node_id, title, text, m.start()))
    out = []
    canonical = {}
    for entity in entities:
        for name in [getattr(entity, "name", ""), *(getattr(entity, "aliases", []) or [])]:
            if name:
                canonical.setdefault(name.casefold(), name)
                corpus_names.add(name.casefold())
    for canon_key, canon in canonical.items():
        if counts[canon_key] == 0:
            out.append(Finding("unused", canon, "", 0, "", "", 0, "Nämns inte i manuset"))
        for key, variants in forms.items():
            if key != canon_key and len(key) >= 4 and key[0] == canon_key[:1] and _edit_distance_one(key, canon_key) and sum(variants.values()) >= 2:
                variant = max(variants, key=variants.get)
                node_id, title, text, offset = first[(key, variant)]
                out.append(Finding("name_variant", variant, variant, _occurrence(text, variant, offset), node_id, title,
                                   sum(variants.values()), f"Variant av {canon}"))
    for key, variants in forms.items():
        upper = [v for v in variants if v[:1].isupper()]
        lower = [v for v in variants if v[:1].islower()]
        if upper and lower and sum(variants[v] for v in upper) >= 2 and sum(variants[v] for v in lower) >= 2:
            variant = min(upper + lower, key=lambda v: first[(key, v)][3])
            node_id, title, text, offset = first[(key, variant)]
            out.append(Finding("capitalisation", variant, variant, _occurrence(text, variant, offset), node_id, title,
                               sum(variants.values()), "Både versal och gemen stavning förekommer"))
    return out


def report(project, entities=None, min_count: int = TIGHT_REPEATS) -> dict:
    from core.style_rules import style_findings   # hit: annars blir det en cirkel

    scenes = scenes_in_order(project)
    findings = repeats(scenes, min_count=min_count)
    findings.extend(style_findings(scenes))
    if entities:
        findings.extend(name_consistency(scenes, entities))
    counts = {kind: sum(f.kind == kind for f in findings)
              for kind in ("repeat", "phrase", "name_variant", "capitalisation", "unused",
                           "filler", "cliche", "adverb", "dialogue_tag")}
    # Word count comes from the project model, never from a token count here:
    # every word figure in the app has to be the same figure.
    return {"scenes": len(scenes), "words": project.total_words(),
            "findings": findings, "counts": counts}


def _self_check() -> int:
    from types import SimpleNamespace

    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    root = tempfile.mkdtemp(prefix="analysis-check-")
    try:
        project = Project.create(root, "Analysis check", template="enkel")
        scene = project.manuscript()[0]
        project.write(scene.id, "<p>Anna såg å ä ö 😀. Anna såg. En gång såg. %</p>")
        s2 = project.add_node("scene", "Second")
        project.write(s2.id, "<p>blorpt blorpt</p>")
        s3 = project.add_node("scene", "Third")
        project.write(s3.id, "<p>blorpt blorpt blorpt. skogen teg skogen teg skogen teg. "
                             "att gå att gå att gå.</p>")
        scenes = scenes_in_order(project)
        findings = repeats(scenes)
        blorpt = next((f for f in findings if f.label.casefold() == "blorpt"), None)
        kolla(blorpt is not None and blorpt.count == 4,
              "täta förekomster av samma ord blir ett fynd — två i tredje scenen, ett i "
              f"andra och ett över scenbytet ({blorpt.count if blorpt else None})")
        kolla(blorpt is not None and "gånger tätt" in blorpt.note,
              f"och noten skiljer tätt från totalt ({blorpt.note if blorpt else None})")
        kolla(blorpt is not None and blorpt.quote in scenes[1][2] + scenes[2][2],
              "och citatet står i texten")
        fras = next((f for f in findings if f.kind == "phrase" and f.label == "skogen teg"), None)
        kolla(fras is not None and fras.count == 2,
              f"en fras med innehållsord i båda ändar blir ett fynd ({fras.count if fras else None})")
        kolla(fras is not None and "2 ord isär" in fras.note,
              f"och noten säger hur tätt ({fras.note if fras else None})")
        kolla(not any(f.label == "att gå" for f in findings),
              "medan 'att gå' lämnas i fred — grammatik, inte en tic")
        kolla(not any(f.label.casefold() == "anna" for f in findings),
              "ett namn två gånger i samma mening är inget fynd vid tröskeln")
        kolla(all(ch in scenes[0][2] for ch in ("å", "ä", "ö", "😀", "%")),
              "texten behåller å, ä, ö, emoji och procenttecken")

        # Två felstavningar av ett codexnamn, och ett namn som aldrig nämns.
        project.write(scene.id, "<p>Anna Anna Anna Annna Annna</p>")
        scenes = scenes_in_order(project)
        names = name_consistency(scenes, [
            SimpleNamespace(name="Anna", aliases=[], type="character"),
            SimpleNamespace(name="Unused", aliases=[], type="character")])
        kolla(any(f.kind == "name_variant" and f.label == "Annna" for f in names),
              "felstavningen av codexnamnet hittas")
        kolla(any(f.kind == "unused" and f.label == "Unused" for f in names),
              "och codexnamnet som aldrig nämns")
        anna = next((f for f in repeats(scenes) if f.label.casefold() == "anna"), None)
        kolla(anna is not None and anna.occurrence == 2 and anna.quote in scenes[0][2],
              "namnet får en plats markören kan stå på — den tätaste träffen, inte den "
              f"första ({anna.occurrence if anna else None})")

        empty_root = tempfile.mkdtemp(prefix="analysis-empty-")
        try:
            empty_project = Project.create(empty_root, "Empty", template="enkel")
            kolla(report(empty_project)["findings"] == [], "ett tomt projekt ger en tom rapport")
        finally:
            shutil.rmtree(empty_root, ignore_errors=True)

        # Närheten är det som gör rapporten användbar: samma ord fyra gånger
        # med 50 ord emellan är fyra vanliga ord, tre gånger direkt efter
        # varandra är en tic. Utan kravet gav en riktig roman 552–892 fynd,
        # med det 82–154.
        fyll = " ".join(f"fyll{i}" for i in range(50))
        project.write(scene.id, f"<p>häst {fyll} häst {fyll} häst {fyll} häst tyst tyst tyst</p>")
        nära = {f.label.casefold(): f for f in repeats(scenes_in_order(project))}
        kolla("häst" not in nära, "fyra förekomster med 50 ord emellan är inget fynd")
        kolla("tyst" in nära and "1 ord isär" in nära["tyst"].note,
              f"tre på rad är ett fynd ({nära['tyst'].note if 'tyst' in nära else None})")
        kolla(report(project)["words"] == project.total_words(),
              "och ordtalet i rapporten är projektets eget")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(f"analysis: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
