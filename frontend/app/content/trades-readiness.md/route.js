import { toMarkdown } from "../../../lib/content";

// Clean Markdown mirror of /content/trades-readiness, for LLMs and agents.
// Driven by the same structured source as the HTML page (lib/content.js), so
// the two can never fall out of sync. Static: content only changes on deploy.
export function GET() {
  return new Response(toMarkdown("trades-readiness"), {
    headers: { "Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "public, max-age=3600" }
  });
}
