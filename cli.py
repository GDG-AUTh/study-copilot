"""Generate study material from the command line and save it as JSON.

Useful for checking the model's output, e.g. with the grounding-critic subagent:

    python cli.py sample_lectures/lecture2.pdf out/lecture2.json
    python cli.py sample_lectures/lecture2.pdf out/lecture2-local.json --private
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

import llm_client


def main(argv: list[str] | None = None, client=None) -> int:
    parser = argparse.ArgumentParser(description="Study Copilot: PDF -> JSON study pack")
    parser.add_argument("pdf", type=Path, help="lecture PDF")
    parser.add_argument("out", type=Path, help="where to save the JSON")
    parser.add_argument("--private", action="store_true", help="use local Gemma through Ollama")
    args = parser.parse_args(argv)

    load_dotenv(override=True)  # .env wins over an old key in the shell
    try:
        pack = llm_client.generate_study_pack(args.pdf.read_bytes(), client=client, private=args.private)
    except (OSError, llm_client.LLMError) as exc:
        print(f"Σφάλμα: {exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(pack.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Αποθηκεύτηκε στο {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
