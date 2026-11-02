"""Every call to a language model goes through this module.

One interface, two backends:
- Gemini (cloud), in two steps:
    1. "read": Gemini reads the slides (text, diagrams, tables, code) and writes
       faithful notes for every page.
    2. "generate": from the notes and the PDF it writes the study material.
  Splitting reading from writing gives much better flashcards and correct pages.
- Gemma (local, through Ollama): we extract the text with pypdf and do one step.
Both return the same validated StudyResult, so the rest of the app never knows
which one answered.

After the model answers, plain Python cleans the result: drops duplicate cards,
fixes page numbers, balances the position of the correct quiz answer and checks
that every quiz quote really appears in the lecture.

Keeping all model calls in one place means the tests can replace the real
clients with mocks: no network, no quota, same answer every time.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

# Before the settings below are read. .env wins over an old key in the shell.
load_dotenv(Path(__file__).parent / ".env", override=True)

# Main model and fallbacks. Change them here (or with the env vars), nowhere else.
# Vertex AI has no "latest" aliases, so it needs real model names.
_VERTEX = bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))
# Pro writes the deepest cards (about 2.5 minutes per lecture); 3.5 Flash is close and takes 1 minute.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview" if _VERTEX else "gemini-flash-latest")
_FALLBACKS = "gemini-3.5-flash" if _VERTEX else "gemini-2.5-flash"
FALLBACK_MODELS = [m.strip() for m in os.environ.get("GEMINI_FALLBACK_MODELS", _FALLBACKS).split(",") if m.strip()]

# Local model for private mode and for when Gemini is unavailable.
# gemma4:e2b-it-qat (~4.3 GB) fits a Mac with 8 GB RAM. Plain gemma4:e2b does not: on a Mac
# it is a 7.5 GB build. With 16+ GB RAM try gemma4:e4b.
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "gemma4:e2b-it-qat")

# Small local models have a limited context: send at most this many pages.
MAX_LOCAL_PAGES = int(os.environ.get("MAX_LOCAL_PAGES", 30))

# Above this size the PDF goes through the Gemini Files API instead of inline
# (inline requests are limited to 20 MB, and base64 makes the PDF ~33% bigger).
INLINE_PDF_LIMIT = 14 * 1024 * 1024

# How many times to retry a temporary Gemini error (rate limit, overloaded server).
MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", 3))
MAX_RETRY_WAIT = 30  # seconds

# Give up on one Gemini call after this long, so a stuck request can never hang the app.
GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", 240))  # seconds

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Bump when the pipeline changes in a way that should ignore old cached answers.
PIPELINE_VERSION = "turbo-1"

# Study modes, in the order they appear in the UI. Each mode has prompts/<mode>.md.
MODES = ["summary", "flashcards", "quiz", "definitions"]

# Lowest number of items we accept per mode before asking the model again.
MIN_COUNTS = {"summary": 4, "flashcards": 8, "quiz": 4, "definitions": 3}


# Schemas the model must follow. No default values: Gemini rejects them in a schema.

class PageNote(BaseModel):
    page: int
    title: str
    content: str
    key_terms: list[str]


class LectureNotes(BaseModel):
    title: str
    pages: list[PageNote]


class SummaryBullet(BaseModel):
    text: str
    page: int


CardKind = Literal["definition", "concept", "process", "comparison", "application", "code"]


class Flashcard(BaseModel):
    front: str
    back: str
    kind: CardKind
    page: int


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str
    source_quote: str
    difficulty: Literal["easy", "medium", "hard"]
    page: int


class Definition(BaseModel):
    term: str
    definition: str
    page: int


class StudyPack(BaseModel):
    """The JSON schema the model must follow for the study material."""

    title: str
    summary: list[SummaryBullet]
    flashcards: list[Flashcard]
    quiz: list[QuizQuestion]
    definitions: list[Definition]


# What the app gets back: the pack, plus what Python checked afterwards.

class CheckedQuestion(QuizQuestion):
    verified: bool | None = None  # quote found in the PDF text; None = PDF has no text


class StudyResult(BaseModel):
    title: str
    pages: int
    summary: list[SummaryBullet]
    flashcards: list[Flashcard]
    quiz: list[CheckedQuestion]
    definitions: list[Definition]


class LLMError(Exception):
    """An error with a message that is safe to show to the user (in Greek)."""


class GeminiUnavailable(LLMError):
    """Gemini cannot answer right now (no key, no credits, limits, offline).

    Nothing is wrong with the lecture, so the app can use the local model instead.
    """


class _Retryable(Exception):
    """A temporary problem: wait and try again (or try the next model)."""

    def __init__(self, message: str, wait: float = 0):
        super().__init__(message)
        self.wait = wait


class _ModelUnavailable(Exception):
    """This model cannot be used (retired, unknown name): try the next one."""


# Prompts

def _read_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def target_counts(pages: int) -> dict[str, int]:
    """How many items to ask for, scaled to the length of the lecture."""
    pages = max(pages, 1)
    return {
        "summary": min(max(pages + 2, 6), 14),
        "flashcards": min(max(pages * 3, 12), 40),
        "quiz": min(max(pages + 2, 6), 15),
        "definitions": min(max(pages * 2, 6), 25),
    }


def build_prompt(pages: int = 10) -> str:
    """The prompt for the "generate" step: shared rules plus the prompt of every mode."""
    parts = [_read_prompt("base")] + [_read_prompt(mode) for mode in MODES]
    prompt = "\n\n".join(parts)
    for mode, n in target_counts(pages).items():
        prompt = prompt.replace(f"{{{{n_{mode}}}}}", str(n))
    return prompt


def build_notes_prompt() -> str:
    """The prompt for the "read" step."""
    return _read_prompt("notes")


def prompts_fingerprint() -> str:
    """Changes whenever a prompt file or the pipeline changes (used by the cache)."""
    text = PIPELINE_VERSION + build_notes_prompt() + build_prompt()
    return hashlib.sha256(text.encode()).hexdigest()


# PDF text

def page_texts(pdf_bytes: bytes, max_pages: int | None = None) -> list[str]:
    """Text of every page ('' for pages without text, e.g. scanned or image-only)."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = reader.pages if max_pages is None else reader.pages[:max_pages]
        return [(page.extract_text() or "").strip() for page in pages]
    except Exception as exc:
        raise LLMError("Δεν ήταν δυνατό να διαβαστεί το PDF. Είναι κατεστραμμένο ή κλειδωμένο με κωδικό;") from exc


