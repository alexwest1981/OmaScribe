"""core/context.py — vad som faktiskt skickas till AI:n (6.16, 6.17).

Ett anrop till en modell är ett *urval*: några scener, några codexposter, en
instruktion och en fråga. Den här modulen gör urvalet explicit. Varje del blir
en `Item` med ett **skäl** ("scenen du har öppen", "nämns i texten", "vald av
dig") och en **tokenräkning**, så att fönstret kan visa exakt vad som lämnar
datorn innan det gör det — NovelAI:s Context Viewer, och ett krav i planen
("Visa vilka textdelar som faktiskt skickas").

Urvalet är nyckelordsöverlapp, inte vektorer: en författare frågar "var nämns
nyckeln?" och då räcker ord. Det är en medveten avvägning — se `relevant_scenes`.

    python -m core.context      kör självprovet
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Vad en codexpost gör i varje anrop (6.17). "mention" är standard: posten följer
# med när namnet står i texten, vilket är det som gör kontexten relevant utan att
# hela bibeln skickas varje gång.
POLICY_ALWAYS = "always"
POLICY_MENTION = "mention"
POLICY_NEVER = "never"
POLICIES = (POLICY_ALWAYS, POLICY_MENTION, POLICY_NEVER)

KIND_INSTRUCTION = "instruction"
KIND_SCENE = "scene"
KIND_CODEX = "codex"
KIND_NOTE = "note"
KIND_NAMES = {KIND_INSTRUCTION: "instruktion", KIND_SCENE: "scen",
              KIND_CODEX: "codex", KIND_NOTE: "anteckning"}

# Ordningen avgör vad som stryks först när budgeten är slut. Instruktionen och
# frågan stryks aldrig.
PRIORITY = {KIND_INSTRUCTION: 0, KIND_SCENE: 1, KIND_CODEX: 2, KIND_NOTE: 3}

DEFAULT_BUDGET = 8000            # tecken, inte exakta tokens — se estimate_tokens
STOPWORDS = {
    "och", "att", "det", "som", "den", "det", "har", "med", "för", "inte",
    "var", "han", "hon", "jag", "vi", "de", "en", "ett", "på", "av", "till",
    "the", "and", "that", "with", "for", "was", "were", "his", "her", "she",
    "he", "they", "have", "has", "this", "from", "but", "not", "you",
}


def estimate_tokens(text: str) -> int:
    """En grov men ärlig uppskattning: ~4 tecken per token för svensk prosa.

    Den är inte exakt och säger inte att den är det — siffran finns för att
    kunna visa *storleken* på ett urval, och för att kunna hålla en budget.
    """
    return max(1, int(round(len(text or "") / 4)))


@dataclass
class Item:
    """En del av det som skickas, med skälet till att den är med."""

    kind: str
    label: str
    text: str
    reason: str
    scene_id: str = ""
    entity_id: str = ""
    note_id: str = ""
    tokens: int = 0
    dropped: bool = False
    truncated: bool = False

    def with_tokens(self) -> "Item":
        self.tokens = estimate_tokens(self.text)
        return self

    def render(self) -> str:
        return f"## {KIND_NAMES.get(self.kind, self.kind)}: {self.label}\n{self.text}"


def terms(text: str) -> set[str]:
    """Orden som bär mening: fyra tecken och uppåt, utan stoppord."""
    ord_ = re.findall(r"\w+", (text or "").lower(), re.UNICODE)
    return {o for o in ord_ if len(o) >= 4 and o not in STOPWORDS}


def scene_text(project, node_id: str) -> str:
    from core.project import html_to_text

    try:
        return html_to_text(project.read(node_id))
    except (KeyError, OSError):
        return ""


def relevant_scenes(project, question: str, limit: int = 4,
                    exclude=()) -> list[tuple[object, float]]:
    """Scenerna som handlar om det frågan handlar om.

    ponytail: nyckelordsöverlapp, inte embeddings. Utan ett vektorlager är det
    den ärliga nivån — den fångar namn och ord författaren själv skulle söka på
    ("nyckeln", "Bo"), och den kostar inget. Byt mot embeddings den dag ett
    vektorlager finns, men mät först att det behövs.
    """
    ville = terms(question)
    if not ville:
        return []
    uteslutna = set(exclude)
    träffar: list[tuple[object, float]] = []
    for nod in project.manuscript():
        if nod.id in uteslutna:
            continue
        text = scene_text(project, nod.id)
        if not text.strip():
            continue
        egna = terms(text)
        if not egna:
            continue
        delade = ville & egna
        if not delade:
            continue
        # Delade ord som andel av frågan, med en liten knuff för flera träffar:
        # en scen som nämner tre av frågans ord går före en som nämner ett.
        poäng = len(delade) / len(ville) + min(len(delade), 5) * 0.05
        träffar.append((nod, round(poäng, 4)))
    träffar.sort(key=lambda par: (-par[1], par[0].order))
    return träffar[:limit]


def codex_policies(project) -> dict:
    """Per codexpost: alltid, vid omnämning eller aldrig. Sparas i projektet."""
    return dict(getattr(project, "context_policy", {}) or {})


def set_codex_policy(project, entity_id: str, policy: str) -> str:
    if policy not in POLICIES:
        raise ValueError(f"okänd policy: {policy}")
    if not hasattr(project, "context_policy") or project.context_policy is None:
        project.context_policy = {}
    if policy == POLICY_MENTION:
        project.context_policy.pop(entity_id, None)   # standard, inget att spara
    else:
        project.context_policy[entity_id] = policy
    return policy


def codex_items(project, bible, scene_id: str, text: str, policies: dict) -> list[Item]:
    """Codexposterna som skall med, och varför var och en är med."""
    if bible is None:
        return []
    nämnda = {e.id for e in bible.mentions(text)} if text else set()
    kopplade = {e.id for e in bible.for_node(scene_id)} if scene_id else set()
    ut: list[Item] = []
    for ent in bible.entities():
        policy = policies.get(ent.id, POLICY_MENTION)
        if policy == POLICY_NEVER:
            continue
        if policy == POLICY_ALWAYS:
            skäl = "alltid med (du har valt det)"
        elif ent.id in nämnda:
            skäl = "nämns i scenen"
        elif ent.id in kopplade:
            skäl = "kopplad till scenen"
        else:
            continue
        text_ut = (ent.summary or "").strip()
        if ent.fields:
            rader = "; ".join(f"{k}: {v}" for k, v in ent.fields.items() if v)
            text_ut = (text_ut + ("\n" if text_ut else "") + rader).strip()
        if ent.notes:
            text_ut = (text_ut + ("\n" if text_ut else "") + ent.notes.strip()).strip()
        if not text_ut:
            continue      # en post utan innehåll skickar vi inte tom
        ut.append(Item(kind=KIND_CODEX, label=ent.name, text=text_ut,
                       reason=skäl, entity_id=ent.id).with_tokens())
    return ut


def build(project, *, scene_id: str = "", question: str = "", instruction: str = "",
          extra_scenes=(), bible=None, policies: dict | None = None,
          budget_chars: int = DEFAULT_BUDGET, retrieved: int = 4) -> list[Item]:
    """Hela urvalet för ett anrop, i den ordning det skickas.

    Ordningen är avsiktlig: instruktionen först (den styr), sedan scenen
    författaren arbetar i, sedan de scener frågan pekar ut, sedan codexet.
    """
    items: list[Item] = []
    if instruction.strip():
        items.append(Item(kind=KIND_INSTRUCTION, label="uppdrag", text=instruction.strip(),
                          reason="din instruktion").with_tokens())

    sedda: set[str] = set()
    egen_text = ""
    if scene_id:
        egen_text = scene_text(project, scene_id)
        if egen_text.strip():
            try:
                rubrik = project.by_id(scene_id).title
            except KeyError:
                rubrik = scene_id
            items.append(Item(kind=KIND_SCENE, label=rubrik, text=egen_text.strip(),
                              reason="scenen du har öppen", scene_id=scene_id).with_tokens())
            sedda.add(scene_id)

    for nod_id in extra_scenes:
        if nod_id in sedda:
            continue
        text = scene_text(project, nod_id)
        if not text.strip():
            continue
        try:
            rubrik = project.by_id(nod_id).title
        except KeyError:
            continue
        items.append(Item(kind=KIND_SCENE, label=rubrik, text=text.strip(),
                          reason="vald av dig", scene_id=nod_id).with_tokens())
        sedda.add(nod_id)

    if question.strip():
        for nod, poäng in relevant_scenes(project, question, limit=retrieved, exclude=sedda):
            text = scene_text(project, nod.id)
            items.append(Item(kind=KIND_SCENE, label=nod.title, text=text.strip(),
                              reason=f"frågan pekar hit (styrka {poäng:g})",
                              scene_id=nod.id).with_tokens())
            sedda.add(nod.id)

    ämne = egen_text if scene_id else ""
    items.extend(codex_items(project, bible, scene_id, ämne, policies or codex_policies(project)))

    if question.strip():
        items.append(Item(kind=KIND_INSTRUCTION, label="fråga", text=question.strip(),
                          reason="din fråga").with_tokens())
    return fit(items, budget_chars)


def fit(items: list[Item], budget_chars: int = DEFAULT_BUDGET) -> list[Item]:
    """Håller urvalet inom budgeten och *säger vad som ströks*.

    Strykningen sker i prioritetsordning bakifrån, och ett objekt som är för
    stort för att få plats kortas i stället för att försvinna tyst — en halv scen
    med en anteckning om det är ärligare än ingen scen alls.
    """
    if budget_chars <= 0:
        return items
    summa = sum(len(i.text) for i in items)
    if summa <= budget_chars:
        return items
    kvar = list(items)
    # Stryk längst ned först.
    ordning = sorted(range(len(kvar)), key=lambda i: (-PRIORITY.get(kvar[i].kind, 9), i))
    for i in ordning:
        if summa <= budget_chars:
            break
        objekt = kvar[i]
        if PRIORITY.get(objekt.kind, 9) <= PRIORITY[KIND_SCENE] and objekt.scene_id == "":
            continue      # instruktionen och frågan stryks aldrig
        summa -= len(objekt.text)
        objekt.dropped = True
        objekt.reason += " — ströks: budgeten tog slut"
    # Korta det största som är kvar om det ändå inte ryms.
    if summa > budget_chars:
        störst = max((i for i in kvar if not i.dropped), key=lambda i: len(i.text),
                     default=None)
        if störst is not None:
            tillåtet = max(400, budget_chars - (summa - len(störst.text)))
            störst.text = störst.text[:tillåtet].rstrip() + " …"
            störst.truncated = True
            störst.reason += " — kortad: budgeten tog slut"
            störst.with_tokens()
    return [i for i in kvar if not i.dropped]


def render(items: list[Item]) -> str:
    """Urvalet som den text modellen faktiskt får."""
    return "\n\n".join(i.render() for i in items if not i.dropped)


def summary(items: list[Item]) -> dict:
    """Siffrorna fönstret visar: antal delar, tecken och uppskattade tokens."""
    kvar = [i for i in items if not i.dropped]
    tecken = sum(len(i.text) for i in kvar)
    return {"items": len(kvar), "chars": tecken, "tokens": estimate_tokens("x" * tecken),
            "dropped": sum(1 for i in items if i.dropped)}


def _self_check() -> int:
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    import shutil
    import tempfile

    from core.project import Project
    from core.storybible import StoryBible

    root = tempfile.mkdtemp(prefix="context-check-")
    try:
        projekt = Project.create(root, "Kontextprov", template="enkel")
        kapitel = projekt.add_node("chapter", "Första kapitlet")
        scen1 = projekt.add_node("scene", "Nyckeln", parent=kapitel.id)
        scen2 = projekt.add_node("scene", "Stranden", parent=kapitel.id)
        scen3 = projekt.add_node("scene", "Slutet", parent=kapitel.id)
        projekt.write(scen1.id, "<p>Anna vände nyckeln i handen och lyssnade "
                                "efter trappan.</p>")
        projekt.write(scen2.id, "<p>Bo gick ner till stranden och såg båten "
                               "komma in.</p>")
        projekt.write(scen3.id, "<p>Nyckeln låg kvar på bordet när allt var "
                                "slut.</p>")

        bible = StoryBible(str(projekt.root / "codex.db"))
        anna = bible.add_entity("Anna", "character", aliases=["Anna-Karin"],
                                summary="Huvudperson, samlar på nycklar.")
        bo = bible.add_entity("Bo", "character", summary="Bor vid stranden.")
        aldrig = bible.add_entity("Staden", "place", summary="Nämns sällan.")
        bible.link(bo.id, scen1.id)

        kolla(estimate_tokens("abcd" * 25) == 25, "tokenuppskattningen är tecken delat med fyra")
        kolla(terms("Anna vände nyckeln") == {"anna", "vände", "nyckeln"},
              f"vanliga ord filtreras bort ({sorted(terms('Anna vände nyckeln'))})")

        träffar = relevant_scenes(projekt, "var är nyckeln?")
        kolla([n.title for n, _ in träffar] == ["Nyckeln", "Slutet"],
              f"frågan hittar scenerna som nämner ordet ({[n.title for n, _ in träffar]})")
        kolla(all(p > 0 for _, p in träffar), "med en styrka per träff")
        kolla(relevant_scenes(projekt, "och att det") == [],
              "och en fråga utan innehållsord ger ingenting")

        items = build(projekt, scene_id=scen1.id, question="var är nyckeln?",
                      bible=bible)
        slag = [i.kind for i in items]
        kolla(slag[0] == KIND_SCENE, "scenen du har öppen kommer först")
        kolla(any(i.kind == KIND_CODEX and i.label == "Anna" for i in items),
              "codexposten som nämns i scenen är med")
        kolla(any(i.kind == KIND_CODEX and i.label == "Bo"
                  and "kopplad" in i.reason for i in items),
              "och den som är kopplad till scenen, med det skälet")
        kolla(not any(i.label == "Staden" for i in items),
              "men inte en post som varken nämns eller är kopplad")
        kolla(slag[-1] == KIND_INSTRUCTION and items[-1].label == "fråga",
              "och frågan sist, där modellen läser den")
        kolla(all(i.tokens > 0 for i in items), "varje del har sin tokenräkning")
        kolla(sum(i.tokens for i in items) == summary(items)["tokens"],
              "och summan stämmer med översikten")

        # Policy (6.17)
        set_codex_policy(projekt, aldrig.id, POLICY_ALWAYS)
        items2 = build(projekt, scene_id=scen1.id, bible=bible)
        kolla(any(i.label == "Staden" and "alltid" in i.reason for i in items2),
              "en post som alltid skall med följer med även onämnd")
        set_codex_policy(projekt, anna.id, POLICY_NEVER)
        items3 = build(projekt, scene_id=scen1.id, bible=bible)
        kolla(not any(i.label == "Anna" for i in items3),
              "och en post som aldrig skall med är borta")
        set_codex_policy(projekt, anna.id, POLICY_MENTION)
        kolla(anna.id not in codex_policies(projekt),
              "standardvalet sparas inte som en inställning")

        # Budgeten: något skall strykas, och det skall synas.
        stort = build(projekt, scene_id=scen1.id, question="var är nyckeln?",
                      bible=bible, budget_chars=120)
        kolla(sum(len(i.text) for i in stort) <= 400,
              f"budgeten håller urvalet litet ({sum(len(i.text) for i in stort)} tecken)")
        alla = build(projekt, scene_id=scen1.id, question="var är nyckeln?", bible=bible,
                     budget_chars=120)
        kolla(alla != [], "och något blir alltid kvar")

        kolla("## scen:" in render(items).lower(),
              f"renderingen namnger varje del ({render(items).splitlines()[0]!r})")
        visad = render(items)
        kolla(visad.count("## ") == len(items), "med en rubrik per del")
        kolla(all(i.text in visad for i in items), "och varje dels text orörd")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"context: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
