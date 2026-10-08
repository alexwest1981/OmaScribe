"""core/languages.py — en tabell för allt som är språkberoende utanför språkfilerna.

Språkfilerna (`locales/<kod>.json`) bär texten. Den här filen bär resten: vad
språket heter, vilken kod stavningskontrollen och avstavningen vill ha, vad
AI:et skall kallas i en prompt, och om decimaltecknet är komma.

Koderna är **mätta**, inte gissade:

* `lt` mot LanguageTool (`GET https://api.languagetool.org/v2/languages`):
  finska och isländska finns inte där — `lt: None` är ett svar, inte ett fel.
* `pyphen` mot pyphen.LANGUAGES (85 ordlistor): finska saknas också där.

Ett språk utan `lt` får ingen stavningskontroll; ett utan `pyphen` avstavas inte.
Appen säger det rakt ut i stället för att låtsas.
"""

import json
import os

# native  — språkets namn på sig självt, det som står i väljaren
# english — namnet på engelska (loggar, felsökning)
# lt      — LanguageTool-koden, eller None om språket inte stöds
# pyphen  — pyphens ordbokskod, eller None om det inte finns någon
# ai      — språkets namn i en AI-prompt ("svara på <det här>")
# comma   — decimaltecken: True = komma, False = punkt
# plural  — antal former för räkneord ("one_other" eller "other" för fi/de bland annat)
LANGUAGES = {
    "en": {"native": "English",        "english": "English",             "lt": "en-US", "pyphen": "en_US", "ai": "English",               "comma": False, "plural": "one_other"},
    "sv": {"native": "Svenska",        "english": "Swedish",             "lt": "sv-SE", "pyphen": "sv",    "ai": "Swedish (svenska)",     "comma": True,  "plural": "one_other"},
    "nb": {"native": "Norsk bokmål",   "english": "Norwegian Bokmål",    "lt": "nb",    "pyphen": "nb_NO", "ai": "Norwegian Bokmål",      "comma": True,  "plural": "one_other"},
    "da": {"native": "Dansk",          "english": "Danish",              "lt": "da-DK", "pyphen": "da_DK", "ai": "Danish",                "comma": True,  "plural": "one_other"},
    "fi": {"native": "Suomi",          "english": "Finnish",             "lt": None,    "pyphen": None,    "ai": "Finnish (suomi)",       "comma": True,  "plural": "one_other"},
    "is": {"native": "Íslenska",       "english": "Icelandic",           "lt": None,    "pyphen": "is",    "ai": "Icelandic (íslenska)",  "comma": True,  "plural": "one_other"},
    "de": {"native": "Deutsch",        "english": "German",              "lt": "de-DE", "pyphen": "de_DE", "ai": "German (Deutsch)",      "comma": True,  "plural": "one_other"},
    "fr": {"native": "Français",       "english": "French",              "lt": "fr",    "pyphen": "fr",    "ai": "French (français)",     "comma": True,  "plural": "one_other"},
    "es": {"native": "Español",        "english": "Spanish",             "lt": "es",    "pyphen": "es",    "ai": "Spanish (español)",     "comma": True,  "plural": "one_other"},
    "pt": {"native": "Português",      "english": "Portuguese",          "lt": "pt-PT", "pyphen": "pt_PT", "ai": "Portuguese (português)", "comma": True, "plural": "one_other"},
    "it": {"native": "Italiano",       "english": "Italian",             "lt": "it-IT", "pyphen": "it_IT", "ai": "Italian (italiano)",    "comma": True,  "plural": "one_other"},
}

DEFAULT = "en"


def meta(code: str) -> dict:
    """Raden för språket, eller engelskan om koden är okänd."""
    return LANGUAGES.get(_clean(code), LANGUAGES[DEFAULT])


def _clean(code: str) -> str:
    """'sv_SE' och 'sv-SE' är samma språk som 'sv'."""
    return (code or "").replace("-", "_").split("_")[0].lower()


def native(code: str) -> str:
    """Språkets namn på sig självt."""
    return meta(code)["native"]


def english(code: str) -> str:
    return meta(code)["english"]


def ai_name(code: str) -> str:
    """Namnet en AI-prompt skall använda ('Swedish (svenska)')."""
    return meta(code)["ai"]


def lt_code(code: str) -> str | None:
    """LanguageTool-koden, eller None — finska och isländska stöds inte där."""
    return meta(code)["lt"]


def pyphen_code(code: str) -> str | None:
    """pyphens ordbokskod, eller None — finska har ingen ordlista."""
    return meta(code)["pyphen"]


def decimal_comma(code: str) -> bool:
    return meta(code)["comma"]


def known(code: str) -> bool:
    return _clean(code) in LANGUAGES


def next_language(current: str) -> str:
    """Nästa språk i listan över språkfiler — menyvalet går laget runt."""
    koder = sorted(meta(k)["native"] and k for k in _locale_codes())
    if not koder:
        return DEFAULT
    nuv = _clean(current)
    return koder[(koder.index(nuv) + 1) % len(koder)] if nuv in koder else koder[0]


def _locale_codes() -> list[str]:
    """Språkkoderna som faktiskt har en språkfil."""
    try:
        return [os.path.splitext(f)[0] for f in os.listdir(_LOCALES_DIR) if f.endswith(".json")]
    except OSError:
        return []


_LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")


# Stoppordlistorna ligger i resources/stopwords.json: engelska, svenska, norska,
# danska, finska, tyska, franska, spanska, portugisiska och italienska ur
# stopwords-iso (MIT), isländska ur atlijas/icelandic-stop-words (CC BY-SA 4.0,
# sammanställd ur BÍN vid Stofnun Árna Magnússonar). Norskan ligger under "no"
# där, isländskan är den enda som inte finns i stopwords-iso.
_STOPWORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "resources", "stopwords.json")
_stopwords_cache: dict = {}


def stopwords(code: str) -> frozenset:
    """Funktionsorden för språket — tom mängd om listan inte finns.

    Tom är ett svar: analysen hoppar då över stoppordsfiltret i stället för att
    filtrera med ett annat språks ord.
    """
    kod = _clean(code)
    if not _stopwords_cache:
        try:
            with open(_STOPWORDS_PATH, "r", encoding="utf-8") as f:
                _stopwords_cache.update(json.load(f))
        except (OSError, ValueError) as e:
            print(f"[languages] kunde inte läsa stopporden: {e}")
    return frozenset(_stopwords_cache.get(kod, ()))


if __name__ == "__main__":
    # Självkontroll: tabellen, koden och de två verktygen skall hålla ihop.
    assert native("sv") == "Svenska" and native("sv_SE") == "Svenska"
    assert native("de-DE") == "Deutsch" and native("xx") == "English"
    assert lt_code("fi") is None and lt_code("de") == "de-DE"
    assert pyphen_code("fi") is None and pyphen_code("sv") == "sv"
    assert decimal_comma("sv") and not decimal_comma("en")
    try:
        import pyphen
        for kod, rad in LANGUAGES.items():
            if rad["pyphen"]:
                assert pyphen.Pyphen(lang=rad["pyphen"]).inserted("avstavningsexempel")
            if rad["lt"]:
                assert rad["lt"].split("-")[0]
    except ImportError:
        print("pyphen saknas — hoppar över ordbokskontrollen")
    print(f"languages: {len(LANGUAGES)} språk, tabellen stämmer")
