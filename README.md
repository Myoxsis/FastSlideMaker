# Fast Slide Maker

Fast Slide Maker is a slide-generation agent scaffold with a FastAPI backend and a lightweight HTML/CSS/JS frontend.

## What is included

- Modular Python package layout under `app/`
- Pipeline stages with clear boundaries:
  - `generation` (LLM or mock)
  - `validation`
  - `rendering`
  - `export`
- Ollama configuration module with environment overrides
- Mock mode fallback when Ollama is unavailable
- Deterministic mock scenarios with canned prompts and sample JSON outputs
- Static frontend and Jinja template
- Sample JSON request/response files
- Placeholder unit/integration test structure

## Quickstart

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

Optional `.env` file:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TEMPERATURE=0.4
OLLAMA_TOP_P=0.9
OLLAMA_MAX_TOKENS=1200
ENABLE_MOCK_MODE=true
REQUEST_TIMEOUT_SECONDS=20
```

Mock mode examples endpoint:

```bash
curl http://127.0.0.1:8000/api/mock-mode/examples
```

### 3) Run the app

```bash
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000

### 4) Run tests

```bash
pytest
```

## Project layout

```text
app/
  api/routes.py
  core/config.py
  core/startup.py
  models/schemas.py
  services/generation.py
  services/validation.py
  services/rendering.py
  services/export.py
templates/index.html
static/css/styles.css
static/js/app.js
samples/*.json
tests/unit/*.py
tests/integration/*.py
```
