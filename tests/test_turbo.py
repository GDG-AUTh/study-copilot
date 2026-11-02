"""The turbo pipeline: Gemini error handling, retries, fallback models and cleaning the answer."""
import io
import json
from types import SimpleNamespace

import pytest

import llm_client
from conftest import FIXTURES, FakeClient, bad_json

LECTURE1 = FIXTURES.parent.parent / "sample_lectures" / "lecture1.pdf"


class ScriptedModels:
    """Raises the given errors in order, then answers like FakeModels."""

    def __init__(self, errors, pack_json):
        self.errors = list(errors)
        self.fake = FakeClient(pack_json).models
        self.models_used = []

    def generate_content(self, **kwargs):
        self.models_used.append(kwargs["model"])
        if self.errors:
            raise self.errors.pop(0)
        return self.fake.generate_content(**kwargs)


def scripted(errors, pack_json):
    return SimpleNamespace(models=ScriptedModels(errors, pack_json))


class APIError(Exception):
    """Looks like google.genai.errors.APIError: has a numeric `code`."""

    def __init__(self, code, message):
        super().__init__(f"{code} {message}")
        self.code = code


# Gemini errors

def test_depleted_credits_402_has_its_own_message(tiny_pdf, pack_json):
    client = scripted([APIError(402, "RESOURCE_EXHAUSTED. Your prepayment credits are depleted.")], pack_json)
    with pytest.raises(llm_client.LLMError, match="credits"):
        llm_client.generate_study_pack(tiny_pdf, client=client)
    assert len(client.models.models_used) == 1  # no pointless retries


def test_rate_limit_is_retried_then_succeeds(tiny_pdf, pack_json):
    client = scripted([APIError(429, "RESOURCE_EXHAUSTED retryDelay: '3s'")] * 2, pack_json)
    result = llm_client.generate_study_pack(tiny_pdf, client=client)
    assert result.quiz
    assert len(client.models.models_used) == 4  # 2 failures + read + write


def test_overloaded_server_is_retried(tiny_pdf, pack_json):
    client = scripted([APIError(503, "UNAVAILABLE. The model is overloaded.")], pack_json)
    assert llm_client.generate_study_pack(tiny_pdf, client=client).flashcards


