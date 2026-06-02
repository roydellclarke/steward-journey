# StewardPath Standalone Architecture

Stage 2 extracts StewardPath into independent frontend and backend services.

```text
frontend/
  Next.js UI
  calls FastAPI through NEXT_PUBLIC_API_BASE_URL

backend/
  FastAPI API
  deterministic analysis
  optional Kimi + DeepSeek augmentation
  file-backed project persistence
```

## Local Development

Backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Docker

```bash
docker compose up --build
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:8000`

## Persistence

Backend project data is stored under `STEWARDPATH_DATA_ROOT`.

Default local path:

```text
backend/data/stewardpath/projects/
```

Docker path:

```text
/data/stewardpath/projects/
```

## Product Language Rule

Internal frameworks and source research should stay internal. The owner-facing UI should say things like `What Matters`, `Business Quality`, `Transfer Risks`, and `Successor Fit`, not methodology labels.
