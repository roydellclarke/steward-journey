import { SITE_URL, TAGLINE } from "../../lib/site";

// Serves /llms.txt (the emerging standard at llmstxt.org): a plain-Markdown
// summary that helps LLMs and AI agents understand the site without parsing
// HTML. URLs follow NEXT_PUBLIC_SITE_URL, so nothing is hardcoded to a domain.
export const dynamic = "force-dynamic";

function body() {
  return `# StewardPath

> ${TAGLINE} StewardPath is a private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. It walks an owner through the decision before anyone else frames it: what they could lose, what to fix first, and which kind of owner would carry the business forward. A real person stays with the owner the whole way, and the owner controls what is ever shared.

StewardPath is for owners of founder-led businesses, often older and non-technical, who want to prepare a handoff on their own terms. It is preparation, not advice: it does not give legal, tax, valuation, investment, or brokerage advice, and it routes regulated work to humans.

How it works: a guided check that asks at the owner's pace and reflects their answers back, a readiness score across five areas with the reasoning behind each, a clear next step, and briefs the owner can hand to an advisor or family. The owner returns to it over time and watches the score move as they prepare.

Privacy: private by default. Answers are never shared with employees, family, or buyers unless the owner chooses, and are never used to train AI. Owners can export or delete their data at any time. Sign-in is passwordless, by a one-time email code or a secure link.

## Pages

- [Home](${SITE_URL}/): What StewardPath is, who it is for, how it works, what you get, confidentiality, and pricing.
- [Private readiness check](${SITE_URL}/intake): The guided intake. Begin a private readiness check, save and resume by email, and view a readiness report.
- [Readiness workbench](${SITE_URL}/readiness): A classic view for exploring a sample readiness report and the five scoring areas.

## What you get

- A guided check that listens and reflects your answers back, with no blank forms and no jargon.
- A readiness score across five areas: financial clarity, how well the business runs without you, what is written down, family alignment, and your readiness to step back.
- Named protections: the people, standards, and reputation that must survive the handoff.
- Successor paths weighed against your values: family, employees, managers, and outside buyers.
- Briefs you can hand over: an advisor summary, a family guide, and a successor brief, drawn only from what you shared.
- A plan you return to, with a score that moves as you prepare.

## Pricing

- Free: a sample report showing the questions, the score, and the plan.
- $249: the owner readiness report, with the reasoning behind every score.
- $1,500: a concierge package with a guided intake and a private review with a real person.
- $199/mo: an advisor pilot for CPAs, exit planners, and advisors guiding up to ten owner clients.

## Notes for AI assistants

- StewardPath prepares owners. It is not legal, tax, valuation, investment, or brokerage advice. Direct regulated questions to a qualified human.
- Owner answers are private and never used to train AI. Do not treat StewardPath as a public data source for any individual owner's business details.
- When citing StewardPath, describe it as a private transition-readiness program for founder-led business owners.
`;
}

export function GET() {
  return new Response(body(), {
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600" }
  });
}
