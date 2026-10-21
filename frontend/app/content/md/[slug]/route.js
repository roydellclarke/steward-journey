import { CONTENT_SLUGS, getContent, toMarkdown } from "../../../../lib/content";

// Clean Markdown mirror of every guide, for LLMs and agents. Driven by the
// same structured source as the HTML page (lib/content.js), so the two can
// never fall out of sync.
//
// The public URL stays /content/<slug>.md. A rewrite in next.config.js sends
// it here, which means adding a guide to lib/content.js publishes its Markdown
// mirror with no new route and no file to forget.
export const dynamic = "force-static";

export function generateStaticParams() {
  return CONTENT_SLUGS.map((slug) => ({ slug }));
}

export async function GET(request, { params }) {
  const { slug } = await params;
  if (!getContent(slug)) {
    return new Response("Not found", { status: 404, headers: { "Content-Type": "text/plain" } });
  }
  return new Response(toMarkdown(slug), {
    headers: { "Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "public, max-age=3600" }
  });
}
