// Transactional pages must never be indexed.
export const metadata = { title: "Checkout", robots: { index: false, follow: false } };
export default function Layout({ children }) { return children; }
