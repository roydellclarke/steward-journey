import { Inter, Manrope } from "next/font/google";
import "./theme.css";
import "./styles.css";
import { SiteHeader, SiteFooter } from "./Chrome";

// Body: Inter (modern, familiar, highly legible). Display: Manrope (modern,
// sleek) for headings. Self-hosted by next/font; exposed as CSS variables.
const inter = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-display", display: "swap" });

export const metadata = {
  title: "StewardPath, private readiness with you the whole way",
  description: "A private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. We stay with you the whole way, and you control what's ever shared."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-theme="steward" className={`${inter.variable} ${manrope.variable}`}>
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
