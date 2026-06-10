"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { authApi } from "../../lib/auth";

// Advisor landing for the $199/mo pilot. The full multi-client workspace is a
// later build; for now this confirms the subscription and sets expectations.
export default function AdvisorArea() {
  const [account, setAccount] = useState({ authenticated: false, email: "", active: false });

  useEffect(() => {
    authApi.me().then((me) => {
      const active = (me.entitlements || []).some((e) => e.product === "advisor" && e.status === "active");
      setAccount({ authenticated: !!me.authenticated, email: me.email || "", active });
    }).catch(() => {});
  }, []);

  return (
    <main className="publicShell">
      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Advisor pilot</p>

          {account.active ? (
            <>
              <h1>You're in. Your advisor pilot is active.</h1>
              <p>
                Thank you for joining. Your pilot covers up to ten owner clients,
                each one arriving prepared with their own private readiness.
              </p>
              <p>
                Your client workspace is being set up. We will email {account.email || "you"}
                {" "}as soon as it is ready, with the steps to invite your first owner.
                In the meantime, you can walk the owner experience yourself to see
                what each client receives.
              </p>
              <p style={{ marginTop: 24 }}>
                <Link className="primaryCta" href="/intake">See the owner experience</Link>
              </p>
            </>
          ) : (
            <>
              <h1>The advisor pilot</h1>
              <p>
                For CPAs, exit planners, and advisors guiding up to ten owner
                clients. Each one arrives prepared. Start the pilot from the
                pricing section on the home page.
              </p>
              <p style={{ marginTop: 24 }}>
                <Link className="primaryCta" href="/">Back to pricing</Link>
              </p>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
