"use client";

import { usePathname } from "next/navigation";

// Minimal monoline mark: a path cresting to a single point, a way forward,
// guided. Thin stroke in ink, in keeping with the modern-luxe aesthetic.
function BrandMark() {
  return (
    <svg className="brandMark" viewBox="0 0 28 28" fill="none" aria-hidden="true">
      <path
        d="M3.5 20.5C8 20.5 9.5 8.5 14 8.5s6 12 10.5 12"
        stroke="#15171a"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle cx="14" cy="5.4" r="1.7" fill="#15171a" />
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
        <span className="brandText">
          <span className="brandName">StewardPath</span>
          <span className="brandTag">The handoff, on your terms.</span>
        </span>
      </a>
      {isMarketing ? (
        <nav className="siteNav" aria-label="Primary">
          <a href="/#how-it-works">How it works</a>
          <a href="/#confidentiality">Privacy</a>
          <a className="navCta" href="/intake">Start privately</a>
        </nav>
      ) : (
        <span className="secureChip">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="4" y="10" width="16" height="11" rx="2.5" fill="#4a6a55" />
            <path d="M8 10V7.5a4 4 0 0 1 8 0V10" stroke="#4a6a55" strokeWidth="2" />
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
          <span className="brandText">
            <span className="brandName">StewardPath</span>
            <span className="brandTag">The handoff, on your terms.</span>
          </span>
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
        StewardPath is educational preparation support, not legal, tax, investment, valuation, or brokerage advice.
      </p>
    </footer>
  );
}
