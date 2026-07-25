// Retired route: redirects to /intake. Keep it out of search.
export const metadata = { title: "Readiness", robots: { index: false, follow: false } };
export default function Layout({ children }) { return children; }
