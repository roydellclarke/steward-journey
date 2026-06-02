# Frontend Agent Guide

This folder is the standalone Next.js frontend for StewardPath.

## Purpose

The frontend owns the owner/advisor user experience. It calls the FastAPI backend through `NEXT_PUBLIC_API_BASE_URL`.

## Run

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Structure

- `app/page.jsx`: main StewardPath workbench.
- `app/styles.css`: product styling.
- `lib/api.js`: backend API client and profile mapping.

## Rules

- Keep owner-facing labels plain. Do not expose internal framework names or research-source labels.
- Preserve project persistence controls and analysis history.
- Do not put durable business logic or file persistence in the frontend.
