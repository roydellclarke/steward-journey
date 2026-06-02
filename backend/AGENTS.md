# Backend Agent Guide

This folder is the standalone FastAPI backend for StewardPath.

## Purpose

The backend owns analysis, project persistence, analysis history, and future export generation.

## Run

```bash
python3 -m pip install -e backend
uvicorn app.main:app --app-dir backend --reload --port 8000
```

## Structure

- `app/main.py`: FastAPI routes.
- `app/models/`: Pydantic request/response schemas.
- `app/services/`: deterministic and optional LLM reasoning.
- `app/storage/`: file-backed persistence.
- `data/`: local runtime project data, not committed.

## Rules

- Do not expose internal framework/source-material labels in owner-facing responses.
- Do not commit real owner data or API keys.
- Keep storage swappable; file-backed storage should be easy to migrate to SQLite/Postgres later.
- Preserve no-LLM mode.
