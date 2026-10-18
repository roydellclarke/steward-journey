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
- `/for-advisors` states that StewardPath takes no commission and runs no deals.
  That claim follows the business model, not the other way round. If the model
  ever earns a referral fee or a share of a transaction, change that page in the
  same commit.
- The discovery path (the three-question read, `/sample`, the moment pages, the
  advisor door) is covered by a browser suite. Run it against the app with
  `cd e2e && npm install && BASE=http://localhost:3000 npm run test:discovery`.
  It needs Chrome on the machine and nothing else: no Stripe keys, no email.
  The report gate check is opt-in, because it needs a project the backend has
  already analyzed. Create one, analyze it, then pass its id:
  `GATE_PROJECT=<project-id> npm run test:discovery`.
