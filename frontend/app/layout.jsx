import "./styles.css";

export const metadata = {
  title: "StewardPath",
  description: "Legacy transfer readiness workbench"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
