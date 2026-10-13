# StewardPath — Concierge-Experience UPGRADE Brief (v3)

> **This is an UPGRADE to an existing, running StewardPath system — NOT a greenfield build.**
> Preserve and integrate with what already exists (current readiness scoring, existing outputs, existing data). Augment, do not replace. Where the upgrade introduces a new intake-state schema, **migrate existing records forward via `schemaVersion`** rather than discarding them. Treat every section below as an addition or enhancement layered onto current functionality.
>
> **Build order:** this is a FULL-PRODUCT spec. Ship the MVP subset first (see "MVP Scope & Phased Rollout"); do not build everything before validating trust and willingness to pay.

## Role & objective
You are upgrading **StewardPath**, a private readiness-and-decision-preparation system for founder-led business owners (typically 10–100 employees, often older, non-technical, privacy-sensitive) preparing for a future sale, succession, or ownership transition.

The objective is to make the system **feel like a concierge** — like the owner is being *listened to and accompanied* through a high-stakes, emotional, once-in-a-lifetime decision — while keeping marginal delivery cost near zero. StewardPath is strictly a *preparation* tool. It is **not** a broker, valuation, legal, tax, or investment advisor; route all regulated work to humans.

## North-star principle
Deliver **accompaniment, not an artifact.** The product is the feeling of being heard and guided over time, not a PDF. That feeling is produced by **relevance and recall** — reflecting content back and tying each next step to what the owner already said. Sell a longitudinal *program* (intake → roadmap → re-scoring over time), not a one-time report.

---

## Stakeholders (make every generated output audience-aware)
- **Owner** — primary user; supplies inputs, sets non-negotiables, controls disclosure, consumes outputs.
- **Employees / customers** — protected interests and risk/value factors; never users, but central emotional drivers.
- **Family** — alignment factor, audience for the family-conversation guide, possible successor path.
- **Successors/buyers** (family, employee ownership, MBO, independent, strategic, PE) — counterparties; drive buyer-fit comparison and successor-fit brief.
- **Advisors** (CPA, estate attorney, exit planner, wealth advisor, community bank) — paying segment, output recipient, trust anchor, and referral target.
- **Brokers / deal-flow buyers** — downstream monetization; pay for qualified, prepared seller leads.
- **Operator/concierge** (human) — single trust-anchor touchpoint; small, fixed time per customer.

---

## CRITICAL REQUIREMENTS ADDED IN THIS UPGRADE
Not optional polish. Each is a precondition for the product working; rationale included.

1. **Visible data security & confidentiality (surfaced, not just backend).** The whole funnel depends on the owner sharing highly sensitive data; the top purchase objections are about confidentiality. See "Security & Confidentiality UX Reassurance Points" for the concrete surfaces. No visible trust → no data → no product.
2. **Graceful incompleteness; "I don't know" as a signal.** Never block on missing data or produce garbage scores. Allow `unknown`/`estimated`/`skipped`, keep moving, treat those statuses as readiness gaps that feed the score and roadmap.
3. **Emotional sequencing & drop-off mitigation.** The hardest questions are where this audience abandons. Sequence easy → hard, signpost and reassure before sensitive sections, allow defer-and-return. A conversion mechanism.
4. **Save/resume + durable per-owner longitudinal record.** The "program, not report" model and re-scoring revenue require persistence and snapshots that show change over time.
5. **Score explainability / methodology transparency.** Every score and flagged driver must expose a "why." Advisors won't stake their reputation on a black box; owners won't trust an opaque number.
6. **Hallucination / grounding guardrails on synthesis.** Ground all outputs strictly in the owner's inputs; never fabricate figures or facts; hedge appropriately. Distinct from scope guardrails.
7. **Anonymized-aggregation-ready data design.** The benchmarking moat only exists if the schema supports privacy-preserving aggregation from day one — hence banded values.
8. **Defined human-handoff artifact.** The single human touchpoint must receive a specified, fully-prepped package (see Handoff Spec). Makes the fixed-time, scalable touchpoint real.
9. **Accessibility for an older, non-technical audience.** Large readable type, low cognitive load per screen, plain language, no jargon, mobile-friendly. Materially affects completion.