def with_page_markers(texts: list[str]) -> str:
    return "\n\n".join(f"--- Σελίδα {n} ---\n{t}" for n, t in enumerate(texts, start=1) if t)


# Public entry point

def generate_study_pack(pdf_bytes: bytes, client=None, private: bool = False, ollama_client=None) -> StudyResult:
    """Return a checked StudyResult, from Gemini (default) or local Gemma (private=True)."""
    if private:
        return _generate_local(pdf_bytes, ollama_client)
    return _generate_gemini(pdf_bytes, client)


# Gemini

def gemini_configured() -> bool:
    return bool(os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GEMINI_API_KEY"))


def _default_client():
    """Vertex AI when a Cloud project is set (that route can use trial credits), else an API key."""
    from google import genai
    from google.genai import types

    http = types.HttpOptions(timeout=GEMINI_TIMEOUT * 1000)
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project:
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
        try:
            return genai.Client(vertexai=True, project=project, location=location, http_options=http)
        except Exception as exc:
            raise _classify(exc) from exc
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise GeminiUnavailable("Λείπει το GEMINI_API_KEY. Αντίγραψε το .env.example σε .env και βάλε το κλειδί σου.")
    return genai.Client(api_key=key, http_options=http)


def _generate_gemini(pdf_bytes: bytes, client=None) -> StudyResult:
    from google.genai import types

    texts = page_texts(pdf_bytes)
    n_pages = len(texts)
    client = client or _default_client()
    pdf_part, uploaded = _pdf_part(client, pdf_bytes, types)
    try:
        # Step 1: read the slides, page by page.
        anchors = with_page_markers(texts)
        notes_contents = [pdf_part, build_notes_prompt().replace("{{n_pages}}", str(n_pages))]
        if anchors:
            notes_contents.append("# Text extracted from the PDF (to match page numbers)\n\n" + anchors)
        notes_raw = _call_gemini(client, notes_contents, LectureNotes)
        notes = _parse(LectureNotes, notes_raw)

        # Step 2: write the study material from the notes and the PDF.
        prompt = build_prompt(n_pages)
        notes_text = "# Lecture notes (page by page)\n\n" + notes.model_dump_json(indent=1)
        feedback = ""
        for attempt in range(2):
            raw = _call_gemini(client, [pdf_part, notes_text, prompt + feedback], StudyPack)
            pack = _parse(StudyPack, raw)
            result = finalize(pack, texts)
            problem = shortfall(result)
            if not problem:
                return result
            feedback = (f"\n\nIMPORTANT: your previous answer was rejected because {problem}. "
                        "Follow the requested counts exactly.")
        raise LLMError(f"Το μοντέλο δεν έφτιαξε αρκετό υλικό ({problem}). Δοκίμασε ξανά.")
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass  # the Files API deletes it anyway after 48 hours


def _pdf_part(client, pdf_bytes: bytes, types):
    """Small PDFs go inline; large ones through the Files API. Returns (part, uploaded_file)."""
    # Vertex AI has no Files API; it takes the PDF inline.
    if len(pdf_bytes) <= INLINE_PDF_LIMIT or getattr(client, "vertexai", False) is True:
        return types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"), None
    try:
        uploaded = client.files.upload(file=io.BytesIO(pdf_bytes), config={"mime_type": "application/pdf"})
        for _ in range(30):
            state = str(getattr(uploaded, "state", "") or "")
            if "PROCESSING" not in state:
                break
            time.sleep(1)
            uploaded = client.files.get(name=uploaded.name)
    except Exception as exc:
        problem = _classify(exc)
        if isinstance(problem, LLMError):
            raise problem from exc
        raise GeminiUnavailable("Δεν ήταν δυνατό να ανέβει το PDF στο Gemini. Δοκίμασε ξανά.") from exc
    if "FAILED" in str(getattr(uploaded, "state", "")):
        raise LLMError("Το Gemini δεν μπόρεσε να επεξεργαστεί αυτό το PDF.")
    return uploaded, uploaded


def _call_gemini(client, contents, schema) -> str:
    """One structured call, with retries for temporary errors and fallback models."""
    from google.genai import types

    config = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema)
    last: Exception | None = None
    for model in [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]:
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(model=model, contents=contents, config=config)
                text = _response_text(response)
                if not text:
                    raise _Retryable("empty response")
                return text
            except Exception as exc:
                problem = exc if isinstance(exc, _Retryable) else _classify(exc)
                if isinstance(problem, LLMError):
                    raise problem from exc
                last = problem
                if isinstance(problem, _ModelUnavailable) or "timed out" in str(problem).lower():
                    break  # next model: asking a stuck model again only wastes minutes
                if attempt < MAX_RETRIES - 1:
                    time.sleep(min(problem.wait or 2 ** (attempt + 1), MAX_RETRY_WAIT))
    if isinstance(last, _ModelUnavailable):
        raise GeminiUnavailable(f"Το μοντέλο {MODEL} δεν είναι διαθέσιμο για το κλειδί σου. "
                       "Βάλε άλλο μοντέλο στο GEMINI_MODEL του .env (π.χ. gemini-2.5-flash).")
    if last is not None and "429" in str(last):
        raise GeminiUnavailable("Ξεπεράστηκε το όριο αιτημάτων ανά λεπτό του Gemini. Περίμενε ένα λεπτό και ξαναδοκίμασε.")
    if last is not None and "empty" in str(last):
        raise GeminiUnavailable("Το Gemini δεν επέστρεψε απάντηση (ίσως μπλόκαρε το περιεχόμενο). Δοκίμασε ξανά.")
    raise GeminiUnavailable("Το Gemini είναι προσωρινά υπερφορτωμένο. Δοκίμασε ξανά σε λίγο.")


