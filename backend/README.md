# StewardPath Backend

Standalone FastAPI service for StewardPath project persistence and analysis.

## Run Locally

```bash
cd backend
python3 -m pip install -e .
uvicorn app.main:app --reload --port 8000
```

## Key Endpoints

- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `POST /analyze`
- `GET /projects/{project_id}/analyses`
- `GET /projects/{project_id}/analyses/latest`

## Storage

By default, project files are stored under:

```text
backend/data/stewardpath/projects/
```

Override with:

```bash
export STEWARDPATH_DATA_ROOT=/path/to/data/stewardpath
```
