# StewardPath, investor brief

> Grounded in what is built in this repository. Market sizing, traction, and financials are placeholders for the founder to fill with sourced numbers. Nothing here invents figures.

## Elevator (about 130 words)

StewardPath is a private, guided readiness program for founder-led and family business owners preparing a sale, succession, or transition. It walks the owner through the decision before a broker or buyer frames it: what they could lose, what to fix first, and which kind of owner would carry the business forward. The owner gets a readiness score across five plain areas, each with its reasoning, plus briefs they can hand to an advisor or family. A real person stays with them, and the owner controls what is ever shared. It is preparation, not advice, and it routes regulated work to humans. The model is a program the owner returns to, with a score that moves as they prepare, so the data and the trust compound over time.

## The problem

Owners of founder-led businesses are unprepared for the largest financial event of their lives. They often have no clear successor, real fear of the wrong buyer, books that are not ready, and knowledge that lives only in their head. Brokers and buyers frame the deal first, and the owner reacts. Advisors get a partial picture late and bill for the cleanup. The owner is frequently older, non-technical, and emotionally invested in people, customers, and a name they refuse to see harmed.

## The product, in full

**Guided, adaptive intake.** A deterministic question bank drives a branching interview that adapts to the owner. Easy questions first, sensitive ones later with a word of reassurance before each. "I don't know" and "skip" are valid answers. After each section, a reflective summary plays back what was shared.

**A readiness score the owner can read.** One number out of 100 across five plain dimensions: financial clarity, how well the business runs without the owner, what is written down, family alignment, and readiness to step back. Every dimension shows its reasoning, grounded only in the owner's inputs.

**Decisions, not just a report.** It names what must be protected, weighs successor paths against the owner's values, lets them rule out paths they would never accept, and produces briefs for an advisor or family.

**A program, not a one-time deliverable.** Answers persist in a versioned record that migrates forward. Readiness snapshots accrue, so the score moves as the owner prepares. This is the relationship the owner returns to, and where the data compounds.

**Privacy as the product.** Default-private. Never shared unless the owner chooses, never used to train AI. Field-level and section-level disclosure controls. Export or delete anytime. An append-only audit log records access, sharing, and deletion with no sensitive payload.

**Deterministic first, AI for wording only.** Scoring, branching, and synthesis run without any model. Optional model augmentation may only improve phrasing, never invent a figure. Output stays trustworthy and auditable.

**Passwordless access built for the audience.** One-time email code (primary) or magic link (fallback). Two gates: save-and-resume, and viewing the report. Signed HttpOnly sessions, per-owner data, access enforced on every route, rate limits per email and per IP, single-use tokens, and no account-existence disclosure.

**A human in the loop.** Not legal, tax, valuation, investment, or brokerage advice. The owner books a private review in one click, and the system packages everything they prepared for the human who picks it up.

**An advisor channel.** Pricing already supports CPAs, exit planners, and advisors guiding multiple owner clients, so each client arrives prepared. A B2B2C path on top of direct-to-owner.

**Discoverable to search and AI.** Public pages ship robots.txt that welcomes AI crawlers, an llms.txt summary, a sitemap, and structured data. The private app and owner data stay out of every index.

## Business model (as configured)

| Tier | Price | What it is |
| --- | --- | --- |
| Sample report | Free | Shows the questions, the score, and the plan. Top of funnel. |
| Owner readiness report | $249 | The owner's private readiness, with the reasoning behind every score. |
| Concierge package | $1,500 | Guided intake plus a private review with a real person. |
| Advisor pilot | $199/mo | For CPAs, exit planners, and advisors guiding up to ten owner clients. |

A self-serve entry, a one-time owner purchase, a high-touch tier, and recurring B2B revenue. Conversion, ACV, and CAC are to be validated with live data.

## Why it is defensible

- **Compounding private data.** The longitudinal, per-owner record gets richer each visit and never leaves the owner's control. Switching cost rises as history and plan accumulate.
- **Trust as a moat.** For this audience, privacy and a real person are the purchase. The architecture enforces both, not just the marketing.
- **Grounded output.** Deterministic scoring plus AI-for-wording-only avoids the hallucination risk that would sink a finance-adjacent tool with skeptical users.
- **Two-sided distribution.** Direct-to-owner plus an advisor channel that brings owners in already prepared.

## Technical foundation

- Backend: FastAPI (Python), file-backed per-owner records plus SQLite for auth and sessions, an append-only audit log, a versioned intake schema with forward migration.
- Frontend: Next.js, a modern-luxe design system on shared tokens, mobile-friendly and accessible.
- Email: Resend or Postmark, with a no-send development mode.
- Packaging: Dockerized services, environment-driven configuration, a backend test suite covering intake logic, scoring, and the full auth surface, with an adversarial security review already folded in.
- Security: per-owner authorization on every data route, hashed secrets, single-use tokens, rate limits, an ops endpoint behind a token, and a fail-fast guard against running production on an insecure key.

## Status (honest cut)

Built and working today: the guided intake, scoring, synthesis and briefs, the longitudinal record, privacy and data-control features, passwordless auth with enforced per-owner access, real transactional email, owner payments through Stripe Checkout across all four tiers, the marketing site, and search/AI discoverability. The product demos end to end on a real email, including a test-mode purchase.

Not yet in place, and worth naming: a registered domain and production deploy, live payment keys in place of test keys, the staffing model behind the human review, and live traction.

## Slide outline (for a deck)

1. Title: StewardPath, the handoff on your terms.
2. Problem: the unprepared owner and the reactive sale.
3. Why now: a large wave of owner transitions, and buyers starting research inside AI assistants. (Add sourced figures.)
4. Product: the guided check, the score, the briefs, demo screenshot.
5. The program: score that moves over time, the data that compounds.
6. Trust and privacy: the moat, shown in the UI.
7. Business model: the four tiers and the advisor channel.
8. Go-to-market: direct-to-owner plus advisors, plus AI and search discoverability.
9. Defensibility: private compounding data, grounded output, two-sided distribution.
10. Team and ask. (To be completed.)
11. Traction and metrics. (To be completed with live numbers.)

## What this brief does not claim

Market size, the count of retiring owners, win rates, and any traction or revenue figures. Those are real and important, and they are the founder's to source. This document describes only what the product does and how it is built.