def _response_text(response) -> str:
    try:
        return (response.text or "").strip()
    except Exception:  # some SDK versions raise when the answer was blocked
        return ""


def _classify(exc: Exception) -> Exception:
    """Turn a Gemini exception into LLMError (stop), _Retryable or _ModelUnavailable."""
    code = getattr(exc, "code", None)
    text = str(exc)
    low = text.lower()
    if code is None:
        match = re.match(r"\s*(\d{3})\b", text)
        code = int(match.group(1)) if match else None

    if "default credentials" in low:
        return GeminiUnavailable("Δεν έχεις συνδεθεί στο Google Cloud. Τρέξε: gcloud auth application-default login")
    if "aiplatform.googleapis.com" in low and code == 403:
        return GeminiUnavailable("Το Vertex AI δεν είναι διαθέσιμο στο project σου. Έλεγξε το GOOGLE_CLOUD_PROJECT "
                                 "και τρέξε: gcloud services enable aiplatform.googleapis.com")
    if code == 402 or "prepayment" in low or "credits are depleted" in low:
        return GeminiUnavailable("Τελείωσαν τα credits του Gemini API στο project σου. Πρόσθεσε credits στο "
                        "AI Studio (https://ai.studio/projects) ή χρησιμοποίησε άλλο κλειδί.")
    if code in (401, 403) or "api key" in low or "api_key" in low or "permission_denied" in low:
        return GeminiUnavailable("Το Gemini απέρριψε το κλειδί. Έλεγξε το GEMINI_API_KEY στο .env.")
    if code == 404 or "not_found" in low or "no longer available" in low:
        return _ModelUnavailable(text)
    if code == 429 or "resource_exhausted" in low:
        if "perday" in low.replace(" ", "") or "per day" in low or "daily" in low:
            return GeminiUnavailable("Εξαντλήθηκε το ημερήσιο όριο του δωρεάν Gemini. Δοκίμασε αύριο ή με άλλο κλειδί.")
        return _Retryable(text, wait=_retry_delay(exc))
    if code in (500, 502, 503, 504) or "unavailable" in low or "overloaded" in low or "deadline" in low:
        return _Retryable(text)
    if code == 400 and ("token" in low and ("exceed" in low or "limit" in low)):
        return LLMError("Η διάλεξη είναι πολύ μεγάλη για το μοντέλο. Χώρισε το PDF σε μικρότερα κομμάτια.")
    if code == 400 and "schema" in low:
        return _ModelUnavailable(text)  # this model does not support the schema: try another
    if code is None and isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return _Retryable(text)
    if code is None and ("connect" in low or "timed out" in low or "timeout" in low):
        return _Retryable(text)
    return GeminiUnavailable("Δεν ήταν δυνατή η επικοινωνία με το Gemini. Δοκίμασε ξανά.")


