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

## Passwordless email auth

Owners never set a password. They prove control of an email with a one-time code (primary) or a magic link in the same email (fallback). Two gates in the intake flow trigger it: saving to resume later, and opening the readiness report. On the first successful sign-in, the in-progress (anonymous) intake project is tied to a durable per-owner record, and the browser gets an HttpOnly session cookie.

Auth state (owners, sign-in challenges, sessions) lives in a small SQLite database, separate from the file-based project data. Codes, tokens, and session ids are stored only as keyed HMAC digests. Single-use is enforced atomically. Requests are rate-limited per email and per IP, and the request response is uniform so it never reveals whether an email exists.

Configure it with these variables (see `.env.example`):

```text
STEWARDPATH_SECRET_KEY        # signs sessions + links; generate a strong value in prod
STEWARDPATH_FRONTEND_ORIGIN   # exact browser origin; CORS + magic-link base URL
STEWARDPATH_AUTH_DB_PATH      # defaults to STEWARDPATH_DATA_ROOT/auth/auth.db
STEWARDPATH_OTP_TTL_MINUTES   # code / link lifetime, default 10
STEWARDPATH_COOKIE_SECURE     # true in prod (HTTPS); false for local http dev
STEWARDPATH_POSTMARK_TOKEN    # Postmark server token; omit to record emails in memory
STEWARDPATH_POSTMARK_FROM     # verified Postmark sender address
```

Without a Postmark token and sender, sign-in emails are kept in memory only, so local dev and tests never send real mail. In production, set both, point `STEWARDPATH_FRONTEND_ORIGIN` at your real frontend URL, set `STEWARDPATH_COOKIE_SECURE=true`, and serve over HTTPS.

## Discoverability (SEO and LLMs)

The public marketing pages are built to be found by search engines and AI assistants, while the sign-in flow and per-owner data stay out of every index.

- `app/robots.js` serves `/robots.txt`: it welcomes search and AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot and anthropic-ai, Google-Extended and Gemini, PerplexityBot, Bingbot, Applebot, Meta-ExternalAgent and FacebookBot, Amazonbot, CCBot, cohere-ai, MistralAI, DeepSeekBot, Bytespider, and more) to public pages, and disallows `/auth/` for every one of them. Unlisted crawlers are covered by the `*` rule.
- `app/sitemap.js` serves `/sitemap.xml` with the public pages.
- `app/llms.txt/route.js` serves `/llms.txt` (the llmstxt.org format): a plain-Markdown summary of what StewardPath is, its pages, and notes for AI assistants (it is preparation, not advice; owner data is private and not for training).
- `app/layout.jsx` carries full metadata (Open Graph, Twitter, canonical, robots) and JSON-LD structured data (Organization, WebSite, Service with pricing offers, and a short FAQ), grounded only in public content.

All of these use `NEXT_PUBLIC_SITE_URL` for absolute links, so set it to the real registered domain in production. Nothing here exposes owner intake data: those routes are client-rendered and behind the session, and the API enforces per-owner access.

## Product Language Rule

Internal frameworks and source research should stay internal. The owner-facing UI should say things like `What Matters`, `Business Quality`, `Transfer Risks`, and `Successor Fit`, not methodology labels.
