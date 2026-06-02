# StewardPath project laws

These are binding for all work in this repo. Follow them every time, without being asked.

## Writing laws (all user-facing copy)

1. **No em-dashes.** Never use "—". Use a comma, a period, or a colon.
2. **Active voice.** "A person reviews your plan", not "your plan is reviewed".
3. **Vary sentence length.** Mix short, punchy lines with longer ones. Never let every sentence run the same length.
4. **Vary paragraph length.** Do not make each paragraph the same number of lines or sentences. Uniform blocks read as machine-generated.
5. **Cut adverbs. Choose strong, concrete words.** Not "jump very high" but "leap", or better, "he cleared six feet". Show the specific, not the intensifier.
6. **No clichés, no AI-tell words.** Banned: "actionable", "leverage" (as a verb), "seamless", "elevate", "unlock", "robust", "delve", "in today's world", "at the end of the day", "game-changer". Prefer plain, owner-facing language.
7. **Plain language for the audience.** Owners are often older and non-technical. No jargon ("SOPs", "operational transferability") in owner-facing text. Define or replace it.
8. **Tone.** Calm, warm, advisor-grade. Never salesy, never alarmist.

## Design laws

1. **Headings fit the line.** A short heading goes on one line on a large screen, two at most on a 15-inch screen. Never wrap a short heading onto three lines. Only break a long heading across lines to rest the reader's eye.
2. **Control whitespace.** Generous but intentional. No large dead gaps between a header bar and the content beneath it.
3. **Modern, legible fonts.** Modern and sleek is the target, never at the cost of legibility or clarity. Use familiar faces where marketing trust demands it.
4. **One design language.** All surfaces consume the shared tokens in `frontend/app/theme.css` (`--sp-*`). Aesthetic: modern luxe minimal. Near-black ink, a single muted sage accent, off-white, hairline borders, whitespace does the work. No AI-cliche purple gradients, no chunky elements.
5. **Branding is consistent.** Logo, header, and footer appear on every page. Data-entry pages carry a visible privacy cue.

## Product laws

1. **Privacy first.** Default-private. Never used to train AI. Owners can export or delete their data anytime. Surface this in the UI, not just the backend.
2. **Preparation only.** Not legal, tax, valuation, investment, or brokerage advice. Route regulated work to humans.
3. **Ground every generated word in the owner's inputs.** Never fabricate figures or facts.
4. **Deterministic-first.** Features work without an LLM; LLM augmentation may only improve wording, never invent.
5. **Migrate, don't discard.** Evolve the intake schema forward by `schemaVersion`; keep existing records.

## Architecture quick reference

- StewardPath = `backend/` (FastAPI, port 8000/8001) + `frontend/` (Next.js, port 3000/3001). The repo also holds a separate "Agent Harness" (`harness/`); StewardPath is the product.
- Shared design tokens: `frontend/app/theme.css`. Chrome (header/footer): `frontend/app/Chrome.jsx`.
- Run backend locally on a free port with a Python 3.12 venv (system Python lacks FastAPI): `uv venv --python 3.12 backend/.venv`.
- Tests: `python -m unittest discover -s backend/tests` (API tests skip without FastAPI).
