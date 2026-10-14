---
name: add-study-mode
description: Adds a new study mode (a new tab or study format such as definitions, timeline or exam questions) to Study Copilot end to end. Use when the user asks for a new tab, mode or kind of study material.
---

# Add a study mode

Follow every step in order. Do not skip steps.

1. **Prompt file.** Create `prompts/<mode>.md` with the instructions for the model. Ask for page numbers and forbid facts that are not in the PDF.
2. **JSON schema.** Add a schema for the new output next to the existing ones and use it in `llm_client.py` for every backend that currently exists in the project. Do not add a backend just to complete this skill. When a backend is added later, extend it to support this mode then.
3. **Mock fixture.** Add an example response for the new mode to the mocked LLM client used by the tests.
4. **New tab.** Add a tab to the UI with a Greek label. Reuse the existing styles and cache, scoped to the PDF and backend/model.
5. **Test.** Add at least one test that uses the mock and checks the new mode end to end. Run `pytest`.
6. **Screenshot.** Run the app on `sample_lectures/lecture1.pdf` and show a screenshot of the new tab.

When done, summarise which files you changed for each step.
