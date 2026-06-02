import { readdir } from "node:fs/promises";
import path from "node:path";

const repoRoot = process.cwd();
const screenshotRoot = path.join(repoRoot, "workspace", "screenshots");

export async function GET() {
  try {
    const names = await readdir(screenshotRoot);
    const screenshots = names
      .filter((name) => name.endsWith(".png"))
      .sort()
      .map((name) => ({ name, url: `/api/screenshot?name=${encodeURIComponent(name)}` }));
    return Response.json({ screenshots });
  } catch {
    return Response.json({ screenshots: [] });
  }
}
