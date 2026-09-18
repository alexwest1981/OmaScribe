"""
core/research.py — "hämta information": slår upp fakta och drar in dem i dokumentet.

Tre lägen, alla körbara utan betald API-nyckel:

  * url    — hämta en eller flera sidor och sammanfatta dem med källhänvisning
  * search — sök via en egen SearXNG-instans (JSON-API, ingen nyckel behövs)
  * ask    — fråga modellen ur dess egen kunskap (utan källor — flaggas tydligt)

Allt nätverkande sker i en QThread. Modellanropet går via chat_completion i
core.ai_client så att endpoint/nyckel/modell styrs av samma inställningar som
resten av appen.
"""

from __future__ import annotations

import html as html_mod
import re
import httpx
from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_client import chat_completion
from core.config import DEFAULT_AI_ENDPOINT, DEFAULT_AI_MODEL

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) OmaScribe/1.0 Safari/537.36"
)

MAX_PAGE_CHARS = 12000      # per sida, innan texten skickas till modellen
MAX_TOTAL_CHARS = 40000     # tak för hela källpaketet
_URL_RE = re.compile(r"^https?://", re.I)
_BARE_DOMAIN_RE = re.compile(r"^[\w\-]+(\.[\w\-]+)+(/\S*)?$")


# ------------------------------------------------------------------ småhjälpare

def looks_like_url(text: str) -> bool:
    """True om texten är en URL eller ett bart domännamn."""
    t = (text or "").strip()
    return bool(_URL_RE.match(t) or (_BARE_DOMAIN_RE.match(t) and " " not in t))


def normalize_url(url: str) -> str:
    """Lägger på https:// om användaren skrev ett bart domännamn."""
    u = (url or "").strip()
    if not u:
        return u
    if not _URL_RE.match(u):
        u = "https://" + u
    return u


def sources_markdown(sources: list) -> str:
    """Bygger en källförteckning i Markdown från [(titel, url)]."""
    if not sources:
        return ""
    lines = ["", "**Källor**", ""]
    for i, s in enumerate(sources, 1):
        title = (s.get("title") or s.get("url") or "").strip()
        url = (s.get("url") or "").strip()
        lines.append(f"{i}. [{title}]({url})" if url else f"{i}. {title}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ HTML → text

def html_to_text(raw: str) -> tuple:
    """Grov men robust textextraktion ur HTML. Returnerar (titel, text)."""
    if not raw:
        return "", ""

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if m:
        title = html_mod.unescape(re.sub(r"\s+", " ", m.group(1))).strip()

    text = raw
    # Ta bort innehåll som aldrig är brödtext
    for tag in ("script", "style", "noscript", "svg", "head", "nav",
                "footer", "header", "form", "iframe", "template"):
        text = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)

    # Blockelement blir radbrytningar
    text = re.sub(r"<(br|hr)\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|section|article|li|tr|h[1-6]|blockquote|pre)\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<li\b[^>]*>", "\n• ", text, flags=re.I)

    # Bort med resten av taggarna
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)

    # Städa blanksteg men behåll styckeindelning
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, text.strip()


def fetch_page(url: str, timeout: float = 20.0) -> dict:
    """Hämtar en sida och returnerar {url, title, text, truncated}. Kastar vid fel."""
    target = normalize_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "sv,en;q=0.8"}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        resp = client.get(target)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "pdf" in ctype.lower():
            raise ValueError("PDF stöds inte ännu — klistra in texten i stället.")
        title, text = html_to_text(resp.text)

    truncated = False
    if len(text) > MAX_PAGE_CHARS:
        text = text[:MAX_PAGE_CHARS]
        truncated = True

    return {
        "url": str(resp.url),
        "title": title or str(resp.url),
        "text": text,
        "truncated": truncated,
    }


def search_searxng(base_url: str, query: str, limit: int = 5, timeout: float = 15.0) -> list:
    """Söker via en SearXNG-instans med JSON-utdata aktiverat."""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        raise ValueError("Ingen SearXNG-adress konfigurerad.")
    params = {"q": query, "format": "json", "language": "sv-SE", "safesearch": "0"}
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        resp = client.get(f"{base}/search", params=params)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            raise ValueError(
                "SearXNG svarade inte med JSON. Lägg till 'json' under "
                "search.formats i din settings.yml och starta om instansen."
            )
    out = []
    for r in (data.get("results") or [])[:limit]:
        out.append({
            "title": r.get("title") or r.get("url", ""),
            "url": r.get("url", ""),
            "snippet": (r.get("content") or "").strip(),
        })
    return out


# ------------------------------------------------------------------- arbetaren

