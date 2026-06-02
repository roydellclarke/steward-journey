import "./styles.css";

export const metadata = {
  title: "StewardPath — private readiness, with you the whole way",
  description: "A private, guided readiness program for founder-led business owners preparing a sale, succession, or transition. Accompaniment, not an artifact — and you control what's ever shared."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
