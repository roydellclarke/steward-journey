// Single source of truth for public site identity used by SEO + LLM discovery
// surfaces (metadata, robots, sitemap, structured data). The real domain MUST be
// set via NEXT_PUBLIC_SITE_URL in production; the default is only a placeholder
// (no domain is assumed to be registered).
const RAW_SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://your-domain.example";

// Launch gate. NEXT_PUBLIC_* values are inlined at build time, so a forgotten
// build arg would otherwise ship a live site whose every canonical, sitemap,
// Open Graph, JSON-LD @id, and llms.txt link points at a dead placeholder
// domain, with nothing failing. Fail the production build loudly instead. Dev
// (NODE_ENV !== "production") keeps the placeholder so local work just runs.
if (process.env.NODE_ENV === "production" && RAW_SITE_URL.includes("your-domain.example")) {
  throw new Error(
    "NEXT_PUBLIC_SITE_URL is unset or still the placeholder. Set the real domain for a production build, e.g. docker build --build-arg NEXT_PUBLIC_SITE_URL=https://yourdomain.com"
  );
}

export const SITE_URL = RAW_SITE_URL.replace(/\/$/, "");
export const SITE_NAME = "StewardPath";
export const TAGLINE = "The handoff on your terms.";
export const DESCRIPTION =
  "A private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. A person stays with you the whole way, and you control what is ever shared.";

// Site-level brand/product FAQ. Single source: the homepage renders these as
// visible text AND emits them as a schema.org FAQPage from this same array, so
// the structured data always matches what is on the page (Google's FAQ rich
// result requires the answers to be visible). Guide pages emit their own
// FAQPage from lib/content.js; this is only the site-wide one.
export const FAQ = [
  {
    q: "Is StewardPath legal, tax, or valuation advice?",
    a: "No. StewardPath prepares you for a sale, succession, or transition. It does not give legal, tax, valuation, investment, or brokerage advice, and it routes regulated work to a qualified person."
  },
  {
    q: "Is my information private?",
    a: "Yes. Your answers are private by default, never shared with employees, family, or buyers unless you choose, and never used to train AI. You can export or delete your data at any time."
  },
  {
    q: "What does the readiness score measure?",
    a: "Five areas: financial clarity, how well the business runs without you, what is written down, family alignment, and your readiness to step back. Each comes with the reasoning behind it."
  },
  {
    q: "How do I prepare to sell my business?",
    a: "Start before a broker or buyer sets the terms. StewardPath gives a private readiness score across five areas, a prioritized action plan that lifts the score as you finish steps, and briefs to hand your advisor, so you walk in ready."
  },
  {
    q: "Who should take over my family business?",
    a: "StewardPath includes a successor-fit scorecard that ranks family members, key employees, managers, and outside buyers by how well they fit your values, not by the size of their offer. A candidate who crosses a non-negotiable is ruled out."
  },
  {
    q: "How do I sell my business without hurting my employees?",
    a: "StewardPath helps you name what you refuse to lose, your people's jobs, your customers' trust, and your name, then weigh buyers and successors against it, so you choose by fit and not only by price."
  },
  {
    q: "How much does StewardPath cost?",
    a: "A free sample, the Owner Readiness Program at $249, a $1,500 concierge package with a private review by a real person, and a $199 per month advisor pilot for CPAs, exit planners, and advisors."
  },
  {
    q: "How is StewardPath different from a business broker?",
    a: "A broker sells the business and optimizes for price. StewardPath helps the owner get ready first and choose the next owner by fit to their values, in private, before any broker or buyer sets the terms. It is preparation, not brokerage."
  }
];

// Public, crawlable app/marketing pages. Private app surfaces (sign-in, owner
// data) are kept out of search and AI indexes on purpose. Guide pages under
// /content are NOT listed here: the sitemap derives them from CONTENT_SLUGS so
// a new guide is indexed the moment it is authored, with no second edit.
// /go-to-market is intentionally NOT listed: it holds internal sales scripts
// and pricing tests, so it is noindex'd (see app/go-to-market/layout.jsx) and
// kept out of the sitemap and llms.txt.
export const PUBLIC_PAGES = [
  { path: "/", priority: 1.0, changeFrequency: "weekly" },
  { path: "/intake", priority: 0.8, changeFrequency: "monthly" }
];

// Sitemap priority/frequency for the derived /content guide pages.
export const CONTENT_PAGE = { priority: 0.7, changeFrequency: "monthly" };

// Never index these. The real boundary is the passwordless login (a crawler
// cannot authenticate, so it cannot read owner data); this is defense-in-depth
// so the URLs never get indexed even though the data is unreachable anyway.
export const PRIVATE_PATHS = ["/auth/", "/api/"];

// AI crawlers and agents we explicitly welcome to the public pages. Naming them
// is a clear signal; the global "*" rule covers any not listed here. Each still
// inherits the same Disallow, so private paths stay protected for every bot.
export const AI_BOTS = [
  // OpenAI (robots tokens are single words; "ChatGPT Agent" is not a valid token)
  "GPTBot", "OAI-SearchBot", "ChatGPT-User",
  // Google (Gemini, AI Overviews, NotebookLM)
  "Google-Extended", "GoogleOther", "Gemini-Deep-Research", "Google-NotebookLM", "Google-CloudVertexBot",
  // Anthropic (Claude)
  "ClaudeBot", "anthropic-ai", "Claude-Web", "Claude-User", "Claude-SearchBot",
  // Microsoft / Bing
  "bingbot", "BingPreview",
  // Perplexity
  "PerplexityBot", "Perplexity-User",
  // Apple
  "Applebot", "Applebot-Extended",
  // Meta (Facebook / Meta AI)
  "Meta-ExternalAgent", "Meta-ExternalFetcher", "FacebookBot", "facebookexternalhit",
  // Amazon
  "Amazonbot",
  // Common Crawl (feeds many open models)
  "CCBot",
  // Other major labs / search assistants
  "cohere-ai", "MistralAI-User", "DeepSeekBot", "PanguBot", "Bytespider", "TikTokSpider",
  "YouBot", "DuckAssistBot", "Diffbot", "PetalBot", "QwenBot"
];
