// Single source of truth for public site identity used by SEO + LLM discovery
// surfaces (metadata, robots, sitemap, structured data). The real domain MUST be
// set via NEXT_PUBLIC_SITE_URL in production; the default is only a placeholder
// (no domain is assumed to be registered).
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://your-domain.example").replace(/\/$/, "");
export const SITE_NAME = "StewardPath";
export const TAGLINE = "The handoff on your terms.";
export const DESCRIPTION =
  "A private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. A person stays with you the whole way, and you control what is ever shared.";

// Public, crawlable pages. Private app surfaces (sign-in, owner data) are kept
// out of search and AI indexes on purpose.
export const PUBLIC_PAGES = [
  { path: "/", priority: 1.0, changeFrequency: "weekly" },
  { path: "/intake", priority: 0.8, changeFrequency: "monthly" },
  { path: "/readiness", priority: 0.5, changeFrequency: "monthly" },
  { path: "/go-to-market", priority: 0.4, changeFrequency: "monthly" }
];

// Never index these: tokens and the per-owner app shell live here.
export const PRIVATE_PATHS = ["/auth/"];

// AI crawlers and agents we explicitly welcome to the public pages. Naming them
// is a clear signal; the global "*" rule covers any not listed here. Each still
// inherits the same Disallow, so private paths stay protected for every bot.
export const AI_BOTS = [
  // OpenAI
  "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ChatGPT Agent",
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
  "YouBot", "DuckAssistBot", "Diffbot", "PetalBot", "Kangaroo Bot", "QwenBot"
];
