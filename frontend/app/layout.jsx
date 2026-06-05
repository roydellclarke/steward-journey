import { Inter, Manrope } from "next/font/google";
import "./theme.css";
import "./styles.css";
import { SiteHeader, SiteFooter } from "./Chrome";
import { SITE_URL, SITE_NAME, DESCRIPTION, TAGLINE } from "../lib/site";

// Body: Inter (modern, familiar, highly legible). Display: Manrope (modern,
// sleek) for headings. Self-hosted by next/font; exposed as CSS variables.
const inter = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-display", display: "swap" });

const TITLE = "StewardPath: private transition readiness for business owners";

export const metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: "%s · StewardPath" },
  description: DESCRIPTION,
  applicationName: SITE_NAME,
  keywords: [
    "business succession planning",
    "exit planning",
    "sell my business",
    "business transition readiness",
    "founder succession",
    "family business succession",
    "business exit readiness score",
    "successor planning",
    "prepare to sell a business"
  ],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: TITLE,
    description: DESCRIPTION,
    locale: "en_US"
  },
  twitter: { card: "summary_large_image", title: TITLE, description: DESCRIPTION },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1, "max-video-preview": -1 }
  },
  category: "business"
};

// Structured data so search engines and AI assistants understand what
// StewardPath is. Grounded in the public site content only (no owner data).
const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: SITE_NAME,
      url: SITE_URL,
      slogan: TAGLINE,
      description: DESCRIPTION
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      name: SITE_NAME,
      url: SITE_URL,
      description: DESCRIPTION,
      publisher: { "@id": `${SITE_URL}/#organization` },
      inLanguage: "en-US"
    },
    {
      "@type": "Service",
      name: "StewardPath transition readiness program",
      serviceType: "Business transition and succession readiness",
      provider: { "@id": `${SITE_URL}/#organization` },
      areaServed: "US",
      audience: { "@type": "Audience", audienceType: "Founder-led and family business owners" },
      description:
        "A private, guided readiness program: a readiness score across five areas, named protections, successor paths weighed against your values, and briefs you can hand to an advisor or family.",
      offers: [
        { "@type": "Offer", name: "Sample report", price: "0", priceCurrency: "USD" },
        { "@type": "Offer", name: "Owner readiness report", price: "249", priceCurrency: "USD" },
        { "@type": "Offer", name: "Concierge package", price: "1500", priceCurrency: "USD" },
        { "@type": "Offer", name: "Advisor pilot", price: "199", priceCurrency: "USD" }
      ]
    },
    {
      "@type": "FAQPage",
      mainEntity: [
        {
          "@type": "Question",
          name: "Is StewardPath legal, tax, or valuation advice?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "No. StewardPath prepares you for a sale, succession, or transition. It does not give legal, tax, valuation, investment, or brokerage advice, and it routes regulated work to a qualified person."
          }
        },
        {
          "@type": "Question",
          name: "Is my information private?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Yes. Your answers are private by default, never shared with employees, family, or buyers unless you choose, and never used to train AI. You can export or delete your data at any time."
          }
        },
        {
          "@type": "Question",
          name: "What does the readiness score measure?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Five areas: financial clarity, how well the business runs without you, what is written down, family alignment, and your readiness to step back. Each comes with the reasoning behind it."
          }
        }
      ]
    }
  ]
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-theme="steward" className={`${inter.variable} ${manrope.variable}`}>
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
