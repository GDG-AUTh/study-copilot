"""Cache per file, backend, model and prompts, plus the choice of engine.

The same PDF never costs a second model call, but editing a prompt in prompts/
or switching model (GEMINI_MODEL, LOCAL_MODEL) gives a fresh answer.
Failed answers are never cached.

Engines: "cloud" (Gemini), "local" (Ollama) or "auto": Gemini first, and the local
model when Gemini cannot answer, so a problem with the key never stops the student.
The fallback only goes from cloud to local, never the other way: a PDF the user asked
to keep on this computer is never sent anywhere.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import llm_client

# After Gemini fails, go straight to the local model for this long (seconds).
GEMINI_COOLDOWN = 300


@dataclass
class EngineState:
    """What we learned about the engines while running. Shown by the UI."""

    gemini_problem: str = ""
    gemini_down_until: float = 0
    working: str | None = None  # engine that is generating right now

    def gemini_down(self) -> bool:
        return time.monotonic() < self.gemini_down_until

    def mark_gemini_down(self, problem: str) -> None:
        self.gemini_problem = problem
        self.gemini_down_until = time.monotonic() + GEMINI_COOLDOWN

    def mark_gemini_ok(self) -> None:
        self.gemini_problem = ""
        self.gemini_down_until = 0


def _path(pdf_bytes: bytes, cache_dir: Path, private: bool) -> Path:
    backend = "local" if private else "cloud"
    model = llm_client.LOCAL_MODEL if private else llm_client.MODEL
    key = hashlib.sha256(pdf_bytes + model.encode() + llm_client.prompts_fingerprint().encode()).hexdigest()
    return Path(cache_dir) / f"{key}-{backend}.json"


def get_or_create(pdf_bytes: bytes, cache_dir: Path, private: bool = False,
                  client=None, ollama_client=None, on_progress=None) -> tuple[dict, bool]:
    """Return (study pack as dict, came_from_cache)."""
    path = _path(pdf_bytes, cache_dir, private)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), True
    pack = llm_client.generate_study_pack(pdf_bytes, client=client, private=private,
                                          ollama_client=ollama_client, on_progress=on_progress)
    payload = pack.model_dump()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload, False


def study(pdf_bytes: bytes, cache_dir: Path, engine: str = "auto", state: EngineState | None = None,
          client=None, ollama_client=None, on_progress=None) -> dict:
    """Run the chosen engine. Returns the pack plus cached, engine and notice."""
    state = state or EngineState()

    def run(private: bool) -> tuple[dict, bool]:
        state.working = "local" if private else "cloud"
        try:
            return get_or_create(pdf_bytes, cache_dir, private=private, client=client,
                                 ollama_client=ollama_client, on_progress=on_progress)
        finally:
            state.working = None

    def done(payload: dict, cached: bool, used: str, notice: str = "") -> dict:
        return payload | {"cached": cached, "engine": used, "notice": notice}

    if engine == "local":
        if llm_client.ON_CLOUD:
            raise llm_client.LLMError("Το τοπικό μοντέλο δουλεύει μόνο όταν τρέχεις την εφαρμογή στον υπολογιστή σου.")
        return done(*run(True), "local")

    has_cloud_answer = _path(pdf_bytes, cache_dir, False).exists()
    if engine == "cloud" or has_cloud_answer or not state.gemini_down():
        try:
            payload, cached = run(False)
            if not cached:
                state.mark_gemini_ok()
            return done(payload, cached, "cloud")
        except llm_client.GeminiUnavailable as exc:
            state.mark_gemini_down(str(exc))
            if engine == "cloud" or llm_client.ON_CLOUD:
                raise

    problem = state.gemini_problem
    if llm_client.ON_CLOUD:  # Gemini was skipped because it failed a moment ago, and nothing else is here
        raise llm_client.GeminiUnavailable(problem)
    try:
        payload, cached = run(True)
    except llm_client.LLMError as exc:
        raise llm_client.LLMError(f"{problem} Ούτε το τοπικό μοντέλο μπόρεσε να απαντήσει: {exc}") from exc
    return done(payload, cached, "local", problem)