def _retry_delay(exc: Exception) -> float:
    """Gemini says how long to wait in a RetryInfo detail, e.g. "retryDelay": "23s"."""
    match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", str(getattr(exc, "details", "")) + str(exc))
    return float(match.group(1)) if match else 0


def _parse(schema: type[BaseModel], raw: str):
    try:
        return schema.model_validate_json(_strip_fences(raw))
    except ValidationError as exc:
        raise LLMError("Το μοντέλο επέστρεψε απάντηση σε λάθος μορφή. Δοκίμασε ξανά.") from exc


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    return raw


# Cleaning the model's answer

def parse_study_pack(raw: str, texts: list[str] | None = None) -> StudyResult:
    """Validate the model's JSON and clean it. Used for answers that skip the Gemini pipeline."""
    pack = _parse(StudyPack, raw)
    result = finalize(pack, texts or [])
    problem = shortfall(result, minimum=1)
    if problem:
        raise LLMError(f"Το μοντέλο επέστρεψε ελλιπές υλικό ({problem}). Δοκίμασε ξανά.")
    return result


def shortfall(result: StudyResult, minimum: int | None = None) -> str:
    """Describe what is missing, or '' if every mode has enough items."""
    for mode in MODES:
        low = MIN_COUNTS[mode] if minimum is None else minimum
        n = len(getattr(result, mode))
        if n < low:
            return f"{n} στοιχεία για «{mode}», χρειάζονται τουλάχιστον {low}"
    return ""


