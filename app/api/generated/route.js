import { readFile } from "node:fs/promises";
import path from "node:path";

const repoRoot = process.cwd();
const generatedPath = path.join(repoRoot, "workspace", "src", "index.html");

export async function GET() {
  try {
    const html = await readFile(generatedPath, "utf8");
    return new Response(html, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store"
      }
    });
  } catch {
    return new Response("<p>No generated page yet. Run the loop first.</p>", {
      headers: { "Content-Type": "text/html; charset=utf-8" },
      status: 404
    });
  }
}
