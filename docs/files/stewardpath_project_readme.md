# StewardPath — Project Knowledge Base (README / index)

This Project is the **strategy and thinking** workspace for StewardPath. The code lives in a separate Git repo; this is not a build environment. The files below are the current source of truth for the business.

## Source-of-truth hierarchy
1. **`stewardpath_master_strategy.md`** — the top-level strategy. If any other doc conflicts with it, this wins. Everything tagged *(hypothesis)* here is pending Phase 0 validation.
2. **`stewardpath_implementation_prompt.md`** — the product/build spec (v3). Authoritative for how the product works.
3. Everything else — supporting detail under those two.

## What each file is

**Strategy & validation (living — update these as you learn)**
- `stewardpath_master_strategy.md` — consolidated grand strategy; the map.
- `stewardpath_beachhead_decision.md` — chosen beachhead: founder-led HVAC/plumbing/trades, 55+, offer-triggered, national.
- `stewardpath_phase0_test_plan.md` — the validation gate: hypotheses H1–H4, thresholds, go/pivot/stop rule.

**Customer discovery (bring to conversations; feed findings back)**
- `stewardpath_jtbd_interview_guide.md` — current-owner interview guide.
- `stewardpath_jtbd_interview_guide_past_sellers.md` — past-seller guide (mine triggers + verbatim language).

**Language & marketing (replace copy with verbatim owner language post-Phase 0)**
- `stewardpath_hvac_plumbing_language_bank.md` — trade vocabulary; the two-register rule.
- `stewardpath_trigger_map_and_ai_discoverability.md` — triggers → questions → loss-averse angles; where owners look.
- `stewardpath_social_ad_library.md` — trigger-led, loss-averse ad copy by channel.
- `stewardpath_ai_discoverability_files.md` — robots.txt / llms.txt / markdown-mirror setup (reference for the repo).

**Product & funding (reference)**
- `stewardpath_implementation_prompt.md` — product brief v3 (schema, branching, synthesis prompts, MVP scope).
- `stewardpath_investment_case.md` — TAM/SAM/SOM, business model, funder-by-funder angles.

## Not in this Project (they live in the code repo)
The three Claude Code prompts (MVP build, auth, strategy-update) are build instructions — keep them in `docs/` in the repo, not here.

## The update discipline
This is a *living* knowledge base. When a customer conversation teaches you something real — the actual trigger language, a price someone paid, a wrong assumption — update the relevant file here first (it's the source of truth), then let it flow to the repo if it changes the build. Learning accumulates in the Project; it gets built in the repo.

## Standing reminder
Everything marked *(hypothesis)* is unvalidated. The bottleneck is not more planning — it is talking to trade owners. The most valuable next update to this knowledge base is what a real HVAC/plumbing owner said on the phone.
