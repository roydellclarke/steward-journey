# StewardPath MVP

StewardPath is an LLM-ready legacy transfer workbench for aging business
owners who want continuity, not just a transaction.

The MVP currently includes:

- owner intake,
- JTBD analysis,
- growth-discovery dashboard,
- Buffett-style business quality lens,
- transfer readiness scoring,
- buyer/successor path comparison,
- roadmap generation,
- owner-facing narrative drafts,
- legal/tax/investment/valuation disclaimers.

## Local Frontend

The first MVP screen is served inside the existing Next app:

```text
http://localhost:3001/mvp
```

## FastAPI Backend

The backend reasoning module is deterministic and local-first:

```bash
uvicorn mvp.stewardpath.backend.main:app --host 127.0.0.1 --port 8090
```

Endpoints:

```text
GET  /health
GET  /sample
POST /analyze
```

## Current Boundary

This is not yet a live LLM product. The MVP uses deterministic reasoning so the
product shape, data schema, and owner-facing experience can be validated before
cloud model behavior is introduced.

Next steps:

- connect the Next screen to the FastAPI `/analyze` endpoint,
- add LLM-backed JTBD interviewing,
- persist owner sessions locally,
- generate downloadable PDF advisor brief,
- add Evaluator browser tests for the MVP route.

