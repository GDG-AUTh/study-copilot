"""Cache per file, backend, model and prompts.

The same PDF never costs a second model call, but editing a prompt in prompts/
or switching model (GEMINI_MODEL, LOCAL_MODEL) gives a fresh answer.
Failed answers are never cached.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import llm_client


def get_or_create(pdf_bytes: bytes, cache_dir: Path, private: bool = False,
                  client=None, ollama_client=None) -> tuple[dict, bool]:
    """Return (study pack as dict, came_from_cache)."""
    backend = "local" if private else "cloud"
    model = llm_client.LOCAL_MODEL if private else llm_client.MODEL
    key = hashlib.sha256(pdf_bytes + model.encode() + llm_client.prompts_fingerprint().encode()).hexdigest()
    path = Path(cache_dir) / f"{key}-{backend}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), True
    pack = llm_client.generate_study_pack(pdf_bytes, client=client, private=private,
                                          ollama_client=ollama_client)
    payload = pack.model_dump()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload, False
