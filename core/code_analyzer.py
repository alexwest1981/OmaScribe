"""
core/code_analyzer.py — AI som läser koden i dokumentet.

Två uppgifter, i praktiken samma anrop:

  * analysera koden och rapportera problem (buggar, stil, formatering)
  * lämna tillbaka en formaterad version som går att sätta in i dokumentet

Formateringen är det viktiga här: modellen får inte ändra kodens beteende,
bara hur den ser ut. Prompten säger det uttryckligen, och svaret är JSON så
att appen kan visa problemen var för sig i stället för som en textklump.

Promptbygge och svarsfolkning är rena funktioner, så de går att testa utan
nätverk (`python core/code_analyzer.py`).
"""

import json
import re
from PyQt6.QtCore import QThread, pyqtSignal

from core.config import DEFAULT_AI_ENDPOINT, DEFAULT_AI_MODEL

from core.ai_client import chat_completion, parse_json_response
from core import directives

MAX_CODE_CHARS = 24000      # tak innan koden kapas
SEVERITIES = ("error", "warning", "style")


def build_prompt(code: str, lang: str = "", lang_ui: str = "sv",
                 format_only: bool = False, doc_context: str = "") -> tuple:
    """Bygger (system, användare) för kodanalysen."""
    sv = str(lang_ui or "").lower().startswith("sv")
    target = "svenska" if sv else "English"
    detected = lang or directives.detect_language(code) or "okänt"

    if sv:
        sys_prompt = (
            "Du är en erfaren kodgranskare inbyggd i ett ordbehandlingsprogram. "
            f"Svara på {target}.\n"
            f"Koden är skriven i {detected}.\n\n"
            + ("Uppgift: formatera om koden korrekt.\n"
               if format_only else
               "Uppgift: granska koden och formatera om den.\n")
            + "Regler:\n"
            "1. Ändra ALDRIG kodens beteende. Bara indrag, radbrytning, mellanslag, "
            "citattecken och konsekvent stil.\n"
            "2. Följ språkets vedertagna konventioner för indrag och formatering.\n"
            "3. Hitta inte på kod som inte finns där. Är koden redan korrekt formaterad "
            "lämnar du den oförändrad.\n"
            "4. 'formatted' ska innehålla hela koden, komplett och körbar — inte ett utdrag "
            "och inte förklaringar inbäddade i koden.\n"
            "5. 'line' i ett problem är radnumret i den kod du fick, räknat från 1.\n"
            "6. Var konkret. 'Dålig stil' utan förklaring är värdelöst.\n\n"
            "Svara ENDAST med giltig JSON:\n"
            '{"language": "språk", "purpose": "en mening om vad koden gör", '
            '"issues": [{"severity": "error|warning|style", "line": 1, '
            '"message": "vad som är fel", "suggestion": "hur det blir bättre"}], '
            '"formatted": "hela den formaterade koden"}\n'
            "Inga kodstaket runt svaret."
        )
        user = f"Koden ({detected}):\n\n{code}"
        if doc_context:
            user += f"\n\nSammanhang från dokumentet:\n{doc_context[:800]}"
    else:
        sys_prompt = (
            "You are an experienced code reviewer embedded in a word processor. "
            f"Reply in {target}.\n"
            f"The code is written in {detected}.\n\n"
            + ("Task: reformat the code correctly.\n" if format_only else
               "Task: review the code and reformat it.\n")
            + "Rules:\n"
            "1. NEVER change the behaviour of the code. Only indentation, line breaks, "
            "whitespace, quotes and consistent style.\n"
            "2. Follow the language's conventional indentation and formatting.\n"
            "3. Do not invent code that is not there. If it is already correctly formatted, "
            "return it unchanged.\n"
            "4. 'formatted' must contain the complete, runnable code — not an excerpt and no "
            "explanations embedded in the code.\n"
            "5. 'line' in an issue is the line number in the code you received, counting from 1.\n"
            "6. Be specific. 'Bad style' with no explanation is worthless.\n\n"
            "Reply with ONLY valid JSON:\n"
            '{"language": "language", "purpose": "one sentence on what the code does", '
            '"issues": [{"severity": "error|warning|style", "line": 1, '
            '"message": "what is wrong", "suggestion": "how to improve it"}], '
            '"formatted": "the complete formatted code"}\n'
            "No markdown fences around the reply."
        )
        user = f"Code ({detected}):\n\n{code}"
        if doc_context:
            user += f"\n\nContext from the document:\n{doc_context[:800]}"

    return sys_prompt, user


