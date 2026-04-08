# FastSlideMaker

FastSlideMaker is a local-first app that generates business-quality slides from prompts for process and IT solution design use cases.

## Core design

- Uses an LLM (Ollama) to generate **semantic JSON**.
- Semantic JSON is the **source of truth**.
- Frontend renders deterministic HTML previews from JSON.
- Exporter maps JSON to **native editable PPTX objects** (text boxes, shapes, connectors).
- No screenshot-based export and no arbitrary HTML-to-PPT conversion.

## Stack

- Backend: FastAPI + Python
- Frontend: HTML/CSS/vanilla JS
- LLM: local Ollama HTTP endpoint (`http://localhost:11434`)
- Export: `python-pptx`

## Required modules implemented

- `request_interpreter.py`
- `deck_planner.py`
- `slide_generator.py`
- `llm_client.py`
- `schema.py`
- `validator.py`
- `layout_engine.py`
- `pptx_exporter.py`
- `project_store.py`
- `app.py`
- `templates/`
- `static/`
- `samples/`

## Supported slide types

- `executive_summary`
- `process_flow`
- `swimlane`
- `current_vs_target`
- `layered_architecture`
- `integration_map`
- `roadmap`
- `issue_implication_recommendation`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

## Typical flow

1. Enter prompt (e.g., "Create a 5-slide deck explaining the lead-to-cash process and the target solution architecture").
2. Backend interprets request and builds a deck plan.
3. LLM generates semantic JSON (or mock fallback if Ollama is unavailable).
4. Validator normalizes JSON to schema.
5. UI renders HTML previews.
6. Export endpoint generates editable PPTX.

## API endpoints

- `POST /api/generate` - generate and save deck
- `GET /api/projects` - list projects
- `GET /api/projects/{project_id}` - fetch project JSON
- `GET /api/projects/{project_id}/preview` - deterministic preview view model
- `GET /api/projects/{project_id}/export` - download PPTX

## Samples

- Prompt examples: `samples/sample_prompts.txt`
- Example semantic JSON: `samples/sample_generated_deck.json`
- Saved projects and exports are written under `samples/projects/` and `samples/exports/`

## Notes

- The LLM does not control coordinates.
- Layout and export are deterministic and template-driven.
- Template-rich rendering is implemented for:
  - `process_flow`
  - `layered_architecture`
  - `roadmap`
