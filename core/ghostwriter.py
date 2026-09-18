"""
core/ghostwriter.py — skriv vidare i användarens röst när det tar stopp.

Två delar:

  StyleProfile   analyserar en text och beskriver dess röst i ord (meninglängd,
                 person, tonläge, typiska fraser) så att modellen kan härma den
                 i stället för att producera generisk AI-prosa.
  GhostwriterWorker
                 fyra lägen — continue / expand / angle / unstick — som alla
                 returnerar färdig text att sätta in i dokumentet.

Lägena continue, expand och angle ger flera varianter så att användaren väljer
riktning i stället för att få ett enda förslag att förkasta.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_client import chat_completion, parse_json_response
from core.config import DEFAULT_AI_ENDPOINT, DEFAULT_AI_MODEL

# Vanliga småord som inte säger något om stilen
STOPWORDS = {
    # svenska
    "och", "att", "det", "som", "en", "ett", "är", "på", "för", "med", "den", "de",
    "inte", "av", "till", "har", "jag", "vi", "du", "man", "kan", "så", "om", "men",
    "vara", "sig", "från", "vid", "när", "då", "hur", "vad", "han", "hon", "dem",
    "också", "bara", "efter", "över", "under", "mellan", "eller", "skulle", "blir",
    "blev", "varit", "hade", "här", "där", "detta", "dessa", "denna", "sin", "sitt",
    # engelska
    "the", "and", "that", "this", "with", "for", "are", "was", "were", "have",
    "has", "had", "not", "but", "you", "your", "they", "them", "from", "will",
    "would", "there", "their", "what", "when", "which", "into", "than", "then",
    "been", "more", "some", "such", "can", "could", "should", "about", "also",
    "these", "those",
}

FORMAL_MARKERS = {
    "sv": ["därmed", "emellertid", "således", "icke", "tillika", "avseende",
           "beträffande", "följaktligen", "innebär", "såväl", "ej", "påvisar"],
    "en": ["therefore", "however", "furthermore", "moreover", "consequently",
           "regarding", "concerning", "thus", "hence", "demonstrates"],
}
CASUAL_MARKERS = {
    "sv": ["ju", "liksom", "typ", "ganska", "rätt", "himla", "grej", "kolla",
           "fixa", "grejen", "ball", "asbra", "nice"],
    "en": ["kinda", "sorta", "pretty", "stuff", "things", "really", "totally",
           "awesome", "cool", "gonna", "wanna"],
}
FIRST_PERSON = {"sv": ["jag", "vi", "mig", "oss", "min", "mitt", "mina", "vår", "vårt"],
                "en": ["i", "we", "me", "us", "my", "our", "mine", "ours"]}
SECOND_PERSON = {"sv": ["du", "dig", "din", "ditt", "dina", "ni", "er"],
                 "en": ["you", "your", "yours"]}


class StyleProfile:
    """Beskriver stilen i en text med hjälp av mätbara drag."""

    @staticmethod
    def _lang_key(lang: str) -> str:
        return "sv" if str(lang or "").lower().startswith("sv") else "en"

    @staticmethod
    def analyze(text: str, lang: str = "en") -> dict:
        raw = (text or "").strip()
        if not raw:
            return {}

        lk = StyleProfile._lang_key(lang)
        sentences = [s for s in re.split(r"(?<=[.!?…])\s+", raw) if s.strip()]
        words = re.findall(r"[A-Za-zÅÄÖåäöÉéÜü]+", raw.lower())
        paragraphs = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]

        n_sent = max(1, len(sentences))
        n_words = max(1, len(words))

        long_words = [w for w in words if len(w) >= 7]
        content = [w for w in words if w not in STOPWORDS and len(w) > 2]

        first_p = sum(1 for w in words if w in FIRST_PERSON[lk])
        second_p = sum(1 for w in words if w in SECOND_PERSON[lk])
        if first_p > n_words * 0.02 and first_p >= second_p:
            person = "första person (jag/vi)" if lk == "sv" else "first person (I/we)"
        elif second_p > n_words * 0.02:
            person = "tilltal (du/ni)" if lk == "sv" else "second person (you)"
        else:
            person = "tredje person / opersonligt" if lk == "sv" else "third person / impersonal"

        formal_hits = sum(raw.lower().count(m) for m in FORMAL_MARKERS[lk])
        casual_hits = sum(raw.lower().count(m) for m in CASUAL_MARKERS[lk])
        if formal_hits > casual_hits * 1.5:
            tone = "formell" if lk == "sv" else "formal"
        elif casual_hits > formal_hits:
            tone = "ledig och talspråklig" if lk == "sv" else "casual and conversational"
        else:
            tone = "neutral och saklig" if lk == "sv" else "neutral"

        # Vanliga fraser: återkommande ordpar
        bigrams = Counter(
            " ".join(content[i:i + 2]) for i in range(len(content) - 1)
            if len(content[i]) > 2 and len(content[i + 1]) > 2
        )

        return {
            "sentences": len(sentences),
            "words": len(words),
            "paragraphs": len(paragraphs),
            "avg_sentence_words": round(n_words / n_sent, 1),
            "avg_paragraph_sentences": round(len(sentences) / max(1, len(paragraphs)), 1),
            "avg_word_length": round(sum(len(w) for w in words) / n_words, 1),
            "long_word_ratio": round(len(long_words) / n_words, 3),
            "person": person,
            "tone": tone,
            "questions": raw.count("?"),
            "exclamations": raw.count("!"),
            "semicolons": raw.count(";"),
            "dashes": raw.count("—") + raw.count(" – "),
            "quote_style": "typografiska" if ("”" in raw or "”" in raw) else "raka",
            "top_words": [w for w, _c in Counter(content).most_common(12)],
            "phrases": [p for p, c in bigrams.most_common(6) if c >= 2],
        }

    @staticmethod
    def describe(profile: dict, lang: str = "en") -> str:
        """Gör om profilen till en kompakt instruktion för modellen."""
        if not profile:
            return ""
        lk = StyleProfile._lang_key(lang)
        n = profile.get("avg_sentence_words", 0)
        if n and n < 12:
            length = "korta meningar" if lk == "sv" else "short sentences"
        elif n and n > 22:
            length = "långa, utbyggda meningar" if lk == "sv" else "long, elaborate sentences"
        else:
            length = "medellånga meningar" if lk == "sv" else "medium-length sentences"

        bits = [
            f"{profile.get('avg_sentence_words')} ord per mening ({length})",
            f"cirka {profile.get('avg_paragraph_sentences')} meningar per stycke",
            profile.get("person", ""),
            f"tonläge: {profile.get('tone', '')}",
            f"ordlängd i snitt {profile.get('avg_word_length')} tecken",
        ]
        if profile.get("questions"):
            bits.append(f"{profile['questions']} frågetecken")
        if profile.get("dashes"):
            bits.append("använder tankstreck")
        if profile.get("top_words"):
            bits.append("återkommande ord: " + ", ".join(profile["top_words"]))
        if profile.get("phrases"):
            bits.append("återkommande fraser: " + "; ".join(profile["phrases"]))

        head = "Uppmätt stil i befintlig text" if lk == "sv" else "Measured style of the existing text"
        return f"{head}: " + " | ".join(b for b in bits if b)


class GhostwriterWorker(QThread):
    """Genererar text som fortsätter användarens dokument i samma röst."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)   # {variants, mode, profile}
    failed = pyqtSignal(str)

    MODES = ("continue", "expand", "angle", "unstick")

    def __init__(self, config, mode: str, document_text: str, instruction: str = "",
                 reference_text: str = "", lang: str = "en", variants: int = 3):
        super().__init__()
        self.config = config
        self.mode = mode if mode in self.MODES else "continue"
        self.document_text = document_text or ""
        self.instruction = (instruction or "").strip()
        self.reference_text = reference_text or ""
        self.lang = lang
        self.variants = max(1, min(int(variants), 4))
        self._stopped = False

    def stop(self):
        self._stopped = True

    # -- anropas i tråden ---------------------------------------------------

    def run(self):
        try:
            self.progress.emit(self.mode)
            profile = StyleProfile.analyze(self.document_text or self.reference_text, self.lang)
            style_note = StyleProfile.describe(profile, self.lang)

            sys_prompt, user_prompt, want_variants = self._build_prompt(style_note)

            endpoint = self.config.get("ai_endpoint", DEFAULT_AI_ENDPOINT)
            api_key = self.config.get("ai_key", "")
            model = self.config.get("ai_model", DEFAULT_AI_MODEL)

            out = chat_completion(endpoint, api_key, model, sys_prompt, user_prompt,
                                  timeout=120.0, temperature=0.85)
            if self._stopped:
                return

            variants = self._parse_variants(out, want_variants)
            self.finished.emit({
                "variants": variants,
                "mode": self.mode,
                "profile": profile,
            })
        except Exception as e:
            self.failed.emit(str(e))

    # -- promptbygge --------------------------------------------------------

    def _build_prompt(self, style_note: str) -> tuple:
        lk = "sv" if str(self.lang).lower().startswith("sv") else "en"
        target_lang = "svenska" if lk == "sv" else "English"

        tail = self.document_text[-2500:] if self.document_text else ""
        ref = self.reference_text[:2500] if self.reference_text else ""

        rules_sv = (
            "Regler:\n"
            "1. Skriv på svenska, i SAMMA röst som texten nedan. Härma meningslängd, "
            "ordval och tonläge. Det ska inte gå att se att en maskin skrev fortsättningen.\n"
            "2. Upprepa INTE texten som redan står där. Fortsätt bara.\n"
            "3. Hitta inte på fakta, siffror eller citat som inte finns i underlaget.\n"
            "4. Ingen rubrik, ingen metakommentar, ingen förklaring av vad du gjorde. "
            "Bara själva texten.\n"
            "5. Undvik AI-typiska fraser som \"i dagens samhälle\", \"det är viktigt att notera\", "
            "\"sammanfattningsvis\"."
        )
        rules_en = (
            "Rules:\n"
            "1. Write in English, in the SAME voice as the text below. Match sentence length, "
            "word choice and tone. It must not be detectable that a machine wrote it.\n"
            "2. Do NOT repeat text that is already there. Only continue.\n"
            "3. Do not invent facts, numbers or quotes not present in the material.\n"
            "4. No heading, no meta-commentary, no explanation of what you did. Just the text.\n"
            "5. Avoid AI clichés such as \"in today's world\", \"it is important to note\", "
            "\"in conclusion\"."
        )
        rules = rules_sv if lk == "sv" else rules_en

        base = (
            f"You are a ghostwriter. You continue someone else's document in THEIR voice, "
            f"never your own. Output language: {target_lang}.\n\n"
        )
        if style_note:
            base += style_note + "\n\n"

        want_variants = True

        if self.mode == "continue":
            task_sv = (
                f"Uppgift: skriv fortsättningen på texten — {self.variants} olika alternativ. "
                "Varje alternativ är 1–2 stycken som naturligt tar vid där texten slutar."
            )
            task_en = (
                f"Task: write the continuation of the text — {self.variants} different options. "
                "Each option is 1–2 paragraphs that pick up naturally where the text ends."
            )
            task = task_sv if lk == "sv" else task_en

        elif self.mode == "expand":
            task_sv = (
                "Uppgift: användaren har en idé eller punktlista som ska bli löpande text. "
                f"Skriv ut den till {self.variants} olika textversioner som passar in i dokumentet."
            )
            task_en = (
                "Task: the user has an idea or a bullet list that should become prose. "
                f"Expand it into {self.variants} different written versions that fit the document."
            )
            task = task_sv if lk == "sv" else task_en

        elif self.mode == "angle":
            task_sv = (
                f"Uppgift: föreslå {self.variants} olika riktningar texten kan ta härnäst. "
                "Varje förslag är ett kort stycke som visar hur just den riktningen låter — "
                "inte en beskrivning av riktningen."
            )
            task_en = (
                f"Task: propose {self.variants} different directions the text could take next. "
                "Each option is a short paragraph demonstrating how that direction actually "
                "reads — not a description of it."
            )
            task = task_sv if lk == "sv" else task_en

        else:  # unstick
            want_variants = False
            task_sv = (
                "Uppgift: skribenten körde fast. Ställ 4–6 konkreta frågor som skulle låsa upp "
                "texten. Frågorna ska utgå från vad som redan står — inte allmänna skrivråd. "
                "Returnera en numrerad lista, inget annat."
            )
            task_en = (
                "Task: the writer is stuck. Ask 4–6 concrete questions that would unblock the "
                "text. Base them on what is already written — not generic writing advice. "
                "Return a numbered list, nothing else."
            )
            task = task_sv if lk == "sv" else task_en

        if self.instruction:
            task += (f"\n\nAnvändarens egen instruktion (följ den): {self.instruction}"
                     if lk == "sv" else
                     f"\n\nThe user's own instruction (follow it): {self.instruction}")

        if want_variants:
            base += (
                task + "\n\n" + rules + "\n\n"
                f"Return ONLY valid JSON: {{\"variants\": [\"...\", \"...\"]}} with exactly "
                f"{self.variants} strings. No markdown fences."
            )
        else:
            base += task + "\n\n" + rules + "\n\nReturn only the list, no preamble."

        user = ""
        if ref:
            user += ("--- Referenstext att matcha i stil ---\n" + ref + "\n\n" if lk == "sv"
                     else "--- Reference text to match in style ---\n" + ref + "\n\n")
        if self.mode == "expand":
            user += ("--- Idé/utkast att skriva ut ---\n" + (self.instruction or tail)
                     if lk == "sv" else
                     "--- Idea/draft to expand ---\n" + (self.instruction or tail))
        else:
            user += ("--- Dokumentet hittills (slutet av det) ---\n" + tail if lk == "sv"
                     else "--- Document so far (its end) ---\n" + tail)

        return base, user, want_variants

    @staticmethod
    def _parse_variants(raw: str, want_variants: int) -> list:
        """Plockar ut varianter ur modellsvaret, med fallback om JSON uteblir."""
        text = (raw or "").strip()

        try:
            data = parse_json_response(text)
            if isinstance(data, dict):
                vals = data.get("variants") or data.get("options")
                if isinstance(vals, list):
                    out = [str(v).strip() for v in vals if str(v).strip()]
                    if out:
                        return out
            if isinstance(data, list):
                out = [str(v).strip() for v in data if str(v).strip()]
                if out:
                    return out
        except Exception:
            pass

        # Fallback: dela på --- eller på numrerade rubriker
        parts = [p.strip() for p in re.split(r"\n\s*---+\s*\n", text) if p.strip()]
        if len(parts) < 2:
            parts = [p.strip() for p in re.split(r"\n(?=\s*\d+[.)]\s)", text) if p.strip()]
        if len(parts) < 2 and want_variants == 1:
            return [text]

        cleaned = []
        for p in parts:
            p = re.sub(r"^\s*\d+[.)]\s*", "", p).strip()
            if p:
                cleaned.append(p)
        return cleaned or [text]
