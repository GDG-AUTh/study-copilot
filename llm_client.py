"""Every call to a language model goes through this module.

Keeping all model calls in one place means the tests can replace the real
client with a mock: no network, no quota, same answer every time.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ValidationError

# Free-tier Flash model. Change it here (or with the GEMINI_MODEL env var), nowhere else.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Study modes, in the order they appear in the UI. Each mode has prompts/<mode>.md.
MODES = ["summary", "flashcards", "quiz", "definitions"]

# Expected number of items per mode (min, max).
COUNTS = {"summary": (6, 8), "flashcards": (10, 10), "quiz": (5, 5), "definitions": (5, 15)}


class SummaryBullet(BaseModel):
    text: str
    page: int


class Flashcard(BaseModel):
    front: str
    back: str
    page: int


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str
    source_quote: str
    page: int


class Definition(BaseModel):
    term: str
    definition: str
    page: int


class StudyPack(BaseModel):
    """The JSON schema the model must follow."""

    summary: list[SummaryBullet]
    flashcards: list[Flashcard]
    quiz: list[QuizQuestion]
    definitions: list[Definition]


class LLMError(Exception):
    """An error with a message that is safe to show to the user (in Greek)."""


def build_prompt() -> str:
    """Join the shared instructions with the prompt of every mode."""
    parts = [(PROMPTS_DIR / "base.md").read_text(encoding="utf-8")]
    for mode in MODES:
        parts.append((PROMPTS_DIR / f"{mode}.md").read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def _default_client():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMError("Λείπει το GEMINI_API_KEY. Αντίγραψε το .env.example σε .env και βάλε το κλειδί σου.")
    from google import genai

    return genai.Client(api_key=key)


def generate_study_pack(pdf_bytes: bytes, client=None) -> StudyPack:
    """Send the PDF to Gemini and return a validated StudyPack."""
    from google.genai import types

    client = client or _default_client()
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                build_prompt(),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StudyPack,
                temperature=0.3,
            ),
        )
    except Exception as exc:  # network, quota, invalid key...
        text = str(exc)
        if "429" in text or "RESOURCE_EXHAUSTED" in text:
            raise LLMError("Ξεπεράστηκε το όριο του δωρεάν Gemini. Περίμενε ένα λεπτό και ξαναδοκίμασε.") from exc
        if "API key" in text or "401" in text or "403" in text:
            raise LLMError("Το Gemini απέρριψε το κλειδί. Έλεγξε το GEMINI_API_KEY στο .env.") from exc
        raise LLMError("Δεν ήταν δυνατή η επικοινωνία με το Gemini. Δοκίμασε ξανά.") from exc
    return parse_study_pack(response.text or "")


def parse_study_pack(raw: str) -> StudyPack:
    """Validate the model's JSON: right shape, right number of items, valid answers."""
    try:
        pack = StudyPack.model_validate_json(raw)
    except ValidationError as exc:
        raise LLMError("Το μοντέλο επέστρεψε απάντηση σε λάθος μορφή. Δοκίμασε ξανά.") from exc
    check_pack(pack)
    return pack


def check_pack(pack: StudyPack) -> None:
    for mode in MODES:
        low, high = COUNTS[mode]
        n = len(getattr(pack, mode))
        if not low <= n <= high:
            raise LLMError(f"Το μοντέλο επέστρεψε {n} στοιχεία για «{mode}» αντί για {low}–{high}. Δοκίμασε ξανά.")
    for q in pack.quiz:
        if len(q.options) != 4 or not 0 <= q.answer_index < 4:
            raise LLMError("Μια ερώτηση του quiz δεν έχει 4 επιλογές με έγκυρη σωστή απάντηση. Δοκίμασε ξανά.")
