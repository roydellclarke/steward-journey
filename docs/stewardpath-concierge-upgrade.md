# StewardPath Concierge-Experience Upgrade (v3 brief / schema v4)

This documents the upgrade layered onto the running StewardPath system. It is
**additive** — every existing endpoint, page, and data file keeps working.

## What shipped (MVP non-negotiables)

| Requirement | Where |
|---|---|
| Visible security & confidentiality UX | Pre-intake trust screen + per-section reassurance (`frontend/app/intake/page.jsx`, `app/intake/questions.py` `SECTION_REASSURANCE`) |
| Graceful incompleteness (`unknown`/`skipped`) | `Field.status` signals; never block (`app/storage/intake_state.py`, branching) |
| Emotional sequencing & drop-off mitigation | `SECTION_ORDER`, security gating, reflective moments, tone flags (`app/intake/branching.py`) |
| Save/resume + longitudinal record | Durable `intake_state.json`, `meta.snapshots`, `localStorage` resume |
| Score explainability | `app/services/scoring.py` `scoreRationale` per driver, "Why?" expanders in report |
| Hallucination / grounding guardrails | Deterministic-first synthesis; LLM may only reword narratives under a strict grounding prompt (`app/services/synthesis.py`) |
| Anonymized-aggregation-ready | Banded values (`RevenueBand`, `EmployeeBand`, `AgeBand`) in the schema |
| Human-handoff artifact | `app/intake/handoff.py` → `GET /projects/{id}/handoff` |
| Accessibility | Large type, low cognitive load, plain language (`frontend/app/intake/intake.css`) |

## Schema migration (lossless)

`INTAKE_SCHEMA_VERSION = 4`. `migrate_profile_to_intake_state` preserves every
answered field from existing v3 records and only fills missing structure; it is
idempotent. Records are migrated forward on every read in `ProjectStore`.

## New API surface (all additive)

- `GET  /intake/questions` — curated question bank + reassurance copy
- `POST /intake/plan` — deterministic adaptive plan (next question, gates, routing)
- `POST /intake/reflect` — grounded reflective-summary moment
- `POST /intake/score` — grounded score + rationale + full synthesis
- `GET/PUT /projects/{id}/intake` — durable intake state (PUT merges a patch)
- `POST /projects/{id}/intake/analyze` — score + synthesize + save (+ snapshot)
- `GET  /projects/{id}/handoff` — human-review prep package
- `POST /projects/{id}/book-review` — book the single human touchpoint
- `GET  /projects/{id}/snapshots` — change-over-time
- `GET  /projects/{id}/export`, `DELETE /projects/{id}` — "your data" controls

Existing `/analyze`, `/projects`, `/leads` are unchanged (they now also accept an
optional `intakeState` but ignore it if absent).

## Where RAG / semantic vector memory IS and IS NOT used

**NOT used (by design):** within-session recall. The entire `IntakeState` fits in
context and is passed to the model directly as structured state. This is more
reliable and free — see `reflection.py` / `synthesis.py`, which read fields, not a
vector store. There is **no RAG anywhere in the current MVP.**

**Reserved for later phases only** (not built yet): RAG / semantic memory is
appropriate solely for large/growing corpora —
1. peer benchmarking across many owners (Phase 3, needs data volume first),
2. an exit-readiness knowledge base,
3. retrieval over owner-uploaded documents too large to field-extract (the
   `uploads[]` slot exists in the schema but document extraction is deferred).

If/when added, RAG must stay outside the within-session intake loop.

## Phasing

Shipped: Phase 1 self-serve MVP (rules-only adaptivity, deterministic synthesis,
optional LLM rewording). Deferred per the brief: LLM-generated clarifiers (bank
exists, selection layer is Phase 2), productized re-scoring cadence (timestamps +
snapshots are already captured), referral/deal-flow, automated human touchpoint,
peer benchmarking (RAG).

## Tests

`backend/tests/test_intake_upgrade.py` — 25 tests (schema lossless/idempotent,
branching rules, grounded scoring/synthesis, no-fabrication, reflection, handoff,
storage, and a FastAPI lifecycle suite that auto-skips when FastAPI is absent so
the offline harness env stays green).
