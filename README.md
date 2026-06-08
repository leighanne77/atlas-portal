# Atlas — voice-enabled team knowledge base

A small full-stack app demonstrating end-to-end engineering across a
modern AI + cloud stack:

- **FastAPI + React** running on **Google Cloud Run** as a single
  multi-stage container
- **Provider-abstracted LLM layer** with **Google Gemini** as the
  default and **Anthropic Claude** as the swappable alternative —
  both implement the same `LLMProvider` Protocol, so swapping vendors
  is one config change
- **Voice loop** — dictation via **Google Cloud Speech (Chirp 2)**;
  spoken replies via **ElevenLabs TTS**
- **Google OAuth + JWT** for sign-in, **PostgreSQL** on **Cloud SQL**
  for data, **Secret Manager** for credentials, **Alembic** for
  migrations
- Tool-use loop: the LLM calls typed Pydantic-validated tools
  (`search_contacts`, `create_contact`, `update_contact`,
  `delete_contact`, `get_pipeline_summary`) and the chat surface
  renders the results as cards

This is a portfolio cut of a larger internal tool. Real users, real
business names, and real contact data have been removed; the
architecture, code patterns, and test discipline are preserved.

## Architecture

```
 ┌────────────────────────────┐        ┌──────────────────────────┐
 │  React + Vite + Tailwind   │  REST  │  FastAPI (Python 3.11)   │
 │  Dictation button → STT    │ ────▶  │   ↳ /chat   → LLMProvider │
 │  Chat surface + cards      │        │   ↳ /voice  → Chirp/TTS   │
 │  Auto-play TTS reply       │        │   ↳ /auth   → Google OAuth│
 └────────────────────────────┘        │   ↳ /contacts (CRUD)      │
                                       └────────────┬─────────────┘
                                                    │ SQLAlchemy + Alembic
                                                    ▼
                                       ┌──────────────────────────┐
                                       │  PostgreSQL (Cloud SQL)  │
                                       └──────────────────────────┘
```

The LLM seam is in [`app/services/llm/`](app/services/llm/):

- [`base.py`](app/services/llm/base.py) — the `LLMProvider` Protocol
  and shared response shapes (`LLMResponse`, `LLMTextBlock`,
  `LLMToolUseBlock`, `LLMUsage`)
- [`gemini_provider.py`](app/services/llm/gemini_provider.py) — the
  default; converts cross-provider messages and tool definitions into
  Gemini's `generate_content` shape and back
- [`anthropic_provider.py`](app/services/llm/anthropic_provider.py)
  — the alternative; a thin pass-through since Anthropic's wire
  format was the original shape

The chat router in [`app/routers/chat.py`](app/routers/chat.py)
imports `call_llm` from the package and never touches a vendor SDK
directly. The same Protocol pattern is used for the TTS layer in
[`app/services/voice/`](app/services/voice/).

## Local development

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env       # fill in values
docker compose up -d       # local Postgres
alembic upgrade head
python -m scripts.seed_dummy_data
uvicorn app.main:app --reload

# Frontend (in another shell)
cd frontend
npm install
npm run dev
```

## Tests

```bash
pytest           # backend
cd frontend && npm run build   # type-check + Vite build
```

## Deploy

`Dockerfile` is multi-stage (Node 20 → Python 3.11-slim). The
`Makefile` wraps a multi-arch `buildx` push to Artifact Registry and
a `gcloud run services update`. Cloud Run revisions pick up the
new container with no downtime.

## What's NOT in this cut

- A second internal tool that lived alongside this one
- Approval / governance workflow on contact edits
- Sheets/Drive export, Google Tasks integration
- Audit log + admin dashboards
- Cost-alert email job + per-user budget overrides

Those features make sense for a real internal portal but distract
from the architectural story this repo is meant to demonstrate.
