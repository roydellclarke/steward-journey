import "./styles.css";

export const metadata = {
  title: "Agent Harness Console",
  description: "Local UI for the adversarial long-running agent harness"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
