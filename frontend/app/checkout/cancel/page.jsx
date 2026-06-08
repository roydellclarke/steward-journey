"use client";

import Link from "next/link";

// Stripe sends the owner here if they back out of checkout. No charge was made.
export default function CheckoutCancel() {
  return (
    <main className="publicShell">
      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Payment</p>
          <h2>No charge was made.</h2>
          <p>
            You left checkout before paying, so nothing happened. You can pick the
            option again whenever you are ready, or start the free check first.
          </p>
          <p style={{ marginTop: 24 }}>
            <Link className="primaryCta" href="/">Back to the options</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