def test_daily_quota_stops_with_clear_message(tiny_pdf, pack_json):
    error = APIError(429, "RESOURCE_EXHAUSTED quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    with pytest.raises(llm_client.LLMError, match="ημερήσιο"):
        llm_client.generate_study_pack(tiny_pdf, client=scripted([error], pack_json))


def test_retired_model_falls_back_to_the_next_one(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "MODEL", "gemini-old")
    monkeypatch.setattr(llm_client, "FALLBACK_MODELS", ["gemini-new"])
    client = scripted([APIError(404, "models/gemini-old is no longer available")], pack_json)
    llm_client.generate_study_pack(tiny_pdf, client=client)
    assert client.models.models_used[:2] == ["gemini-old", "gemini-new"]


def test_no_model_available_says_which_env_var_to_change(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "FALLBACK_MODELS", [])
    client = scripted([APIError(404, "NOT_FOUND")], pack_json)
    with pytest.raises(llm_client.LLMError, match="GEMINI_MODEL"):
        llm_client.generate_study_pack(tiny_pdf, client=client)


def test_rate_limit_that_never_ends_gives_friendly_error(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "FALLBACK_MODELS", [])
    client = scripted([APIError(429, "RESOURCE_EXHAUSTED")] * 10, pack_json)
    with pytest.raises(llm_client.LLMError, match="ανά λεπτό"):
        llm_client.generate_study_pack(tiny_pdf, client=client)


def test_invalid_key_message(tiny_pdf, pack_json):
    client = scripted([APIError(400, "INVALID_ARGUMENT. API key not valid.")], pack_json)
    with pytest.raises(llm_client.LLMError, match="κλειδί"):
        llm_client.generate_study_pack(tiny_pdf, client=client)


def test_answer_wrapped_in_code_fences_is_accepted(tiny_pdf, pack_json):
    client = FakeClient(f"```json\n{pack_json}\n```")
    assert llm_client.generate_study_pack(tiny_pdf, client=client).quiz


def test_large_pdf_goes_through_the_files_api(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "INLINE_PDF_LIMIT", 10)
    uploaded = SimpleNamespace(name="files/abc", state="ACTIVE")
    files = SimpleNamespace(upload=lambda **kw: uploaded, get=lambda **kw: uploaded,
                            delete=lambda **kw: deleted.append(kw["name"]))
    deleted = []
    client = FakeClient(pack_json)
    client.files = files
    llm_client.generate_study_pack(tiny_pdf, client=client)
    assert client.models.all_kwargs[0]["contents"][0] is uploaded
    assert deleted == ["files/abc"]


# Cleaning the answer

def lecture1_texts():
    return llm_client.page_texts(LECTURE1.read_bytes())


def test_quiz_quotes_are_checked_against_the_lecture(pack_json):
    result = llm_client.parse_study_pack(pack_json, lecture1_texts())
    assert all(q.verified for q in result.quiz)


def test_made_up_quote_is_not_verified_and_goes_last(pack_json):
    quiz = json.loads(pack_json)["quiz"]
    quiz[0]["source_quote"] = "Ο bogosort είναι ο ταχύτερος αλγόριθμος ταξινόμησης στον κόσμο."
    result = llm_client.parse_study_pack(bad_json(quiz=quiz), lecture1_texts())
    assert result.quiz[-1].question == quiz[0]["question"]
    assert result.quiz[-1].verified is False


def test_wrong_page_is_fixed_from_the_quote(pack_json):
    quiz = json.loads(pack_json)["quiz"]
    right_page = quiz[0]["page"]
    quiz[0]["page"] = 1
    result = llm_client.parse_study_pack(bad_json(quiz=quiz), lecture1_texts())
    fixed = next(q for q in result.quiz if q.question == quiz[0]["question"])
    assert fixed.page == right_page


def test_pages_outside_the_pdf_are_clamped(pack_json):
    cards = json.loads(pack_json)["flashcards"]
    cards[0]["page"] = 99
    result = llm_client.parse_study_pack(bad_json(flashcards=cards), lecture1_texts())
    assert all(1 <= c.page <= result.pages for c in result.flashcards)


def test_duplicate_flashcards_are_removed(pack_json):
    cards = json.loads(pack_json)["flashcards"]
    cards.append({**cards[0], "front": cards[0]["front"].upper() + " "})
    result = llm_client.parse_study_pack(bad_json(flashcards=cards))
    assert len(result.flashcards) == 10


def test_correct_answer_keeps_its_text_but_moves_position(pack_json):
    original = json.loads(pack_json)["quiz"]
    result = llm_client.parse_study_pack(pack_json)
    positions = set()
    for before, after in zip(original, result.quiz):
        assert after.options[after.answer_index] == before["options"][before["answer_index"]]
        assert sorted(after.options) == sorted(before["options"])
        positions.add(after.answer_index)
    assert len(positions) > 1


def test_question_with_duplicate_options_is_dropped(pack_json):
    quiz = json.loads(pack_json)["quiz"]
    quiz[0]["options"][1] = quiz[0]["options"][0]
    result = llm_client.parse_study_pack(bad_json(quiz=quiz))
    assert len(result.quiz) == 4


def test_counts_scale_with_the_length_of_the_lecture():
    short, long = llm_client.target_counts(3), llm_client.target_counts(30)
    assert short["flashcards"] >= 12
    assert long["flashcards"] > short["flashcards"]
    assert "{{" not in llm_client.build_prompt(6)
    assert "18 flashcards" in llm_client.build_prompt(6) or "About 18" in llm_client.build_prompt(6)


def test_notes_prompt_asks_for_every_page():
    prompt = llm_client.build_notes_prompt()
    assert "EVERY page" in prompt and "{{n_pages}}" in prompt


# Choosing the engine: a problem with the key must not stop the student

class FakeOllama:
    def __init__(self, content=None, error=None, models=("gemma4:e2b",)):
        self.content, self.error, self.calls, self.models = content, error, 0, models

    def chat(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return SimpleNamespace(message=SimpleNamespace(content=self.content))

    def list(self):
        if self.error:
            raise self.error
        return SimpleNamespace(models=[SimpleNamespace(model=m) for m in self.models])


def post_pdf(http, pdf, **form):
    return http.post("/api/study", data={"pdf": (io.BytesIO(pdf), "l.pdf"), **form},
                     content_type="multipart/form-data")


def make(tmp_path, gemini, ollama):
    from app import create_app

    return create_app(client=gemini, ollama_client=ollama, cache_dir=tmp_path).test_client()


NO_CREDITS = APIError(402, "RESOURCE_EXHAUSTED. Your prepayment credits are depleted.")


def test_no_credits_falls_back_to_local_without_an_error(tmp_path, tiny_pdf, pack_json):
    ollama = FakeOllama(pack_json)
    response = post_pdf(make(tmp_path, scripted([NO_CREDITS], pack_json), ollama), tiny_pdf)
    assert response.status_code == 200
    data = response.get_json()
    assert data["engine"] == "local" and data["flashcards"]
    assert "credits" in data["notice"]
    assert ollama.calls == 1


def test_after_a_failure_gemini_is_not_called_again_for_a_while(tmp_path, tiny_pdf, pack_json):
    gemini = scripted([NO_CREDITS], pack_json)
    http = make(tmp_path, gemini, FakeOllama(pack_json))
    post_pdf(http, tiny_pdf)
    data = post_pdf(http, tiny_pdf + b"\n%other").get_json()
    assert data["engine"] == "local" and "credits" in data["notice"]
    assert len(gemini.models.models_used) == 1


def test_choosing_gemini_always_tries_it_and_recovers(tmp_path, tiny_pdf, pack_json):
    gemini = scripted([NO_CREDITS], pack_json)
    http = make(tmp_path, gemini, FakeOllama(pack_json))
    post_pdf(http, tiny_pdf)
    data = post_pdf(http, tiny_pdf, engine="cloud").get_json()
    assert data["engine"] == "cloud" and data["notice"] == ""
    assert http.get("/api/status").get_json()["gemini"]["down"] is False


def test_choosing_gemini_shows_its_error_and_does_not_use_local(tmp_path, tiny_pdf, pack_json):
    ollama = FakeOllama(pack_json)
    response = post_pdf(make(tmp_path, scripted([NO_CREDITS], pack_json), ollama), tiny_pdf, engine="cloud")
    assert response.status_code == 502 and "credits" in response.get_json()["error"]
    assert ollama.calls == 0


def test_local_engine_never_touches_gemini(tmp_path, tiny_pdf, pack_json):
    gemini = scripted([], pack_json)
    data = post_pdf(make(tmp_path, gemini, FakeOllama(pack_json)), tiny_pdf, engine="local").get_json()
    assert data["engine"] == "local" and data["notice"] == ""
    assert gemini.models.models_used == []


def test_both_engines_down_explains_both(tmp_path, tiny_pdf, pack_json):
    ollama = FakeOllama(error=ConnectionError("Failed to connect to Ollama"))
    response = post_pdf(make(tmp_path, scripted([NO_CREDITS], pack_json), ollama), tiny_pdf)
    assert response.status_code == 502
    message = response.get_json()["error"]
    assert "credits" in message and "Ollama" in message


def test_broken_lecture_answer_does_not_trigger_the_fallback(tmp_path, tiny_pdf):
    ollama = FakeOllama("{}")
    response = post_pdf(make(tmp_path, FakeClient("not json"), ollama), tiny_pdf)
    assert response.status_code == 502
    assert ollama.calls == 0


def test_unknown_engine_is_rejected(tmp_path, tiny_pdf, pack_json):
    http = make(tmp_path, FakeClient(pack_json), FakeOllama(pack_json))
    assert post_pdf(http, tiny_pdf, engine="magic").status_code == 400


@pytest.mark.parametrize("ollama, state", [
    (FakeOllama(models=("gemma4:e2b",)), "ready"),
    (FakeOllama(models=("gemma3:1b",)), "not_installed"),
    (FakeOllama(error=ConnectionError("refused")), "not_running"),
])
def test_status_reports_the_local_model(tmp_path, pack_json, ollama, state, monkeypatch):
    monkeypatch.setattr(llm_client, "LOCAL_MODEL", "gemma4:e2b")
    status = make(tmp_path, FakeClient(pack_json), ollama).get("/api/status").get_json()
    assert status["local"] == {"model": "gemma4:e2b", "state": state}
    assert status["gemini"]["has_key"] is True


# Vertex AI: the route that can use Google Cloud trial credits

def fake_genai(monkeypatch, error=None):
    from google import genai

    seen = {}

    def build(**kwargs):
        if error:
            raise error
        seen.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(genai, "Client", build)
    return seen


def test_cloud_project_uses_vertex_and_not_the_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-project")
    monkeypatch.setenv("GEMINI_API_KEY", "old-key")
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    seen = fake_genai(monkeypatch)
    llm_client._default_client()
    assert (seen["vertexai"], seen["project"], seen["location"]) == (True, "my-project", "global")
    assert "api_key" not in seen
    assert seen["http_options"].timeout == llm_client.GEMINI_TIMEOUT * 1000


def test_without_a_project_the_key_is_used(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "a-key")
    seen = fake_genai(monkeypatch)
    llm_client._default_client()
    assert seen["api_key"] == "a-key" and "vertexai" not in seen


def test_not_signed_in_to_google_cloud_says_what_to_run(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-project")
    fake_genai(monkeypatch, error=RuntimeError("Your default credentials were not found."))
    with pytest.raises(llm_client.GeminiUnavailable, match="gcloud auth application-default login"):
        llm_client._default_client()


def test_vertex_sends_a_large_pdf_inline(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "INLINE_PDF_LIMIT", 10)
    client = FakeClient(pack_json)
    client.vertexai = True
    llm_client.generate_study_pack(tiny_pdf, client=client)
    assert client.models.all_kwargs[0]["contents"][0].inline_data.data == tiny_pdf


def test_model_too_big_for_memory_says_so(tiny_pdf):
    error = RuntimeError("model requires 6.9 GiB but only 4.8 GiB are available")
    with pytest.raises(llm_client.LLMError, match="μνήμη"):
        llm_client.generate_study_pack(tiny_pdf, private=True, ollama_client=FakeOllama(error=error))


def test_stuck_model_moves_to_the_next_one_without_retrying(tiny_pdf, pack_json, monkeypatch):
    monkeypatch.setattr(llm_client, "MODEL", "gemini-slow")
    monkeypatch.setattr(llm_client, "FALLBACK_MODELS", ["gemini-fast"])
    client = scripted([TimeoutError("The read operation timed out")], pack_json)
    llm_client.generate_study_pack(tiny_pdf, client=client)
    assert client.models.models_used[:2] == ["gemini-slow", "gemini-fast"]
