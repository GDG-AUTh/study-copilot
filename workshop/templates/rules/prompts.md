---
trigger: glob
globs: "prompts/*.md"
---

# Rules for model prompts

When creating or editing any file in `prompts/`:

- Every prompt asks the model to include the source page for each item.
- Every prompt forbids facts, names or numbers that do not appear in the provided PDF text.
- Every prompt asks for output that matches the JSON schema of its mode; no free text outside the JSON.
- Prompts ask for Greek output for the student-facing text.
- Keep each prompt under 40 lines.
