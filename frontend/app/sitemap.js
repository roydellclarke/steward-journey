import { SITE_URL, PUBLIC_PAGES } from "../lib/site";

export default function sitemap() {
  const lastModified = new Date();
  return PUBLIC_PAGES.map((page) => ({
    url: `${SITE_URL}${page.path}`,
    lastModified,
    changeFrequency: page.changeFrequency,
    priority: page.priority
  }));
}
