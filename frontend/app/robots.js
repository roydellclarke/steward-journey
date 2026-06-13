import { SITE_URL, PRIVATE_PATHS, AI_BOTS } from "../lib/site";

// Welcomes search engines and AI crawlers to the public marketing pages while
// keeping the sign-in flow and per-owner app shell out of every index. Each
// named AI bot gets the same allow/disallow as "*", because a crawler obeys
// only its most specific matching group, so the Disallow must be repeated.
export default function robots() {
  const rule = { allow: "/", disallow: PRIVATE_PATHS };
  return {
    rules: [
      { userAgent: "*", ...rule },
      ...AI_BOTS.map((userAgent) => ({ userAgent, ...rule }))
    ],
    // No Host directive: it is non-standard and ignored by most crawlers.
    sitemap: `${SITE_URL}/sitemap.xml`
  };
}
