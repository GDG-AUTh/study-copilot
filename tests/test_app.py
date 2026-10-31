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


def test_slides_are_read_first_then_material_is_written(make_app, fake_client, tiny_pdf):
    upload(make_app(fake_client), tiny_pdf)
    read, write = fake_client.models.all_kwargs
    for kwargs in (read, write):
        assert kwargs["model"] == llm_client.MODEL
        assert kwargs["config"].response_mime_type == "application/json"
    assert read["config"].response_schema is llm_client.LectureNotes
    assert any("--- Σελίδα 1 ---" in str(part) for part in read["contents"])
    assert write["config"].response_schema is llm_client.StudyPack
    assert any("teaching assistant" in str(part) for part in write["contents"])
    assert any("Lecture notes" in str(part) for part in write["contents"])


def test_same_pdf_uses_cache_not_a_second_call(make_app, fake_client, tiny_pdf):
    client = make_app(fake_client)
    upload(client, tiny_pdf)
    second = upload(client, tiny_pdf)
    assert second.get_json()["cached"] is True
    assert fake_client.models.calls == 2  # read + write, only for the first upload


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


def test_too_few_quiz_questions_asks_again_then_fails(make_app, pack_json, tiny_pdf):
    import json
    two = json.loads(pack_json)["quiz"][:2]
    fake = FakeClient(bad_json(quiz=two))
    response = upload(make_app(fake), tiny_pdf)
    assert response.status_code == 502
    assert "quiz" in response.get_json()["error"]
    assert fake.models.calls == 3  # read + write + one more write with feedback
    assert "rejected" in str(fake.models.last_kwargs["contents"][-1])


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