def parse_analysis(raw: str, original_code: str) -> dict:
    """Tolkar modellens svar. Kastar ValueError om inget JSON går att läsa."""
    data = parse_json_response(raw)
    if not isinstance(data, dict):
        raise ValueError("svaret var inte ett JSON-objekt")

    code = data.get("formatted")
    if not isinstance(code, str):
        code = ""
    # Modeller lägger ibland dit staket runt koden i fältet
    code = re.sub(r"^\s*```[A-Za-z0-9_+#.\-]*\s*\n", "", code)
    code = re.sub(r"\n\s*```\s*$", "", code.strip())

    issues = []
    for item in (data.get("issues") or []):
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity", "style")).lower()
        issues.append({
            "severity": sev if sev in SEVERITIES else "style",
            "line": item.get("line") if isinstance(item.get("line"), int) else None,
            "message": str(item.get("message", "")).strip(),
            "suggestion": str(item.get("suggestion", "")).strip(),
        })
    issues.sort(key=lambda i: (SEVERITIES.index(i["severity"]), i["line"] or 0))

    return {
        "language": str(data.get("language", "") or "").strip(),
        "purpose": str(data.get("purpose", "") or "").strip(),
        "issues": issues,
        "formatted": code,
        # Sätts av anroparen men är bra att ha med i jämförelsen
        "changed": code.strip() != (original_code or "").strip(),
        "counts": {
            "error": sum(1 for i in issues if i["severity"] == "error"),
            "warning": sum(1 for i in issues if i["severity"] == "warning"),
            "style": sum(1 for i in issues if i["severity"] == "style"),
        },
    }


class CodeAnalysisWorker(QThread):
    """Kör kodanalysen i bakgrunden."""

    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, config, code: str, lang: str = "", doc_context: str = "",
                 lang_ui: str = "sv", format_only: bool = False):
        super().__init__()
        self.config = config
        self.code = code or ""
        self.lang = lang
        self.doc_context = doc_context
        self.lang_ui = lang_ui
        self.format_only = format_only

    def run(self):
        try:
            code = self.code[:MAX_CODE_CHARS]
            sys_prompt, user_prompt = build_prompt(
                code, self.lang, self.lang_ui, self.format_only, self.doc_context)
            endpoint = self.config.get("ai_endpoint", DEFAULT_AI_ENDPOINT)
            api_key = self.config.get("ai_key", "")
            model = self.config.get("ai_model", DEFAULT_AI_MODEL)
            raw = chat_completion(endpoint, api_key, model, sys_prompt, user_prompt,
                                  timeout=150.0, temperature=0.15)
            self.finished.emit(parse_analysis(raw, code))
        except Exception as e:
            self.failed.emit(str(e))


# ------------------------------------------------------------------ självtest

def _self_test() -> int:
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f"{label}: fick {got!r}, väntade {want!r}")

    code = "def f( x ):\n  return x+1"
    sys_sv, user_sv = build_prompt(code, "python", "sv")
    check("svenska i systemprompt", "Svara på svenska" in sys_sv, True)
    check("språket nämns", "python" in sys_sv.lower(), True)
    check("koden med i anropet", code in user_sv, True)
    check("beteendet får inte ändras", "ALDRIG" in sys_sv, True)

    sys_en, _ = build_prompt(code, "python", "en")
    check("engelska", "Reply in English" in sys_en, True)

    _, user_fmt = build_prompt(code, "", "sv", format_only=True)
    check("språk gissas när det saknas", "python" in user_fmt.lower(), True)

    good = json.dumps({
        "language": "Python", "purpose": "Adderar ett till ett tal.",
        "issues": [
            {"severity": "style", "line": 1, "message": "Mellanslag i parentesen.",
             "suggestion": "Skriv f(x)."},
            {"severity": "error", "line": 2, "message": "Fel indrag.", "suggestion": "Fyra mellanslag."},
        ],
        "formatted": "def f(x):\n    return x + 1",
    })
    res = parse_analysis(good, code)
    check("språk", res["language"], "Python")
    check("antal problem", len(res["issues"]), 2)
    check("allvarligast först", [i["severity"] for i in res["issues"]], ["error", "style"])
    check("räknas per allvarlighetsgrad", res["counts"], {"error": 1, "warning": 0, "style": 1})
    check("koden formaterad", res["formatted"], "def f(x):\n    return x + 1")
    check("markerat som ändrad", res["changed"], True)

    # staket runt koden ska skalas av
    fenced = json.dumps({"language": "python", "purpose": "", "issues": [],
                         "formatted": "```python\nx = 1\n```"})
    check("staket avskalade", parse_analysis(fenced, "x=1")["formatted"], "x = 1")

    # oförändrad kod ska inte flaggas som ändrad
    same = json.dumps({"language": "python", "purpose": "", "issues": [],
                       "formatted": "x = 1", "extra": "ignoreras"})
    check("oförändrad kod", parse_analysis(same, "x = 1")["changed"], False)

    # okänd allvarlighetsgrad och skräp i listan ska inte krascha
    messy = json.dumps({"language": "python", "issues": ["inte ett objekt", {"severity": "katastrof"}],
                        "formatted": "x = 1"})
    parsed = parse_analysis(messy, "x=1")
    check("skräppost filtreras", len(parsed["issues"]), 1)
    check("okänd grad blir style", parsed["issues"][0]["severity"], "style")

    # trasigt svar ska ge ett tydligt fel
    try:
        parse_analysis("Ingen JSON här alls", code)
        failures.append("trasigt svar: borde ha kastat")
    except ValueError:
        pass

    # kodstaket i svaret runt hela objektet
    wrapped = "```json\n" + good + "\n```"
    check("staket runt objektet", parse_analysis(wrapped, code)["language"], "Python")

    if failures:
        print("SJÄLVTEST MISSLYCKADES:")
        for f in failures:
            print("  ✗", f)
        return 1
    print("✓ Alla kodanalystester passerade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
