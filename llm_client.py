"""Every call to a language model goes through this module.

One interface, two backends:
- Gemini (cloud): reads the PDF directly.
- Gemma 4 (local, through Ollama): we extract the text with pypdf first.
Both use the same JSON schema, so the rest of the app never knows which one answered.

Keeping all model calls in one place means the tests can replace the real
clients with mocks: no network, no quota, same answer every time.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ValidationError

# Free-tier Flash model. Change it here (or with the GEMINI_MODEL env var), nowhere else.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

# Local model for private mode. gemma3:1b is small (~0.8 GB) and runs on any laptop;
# with a good connection and 8+ GB RAM, try gemma4:e2b (~7 GB) for better answers.
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "gemma3:1b")

# Small local models have a limited context: send at most this many pages.
MAX_LOCAL_PAGES = int(os.environ.get("MAX_LOCAL_PAGES", 30))

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


def generate_study_pack(pdf_bytes: bytes, client=None, private: bool = False, ollama_client=None) -> StudyPack:
    """Return a validated StudyPack, from Gemini (default) or local Gemma (private=True)."""
    if private:
        return _generate_local(pdf_bytes, ollama_client)
    return _generate_gemini(pdf_bytes, client)


def _generate_gemini(pdf_bytes: bytes, client=None) -> StudyPack:
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
    except Exception as exc:  # network error, quota or invalid key
        text = str(exc)
        if "429" in text or "RESOURCE_EXHAUSTED" in text:
            raise LLMError("Ξεπεράστηκε το όριο του δωρεάν Gemini. Περίμενε ένα λεπτό και ξαναδοκίμασε.") from exc
        if "API key" in text or "401" in text or "403" in text:
            raise LLMError("Το Gemini απέρριψε το κλειδί. Έλεγξε το GEMINI_API_KEY στο .env.") from exc
        raise LLMError("Δεν ήταν δυνατή η επικοινωνία με το Gemini. Δοκίμασε ξανά.") from exc
    return parse_study_pack(response.text or "")


def parse_study_pack(raw: str, strict: bool = True) -> StudyPack:
    """Validate the model's JSON: right shape, right number of items, valid answers.

    strict=False is for small local models: extra items are trimmed, fewer are accepted
    and invalid quiz questions are dropped, as long as every mode has something.
    """
    try:
        pack = StudyPack.model_validate_json(raw)
    except ValidationError as exc:
        raise LLMError("Το μοντέλο επέστρεψε απάντηση σε λάθος μορφή. Δοκίμασε ξανά.") from exc
    if not strict:
        pack = relax_pack(pack)
    check_pack(pack, strict=strict)
    return pack


def relax_pack(pack: StudyPack) -> StudyPack:
    pack.quiz = [q for q in pack.quiz if len(q.options) == 4 and 0 <= q.answer_index < 4]
    for mode in MODES:
        setattr(pack, mode, getattr(pack, mode)[: COUNTS[mode][1]])
    return pack


def check_pack(pack: StudyPack, strict: bool = True) -> None:
    for mode in MODES:
        low, high = COUNTS[mode]
        if not strict:
            low = 1
        n = len(getattr(pack, mode))
        if not low <= n <= high:
            raise LLMError(f"Το μοντέλο επέστρεψε {n} στοιχεία για «{mode}» αντί για {low}–{high}. Δοκίμασε ξανά.")
    for q in pack.quiz:
        if len(q.options) != 4 or not 0 <= q.answer_index < 4:
            raise LLMError("Μια ερώτηση του quiz δεν έχει 4 επιλογές με έγκυρη σωστή απάντηση. Δοκίμασε ξανά.")


# Private mode: Gemma through Ollama

def extract_text(pdf_bytes: bytes) -> str:
    """Text of the PDF with page markers, so the model can cite pages."""
    import io

    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        raise LLMError("Δεν ήταν δυνατό να διαβαστεί το PDF.") from exc
    pages = []
    for number, page in enumerate(reader.pages[:MAX_LOCAL_PAGES], start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"--- Σελίδα {number} ---\n{text}")
    if not pages:
        raise LLMError("Το PDF δεν έχει κείμενο (μάλλον είναι σκαναρισμένο). "
                       "Η ιδιωτική λειτουργία διαβάζει μόνο κείμενο· δοκίμασε χωρίς αυτήν.")
    return "\n\n".join(pages)


def _default_ollama():
    import ollama

    return ollama.Client(host=os.environ.get("OLLAMA_HOST"))


def _generate_local(pdf_bytes: bytes, ollama_client=None) -> StudyPack:
    text = extract_text(pdf_bytes)
    ollama_client = ollama_client or _default_ollama()
    try:
        response = ollama_client.chat(
            model=LOCAL_MODEL,
            messages=[{"role": "user", "content": f"{build_prompt()}\n\n# Lecture\n\n{text}"}],
            format=StudyPack.model_json_schema(),
            options={"temperature": 0.3},
        )
    except Exception as exc:
        message = str(exc).lower()
        if "not found" in message or "pull" in message:
            raise LLMError(f"Το μοντέλο {LOCAL_MODEL} δεν βρέθηκε. Τρέξε: ollama pull {LOCAL_MODEL}") from exc
        if "connect" in message or "refused" in message or isinstance(exc, ConnectionError):
            raise LLMError("Δεν τρέχει το Ollama. Άνοιξε την εφαρμογή Ollama ή τρέξε «ollama serve».") from exc
        raise LLMError("Το τοπικό μοντέλο δεν απάντησε. Δοκίμασε ξανά.") from exc
    return parse_study_pack(response.message.content or "", strict=False)
