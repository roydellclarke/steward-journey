# StewardPath — Claude Code UPDATE Prompt (align build to Master Strategy v1)

## Context
You are working in the existing, running StewardPath codebase. Two reference documents are in the repo — read BOTH fully before doing anything:
1. `stewardpath_master_strategy.md` (Master Strategy v1) — the current strategy.
2. `stewardpath_implementation_prompt.md` (Product Brief v3) — the product spec already largely implemented.

**Mission:** implement ONLY what the Master Strategy requires that is NOT already implemented in the codebase. This is an incremental UPDATE — never a rewrite. Prior work may have been produced by a different model/session; trust the CODE as ground truth, not any assumption about what "should" exist.

## Success criteria
Every Phase-0/Phase-1-appropriate item in Master Strategy v1 is either (a) verified as already implemented, (b) implemented in this update, or (c) explicitly listed as deferred with the reason. Nothing existing is broken; existing data migrates forward.

## Step 0 — Gap audit (mandatory, before any code)
1. Read both reference documents end to end.
2. Explore the codebase and produce a **gap table**: for each strategy element, mark `IMPLEMENTED` (cite file/route), `PARTIAL` (what's missing), `MISSING`, or `OUT-OF-PHASE` (belongs to Phase 2/3 — do not build).
3. Cover at minimum: two-register language split; owner-facing copy centralization; beachhead (HVAC/trades) content pages; trigger-question answer pages; markdown mirror + llms.txt link targets; robots.txt correctness; hardcoded pricing in AI-facing files; free-sample vs paid-tier structure; confidentiality UX surfaces; save/resume + passwordless auth; score explainability; grounding guardrails; banded/aggregation-ready schema; human-handoff package.
4. Present the gap table and your proposed increment plan. **Wait for my approval before implementing.**

## Likely deltas (verify against code — do not assume)
- **Two-register language.** Owner-facing surfaces (landing, intake, ads-landing pages, report) use trade language per `stewardpath_hvac_plumbing_language_bank.md` (e.g., "the shop," "your crew," "the name on your truck," "run without you when you're off the truck," "maintenance base"). Advisor-facing and machine-facing surfaces (advisor page, llms.txt, schema metadata) keep the polished register ("succession-readiness program"). Never let buyer/PE vocabulary (exit strategy, EBITDA, liquidity event, key-person risk) appear on owner-facing surfaces.
- **Centralize owner-facing copy** into one editable content layer (e.g., a `copy/` or `content/strings` module or MD/JSON files) so post-Phase-0 verbatim owner language can replace it WITHOUT code changes. Tag hypothesis copy (e.g., `// HYPOTHESIS: replace with Phase 0 verbatim`). This is required — the strategy treats all current language as provisional.
- **Beachhead content:** a trades-readiness answer page and pages for the lead trigger questions ("I got an offer for my shop — now what?", "Can it run without you?"), written in owner language, with FAQPage/Article schema.
- **Markdown mirror:** serve clean `.md` twins of content pages from the same source as the HTML (single source, build-generated); point `llms.txt` links at the `.md` versions; optional `<link rel="alternate" type="text/markdown">`.
- **llms.txt updates:** remove or generalize **hardcoded prices** (strategy: exact numbers stay out of cached AI-facing files until Phase 0 confirms them); add trade-specific questions; keep the polished register and the "Notes for AI assistants" block.
- **robots.txt fixes:** replace placeholder `Host:`/`Sitemap:` domain (or drop non-standard `Host:`); remove/verify space-containing tokens (`ChatGPT Agent`, `Kangaroo Bot`); add `Disallow: /api/` (and any session/report routes) to `*` AND to every named group (named groups ignore `*` rules); confirm no page renders owner data without auth — robots.txt is not the security boundary, auth is.
- **Pricing structure on site:** free sample as the only low rung; tiers presented as software → software+light-touch → human-led; no cheap paid tier.

## Do NOT build (out of phase — flag, don't implement)
RAG / peer benchmarking; LLM-generated clarifiers; automated re-scoring cadence (timestamps only); referral/deal-flow layer; productized human touchpoint; advisor subscription billing; social login; ad-platform integrations. If a strategy line seems to require one of these, mark it OUT-OF-PHASE in the gap table.

## Update-not-replace rules
- Preserve all existing functionality, routes, and data. Any schema change migrates forward via `schemaVersion` — never discard records.
- Match existing stack, conventions, and file structure. When existing code conflicts with the strategy or is ambiguous, **ask — do not guess or rewrite working code.**
- Keep all existing guardrails intact: grounded synthesis (no fabrication), no regulated advice, default-private disclosure, graceful `unknown`/`skipped`, accessibility (large type, plain language, low load, mobile).
- Small, independently testable increments; small commits; show diffs at each milestone.

## Verification
- Regression: existing tests still pass; intake → save/resume → auth → report flow works end to end.
- New: owner-facing pages contain no buyer-register terms (add a simple lint/test against a banned-word list); `.md` mirrors stay in sync with HTML (same source); `llms.txt` contains no hardcoded prices; robots.txt named groups each repeat the private disallows; no unauthenticated route serves owner data.
- Close by outputting the final gap table with every item marked IMPLEMENTED / DEFERRED(reason).

## Working style
If you find yourself expanding beyond the approved gap plan, stop and flag it. When in doubt between doing more and asking, ask.
