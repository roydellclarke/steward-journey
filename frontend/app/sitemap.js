import { SITE_URL, PUBLIC_PAGES, CONTENT_PAGE } from "../lib/site";
import { CONTENT_SLUGS } from "../lib/content";

export default function sitemap() {
  const lastModified = new Date();

  // App and marketing pages, plus every authored guide. Content guides are
  // derived from CONTENT_SLUGS so adding a guide indexes it automatically.
  const pages = [
    ...PUBLIC_PAGES,
    ...CONTENT_SLUGS.map((slug) => ({ path: `/content/${slug}`, ...CONTENT_PAGE }))
  ];

  return pages.map((page) => ({
    url: `${SITE_URL}${page.path}`,
    lastModified,
    changeFrequency: page.changeFrequency,
    priority: page.priority
  }));
}