def finalize(pack: StudyPack, texts: list[str]) -> StudyResult:
    """Clean a pack: valid quiz, no duplicates, real pages, balanced answers, checked quotes."""
    n_pages = len(texts)
    norm_pages = [_normalize(t) for t in texts]
    has_text = any(norm_pages)

    def fix_page(page: int, evidence: str = "") -> int:
        if n_pages == 0:
            return max(page, 1)
        if 1 <= page <= n_pages and (not evidence or not has_text):
            return page
        if evidence and has_text:
            found = _find_page(evidence, norm_pages, prefer=page)
            if found:
                return found
        return min(max(page, 1), n_pages)

    summary = _dedupe(pack.summary, lambda b: b.text)
    for b in summary:
        b.page = fix_page(b.page)

    cards = [c for c in pack.flashcards if c.front.strip() and c.back.strip()]
    cards = _dedupe(cards, lambda c: c.front)
    for c in cards:
        c.page = fix_page(c.page)

    definitions = _dedupe([d for d in pack.definitions if d.term.strip()], lambda d: d.term)
    for d in definitions:
        d.page = fix_page(d.page)

    quiz: list[CheckedQuestion] = []
    for q in _dedupe(pack.quiz, lambda q: q.question):
        options = [o.strip() for o in q.options]
        if len(options) != 4 or not 0 <= q.answer_index < 4 or len({_normalize(o) for o in options}) != 4:
            continue
        verified = _quote_found(q.source_quote, norm_pages) if has_text else None
        page = fix_page(q.page, q.source_quote if verified else "")
        options, answer = _balanced(options, q.answer_index, q.question)
        quiz.append(CheckedQuestion(**(q.model_dump() | {
            "options": options, "answer_index": answer, "page": page, "verified": verified})))
    # Questions whose quote we could find in the lecture come first.
    quiz.sort(key=lambda q: q.verified is False)

    return StudyResult(title=pack.title.strip(), pages=n_pages, summary=summary, flashcards=cards,
                       quiz=quiz, definitions=definitions)


def _normalize(text: str) -> str:
    """Lowercase, no accents, no punctuation, single spaces: for fuzzy comparisons."""
    import unicodedata

    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def _dedupe(items: list, key) -> list:
    seen: list[str] = []
    out = []
    for item in items:
        k = _normalize(key(item))
        if not k or any(k == s or SequenceMatcher(None, k, s).ratio() > 0.9 for s in seen):
            continue
        seen.append(k)
        out.append(item)
    return out


def _quote_found(quote: str, norm_pages: list[str]) -> bool:
    return _find_page(quote, norm_pages) is not None


