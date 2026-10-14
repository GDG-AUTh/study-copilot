import io
import json

import cli
import llm_client
from conftest import FIXTURES, FakeClient, bad_json


def upload(client, data: bytes):
    return client.post("/api/study", data={"pdf": (io.BytesIO(data), "lecture.pdf")},
                       content_type="multipart/form-data")


def test_definitions_mode_end_to_end(make_app, fake_client, tiny_pdf):
    data = upload(make_app(fake_client), tiny_pdf).get_json()
    assert 5 <= len(data["definitions"]) <= 15
    assert all({"term", "definition", "page"} <= d.keys() for d in data["definitions"])


def test_every_mode_has_a_prompt_file():
    prompt = llm_client.build_prompt()
    for mode in llm_client.MODES:
        assert (llm_client.PROMPTS_DIR / f"{mode}.md").exists()
        assert f"## {mode}" in prompt


def test_quiz_questions_carry_a_source_quote(make_app, fake_client, tiny_pdf):
    data = upload(make_app(fake_client), tiny_pdf).get_json()
    assert all(q["source_quote"].strip() for q in data["quiz"])


def test_missing_field_gives_friendly_error(make_app, pack_json, tiny_pdf):
    quiz = json.loads(pack_json)["quiz"]
    for q in quiz:
        del q["explanation"]
    response = upload(make_app(FakeClient(bad_json(quiz=quiz))), tiny_pdf)
    assert response.status_code == 502
    assert "λάθος μορφή" in response.get_json()["error"]


def test_invalid_answer_index_is_rejected(pack_json):
    quiz = json.loads(pack_json)["quiz"]
    quiz[0]["answer_index"] = 7
    try:
        llm_client.parse_study_pack(bad_json(quiz=quiz))
    except llm_client.LLMError as exc:
        assert "σωστή απάντηση" in str(exc)
    else:
        raise AssertionError("expected LLMError")


def test_cli_saves_json(tmp_path, fake_client, no_network):
    out = tmp_path / "out" / "pack.json"
    code = cli.main([str(FIXTURES / "tiny.pdf"), str(out)], client=fake_client)
    assert code == 0
    assert json.loads(out.read_text(encoding="utf-8"))["quiz"]
