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

// Public, crawlable app/marketing pages. Private app surfaces (sign-in, owner
// data) are kept out of search and AI indexes on purpose. Guide pages under
// /content are NOT listed here: the sitemap derives them from CONTENT_SLUGS so
// a new guide is indexed the moment it is authored, with no second edit.
export const PUBLIC_PAGES = [
  { path: "/", priority: 1.0, changeFrequency: "weekly" },
  { path: "/intake", priority: 0.8, changeFrequency: "monthly" },
  { path: "/readiness", priority: 0.5, changeFrequency: "monthly" },
  { path: "/go-to-market", priority: 0.4, changeFrequency: "monthly" }
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
