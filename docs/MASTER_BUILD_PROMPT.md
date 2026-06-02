# Production Master Build Prompt

You are a senior AI systems architect, reliability engineer, and implementation
engineer.

Build and maintain a production-oriented adversarial long-running agent harness
for resolving one or more user goals. The system is a bounded goal-seeking
controller, not a single prompt and not a chat-only workflow.

## Runtime

Use Conda for live LLM mode.

```bash
conda env create -f environment.yml
conda activate agent-harness
```

If the default Python is broken or incompatible, use the Conda environment. The
UI must call Python through `HARNESS_PYTHON`, defaulting to `python3` when the
server is started from the activated environment.

## Architecture

Implement exactly three logical agent nodes:

1. **Planner**: turns goals into sprint intent, design brief, risks, and
   acceptance areas.
2. **Generator**: builds or repairs files from the current contract.
3. **Evaluator**: adversarially validates the live result through Puppeteer.

The Orchestrator coordinates state transitions but does not write application
code, approve work, or perform browser validation itself.

## Laws

1. The Generator must never evaluate, approve, or mark its own work complete.
2. Durable inter-agent communication must happen through workspace files, not
   hidden chat history.
3. The Evaluator must be harsh and evidence-oriented.
4. Final approval requires active browser validation.
5. Planner, Generator, and Evaluator must use distinct logical model configs.
6. Every state transition must be traceable to a file, verdict, threshold, or
   explicit Orchestrator decision.
7. Secrets must never be logged, echoed, committed, or written into generated
   source files.

## Model Routing

Use environment-configurable model routing.

```env
HARNESS_USE_LLM=true
PLANNER_MODEL=deepseek/deepseek-reasoner
GENERATOR_MODEL=moonshot/kimi-k2.5
EVALUATOR_MODEL=deepseek/deepseek-reasoner
DEEPSEEK_API_KEY=...
MOONSHOT_API_KEY=...
```

Provider keys should be project-scoped where possible, rotated regularly, and
bounded by provider spend limits or proxy-level budgets. The harness must
maintain local cost logs and abort when `MAX_COST_USD` is exceeded.

## Workspace

Use this durable context container:

```text
workspace/
  goals/
  specs/
  contracts/
  src/
  proposals/
  feedback/
  state/
  rubrics/
  traces/
  reports/
  screenshots/
```

All file tools must restrict paths to the workspace root and reject traversal.

## Observability

Every run must have a `run_id`.

Write structured events to:

```text
workspace/state/events.jsonl
```

Each event must include:

- timestamp,
- run_id,
- phase,
- event name,
- agent if relevant,
- iteration,
- summarized details,
- no secrets.

The Orchestrator must log:

- workspace initialization,
- planner invocation,
- contract handshake rounds,
- build start/end,
- evaluator start/end,
- pass/fail verdicts,
- threshold stops,
- completion,
- abort,
- context compaction.

The event log is the first tool for debugging “why did it move to this state?”

## Doctor / Preflight

Provide a `doctor` command that checks:

- workspace path is writable,
- required directories exist,
- Node is available,
- Puppeteer bridge is present,
- Puppeteer package is installed,
- `.env` is present,
- required keys exist when `HARNESS_USE_LLM=true`,
- model routes are configured,
- `HARNESS_PYTHON` resolves.

The doctor must never print secret values.

## Loop

The Orchestrator must run:

1. Initialize workspace.
2. Save user goals.
3. Create or restore run state with a new `run_id`.
4. Invoke Planner to create `/specs/sprint_plan.md` and
   `/specs/design_brief.md`.
5. Invoke Generator to propose `/proposals/test_plan.md`.
6. Invoke Evaluator to accept or reject the test plan.
7. Create `/contracts/current_sprint.md` only after acceptance.
8. Invoke Generator to build or repair.
9. Invoke Evaluator to test through Puppeteer.
10. Continue, replan, complete, or abort based on bounded state.

## Bounds

Expose hyperknobs for:

- minimum sprint iterations,
- maximum sprint iterations,
- maximum total iterations,
- maximum wall-clock minutes,
- maximum cost,
- repeated failure count,
- contract handshake rounds,
- divergence threshold,
- design review requirement,
- context reset cadence.

Abort when any configured upper bound is exceeded.

## Evaluation

The Evaluator must validate:

- desktop viewport,
- mobile viewport,
- no horizontal overflow,
- no critical console errors,
- screenshot evidence,
- CTA behavior,
- goal-specific product identity,
- requested domain concepts,
- design/craft/originality/functionality scores.

The Evaluator writes `/feedback/evaluation_report.md`. A pass without
Puppeteer evidence is invalid.

## UI

Provide a local Next.js console on port `3001`.

The UI should:

- accept goals,
- initialize, run, resume, and abort,
- show phase, verdict, iterations, cost, divergence, and design review state,
- preview the generated app,
- show screenshots,
- show parsed criteria,
- show run timeline,
- create persistent scheduled jobs,
- list job status and run history,
- approve and run gated jobs,
- register connector metadata without exposing secrets,
- show doctor/preflight status,
- never expose API keys.

Port `3000` is reserved for the app under test.

## Production Control Plane

Add a production spine so the harness can run locally, from Claude Desktop, or
from a VPS endpoint without creating separate control paths.

Required modules:

- persistent job registry at `/workspace/state/jobs.json`,
- optional Prefect adapter for background workers, retries, and cron-like
  schedules,
- FastAPI control API with `/jobs`, `/runs`, `/artifacts`, and `/connectors`,
- MCP server exposing safe tools for Claude Desktop,
- connector vault at `/workspace/state/connectors.json`.

All control surfaces must call the same registry and orchestrator code.

Do not expose generic filesystem read/write tools over MCP. Expose named,
bounded tools such as `harness_run_goal`, `harness_create_job`,
`harness_list_jobs`, `harness_read_report`, and `harness_list_artifacts`.

## Connector Safety

External account integrations must use connector-specific guardrails.

For Meta/Facebook:

- never ask for or store a Facebook password,
- use OAuth/Page access tokens only,
- store only environment variable names or secret references in the connector
  vault,
- require explicit approval before publish jobs,
- default to dry-run publishing,
- log post attempts and provider responses,
- never send raw tokens, PII, or connector secrets to LLMs.

Example flow:

```text
OAuth connector configured
→ scheduled content job created
→ Planner creates strategy
→ Generator drafts posts
→ Evaluator checks quality/safety/platform fit
→ human approval gate
→ publisher posts through provider API
→ run history and artifacts are logged
```

## Live LLM File Writes

When live model mode is enabled, the Generator may write files only through safe
file blocks:

```text
```file src/index.html
...
```
```

Only `src/` paths are allowed unless the contract explicitly grants a wider
workspace subdirectory. Path traversal must be rejected.

## Completion

The system may complete only when:

- Evaluator runs Puppeteer,
- every contract criterion passes,
- design review passes when required,
- no critical console errors remain,
- upper bounds are not exceeded,
- `/reports/completion_report.md` is written.

If completion is impossible within bounds, write `/reports/abort_report.md`.

## Maintenance Warning

This harness is not permanent infrastructure. After every major model upgrade,
inspect traces manually and re-evaluate whether adversarial separation is still
needed. If a newer model reliably self-corrects without sycophancy, simplify the
harness.
