"""Study Copilot: turn lecture slides (PDF) into a summary, flashcards and a quiz."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

import llm_client

load_dotenv()

MAX_MB = 20


def create_app(client=None, cache_dir: str | Path | None = None) -> Flask:
    """Create the Flask app. `client` lets the tests pass a mocked LLM client."""
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
    cache = Path(cache_dir or os.environ.get("CACHE_DIR", ".cache"))

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.post("/api/study")
    def study():
        upload = request.files.get("pdf")
        if upload is None or not upload.filename:
            return error("Διάλεξε ένα αρχείο PDF.", 400)
        data = upload.read()
        if not data.startswith(b"%PDF"):
            return error("Το αρχείο δεν είναι PDF.", 400)

        # Cache per file, model and prompts: the same PDF never costs a second call,
        # but editing a prompt in prompts/ or switching model gives a fresh answer.
        key = hashlib.sha256(data + llm_client.MODEL.encode() + llm_client.build_prompt().encode()).hexdigest()
        cached = cache / f"{key}.json"
        if cached.exists():
            return jsonify(json.loads(cached.read_text(encoding="utf-8")) | {"cached": True})

        try:
            pack = llm_client.generate_study_pack(data, client=client)
        except llm_client.LLMError as exc:
            return error(str(exc), 502)

        payload = pack.model_dump()
        cache.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return jsonify(payload | {"cached": False})

    @app.errorhandler(413)
    def too_large(_):
        return error(f"Το αρχείο είναι μεγαλύτερο από {MAX_MB} MB.", 413)

    return app


app = create_app()

if __name__ == "__main__":
    # Port 8000: on macOS port 5000 is often taken by AirPlay.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)), debug=False)
