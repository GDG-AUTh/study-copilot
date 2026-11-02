import io
import threading

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
    read, *writes = fake_client.models.all_kwargs
    assert read["model"] == llm_client.NOTES_MODEL
    assert read["config"].response_schema is llm_client.LectureNotes
    assert any("--- Σελίδα 1 ---" in str(part) for part in read["contents"])
    assert {w["config"].response_schema for w in writes} == set(llm_client.PART_SCHEMAS.values())
    for write in writes:
        assert write["model"] == llm_client.MODEL
        assert write["config"].response_mime_type == "application/json"
        assert any("teaching assistant" in str(part) for part in write["contents"])
        assert any("Lecture notes" in str(part) for part in write["contents"])


def test_same_pdf_uses_cache_not_a_second_call(make_app, fake_client, tiny_pdf):
    client = make_app(fake_client)
    upload(client, tiny_pdf)
    second = upload(client, tiny_pdf)
    assert second.get_json()["cached"] is True
    assert fake_client.models.calls == 5  # read + one write per mode, only for the first upload


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
    quiz_calls = [k for k in fake.models.all_kwargs if k["config"].response_schema is llm_client.QuizPart]
    assert len(quiz_calls) == 2  # once more, with feedback
    assert "rejected" in str(quiz_calls[1]["contents"][-1])


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


# Background jobs: the page follows them and shows material as it is ready

def start_job(client, data, **form):
    return client.post("/api/jobs", data={"pdf": (io.BytesIO(data), "lecture.pdf"), **form},
                       content_type="multipart/form-data")


def wait_for(client, job_id):
    for _ in range(500):
        job = client.get(f"/api/jobs/{job_id}").get_json()
        if job["status"] != "running":
            return job
        threading.Event().wait(0.01)  # the tests turn time.sleep off
    raise AssertionError("job did not finish")


def test_job_runs_in_the_background_and_gives_the_result(make_app, fake_client, tiny_pdf):
    client = make_app(fake_client)
    response = start_job(client, tiny_pdf)
    assert response.status_code == 202
    job = wait_for(client, response.get_json()["id"])
    assert job["status"] == "done"
    assert job["result"]["flashcards"] and job["result"]["engine"] == "cloud"
    assert job["partial"]["title"]
    assert job["seconds"] >= 0


def test_job_reports_the_error_for_the_user(make_app, tiny_pdf):
    client = make_app(FakeClient("this is not json", notes="this is not json"))
    job = wait_for(client, start_job(client, tiny_pdf).get_json()["id"])
    assert job["status"] == "error" and "λάθος μορφή" in job["error"]


def test_job_rejects_a_bad_upload_at_once(make_app, fake_client):
    response = start_job(make_app(fake_client), b"hello")
    assert response.status_code == 400
    assert fake_client.models.calls == 0


def test_unknown_job_is_404(make_app, fake_client):
    assert make_app(fake_client).get("/api/jobs/nope").status_code == 404
