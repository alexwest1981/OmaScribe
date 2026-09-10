import json
import httpx
from PyQt6.QtCore import QObject, QThread, pyqtSignal


def chat_completion(endpoint, api_key, model, system_prompt, user_prompt,
                    timeout=30.0, temperature=0.3):
    """Synkront anrop mot en OpenAI-kompatibel /chat/completions.

    Kastar httpx.HTTPStatusError vid felstatus och httpx.HTTPError vid
    nätverksfel. Används av AIWorker och av research-/ghostwriter-arbetarna
    så att all HTTP-logik bor på ett ställe.
    """
    url = f"{endpoint.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def parse_json_response(raw: str) -> dict:
    """Tolerant tolkning av ett JSON-svar från en modell.

    Hanterar ```json-staket, inledande prosa och efterföljande text genom att
    plocka ut det första kompletta {...}-objektet.
    """
    text = (raw or "").strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("inget JSON-objekt hittades i svaret")


class AIWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, endpoint, api_key, model, system_prompt, user_prompt):
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def run(self):
        try:
            content = chat_completion(
                self.endpoint, self.api_key, self.model,
                self.system_prompt, self.user_prompt
            )
            self.finished.emit({"success": True, "content": content})
        except httpx.HTTPStatusError as e:
            self.error.emit(f"AI API Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            self.error.emit(f"Connection failed: {str(e)}")


class AIClient(QObject):
    review_completed = pyqtSignal(dict)
    review_error = pyqtSignal(str)
    transform_completed = pyqtSignal(str)
    ai_status_changed = pyqtSignal(str)

    def __init__(self, config_mgr):
        super().__init__()
        self.config = config_mgr
        self._active_workers = set()
        self._review_worker = None

    def review_document(self, text, lang="en"):
        if not text or len(text.strip()) < 10:
            return

        # Abort previous review worker if still running
        if self._review_worker is not None and self._review_worker.isRunning():
            self._review_worker.terminate()
            self._review_worker.wait()

        self.ai_status_changed.emit("analyzing")

        lang_desc = "Swedish (Svenska)" if lang in ("sv", "svenska", "swedish") else "English"
        lang_note = "Respond in Swedish for the summary, tone, and suggestions' explanations." if lang in ("sv", "svenska", "swedish") else "Respond in English for the summary, tone, and suggestions' explanations."

        sys_prompt = f"""You are an elite, professional editor and writing coach.
Analyze the following document written in {lang_desc}. {lang_note}
Respond ONLY with a valid JSON object matching this schema:
{{
  "readability_score": 88,
  "tone": "Professional & Engaging",
  "summary": "Brief 1-2 sentence overview of the document",
  "suggestions": [
    {{
      "type": "grammar" | "clarity" | "style" | "tone",
      "original": "exact substring from text",
      "replacement": "improved phrasing",
      "explanation": "why this improves the text"
    }}
  ]
}}
Do NOT wrap with markdown fences. Return raw JSON.
"""

        endpoint = self.config.get("ai_endpoint", "http://localhost:8000/v1")
        api_key = self.config.get("ai_key", "")
        model = self.config.get("ai_model", "claude-3-5-sonnet")

        worker = AIWorker(endpoint, api_key, model, sys_prompt, text)
        self._review_worker = worker
        self._active_workers.add(worker)

        worker.finished.connect(lambda res, w=worker: self._on_review_finished(res, w))
        worker.error.connect(lambda err, w=worker: self._on_review_error(err, w))
        worker.start()

    def _on_review_finished(self, res, worker):
        self._active_workers.discard(worker)
        if self._review_worker == worker:
            self._review_worker = None

        self.ai_status_changed.emit("ready")
        raw = res.get("content", "")
        # Clean JSON if fenced
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw.strip())
            self.review_completed.emit(data)
        except Exception as e:
            print(f"[AIClient] JSON parse error: {e}, raw was: {raw[:100]}")
            self.review_error.emit(f"AI response format error: {e}")

    def _on_review_error(self, err_msg, worker):
        self._active_workers.discard(worker)
        if self._review_worker == worker:
            self._review_worker = None

        self.ai_status_changed.emit("ready")
        print(f"[AIClient] {err_msg}")
        self.review_error.emit(err_msg)

    def transform_text(self, selected_text, instruction, context_before="", context_after=""):
        self.ai_status_changed.emit("analyzing")
        sys_prompt = "You are a precise writing assistant. Follow the user's instruction to rewrite or generate text. Return ONLY the replacement text without any conversational preamble or markdown codeblocks unless specifically requested."
        
        user_prompt = f"""Context before: {context_before[-200:]}
Target text to transform: {selected_text}
Context after: {context_after[:200]}

Instruction: {instruction}
"""
        endpoint = self.config.get("ai_endpoint", "http://localhost:8000/v1")
        api_key = self.config.get("ai_key", "")
        model = self.config.get("ai_model", "claude-3-5-sonnet")

        worker = AIWorker(endpoint, api_key, model, sys_prompt, user_prompt)
        self._active_workers.add(worker)

        worker.finished.connect(lambda res, w=worker: self._on_transform_done(res.get("content", ""), w))
        worker.error.connect(lambda err, w=worker: self._on_transform_done(f"[Error: {err}]", w))
        worker.start()

    def _on_transform_done(self, content, worker):
        self._active_workers.discard(worker)
        self.ai_status_changed.emit("ready")
        self.transform_completed.emit(content.strip())