---

## Security & Confidentiality UX Reassurance Points
(Expands Requirement #1. Confidentiality is the top purchase objection; these surfaces are what make an owner willing to share.)

**Backend (must exist):** encryption in transit (TLS) and at rest; role-based access (least privilege); configurable retention + hard delete on request; explicit stance that owner data is NEVER used to train models; audit log of any access/sharing events.

**UX surfaces (must be visible, plain language — not legalese):**
1. **Pre-intake trust moment:** one short screen before any question — what we collect, why, that it stays private by default, that they control all sharing, that data isn't used to train models, that they can delete anytime.
2. **Just-in-time reassurance at each sensitive ask** (financials, family, employees): one calm line — e.g. "This stays private. You decide later what, if anything, to share — and with whom." Pair with a "why we ask" expander.
3. **Default-private everywhere:** `disclosureControls.defaultVisibility = "private"`. Nothing leaves the system without an explicit owner action.
4. **Explicit employee-exposure assurance** (addresses "I don't want employees to find out"): state plainly that nothing is shared with employees or anyone else unless the owner chooses to.
5. **"Your data" control center:** view what's stored, export it, delete it, revoke any sharing — reachable at all times.
6. **Scope clarity:** persistent plain-language note that StewardPath is preparation only — not legal, tax, valuation, or investment advice — and how the optional human review works.
7. **Microcopy tone:** reassuring and human, never alarming or legalistic. Clear limits paradoxically increase trust.

---

## Intake architecture (core build)
1. **Modality:** a guided, adaptive, progressive-disclosure form — form-forward, NOT a blank chatbot. Provide optional free-text "tell me more" escape hatches. The audience needs a bounded, safe, reassuring flow.
2. **State:** maintain a single **structured intake-state object** (schema below) as the source of truth and pass it into model context. Do NOT use a vector store/RAG to recall within-session answers — the full state fits in context; structured state is more reliable and free.
3. **Adaptivity, built in this order:**
   - a. **Deterministic branching** (rules — see Branching Ruleset) for common paths: the 80/20 of the "listening" feeling.
   - b. **LLM-selected/rephrased clarifiers** for the long tail, constrained to a curated question schema (no unconstrained free-generation).
   - c. **Reflective summary moments** (template below): periodically echo a synthesized read and tie the next question to it. Primary driver of feeling heard; near-zero cost.
4. **Use RAG / semantic vector memory ONLY for large/growing corpora:** (i) peer benchmarking across other owners; (ii) an exit-readiness knowledge base; (iii) retrieval over owner-uploaded documents too large to field-extract. Never for within-session recall.

---

## Intake-State Schema
Illustrative TypeScript-style types (use any stack). Every owner-supplied value uses the `Field<T>` wrapper so incompleteness, estimates, re-scoring, and change-over-time are handled uniformly.

```typescript
type FieldStatus =
  | "answered"
  | "estimated"          // owner gave a rough figure
  | "unknown"            // SIGNAL: a readiness/documentation gap, not an error
  | "skipped"            // SIGNAL: deferred; surface for return
  | "pending_document";  // awaiting an upload to confirm

interface Field<T> {
  value: T | null;
  status: FieldStatus;
  confidence?: "low" | "medium" | "high";
  updatedAt: string;     // ISO 8601 — enables change-over-time views
  note?: string;         // free-text "tell me more" escape hatch
}

type Visibility = "private" | "advisor_shareable" | "buyer_shareable_when_vetted";
type RevenueBand = "<250k" | "250k-1m" | "1m-5m" | "5m-20m" | "20m+";
type EmployeeBand = "1-9" | "10-25" | "26-50" | "51-100" | "100+";
type AgeBand = "under_50" | "50-59" | "60-69" | "70+" | "prefer_not";
type SuccessorPath =
  | "family_transfer" | "employee_ownership" | "management_buyout"
  | "independent_buyer" | "strategic_buyer" | "private_equity";

interface IntakeState {
  meta: {
    ownerRecordId: string;
    schemaVersion: number;          // for migrating existing records on upgrade
    createdAt: string;
    updatedAt: string;
    completionPct: number;          // drives save/resume UX
    lastSection?: string;           // where to resume
    snapshots: Array<{ takenAt: string; readinessScore: number }>; // change-over-time
  };

  // Banded for confidentiality AND anonymized aggregation/benchmarking
  business: {
    category: Field<string>;         // service / specialty mfg / trade / family / prof services / distribution / niche B2B
    industry: Field<string>;
    region: Field<string>;           // region, NOT street address
    yearsOperating: Field<number>;
    employeeBand: Field<EmployeeBand>;
    revenueBand: Field<RevenueBand>;
    customerConcentration: Field<"diversified" | "moderate" | "high_few_clients">;
  };

  owner: {
    isFounder: Field<boolean>;
    role: Field<string>;
    ageBand: Field<AgeBand>;         // sensitive; optional
    identityTiedToBusiness: Field<1 | 2 | 3 | 4 | 5>; // 5 = strongly
  };

  financialClarity: {
    booksUpToDate: Field<boolean>;
    financialsDocumented: Field<boolean>;
    revenueTrend: Field<"declining" | "flat" | "growing">;
    profitabilityClear: Field<boolean>;
    ownerCompNormalized: Field<boolean>;
  };

  operationalTransferability: {
    functionsDependentOnOwner: Field<string[]>;   // e.g., ["sales","key relationships"]
    keyPersonRisk: Field<"low" | "medium" | "high">;
    managementDepth: Field<"none" | "thin" | "solid">;
    systemsDocumented: Field<boolean>;
  };

  processDocumentation: {
    sopsExist: Field<boolean>;
    documentedAreas: Field<string[]>;
    tribalKnowledgeRisk: Field<"low" | "medium" | "high">;
  };

  familyAlignment: {
    familyInBusiness: Field<boolean>;
    expectationsKnown: Field<boolean>;
    alignmentLevel: Field<"unknown" | "misaligned" | "partial" | "aligned">;
    conflictRisk: Field<"low" | "medium" | "high">;
  };

  emotionalReadiness: {
    primaryMotivation: Field<string>;             // retire / health / step back / etc.
    urgencyDrivers: Field<string[]>;              // health, age, timing, fatigue
    readinessToLetGo: Field<1 | 2 | 3 | 4 | 5>;
    topConcerns: Field<string[]>;                 // free-list of fears
  };

  protectedInterests: {
    employeeConcerns: Field<string[]>;            // "jobs kept", "culture", etc.
    customerContinuityConcerns: Field<string[]>;
  };

  successorPreferences: {
    acceptablePaths: Field<SuccessorPath[]>;
    unacceptablePaths: Field<SuccessorPath[]>;
    idealBuyerTraits: Field<string[]>;
    dealbreakers: Field<string[]>;
  };

  nonNegotiables: Field<string[]>;                // "must protect" items

  // Per-section disclosure; optional per-field override map
  disclosureControls: {
    defaultVisibility: Visibility;                // default "private"
    sectionOverrides: Record<string, Visibility>;
    fieldOverrides?: Record<string, Visibility>;
  };

  uploads: Array<{
    id: string;
    label: string;
    status: "pending" | "extracted" | "needs_review";
    // store references/derived facts, NOT raw sensitive docs, in state
  }>;

  // SYSTEM-GENERATED (not user input) — kept explainable
  derived?: {
    readinessScore: number;
    driverScores: Record<string, number>;         // the five drivers
    scoreRationale: Record<string, string>;        // "why" per driver — REQUIRED for transparency
    flaggedGaps: string[];
    benchmarkCohort?: string;                      // anonymized peer group
  };
}
```

---

## Reflective-Summary Prompt Template
The highest-leverage component for the concierge feel. Invoke after each major section or every few answers.

```
SYSTEM:
You are the reflective voice of StewardPath. Your only job in this turn is to make the
owner feel genuinely heard and to gently bridge to what comes next. You are NOT giving
legal, tax, valuation, or investment advice.

INPUTS:
- intake_state_slice: {{ relevant portion of the structured IntakeState }}
- next_question: {{ the question the system intends to ask next }}

RULES:
- Reflect back SPECIFICS the owner actually gave, in their own framing. Name concrete
  details (business type, employee count band, the gap or concern they raised).
- Ground everything strictly in intake_state_slice. Do NOT invent facts, numbers, or
  implications. If something is "unknown" or "skipped", treat it as a normal, acceptable
  gap — never imply fault.
- Where the content is emotionally weighty (succession, family, letting go, employees'
  futures), briefly and warmly acknowledge that weight before bridging. Do not be
  falsely cheerful or salesy.
- Then bridge naturally to next_question, framing it as a logical next step given what
  they just shared.
- Plain language, no jargon. Calm, respectful, unhurried. SHORT — a few sentences, not
  a wall of text. This is a concierge murmur, not a report.

OUTPUT:
A short reflection (1 short paragraph) + the bridge to next_question.
```

**Worked example**

*Input state slice:* family specialty-manufacturing business, `employeeBand: "26-50"`, `sopsExist: false`, `familyInBusiness: true`, `alignmentLevel: "partial"`, `topConcerns: ["what happens to my long-time employees"]`.
*Next question:* "Which parts of the day-to-day depend specifically on you?"

*Target output:*
> "So I'm hearing a family manufacturing business you've built up to around 30–50 people, where a lot still lives in your head rather than written down — and that what weighs on you most is your long-time employees being looked after. That care comes through, and it's exactly the kind of thing worth protecting before any conversation with a buyer. With that in mind, it helps to get specific about where the business leans on you personally — which parts of the day-to-day depend specifically on you right now?"

---

## Branching Ruleset (deterministic layer — the 80/20 of "listening")
Rules reference `IntakeState` fields. `unknown`/`skipped` are signals, never blockers. Trigger a reflective-summary moment after each major section and before emotionally heavy ones.

**Confidentiality gating**
- BEFORE any `financialClarity` or `familyAlignment` question → show the relevant Security/Confidentiality reassurance.

**Family & succession**
- IF `business.category == "family"` OR `familyAlignment.familyInBusiness == true` → enable full `familyAlignment` section; add clarifier: is a family member a successor candidate?
- IF `familyInBusiness == false` → collapse family-successor drill-down, but still ask `familyAlignment.expectationsKnown` (family may hold expectations regardless).
- IF `successorPreferences.acceptablePaths` includes `"employee_ownership"` → add clarifier: could employees realistically finance a purchase?

**Operational / owner-dependency**
- IF `processDocumentation.sopsExist == false` → set `tribalKnowledgeRisk` hint "high"; ask `operationalTransferability.functionsDependentOnOwner`.
- IF `operationalTransferability.managementDepth == "none"` → set `keyPersonRisk` "high"; clarifier: who runs the business if you're out for a month?
- IF `functionsDependentOnOwner` includes `"sales"` OR `"key relationships"` → clarifier on relationship transferability.

**Financial (never request exact figures — bands + presence only)**
- IF `financialClarity.booksUpToDate == false` OR `financialsDocumented == false` → record financial-clarity gap; gentle clarifier: is a bookkeeper or CPA involved? Do NOT ask for precise numbers.
- IF `business.revenueBand` in {`"5m-20m"`,`"20m+"`} AND `financialsDocumented == false` → raise this gap's priority in the roadmap.

**Emotional pacing**
- BEFORE `emotionalReadiness` and `familyAlignment` → trigger reassurance + reflection; do not front-load these.
- IF `emotionalReadiness.readinessToLetGo <= 2` → soften tone; surface "you don't need to be ready to sell"; never push timing.
- IF `emotionalReadiness.urgencyDrivers` includes `"health"` → handle with extra care; surface the human touchpoint earlier.

**Incompleteness & session**
- IF any `Field.status` in {`"unknown"`,`"skipped"`} → add to `flaggedGaps` candidates; offer optional revisit at the end; never block.
- IF session ends with `completionPct < 100` → persist + enable resume from `meta.lastSection`.

**Successor weighting & routing**
- IF `successorPreferences.unacceptablePaths` non-empty → exclude/down-weight those paths in buyer-fit; reflect the exclusion back to the owner.
- IF `derived.readinessScore < threshold` AND `urgencyDrivers` present → surface human touchpoint.
- IF `derived.readinessScore >= threshold` → surface warm-handoff / referral.

---

## Synthesis Prompts
All synthesis is grounded strictly in `IntakeState`. Never fabricate facts or figures. Not legal/tax/valuation/investment advice. Frame as considerations, not recommendations.

### 1. Score Rationale (explainability — REQUIRED)
```
SYSTEM:
You explain StewardPath's readiness score in plain language. For each of the five drivers
(financial clarity, operational transferability, process documentation, family alignment,
emotional readiness), state in 1–2 sentences WHY it scored where it did, citing the owner's
actual inputs. Treat "unknown"/"skipped" answers as gaps to note, never as faults. Then list
the top 3 gaps and, for each, the single most useful next step. Do not invent data. Do not
give regulated advice.
INPUTS: derived.driverScores, derived.readinessScore, the underlying IntakeState fields.
OUTPUT: per-driver rationale (grounded in specific inputs) + top 3 gaps with one next step each.
```

### 2. Buyer-Fit Comparison
```
SYSTEM:
You compare the six possible paths (family transfer, employee ownership, management buyout,
independent buyer, strategic buyer, private equity) for THIS owner. For each path, give a
short, balanced read of how it fits the owner's STATED priorities and protected interests —
effect on employees, customers, family, control, and legacy. Exclude or down-weight any path
in successorPreferences.unacceptablePaths and say why. This is NOT financial advice and NOT a
valuation; frame everything as considerations to weigh, hedged appropriately. Ground every
claim in the owner's inputs; do not assert facts about specific buyers.
INPUTS: business.*, protectedInterests.*, successorPreferences.*, nonNegotiables, familyAlignment.*.
OUTPUT: for each (non-excluded) path — a fit summary tied to the owner's priorities, with the
main trade-off named.
```

### 3. Successor-Fit Brief
```
SYSTEM:
You write a concise brief describing the kind of buyer or successor that would be acceptable
to this owner, in the owner's own priorities and voice. Draw only from idealBuyerTraits,
dealbreakers, nonNegotiables, and protectedInterests. Keep it short enough to share with an
advisor. No regulated advice; no fabricated detail.
INPUTS: successorPreferences.idealBuyerTraits, successorPreferences.dealbreakers,
nonNegotiables, protectedInterests.*.
OUTPUT: a short (4–8 sentence) successor-fit brief — what "a good fit" looks like and the
explicit dealbreakers.
```

---

## Feature set (mapped to the value model)
- Adaptive intake + reflection layer (above).
- **Synthesis layer:** personalized narrative read-back; readiness score + the five drivers WITH per-driver rationale; business-quality view; buyer-fit comparison; successor-fit brief. All grounded in inputs; no fabrication.
- **Privacy controls:** default-private; owner controls what is revealed and to whom; surface "what to keep private until buyer fit is proven"; show security reassurance at each sensitive ask.
- **Longitudinal program:** staged action roadmap, periodic re-scoring, progress/change-over-time tracking, gentle non-rushed follow-up cadence, save/resume.
- **Single human-touchpoint hook:** a scheduled "readiness review" slot where the AI hands a fully-prepped package to a human; human time per customer stays small and fixed.
- **Warm-handoff / referral layer:** when a readiness threshold is met, route the qualified owner to vetted advisors/brokers and capture deal-flow value.
- **Outputs:** copyable advisor-ready summary, family-conversation guide, downloadable readiness card.

## Human-Touchpoint Handoff Spec
When an owner books the human review, the system generates a single prep package containing:
1. Readiness score + per-driver scores and rationale.
2. Top 3 flagged gaps and the owner's stated non-negotiables.
3. The owner's stated concerns and emotional drivers (so the human leads with empathy).
4. Disclosure settings (what the owner has/hasn't agreed to share).
5. Suggested talking points and the 2–3 highest-impact next steps.
Keeps the human's prep time fixed and perceived attention high.

## Guardrails
- Not legal/tax/valuation/investment advice; route regulated work to humans.
- Ground all generated content in owner inputs; no fabricated facts or figures.
- Calm, respectful, non-rushed tone; reduce overwhelm at every step.
- Bounded, reassuring, accessible UX for a non-technical, privacy-sensitive, often older audience.

## JTBD alignment hooks (keep later marketing language consistent with these)
- Reflection layer → "feel heard / less alone."
- Security + privacy controls → "less exposed / in control of what's shared."
- Staged roadmap + re-scoring → "less overwhelmed / more in control."
- Score explainability + advisor-ready summary → "more confident, prepared before advisor conversations."
- Single human touchpoint → "supported, not abandoned to software."
- Peer benchmarking → "I can see where I stand."

---

## MVP Scope & Phased Rollout
This brief is a FULL-PRODUCT spec. Do NOT build all of it before validating that owners will share sensitive data and pay. Sequence by riskiest assumption first (**trust + willingness to pay**).

**MVP non-negotiables (cutting any invalidates the test):**
- Security/Confidentiality UX (precondition for any data at all).
- Adaptive intake with the deterministic Branching Ruleset + Reflective-Summary moments (the core "listening" value being tested).
- Save/resume (or owners won't finish a long intake).
- Score + Score-Rationale + two outputs: advisor-ready summary and readiness card.
- Graceful incompleteness (`unknown`/`skipped` handled).
- Hallucination/grounding guardrails (cutting this causes real harm, not just fewer features).

**Defer past MVP:**
- RAG / peer benchmarking (chicken-and-egg: needs data volume you won't have yet).
- LLM-generated clarifiers (start rules-only; add later).
- Full longitudinal re-scoring cadence (capture timestamps now via `Field<T>`; productize later).
- Referral / deal-flow layer (monetization layer 2 — needs a pool of prepared owners first).
- Productized/automated human touchpoint (deliver it by hand early to learn).
- Full six-path buyer-fit (a simplified subset is fine to start).

**Suggested phases:**
- **Phase 0 — Concierge-by-hand (Wizard-of-Oz):** manually deliver the experience to ~5–10 design-partner owners. Validate perceived value + willingness to pay BEFORE heavy build.
- **Phase 1 — Self-serve MVP:** the non-negotiables above, rules-only adaptivity. Measure intake completion, perceived value, and payment.
- **Phase 2 — Program:** longitudinal re-scoring, LLM clarifiers, productized human touchpoint.
- **Phase 3 — Moat & channel:** benchmarking (RAG, once data exists), advisor channel, referral/deal-flow layer.

---

## Deliverables expected from the implementing agent
(Several are drafted in this brief — finalize and wire them against the existing system.)
1. The structured intake-state schema, reconciled with the existing data model (+ migration plan from current records via `schemaVersion`).
2. The Branching Ruleset, wired to the live intake flow.
3. The constrained clarifier question bank/schema for the (Phase 2) LLM layer.
4. The Reflective-Summary prompt template, wired to live state.
5. The three Synthesis prompts (score rationale, buyer-fit, successor-fit), grounded and tested for no-fabrication.
6. The Security/Confidentiality implementation + UX reassurance surfaces.
7. Save/resume + longitudinal snapshot implementation.
8. The human-handoff package generator.
9. Clear documentation of where RAG is and is not used.
