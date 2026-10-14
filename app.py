"""Study Copilot: turn lecture slides (PDF) into a summary, flashcards and a quiz."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

import llm_client
import study_cache

load_dotenv()

MAX_MB = 20


def create_app(client=None, cache_dir: str | Path | None = None, ollama_client=None) -> Flask:
    """Create the Flask app. `client` / `ollama_client` let the tests pass mocked LLM clients."""
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

        private = request.form.get("private") in ("1", "on", "true")
        try:
            payload, cached = study_cache.get_or_create(
                data, cache, private=private, client=client, ollama_client=ollama_client)
        except llm_client.LLMError as exc:
            return error(str(exc), 502)
        backend = f"Gemma ({llm_client.LOCAL_MODEL}, τοπικά)" if private else "Gemini"
        return jsonify(payload | {"cached": cached, "backend": backend})

    @app.errorhandler(413)
    def too_large(_):
        return error(f"Το αρχείο είναι μεγαλύτερο από {MAX_MB} MB.", 413)

    return app


app = create_app()

if __name__ == "__main__":
    # Port 8000: on macOS port 5000 is often taken by AirPlay.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)), debug=False)
