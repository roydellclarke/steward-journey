import "./theme.css";
import "./styles.css";
import { SiteHeader, SiteFooter } from "./Chrome";

export const metadata = {
  title: "StewardPath — private readiness, with you the whole way",
  description: "A private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. We stay with you the whole way — and you control what's ever shared."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-theme="steward">
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
