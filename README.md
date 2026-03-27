# Fast Slide Maker (Offline, Ollama-powered)

Local web app focused on a **minimal PowerPoint-like editor first**, with optional AI assistance for slide generation.

## What this app does

- Provides a manual canvas with essential editing controls:
  - Add and edit text boxes
  - Add images
  - Add basic forms/shapes (rectangle, circle, diamond)
  - Change fill, text, and border colors
  - Drag elements to position them on a slide
- Takes a user prompt and can generate a structured presentation plan (optional).
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

1. Build slides manually from the center toolbar (`+ Text`, `+ Rectangle`, `+ Circle`, `+ Diamond`, `+ Image`).
2. Select elements to update text and colors.
3. Drag elements on the canvas to position them.
4. Enter prompt in Copilot tab only if you want AI-generated slides.
5. (Optional) Upload an existing `.pptx` in Copilot tab to provide reference context.
6. Click **Generate Deck** when needed.
7. Save/load projects and export JSON.

## Example prompt

> Create a 6-slide deck explaining the order-to-cash process and the target IT solution architecture.

## Notes on architecture decisions

- LLM does **content understanding only**.
- Layout is **rule-based and deterministic** (`layout_engine.py`).
- Backend validates output with Pydantic before sending to UI.
- When Ollama is down, app continues in mock mode for end-to-end usability.
