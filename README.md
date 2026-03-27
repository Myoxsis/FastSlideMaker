# Fast Slide Maker (Offline, Ollama-powered)

Local web app that generates consulting-style PowerPoint slide specifications for **process** and **IT solution design** content.

## What this app does

- Takes a user prompt and generates a structured presentation plan.
- Enforces a JSON-first workflow (no free text output from LLM).
- Validates/normalizes slide schema before rendering.
- Uses deterministic layout templates for predictable visual quality.
- Supports editing + single-slide regeneration in-browser.
- Can ingest an existing `.pptx` deck as optional reference context for the LLM.
- Works offline with **Ollama**, and falls back to a mock generator if Ollama is unavailable.

## Tech stack

- Backend: FastAPI (Python)
- Frontend: HTML/CSS/Vanilla JS
- LLM runtime: local Ollama (`http://localhost:11434`)

## Project structure

- `app.py` - FastAPI app + API routes
- `llm_client.py` - Ollama integration + fallback mock client
- `prompt_parser.py` - system/user prompt templates
- `slide_planner.py` - schema models + validation + template selection
- `layout_engine.py` - deterministic layout rules
- `project_store.py` - local save/load utilities
- `templates/` - UI + template placeholders
- `static/` - styles and frontend logic
- `samples/` - sample JSON output

## Ollama setup

1. Install Ollama (Linux/macOS/Windows):
   - https://ollama.com/download
2. Start Ollama service (if not auto-started):
   ```bash
   ollama serve
   ```
3. Pull a local model (example):
   ```bash
   ollama pull llama3
   ```

You can switch models in the UI (`mistral`, `llama3`, etc.).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open: `http://127.0.0.1:8000`

## Usage flow

1. Enter prompt in left panel.
2. (Optional) Upload an existing `.pptx` in Copilot tab to provide reference context.
3. Click **Generate Deck**.
4. Review slides in center panel.
5. Edit structured fields in right panel.
6. Click **Regenerate Slide** for selected slide.
7. Save/load projects and export JSON.

## Example prompt

> Create a 6-slide deck explaining the order-to-cash process and the target IT solution architecture.

## Notes on architecture decisions

- LLM does **content understanding only**.
- Layout is **rule-based and deterministic** (`layout_engine.py`).
- Backend validates output with Pydantic before sending to UI.
- When Ollama is down, app continues in mock mode for end-to-end usability.
