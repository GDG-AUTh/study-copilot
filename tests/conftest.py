"""Shared test helpers: a mocked LLM client so no test ever calls the network."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "tests" / "fixtures"


class FakeModels:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        return SimpleNamespace(text=self.text)


class FakeClient:
    """Looks like google.genai.Client for the parts we use."""

    def __init__(self, text: str):
        self.models = FakeModels(text)


@pytest.fixture
def pack_json() -> str:
    return (FIXTURES / "study_pack.json").read_text(encoding="utf-8")


@pytest.fixture
def fake_client(pack_json):
    return FakeClient(pack_json)


@pytest.fixture
def tiny_pdf() -> bytes:
    return (FIXTURES / "tiny.pdf").read_bytes()


@pytest.fixture
def no_network(monkeypatch):
    """Fail loudly if any code tries to build a real Gemini client."""
    import llm_client

    def boom():
        raise AssertionError("A test tried to use the real Gemini client")

    monkeypatch.setattr(llm_client, "_default_client", boom)


@pytest.fixture
def make_app(tmp_path, no_network):
    from app import create_app

    def _make(client):
        app = create_app(client=client, cache_dir=tmp_path / "cache")
        app.config["TESTING"] = True
        return app.test_client()

    return _make


def bad_json(**changes) -> str:
    data = json.loads((FIXTURES / "study_pack.json").read_text(encoding="utf-8"))
    data.update(changes)
    return json.dumps(data, ensure_ascii=False)
