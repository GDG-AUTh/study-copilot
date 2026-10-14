import io

import pytest

import llm_client
from conftest import FakeClient, bad_json


def upload(client, data: bytes, name="lecture.pdf"):
    return client.post("/api/study", data={"pdf": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def test_index_is_served(make_app, fake_client):
    response = make_app(fake_client).get("/")
    assert response.status_code == 200
    assert "Study Copilot" in response.get_data(as_text=True)


def test_study_returns_summary_flashcards_and_quiz(make_app, fake_client, tiny_pdf):
    response = upload(make_app(fake_client), tiny_pdf)
    assert response.status_code == 200
    data = response.get_json()
    assert 6 <= len(data["summary"]) <= 8
    assert len(data["flashcards"]) == 10
    assert len(data["quiz"]) == 5
    assert all(len(q["options"]) == 4 for q in data["quiz"])
    assert data["cached"] is False


def test_pdf_and_prompt_are_sent_to_the_model(make_app, fake_client, tiny_pdf):
    upload(make_app(fake_client), tiny_pdf)
    kwargs = fake_client.models.last_kwargs
    assert kwargs["model"] == llm_client.MODEL
    assert kwargs["config"].response_mime_type == "application/json"
    assert any("study assistant" in str(part) for part in kwargs["contents"])


def test_same_pdf_uses_cache_not_a_second_call(make_app, fake_client, tiny_pdf):
    client = make_app(fake_client)
    upload(client, tiny_pdf)
    second = upload(client, tiny_pdf)
    assert second.get_json()["cached"] is True
    assert fake_client.models.calls == 1


def test_changing_a_prompt_bypasses_the_cache(make_app, fake_client, tiny_pdf, monkeypatch):
    client = make_app(fake_client)
    upload(client, tiny_pdf)
    monkeypatch.setattr(llm_client, "build_prompt", lambda: "a new, stricter quiz prompt")
    second = upload(client, tiny_pdf)
    assert second.get_json()["cached"] is False
    assert fake_client.models.calls == 2


def test_rejects_missing_file(make_app, fake_client):
    response = make_app(fake_client).post("/api/study", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "PDF" in response.get_json()["error"]


def test_rejects_non_pdf(make_app, fake_client):
    response = upload(make_app(fake_client), b"hello", name="notes.txt")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Το αρχείο δεν είναι PDF."
    assert fake_client.models.calls == 0


def test_rejects_too_large_file(make_app, fake_client, tiny_pdf):
    client = make_app(fake_client)
    client.application.config["MAX_CONTENT_LENGTH"] = 100
    response = upload(client, tiny_pdf)
    assert response.status_code == 413


def test_invalid_json_gives_friendly_error(make_app, tiny_pdf):
    response = upload(make_app(FakeClient("this is not json")), tiny_pdf)
    assert response.status_code == 502
    assert "λάθος μορφή" in response.get_json()["error"]


def test_quiz_with_four_questions_is_rejected(make_app, pack_json, tiny_pdf):
    import json
    four = json.loads(pack_json)["quiz"][:4]
    response = upload(make_app(FakeClient(bad_json(quiz=four))), tiny_pdf)
    assert response.status_code == 502
    assert "quiz" in response.get_json()["error"]


def test_missing_api_key_message(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(llm_client.LLMError, match="GEMINI_API_KEY"):
        llm_client._default_client()


def test_quota_error_is_translated(tiny_pdf):
    class QuotaModels:
        def generate_content(self, **kwargs):
            raise RuntimeError("429 RESOURCE_EXHAUSTED")

    class QuotaClient:
        models = QuotaModels()

    with pytest.raises(llm_client.LLMError, match="όριο"):
        llm_client.generate_study_pack(tiny_pdf, client=QuotaClient())
