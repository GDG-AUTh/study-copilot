"""Study Copilot: turn lecture slides (PDF) into a summary, flashcards and a quiz."""
from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

import llm_client
import study_cache

load_dotenv(override=True)  # .env wins over an old key in the shell

# Cloud Run refuses requests above 32 MB.
MAX_MB = 30 if llm_client.ON_CLOUD else 50
MAX_JOBS = 20  # finished jobs are kept in memory, so the page can come back for them


def create_app(client=None, cache_dir: str | Path | None = None, ollama_client=None) -> Flask:
    """Create the Flask app. `client` / `ollama_client` let the tests pass mocked LLM clients."""
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
    cache = Path(cache_dir or os.environ.get("CACHE_DIR", ".cache"))
    state = study_cache.EngineState()
    jobs: dict[str, dict] = {}

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    def read_upload():
        """Return (pdf bytes, engine), or raise ValueError with a message for the user."""
        upload = request.files.get("pdf")
        if upload is None or not upload.filename:
            raise ValueError("Διάλεξε ένα αρχείο PDF.")
        data = upload.read()
        if not data.startswith(b"%PDF"):
            raise ValueError("Το αρχείο δεν είναι PDF.")
        engine = request.form.get("engine", "auto")
        if request.form.get("private") in ("1", "on", "true"):
            engine = "local"
        if engine not in ("auto", "cloud", "local"):
            raise ValueError("Άγνωστη επιλογή μοντέλου.")
        return data, engine

    def run_study(data: bytes, engine: str, on_progress=None) -> dict:
        result = study_cache.study(data, cache, engine=engine, state=state, client=client,
                                   ollama_client=ollama_client, on_progress=on_progress)
        local = result["engine"] == "local"
        backend = f"{llm_client.LOCAL_MODEL}, τοπικά" if local else f"Gemini ({llm_client.MODEL})"
        return result | {"backend": backend}

    @app.post("/api/study")
    def study():
        """Answer when everything is ready. The page uses /api/jobs instead."""
        try:
            data, engine = read_upload()
        except ValueError as exc:
            return error(str(exc), 400)
        try:
            return jsonify(run_study(data, engine))
        except llm_client.LLMError as exc:
            return error(str(exc), 502)

    @app.post("/api/jobs")
    def start_job():
        """Start in the background: closing the page does not lose the work."""
        try:
            data, engine = read_upload()
        except ValueError as exc:
            return error(str(exc), 400)
        job = {"status": "running", "partial": None, "result": None, "error": None,
               "started": time.monotonic(), "seconds": 0}
        job_id = uuid.uuid4().hex

        def work():
            try:
                job["result"] = run_study(data, engine, on_progress=lambda partial: job.update(partial=partial))
                job["status"] = "done"
            except llm_client.LLMError as exc:
                job.update(status="error", error=str(exc))
            except Exception:
                app.logger.exception("Study job failed")
                job.update(status="error", error="Κάτι πήγε στραβά. Δοκίμασε ξανά.")
            job["seconds"] = int(time.monotonic() - job["started"])

        jobs[job_id] = job
        while len(jobs) > MAX_JOBS:
            jobs.pop(next(iter(jobs)))
        threading.Thread(target=work, daemon=True).start()
        return jsonify({"id": job_id}), 202

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id):
        job = jobs.get(job_id)
        if job is None:
            return error("Η εργασία δεν βρέθηκε.", 404)
        seconds = job["seconds"] if job["status"] != "running" else int(time.monotonic() - job["started"])
        return jsonify(job | {"seconds": seconds, "working": state.working})

    @app.get("/api/status")
    def status():
        """What the UI shows about the engines. Makes no paid call."""
        has_key = client is not None or llm_client.gemini_configured()
        return jsonify({
            "gemini": {"has_key": has_key, "down": state.gemini_down(), "problem": state.gemini_problem},
            "local": llm_client.local_status(ollama_client),
            "working": state.working,
            "max_mb": MAX_MB,
        })

    @app.errorhandler(413)
    def too_large(_):
        return error(f"Το αρχείο είναι μεγαλύτερο από {MAX_MB} MB.", 413)

    return app


app = create_app()

if __name__ == "__main__":
    # Port 8000: on macOS port 5000 is often taken by AirPlay.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)), debug=False)
