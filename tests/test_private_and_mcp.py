import asyncio
import io
from types import SimpleNamespace

import pytest

import llm_client


class FakeOllama:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(message=SimpleNamespace(content=self.content))


def blank_pdf() -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# Private mode (Gemma through Ollama)

def test_private_mode_uses_ollama_with_same_schema(pack_json, tiny_pdf):
    ollama = FakeOllama(pack_json)
    pack = llm_client.generate_study_pack(tiny_pdf, private=True, ollama_client=ollama)
    assert len(pack.quiz) == 5
    call = ollama.calls[0]
    assert call["model"] == llm_client.LOCAL_MODEL
    assert call["format"] == llm_client.StudyPack.model_json_schema()
    assert "--- Σελίδα 1 ---" in call["messages"][0]["content"]


def test_private_mode_never_calls_gemini(tmp_path, pack_json, tiny_pdf, no_network):
    from app import create_app

    class NoGemini:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise AssertionError("Gemini must not be called in private mode")

    app = create_app(client=NoGemini(), ollama_client=FakeOllama(pack_json), cache_dir=tmp_path)
    client = app.test_client()
    response = client.post("/api/study", data={"pdf": (io.BytesIO(tiny_pdf), "l.pdf"), "private": "1"},
                           content_type="multipart/form-data")
    assert response.status_code == 200
    assert llm_client.LOCAL_MODEL in response.get_json()["backend"]


def test_private_mode_accepts_a_smaller_pack_from_a_small_model(pack_json, tiny_pdf):
    import json

    data = json.loads(pack_json)
    data["flashcards"] = data["flashcards"][:3]                      # fewer than 10
    data["quiz"].append({**data["quiz"][0], "options": ["only one"]})  # an invalid extra question
    pack = llm_client.generate_study_pack(tiny_pdf, private=True, ollama_client=FakeOllama(json.dumps(data)))
    assert len(pack.flashcards) == 3
    assert len(pack.quiz) == 5


def test_scanned_pdf_in_private_mode_gives_clear_error():
    with pytest.raises(llm_client.LLMError, match="σκαναρισμένο"):
        llm_client.generate_study_pack(blank_pdf(), private=True, ollama_client=FakeOllama("{}"))


def test_ollama_not_running_message(tiny_pdf):
    ollama = FakeOllama(error=ConnectionError("Failed to connect to Ollama"))
    with pytest.raises(llm_client.LLMError, match="Ollama"):
        llm_client.generate_study_pack(tiny_pdf, private=True, ollama_client=ollama)


def test_model_not_pulled_message(tiny_pdf):
    ollama = FakeOllama(error=RuntimeError("model 'gemma3:1b' not found, try pulling it first"))
    with pytest.raises(llm_client.LLMError, match="ollama pull"):
        llm_client.generate_study_pack(tiny_pdf, private=True, ollama_client=ollama)


def test_cloud_and_local_are_cached_separately(tmp_path, fake_client, pack_json, tiny_pdf, no_network):
    import study_cache

    ollama = FakeOllama(pack_json)
    study_cache.get_or_create(tiny_pdf, tmp_path, client=fake_client)
    _, cached = study_cache.get_or_create(tiny_pdf, tmp_path, private=True, ollama_client=ollama)
    assert cached is False
    _, cached = study_cache.get_or_create(tiny_pdf, tmp_path, private=True, ollama_client=ollama)
    assert cached is True
    assert len(ollama.calls) == 1


def test_changing_a_prompt_or_model_bypasses_the_cache(tmp_path, fake_client, tiny_pdf, no_network, monkeypatch):
    import study_cache

    study_cache.get_or_create(tiny_pdf, tmp_path, client=fake_client)
    monkeypatch.setattr(llm_client, "build_prompt", lambda pages=10: "a new, stricter quiz prompt")
    _, cached = study_cache.get_or_create(tiny_pdf, tmp_path, client=fake_client)
    assert cached is False
    monkeypatch.setattr(llm_client, "MODEL", "another-model")
    _, cached = study_cache.get_or_create(tiny_pdf, tmp_path, client=fake_client)
    assert cached is False
    assert fake_client.models.calls == 6  # read + write, three times


# MCP server

def test_mcp_server_exposes_three_tools():
    import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == ["make_flashcards", "make_quiz", "summarize_lecture"]
    assert all(t.description and len(t.description) > 40 for t in tools)


def test_mcp_make_quiz_returns_questions(monkeypatch, tmp_path, fake_client):
    import mcp_server

    monkeypatch.setattr(mcp_server, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(llm_client, "_default_client", lambda: fake_client)
    pdf = mcp_server.ROOT / "tests" / "fixtures" / "tiny.pdf"
    result = mcp_server.make_quiz(str(pdf), questions=2)
    assert len(result["quiz"]) == 2


def test_mcp_missing_file_is_a_clear_error():
    import mcp_server

    with pytest.raises(ValueError, match="not found"):
        mcp_server.make_quiz("/no/such/lecture.pdf")
