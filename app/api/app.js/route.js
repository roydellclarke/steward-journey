import { readFile } from "node:fs/promises";
import path from "node:path";

const repoRoot = process.cwd();
const appScriptPath = path.join(repoRoot, "workspace", "src", "app.js");

export async function GET() {
  try {
    const js = await readFile(appScriptPath, "utf8");
    return new Response(js, {
      headers: {
        "Content-Type": "application/javascript; charset=utf-8",
        "Cache-Control": "no-store"
      }
    });
  } catch {
    return new Response("", {
      headers: { "Content-Type": "application/javascript; charset=utf-8" },
      status: 404
    });
  }
}
