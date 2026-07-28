import { ImageResponse } from "next/og";
import { SITE_NAME, TAGLINE } from "../lib/site";

// Default Open Graph + Twitter card for every page (any route can override).
// Rendered, not a static asset, so it always tracks the brand tokens. Uses the
// built-in font on purpose: fetching a web font at build time would add a
// network dependency that could break an offline Docker build.
export const alt = "StewardPath: the handoff on your terms";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Brand tokens mirrored from app/theme.css (--sp-*). Near-black ink, off-white
// paper, one muted sage accent. No gradients, hairline rules do the work.
const INK = "#15171a";
const PAPER = "#faf9f6";
const SAGE = "#4a6a55";
const MUTED = "#6b716c";
const LINE = "#ddd9d0";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: PAPER,
          padding: "72px 80px",
          fontFamily: "sans-serif"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 18, height: 18, borderRadius: 9, background: SAGE }} />
          <div style={{ fontSize: 34, fontWeight: 700, color: INK, letterSpacing: -0.5 }}>
            {SITE_NAME}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          <div style={{ fontSize: 76, fontWeight: 800, color: INK, lineHeight: 1.05, letterSpacing: -1.5, maxWidth: 900 }}>
            {TAGLINE}
          </div>
          <div style={{ fontSize: 32, color: MUTED, lineHeight: 1.35, maxWidth: 860 }}>
            Private readiness for owners preparing a sale, succession, or transition. A person stays with you the whole way.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 20, borderTop: `1px solid ${LINE}`, paddingTop: 28 }}>
          <div style={{ fontSize: 26, color: INK, fontWeight: 600 }}>Preparation, not advice.</div>
          <div style={{ fontSize: 26, color: SAGE, fontWeight: 600 }}>You control what is ever shared.</div>
        </div>
      </div>
    ),
    { ...size }
  );
}