def _find_page(quote: str, norm_pages: list[str], prefer: int | None = None) -> int | None:
    """Page (1-based) whose text contains the quote, allowing small differences."""
    q = _normalize(quote)
    if len(q) < 8:
        return None
    order = list(range(len(norm_pages)))
    if prefer and 1 <= prefer <= len(norm_pages):
        order.remove(prefer - 1)
        order.insert(0, prefer - 1)
    for i in order:
        if q in norm_pages[i]:
            return i + 1
    words = q.split()
    for i in order:
        page = norm_pages[i]
        if not page:
            continue
        hits = sum(1 for w in words if w in page)
        if hits / len(words) >= 0.85:
            match = SequenceMatcher(None, page, q, autojunk=False).find_longest_match(0, len(page), 0, len(q))
            if match.size >= min(len(q), 25) * 0.6:
                return i + 1
    return None


def _balanced(options: list[str], answer: int, seed: str) -> tuple[list[str], int]:
    """Move the correct option to a position chosen from the question text.

    Models love putting the right answer first; this spreads it over A-D, and the
    same question always gets the same order (so the cache and tests stay stable).
    """
    target = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 4
    correct = options[answer]
    others = [o for i, o in enumerate(options) if i != answer]
    others.insert(target, correct)
    return others, target


# Private mode: Gemma through Ollama

def extract_text(pdf_bytes: bytes) -> str:
    """Text of the PDF with page markers, so the model can cite pages."""
    text = with_page_markers(page_texts(pdf_bytes, MAX_LOCAL_PAGES))
    if not text:
        raise LLMError("Το PDF δεν έχει κείμενο (μάλλον είναι σκαναρισμένο). "
                       "Η ιδιωτική λειτουργία διαβάζει μόνο κείμενο· δοκίμασε χωρίς αυτήν.")
    return text


def local_status(ollama_client=None) -> dict:
    """Is the local model ready? Never raises: the UI shows the answer."""
    try:
        listed = (ollama_client or _default_ollama()).list()
    except Exception:
        return {"model": LOCAL_MODEL, "state": "not_running"}
    names = [m.model for m in listed.models]
    return {"model": LOCAL_MODEL, "state": "ready" if LOCAL_MODEL in names else "not_installed"}


def _default_ollama():
    import ollama

    return ollama.Client(host=os.environ.get("OLLAMA_HOST"))


def _generate_local(pdf_bytes: bytes, ollama_client=None) -> StudyResult:
    text = extract_text(pdf_bytes)
    texts = page_texts(pdf_bytes, MAX_LOCAL_PAGES)
    ollama_client = ollama_client or _default_ollama()
    try:
        response = ollama_client.chat(
            model=LOCAL_MODEL,
            messages=[{"role": "user", "content": f"{build_prompt(len(texts))}\n\n# Lecture\n\n{text}"}],
            format=StudyPack.model_json_schema(),
            options={"temperature": 0.3, "num_ctx": 16384},
            keep_alive="2m",  # give the RAM back soon after: a laptop needs it
        )
    except Exception as exc:
        message = str(exc).lower()
        if "requires" in message and "available" in message:
            raise LLMError(f"Το μοντέλο {LOCAL_MODEL} δεν χωρά στη μνήμη αυτή τη στιγμή. "
                           "Κλείσε άλλες εφαρμογές ή βάλε μικρότερο στο LOCAL_MODEL του .env.") from exc
        if "not found" in message or "pull" in message:
            raise LLMError(f"Το μοντέλο {LOCAL_MODEL} δεν βρέθηκε. Τρέξε: ollama pull {LOCAL_MODEL}") from exc
        if "connect" in message or "refused" in message or isinstance(exc, ConnectionError):
            raise LLMError("Δεν τρέχει το Ollama. Άνοιξε την εφαρμογή Ollama ή τρέξε «ollama serve».") from exc
        raise LLMError("Το τοπικό μοντέλο δεν απάντησε. Δοκίμασε ξανά.") from exc
    return parse_study_pack(response.message.content or "", texts)
