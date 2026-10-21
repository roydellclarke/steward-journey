import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: __dirname,

  // The Markdown mirrors are published at /content/<slug>.md, which is not a
  // shape Next can express as a dynamic segment. One rewrite sends every one
  // of them to a single route, so a new guide in lib/content.js needs no new
  // file to get its .md twin.
  async rewrites() {
    return [{ source: "/content/:slug.md", destination: "/content/md/:slug" }];
  }
};

export default nextConfig;
