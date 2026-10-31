"""Study Copilot as an MCP server: the same app, now usable as a tool by any AI agent.

Runs over stdio. Add it to an agent (Antigravity, Claude, Copilot in VS Code...) with:

    "study-copilot": {
      "command": "/ABSOLUTE/PATH/study-copilot/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/study-copilot/mcp_server.py"]
    }

Requires the MCP Python SDK below version 2 (pip install "mcp<2").
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import llm_client
import study_cache

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")  # read .env next to this file, whatever the working folder
CACHE_DIR = ROOT / ".cache"

mcp = FastMCP("study-copilot")


def _pack(pdf_path: str, private: bool) -> dict:
    path = Path(pdf_path).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise ValueError(f"PDF not found: {path}. Pass an absolute path to a lecture PDF.")
    try:
        pack, _ = study_cache.get_or_create(path.read_bytes(), CACHE_DIR, private=private)
    except llm_client.LLMError as exc:
        raise ValueError(str(exc)) from exc
    return pack


@mcp.tool()
def summarize_lecture(pdf_path: str, private: bool = False) -> dict:
    """Summarise a university lecture PDF in bullets, each with its page number.

    Use when the user wants a summary, an overview or the main ideas of a lecture.
    pdf_path: absolute path to the lecture PDF.
    private: true to use the local Gemma model, so the file never leaves this computer.
    """
    return {"summary": _pack(pdf_path, private)["summary"]}


@mcp.tool()
def make_flashcards(pdf_path: str, count: int = 20, private: bool = False) -> dict:
    """Create flashcards (front/back, with page numbers) from a university lecture PDF.

    Use when the user wants flashcards or wants to memorise the key facts of a lecture.
    pdf_path: absolute path to the lecture PDF. count: how many cards (1-40, default 20).
    private: true to use the local Gemma model, so the file never leaves this computer.
    """
    count = max(1, min(count, 40))
    return {"flashcards": _pack(pdf_path, private)["flashcards"][:count]}


@mcp.tool()
def make_quiz(pdf_path: str, questions: int = 5, private: bool = False) -> dict:
    """Create a multiple-choice quiz from a university lecture PDF.

    Each question has 4 options, the index of the correct answer, an explanation,
    a supporting quote and the page. Use when the user wants to test themselves on a
    lecture. Ask the questions one at a time and do not reveal answers before the user replies.
    pdf_path: absolute path to the lecture PDF. questions: how many (1-15, default 5).
    private: true to use the local Gemma model, so the file never leaves this computer.
    """
    questions = max(1, min(questions, 15))
    return {"quiz": _pack(pdf_path, private)["quiz"][:questions]}


if __name__ == "__main__":
    mcp.run()
