"use client";

import { useState } from "react";
import { authApi } from "../../lib/auth";

// Copy per gate. No em-dashes (project writing law); commas carry the pauses.
const GATE_COPY = {
  save: {
    eyebrow: "Save and resume",
    title: "Pick this back up later",
    body: "Your answers stay private to you. Want to pick this back up later? Enter your email and we'll send a secure link, no password to remember.",
    sendCta: "Send my secure code",
    verifyCta: "Save and continue"
  },
  report: {
    eyebrow: "Your readiness report",
    title: "Open your report",
    body: "Your readiness report is ready. Enter your email and we'll send a secure link to open it. It stays private, and you decide if you ever share it.",
    sendCta: "Send my secure code",
    verifyCta: "Open my report"
  },
  checkout: {
    eyebrow: "Secure checkout",
    title: "Sign in to continue",
    body: "Enter your email and we'll send a secure code. Signing in first ties your purchase to your account, so you pick up right where you left off next time. No password to remember.",
    sendCta: "Send my secure code",
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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function sendCode() {
    setError("");
    setBusy(true);
    try {
      const res = await authApi.request(email.trim(), projectId, gate);
      setTtl(res.ttlMinutes || 10);
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
    <div className="dataOverlay" role="dialog" aria-modal="true" aria-labelledby="authGateTitle">
      <div className="dataPanel authPanel">
        <div className="dataHead">
          <h2 id="authGateTitle">{copy.title}</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <p className="conciergeEyebrow">{copy.eyebrow}</p>
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
              We sent a 6-digit code to <strong>{email}</strong>. Enter it below. The same email also has a
              secure link you can open instead. The code works once and expires in about {ttl} minutes.
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
