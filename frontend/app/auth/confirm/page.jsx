"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "../../../lib/auth";
import "../../intake/intake.css";

const STORAGE_KEY = "stewardpath.intake.projectId";

const GATE_COPY = {
  save: {
    title: "Confirm it's you",
    body: "Click below to pick your readiness back up where you left it. This link works once."
  },
  report: {
    title: "Confirm it's you",
    body: "Click below to open your readiness report. It stays private, and you decide if you ever share it."
  }
};

// Landing page for the magic link. We peek at the token to validate it WITHOUT
// consuming it, so an email scanner that pre-fetches the link cannot burn it.
// The owner must click the button, which is the explicit POST that consumes it.
export default function ConfirmPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [gate, setGate] = useState("save");
  const [phase, setPhase] = useState("checking"); // checking | ready | confirming | done | error
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get("token") || "";
    if (!t) {
      setPhase("error");
      setError("This link is missing its sign-in token. Please open the most recent email we sent.");
      return;
    }
    setToken(t);
    authApi.peekLink(t)
      .then((res) => { setGate(res.gate || "save"); setPhase("ready"); })
      .catch(() => {
        setPhase("error");
        setError("This link did not work. It may have expired or already been used. Please request a new one.");
      });
  }, []);

  async function confirm() {
    setPhase("confirming");
    setError("");
    try {
      const result = await authApi.confirmLink(token);
      // Carry the project binding to this device so the intake resumes correctly,
      // even if the owner opened the link somewhere new.
      if (result.projectId && typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, result.projectId);
      }
      setPhase("done");
      router.push("/intake");
    } catch (e) {
      setPhase("error");
      setError("This link did not work. It may have expired or already been used. Please request a new one.");
    }
  }

  const copy = GATE_COPY[gate] || GATE_COPY.save;

  return (
    <main className="conciergeShell single">
      <section className="trustCard">
        <p className="conciergeEyebrow">Secure sign-in</p>
        {phase === "error" ? (
          <>
            <h1>That link didn't work</h1>
            <p className="authBody">{error}</p>
            <div className="trustActions">
              <button type="button" className="primaryCta" onClick={() => router.push("/intake")}>
                Back to my readiness
              </button>
            </div>
          </>
        ) : phase === "checking" ? (
          <>
            <h1>Checking your link…</h1>
            <p className="authBody">One moment while we confirm this sign-in link is valid.</p>
          </>
        ) : (
          <>
            <h1>{copy.title}</h1>
            <p className="authBody">{copy.body}</p>
            <div className="trustActions">
              <button type="button" className="primaryCta" onClick={confirm} disabled={phase !== "ready"}>
                {phase === "done" ? "Signing you in…" : phase === "confirming" ? "Confirming…" : "Confirm and continue"}
              </button>
            </div>
            <p className="authPrivacy">Your answers stay private to you. We use this only to confirm it's really you.</p>
          </>
        )}
      </section>
    </main>
  );
}
