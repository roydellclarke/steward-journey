"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiBaseUrl } from "../../../lib/api";

// After Stripe redirects back, confirm the payment server-side by retrieving
// the session. The backend marks the order paid and sends the receipt; we just
// show the owner a calm confirmation.
export default function CheckoutSuccess() {
  const [state, setState] = useState({ phase: "checking", productName: "", amount: "" });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (!sessionId) {
      setState({ phase: "error", productName: "", amount: "", product: "" });
      return;
    }
    fetch(`${apiBaseUrl}/checkout/session/${sessionId}`, { credentials: "include" })
      .then((response) => response.json())
      .then((data) => {
        if (data.paid) {
          setState({ phase: "paid", productName: data.productName || "your order", amount: data.amountDisplay || "", product: data.product || "" });
        } else {
          setState({ phase: "pending", productName: data.productName || "", amount: "", product: data.product || "" });
        }
      })
      .catch(() => setState({ phase: "error", productName: "", amount: "", product: "" }));
  }, []);

  // Each product leads somewhere different. The report and concierge owner
  // continues their private readiness; the advisor goes to the advisor area.
  const NEXT = {
    report: { href: "/intake", cta: "Continue to your private readiness" },
    concierge: { href: "/intake", cta: "Start your guided intake" },
    advisor: { href: "/advisor", cta: "Go to your advisor area" }
  };
  const next = NEXT[state.product] || NEXT.report;

  return (
    <main className="publicShell">
      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Payment</p>
          {state.phase === "checking" && <h2>Confirming your payment...</h2>}

          {state.phase === "paid" && (
            <>
              <h2>Thank you. Your payment is confirmed.</h2>
              <p>
                You bought {state.productName}
                {state.amount ? ` (${state.amount})` : ""}. We sent a confirmation to
                your email. Your account remembers this, so you can leave and pick
                up right where you left off.
              </p>
              {state.product === "concierge" && (
                <p>
                  Your package includes a private review with a real person. Start
                  your guided intake now, and we will reach out to set up the review.
                </p>
              )}
              {state.product === "advisor" && (
                <p>
                  Your advisor pilot is active. Head to your advisor area to get set
                  up with your owner clients.
                </p>
              )}
            </>
          )}

          {state.phase === "pending" && (
            <>
              <h2>We are still confirming this payment.</h2>
              <p>
                Stripe has not marked it complete yet. Give it a moment and refresh.
                If it does not clear, no charge was made and you can try again.
              </p>
            </>
          )}

          {state.phase === "error" && (
            <>
              <h2>We could not confirm this payment.</h2>
              <p>
                If you were charged, you will still get a confirmation email. You can
                also reach us and we will sort it out.
              </p>
            </>
          )}

          {state.phase === "paid" && (
            <p style={{ marginTop: 24 }}>
              <Link className="primaryCta" href={next.href}>{next.cta}</Link>
            </p>
          )}
        </div>
      </section>
    </main>
  );
}
