"use client";

import { usePathname } from "next/navigation";

// Inline SVG so there's no asset dependency. A shield (stewardship / protection)
// with a path line and a guiding point (a way forward) — in the brand green.
function BrandMark() {
  return (
    <svg className="brandMark" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path
        d="M16 2.5l11 3.8v7.9c0 7.1-4.7 12.3-11 14.9-6.3-2.6-11-7.8-11-14.9V6.3L16 2.5z"
        fill="#20543c"
      />
      <path
        d="M9.5 18.2c2.4 0 3.3-3 6.5-3s4.1 3 6.5 3"
        stroke="#bfe0c9"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="16" cy="11" r="2.3" fill="#bfe0c9" />
    </svg>
  );
}

export function SiteHeader() {
  const pathname = usePathname() || "/";
  // Marketing surfaces get light nav; data-entry surfaces get a trust cue.
  const isMarketing = pathname === "/" || pathname.startsWith("/go-to-market");

  return (
    <header className="siteHeader">
      <a className="brand" href="/">
        <BrandMark />
        <span>StewardPath</span>
      </a>
      {isMarketing ? (
        <nav className="siteNav" aria-label="Primary">
          <a href="/#how-it-works">How it works</a>
          <a href="/#confidentiality">Privacy</a>
          <a className="navCta" href="/intake">Start privately</a>
        </nav>
      ) : (
        <span className="secureChip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="4" y="10" width="16" height="11" rx="2.5" fill="#2f7a55" />
            <path d="M8 10V7.5a4 4 0 0 1 8 0V10" stroke="#2f7a55" strokeWidth="2" />
          </svg>
          Private &amp; secure
        </span>
      )}
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="footTop">
        <span className="footBrand">
          <BrandMark />
          StewardPath
        </span>
        <nav className="footLinks" aria-label="Footer">
          <a href="/">Home</a>
          <a href="/intake">Readiness program</a>
          <a href="/#confidentiality">Privacy</a>
        </nav>
      </div>
      <p className="footFine">
        Private by default · never used to train AI · export or delete your data anytime.
      </p>
      <p className="footFine">
        StewardPath is educational preparation support — not legal, tax, investment, valuation, or brokerage advice.
      </p>
    </footer>
  );
}