class ResearchWorker(QThread):
    """Hämtar underlag och låter modellen sammanställa det."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)   # {text, sources, query, mode, warnings}
    failed = pyqtSignal(str)

    def __init__(self, config, query: str, mode: str = "ask", urls=None,
                 document_context: str = "", lang: str = "en"):
        super().__init__()
        self.config = config
        self.query = (query or "").strip()
        self.mode = mode
        self.urls = list(urls or [])
        self.document_context = document_context or ""
        self.lang = lang

    # -- anropas i tråden ---------------------------------------------------

    def run(self):
        try:
            sources, warnings = self._gather()
            text = self._synthesize(sources, warnings)
            self.finished.emit({
                "text": text,
                "sources": sources,
                "query": self.query,
                "mode": self.mode,
                "warnings": warnings,
            })
        except Exception as e:
            self.failed.emit(str(e))

    def _gather(self) -> tuple:
        """Samlar in källmaterial beroende på läge. Returnerar (sources, warnings)."""
        sources, warnings = [], []

        if self.mode == "url":
            for u in self.urls:
                if len(sources) >= 4:
                    break
                self.progress.emit(u)
                try:
                    page = fetch_page(u)
                    sources.append(page)
                except Exception as e:
                    warnings.append(f"{u}: {e}")

        elif self.mode == "search":
            base = self.config.get("research_searxng_url", "")
            self.progress.emit(self.query)
            try:
                hits = search_searxng(base, self.query, limit=5)
            except Exception as e:
                raise ValueError(f"Sökningen misslyckades: {e}")
            if not hits:
                warnings.append("Sökningen gav inga träffar.")
            # Hämta de två första träffarnas sidor för faktiskt innehåll
            for hit in hits[:2]:
                try:
                    page = fetch_page(hit["url"])
                    page["snippet"] = hit.get("snippet", "")
                    sources.append(page)
                except Exception as e:
                    warnings.append(f"{hit['url']}: {e}")
            # Resterande träffar behålls som rena sökresultat
            fetched = {s["url"] for s in sources}
            for hit in hits:
                if hit["url"] not in fetched:
                    sources.append({
                        "url": hit["url"],
                        "title": hit["title"],
                        "text": hit.get("snippet", ""),
                        "snippet_only": True,
                    })

        return sources, warnings

    def _synthesize(self, sources: list, warnings: list) -> str:
        """Låter modellen skriva texten utifrån källmaterialet."""
        lang = "Swedish (svenska)" if str(self.lang).startswith("sv") else "English"

        endpoint = self.config.get("ai_endpoint", DEFAULT_AI_ENDPOINT)
        api_key = self.config.get("ai_key", "")
        model = self.config.get("ai_model", DEFAULT_AI_MODEL)

        if not sources:
            # Ren kunskapsfråga — modellen svarar utan underlag
            sys_prompt = (
                "Du är en researchassistent inbyggd i ett ordbehandlingsprogram. "
                f"Svara på {lang}. Skriv sammanhängande prosa som kan klistras in i ett dokument.\n"
                "VIKTIGT: Du har inga externa källor. Var tydlig och ärlig med vilket som är "
                "allmän kunskap och var du är osäker. Hitta inte på specifika siffror, datum, "
                "citat eller studieresultat. Ingen inledning, ingen avslutande kommentar — "
                "bara själva innehållet, formaterat i Markdown med en rubrik om det passar."
            )
            user_prompt = self.query
            if self.document_context:
                user_prompt += ("\n\n--- Dokumentet användaren arbetar i "
                                "(för sammanhang och ton) ---\n" + self.document_context)
            self.progress.emit(self.query)
            out = chat_completion(endpoint, api_key, model, sys_prompt, user_prompt,
                                  timeout=90.0, temperature=0.3)
            return self._strip_fences(out)

        # Med källor: numrera dem och kräv citering
        blocks, used = [], 0
        for i, s in enumerate(sources, 1):
            body = s.get("text", "")
            if used + len(body) > MAX_TOTAL_CHARS:
                body = body[:max(0, MAX_TOTAL_CHARS - used)]
            used += len(body)
            label = "utdrag från sökresultat" if s.get("snippet_only") else s.get("url", "")
            blocks.append(f"[{i}] {s.get('title', '')} — {label}\n---\n{body}\n---")
        source_block = "\n\n".join(blocks)

        sys_prompt = (
            "Du är en researchassistent inbyggd i ett ordbehandlingsprogram. "
            f"Skriv på {lang}.\n"
            "Uppgift: sammanställ en sammanhängande text utifrån de numrerade källorna nedan.\n"
            "Regler:\n"
            "1. Referera till källorna med [1], [2] osv. direkt efter de påståenden de stöder.\n"
            "2. Använd INGENTING som inte står i källorna. Om underlaget är tunt eller motsägelsefullt, "
            "säg det rakt ut i stället för att fylla ut.\n"
            "3. Hitta inte på siffror, datum eller citat.\n"
            "4. Markdown, sammanhängande prosa. Ingen inledning som \"Här är en sammanfattning\", "
            "ingen avslutande kommentar om vad du gjort."
        )
        user_prompt = f"Fråga/ämne: {self.query}\n\n"
        if self.document_context:
            user_prompt += f"Sammanhang från dokumentet:\n{self.document_context}\n\n"
        user_prompt += f"Källor:\n\n{source_block}"

        self.progress.emit(self.query)
        out = chat_completion(endpoint, api_key, model, sys_prompt, user_prompt,
                              timeout=120.0, temperature=0.3)
        return self._strip_fences(out)

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Tar bort eventuella kodstaket runt hela svaret."""
        t = (text or "").strip()
        if t.startswith("```"):
            parts = t.split("```")
            if len(parts) >= 2:
                t = parts[1]
                if t.startswith(("markdown", "md")):
                    t = t.split("\n", 1)[-1]
        return t.strip()
