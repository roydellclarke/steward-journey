import { readFile } from "node:fs/promises";
import path from "node:path";

const repoRoot = process.cwd();
const screenshotRoot = path.join(repoRoot, "workspace", "screenshots");

function safeScreenshotPath(name) {
  const basename = path.basename(name || "");
  if (!basename.endsWith(".png")) {
    throw new Error("Only PNG screenshots are supported.");
  }
  return path.join(screenshotRoot, basename);
}

export async function GET(request) {
  try {
    const url = new URL(request.url);
    const target = safeScreenshotPath(url.searchParams.get("name"));
    const image = await readFile(target);
    return new Response(image, {
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "no-store"
      }
    });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 404 });
  }
}
