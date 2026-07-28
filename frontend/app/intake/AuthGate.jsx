"use client";

import { useRef, useState } from "react";
import { authApi } from "../../lib/auth";
import { useModalA11y } from "./useModalA11y";

// Copy per gate. No em-dashes (project writing law); commas carry the pauses.
const GATE_COPY = {
  save: {
    eyebrow: "Save and resume",
    title: "Pick this back up later",
    body: "Your answers are already saved and private to you. Enter your email so you can return on any device, even weeks from now. We send a 6-digit code to confirm it is you, plus a secure link that stays good for a while. No password to remember.",
    sendCta: "Email me my link",
    verifyCta: "Save and continue"
  },
  report: {
    eyebrow: "Your readiness report",
    title: "Open your report",
    body: "Your readiness report is ready. Enter your email and we will send you a 6-digit code. You put that code in on the next screen to open your report. It stays private, and you decide if you ever share it.",
    sendCta: "Email me my code",
    verifyCta: "Open my report"
  },
  checkout: {
    eyebrow: "Secure checkout",
    title: "Sign in to continue",
    body: "Enter your email and we will send you a 6-digit code. You put that code in on the next screen. Signing in first ties your purchase to your account, so you pick up right where you left off next time. No password to remember.",
    sendCta: "Email me my code",
    verifyCta: "Continue to payment"
  }
};

// A passwordless sign-in gate. Step 1 captures the email and requests a code.
// Step 2 takes the 6-digit code; the same email also holds a magic link as a
// fallback. On success we hand the result back to the parent.
export default function AuthGate({ gate = "save", projectId, knownEmail = "", onClose, onAuthenticated }) {
  const copy = GATE_COPY[gate] || GATE_COPY.save;
  const [step, setStep] = useState("email"); // email | code
  const [email, setEmail] = useState(knownEmail);
  const [code, setCode] = useState("");
  const [ttl, setTtl] = useState(10);
  const [linkDays, setLinkDays] = useState(14);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const panelRef = useRef(null);
  useModalA11y(panelRef, onClose);

  async function sendCode() {
    setError("");
    setBusy(true);
    try {
      const res = await authApi.request(email.trim(), projectId, gate);
      setTtl(res.ttlMinutes || 10);
      if (res.linkDays) setLinkDays(res.linkDays);
      setStep("code");
    } catch (e) {
      setError(e.message || "Please enter a valid email address.");
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    setError("");
    setBusy(true);
    try {
      const result = await authApi.verify(email.trim(), code.trim());
      onAuthenticated(result);
    } catch (e) {
      setError("That code did not work. It may have expired or already been used. Send a new one and try again.");
      setBusy(false);
    }
  }

  return (
    <div className="dataOverlay" role="dialog" aria-modal="true" aria-labelledby="authGateTitle" ref={panelRef}>
      <div className="dataPanel authPanel">
        <div className="dataHead">
          <h2 id="authGateTitle">{copy.title}</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <p className="conciergeEyebrow">{copy.eyebrow} · {step === "email" ? "Step 1 of 2" : "Step 2 of 2"}</p>
        <p className="authBody">{copy.body}</p>

        {step === "email" ? (
          <form
            onSubmit={(e) => { e.preventDefault(); if (!busy) sendCode(); }}
          >
            <label className="authLabel" htmlFor="authEmail">Your email</label>
            <input
              id="authEmail"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoFocus
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <div className="dataActions">
              <button type="submit" className="primaryCta" disabled={busy || !email.trim()}>
                {busy ? "Sending…" : copy.sendCta}
              </button>
            </div>
          </form>
        ) : (
          <form
            onSubmit={(e) => { e.preventDefault(); if (!busy && code.trim().length >= 6) verify(); }}
          >
            <p className="authSent">
              Check your email. We just sent a 6-digit code to <strong>{email}</strong>. If you do not see it
              in a minute, look in your spam or junk folder. Type the code below to keep going. The code works
              once and expires in about {ttl} minutes. No rush to finish today: the same email has a secure
              link that lasts {linkDays} days, so you can pick this back up later.
            </p>
            <label className="authLabel" htmlFor="authCode">Your 6-digit code</label>
            <input
              id="authCode"
              className="codeInput"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]*"
              maxLength={6}
              autoFocus
              placeholder="••••••"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/[^0-9]/g, ""))}
            />
            <div className="dataActions">
              <button type="submit" className="primaryCta" disabled={busy || code.trim().length < 6}>
                {busy ? "Checking…" : copy.verifyCta}
              </button>
              <button type="button" className="authText" onClick={() => { setCode(""); setStep("email"); }} disabled={busy}>
                Use a different email or resend
              </button>
            </div>
          </form>
        )}

        {error ? <p className="conciergeStatus" role="alert">{error}</p> : null}
        <p className="authPrivacy">Private by default. We use your email only to save your place and keep your readiness yours.</p>
      </div>
    </div>
  );
}
