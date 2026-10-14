# Study Copilot — rules for the agent

These rules apply to every task in this project.

- UI text in Greek; code, comments and commit messages in English.
- Never read, print, log or commit `.env` or any API key. The key is read only from the `GEMINI_API_KEY` environment variable.
- All model calls go through `llm_client.py`. No other file calls Gemini or Ollama directly.
- Prompts for the model live in `prompts/*.md`, never inline in Python code.
- Every model response must match a JSON schema; validate it before using it.
- Every new feature comes with a test that uses the mocked LLM client. Tests never call the network.
- Keep the frontend plain HTML/CSS/JS with no JS libraries.
- Before saying a task is done, run `pytest` and show the result.
