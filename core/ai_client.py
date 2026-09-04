import json
import httpx
from PyQt6.QtCore import QObject, QThread, pyqtSignal

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
        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ],
            "temperature": 0.3
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    self.finished.emit({"success": True, "content": content})
                else:
                    self.error.emit(f"AI API Error {resp.status_code}: {resp.text}")
        except Exception as e:
            self.error.emit(f"Connection failed: {str(e)}")


class AIClient(QObject):
    review_completed = pyqtSignal(dict)
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

        sys_prompt = f"""You are an elite, professional editor and writing coach.
Analyze the following document written in {lang}.
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

    def _on_review_error(self, err_msg, worker):
        self._active_workers.discard(worker)
        if self._review_worker == worker:
            self._review_worker = None

        self.ai_status_changed.emit("ready")
        print(f"[AIClient] {err_msg}")

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
