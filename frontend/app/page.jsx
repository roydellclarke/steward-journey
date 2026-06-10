"use client";

import { useEffect, useState } from "react";
import { apiFetch, startCheckout } from "../lib/api";
import { authApi } from "../lib/auth";
import AuthGate from "./intake/AuthGate";
import "./intake/intake.css"; // overlay/auth modal styles used by AuthGate

// Where each purchased product sends the owner. Payment is tied to their
// account, so a later visit lands them on the right path too.
const PRODUCT_PATH = {
  report: "/intake",
  concierge: "/intake",
  advisor: "/advisor"
};

const CATALOG_LABEL = {
  report: "Owner Readiness Program",
  concierge: "concierge package",
  advisor: "advisor pilot"
};

// What you get. Same strategy (JTBD + loss aversion), tighter prose, varied rhythm.
const sampleSections = [
  ["A guided check that listens", "It asks at your pace and shows you what it heard. No blank forms. No big words."],
  ["A readiness score you can read", "One number across five areas, each with the reason behind it. You see right where you stand."],
  ["What you refuse to lose", "Name the people, standards, and good name that must make it through the handoff. We keep it private."],
  ["The right next owner, your way", "Weigh family, workers, managers, and outside buyers against what matters to you. Rule out any you would never accept."],
  ["Notes you can hand over", "A summary for your advisor, a guide for your family, a note on the right next owner. All built only from what you told us."],
  ["A plan you come back to", "Save it. Come back. Watch the score go up as you get ready."]
];

// What it feels like to use, in plain owner's language. Grade-7 reading level.
const outcomes = [
  ["It listens to you", "It asks one question at a time and shows you what it heard. It feels like a talk, not a form."],
  ["You decide what to share", "Your answers stay private. You choose what to share, and who gets to see it."],
  ["One step at a time", "A clear score and a simple plan turn a big decision into small, doable steps."],
  ["Ready to meet your advisor", "You walk into the CPA or lawyer meeting prepared, with a short summary in hand."],
  ["A real person when you want one", "Ask for a private review and a person takes it from there. You are never left alone with an app."],
  ["You know where you stand", "A clear score in five areas, with the reason behind each one."]
];

const journeySteps = [
  ["1", "Begin privately", "First we show you what we collect, why, and how you stay in control. Then you begin when you are ready."],
  ["2", "Share at your pace", "Easy questions first. Harder ones come later, with a kind word before each. \"I don't know\" is a fine answer."],
  ["3", "See where you stand", "You get a clear score, the reasons behind it, your biggest gaps, and who could take over, weighed your way."],
  ["4", "Bring in a person", "Book a private review. A real person picks up where you left off, and sees only what you chose to share."]
];

const advisorTypes = ["Owner", "CPA", "Exit planner", "Wealth advisor", "Estate lawyer", "Community bank", "Other advisor"];

export default function PublicHome() {
  const [lead, setLead] = useState({
    name: "",
    email: "",
    businessType: "",
    timeline: "",
    role: "Owner"
  });
  const [status, setStatus] = useState("");
  const [payStatus, setPayStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [account, setAccount] = useState({ authenticated: false, email: "", entitlements: [] });
  const [pendingProduct, setPendingProduct] = useState("");

  // On load, see if the owner is already signed in. If so, we can skip the
  // sign-in step at checkout and show a resume path for what they own.
  useEffect(() => {
    authApi.me().then((me) => {
      if (me.authenticated) {
        setAccount({ authenticated: true, email: me.email, entitlements: me.entitlements || [] });
      }
    }).catch(() => {});
  }, []);

  // The first product the owner already paid for, used for the resume banner.
  const ownedProduct = account.entitlements?.find((e) => e.status === "active")?.product || "";

  function updateLead(field, value) {
    setLead((current) => ({ ...current, [field]: value }));
  }

  function scrollToRequest() {
    document.getElementById("request")?.scrollIntoView({ behavior: "smooth", block: "center" });
    setStatus("Add your details below, then choose an option.");
  }

  async function submitLead(intent) {
    if (busy) return;
    if (!lead.name && !lead.email) {
      scrollToRequest();
      setStatus("Add your name or email below, then we will send it.");
      return;
    }
    setBusy(true);
    setStatus("Saving your request...");
    try {
      await apiFetch("/leads", {
        method: "POST",
        body: JSON.stringify({ ...lead, intent })
      });
      const confirmation = intent === "readiness_call"
        ? "Got it. We will reach out privately to set up your readiness review."
        : "Saved. Check your email, or start the private check now.";
      setStatus(confirmation);
    } catch (error) {
      setStatus(`Could not save yet: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function buy(product) {
    if (busy) return;
    // Sign in first so the purchase attaches to the owner's account. If they
    // are not signed in yet, open the gate and resume the purchase after.
    if (!account.authenticated) {
      setPendingProduct(product);
      return;
    }
    setBusy(true);
    setPayStatus("Opening a secure checkout...");
    try {
      await startCheckout(product);
    } catch (error) {
      setPayStatus(`Could not start checkout: ${error.message}`);
      setBusy(false);
    }
  }

  async function onCheckoutAuthed(result) {
    setAccount((prev) => ({ ...prev, authenticated: true, email: result.email }));
    const product = pendingProduct;
    setPendingProduct("");
    if (!product) return;
    // Go straight to Stripe; the session cookie is now set, so /checkout
    // sees the owner. (Calling buy() here would read stale account state.)
    setBusy(true);
    setPayStatus("Opening a secure checkout...");
    try {
      await startCheckout(product);
    } catch (error) {
      setPayStatus(`Could not start checkout: ${error.message}`);
      setBusy(false);
    }
  }

  async function copyAdvisorMessage() {
    try {
      await navigator.clipboard.writeText(advisorMessage);
      setStatus("Copied. Paste it into an email to your advisor.");
    } catch {
      setStatus("Copy is blocked here. Select the message text and copy it manually.");
    }
  }

  const advisorMessage = `I am looking at StewardPath because I want to prepare before a buyer sets the terms. I want to understand what must be protected, where the business leans too much on me, and what to keep private until a buyer has proven they fit.`;

  return (
    <main className="publicShell">
      {pendingProduct ? (
        <AuthGate
          gate="checkout"
          knownEmail={account.email}
          onClose={() => setPendingProduct("")}
          onAuthenticated={onCheckoutAuthed}
        />
      ) : null}

      {account.authenticated && ownedProduct ? (
        <div className="resumeBar">
          <span>Welcome back. You have an active {CATALOG_LABEL[ownedProduct] || "purchase"}.</span>
          <a className="primaryCta" href={PRODUCT_PATH[ownedProduct] || "/intake"}>Pick up where you left off</a>
        </div>
      ) : null}

      <section className="publicHero">
        <p className="publicEyebrow">A private, guided way to get ready to hand off your business</p>
        <h1>Decide what you protect before a buyer decides for you.</h1>
        <div className="heroLower">
          <div className="heroLead">
            <p>
              You built more than a business. You built trust with the people who
              work for you, the customers who count on you, and the town that
              knows your name. StewardPath helps you make the big choice before
              anyone else makes it for you: what you could lose, what to fix
              first, and who should run it next. You will not do this alone.
              Nothing leaves this page unless you say so.
            </p>
            <div className="publicActions">
              <a href="/intake" className="primaryCta">Start private readiness check</a>
              <button type="button" onClick={scrollToRequest}>Request sample report</button>
              <button type="button" onClick={scrollToRequest}>Book a readiness review</button>
            </div>
            <p className="heroAlt">
              Prefer the classic workbench? <a href="/readiness">Open it here</a>.
            </p>
          </div>
          <aside className="heroReport">
            <span>StewardPath helps you answer</span>
            <strong>What should not be lost if you step back?</strong>
            <ul>
              <li>Where the business still needs you</li>
              <li>What a careful buyer will ask about</li>
              <li>Who could take over and fit your values</li>
              <li>What to keep private until a buyer earns it</li>
              <li>What to get ready before you call your advisor</li>
            </ul>
          </aside>
        </div>
      </section>

      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Who this is for</p>
          <h2>You may not be ready to sell. You may be ready to protect the handoff.</h2>
        </div>
        <div className="publicGrid three">
          <article><strong>No clear successor.</strong><p>Your children may not want it. Your team may not be ready. An outside buyer may never understand what makes it work.</p></article>
          <article><strong>The wrong buyer worries you.</strong><p>You want a fair price. You do not want it paid for with your people's jobs, your customers' trust, or your name.</p></article>
          <article><strong>Your advisor needs the full picture.</strong><p>Give your CPA, lawyer, or banker the whole story before a broker tells it for them.</p></article>
        </div>
      </section>

      <section className="publicBand" id="how-it-works">
        <div>
          <p className="publicEyebrow">How it works</p>
          <h2>We stay with you. It is not just a report.</h2>
          <p>StewardPath is something you come back to. You get a guided check, a plan, and a score that goes up as you get ready. It is not a report you file and forget.</p>
        </div>
        <div className="publicGrid">
          {journeySteps.map(([step, title, body]) => (
            <article key={step}>
              <strong>{step}. {title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="publicBand reportPreview">
        <div>
          <p className="publicEyebrow">What you get</p>
          <h2>Turn quiet worry into a clear next step.</h2>
        </div>
        <div className="publicGrid">
          {sampleSections.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="publicBand">
        <div>
          <p className="publicEyebrow">What owners want to feel</p>
          <h2>The point is not a document. It is how the decision feels.</h2>
        </div>
        <div className="publicGrid">
          {outcomes.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="publicBand split" id="confidentiality">
        <div>
          <p className="publicEyebrow">Confidentiality first</p>
          <h2>You decide what stays private until a buyer earns it.</h2>
          <p>
            Share ranges and your own words, never exact numbers. How big the
            sales are, how many customers you lean on, how much rides on you,
            whether the work is written down. It all starts private. Mark
            anything for your advisor only, or share it later with a buyer who
            has shown they fit.
          </p>
        </div>
        <div className="privacyBox">
          <strong>This is not a broker pitch.</strong>
          <p>Private by default. Never shared with employees, family, or buyers unless you choose. Never used to train AI. Export or delete it whenever you want. StewardPath prepares you. It does not give legal, tax, investment, valuation, or brokerage advice.</p>
        </div>
      </section>

      <section className="publicBand leadPanel" id="request">
        <div>
          <p className="publicEyebrow">Request a sample or bring your advisor in</p>
          <h2>Start with a private check. Share only when you are ready.</h2>
        </div>
        <form className="leadForm" onSubmit={(event) => event.preventDefault()}>
          <input placeholder="Your name" value={lead.name} onChange={(event) => updateLead("name", event.target.value)} />
          <input placeholder="Email" value={lead.email} onChange={(event) => updateLead("email", event.target.value)} />
          <input placeholder="Business type" value={lead.businessType} onChange={(event) => updateLead("businessType", event.target.value)} />
          <input placeholder="Timeline, e.g. 1-3 years" value={lead.timeline} onChange={(event) => updateLead("timeline", event.target.value)} />
          <select value={lead.role} onChange={(event) => updateLead("role", event.target.value)}>
            {advisorTypes.map((role) => <option key={role}>{role}</option>)}
          </select>
          <div className="leadButtons">
            <button type="button" onClick={() => submitLead("sample_report")} disabled={busy}>{busy ? "Saving…" : "Request sample report"}</button>
            <button type="button" onClick={() => submitLead("readiness_call")} disabled={busy}>{busy ? "Saving…" : "Book a readiness review"}</button>
            <button type="button" onClick={copyAdvisorMessage}>Copy advisor message</button>
          </div>
        </form>
        {status ? <p className="leadStatus">{status}</p> : null}
      </section>

      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Pricing</p>
          <h2>You're not buying a report. You're starting something you keep.</h2>
          <p>
            Your answers, your progress, and your plan stay private, and they
            grow as you get ready. Get ready now and the legal, tax, and
            accounting work later goes faster. That can mean fewer billable
            hours. The real payoff is peace of mind, whatever you choose next.
          </p>
        </div>
        <div className="offerBand">
          <article><span>Free</span><strong>Sample report</strong><p>See the questions, the score, and the plan StewardPath builds with you.</p><button type="button" className="offerCta ghost" onClick={scrollToRequest}>Start free</button></article>
          <article><span>$249</span><strong>Owner Readiness Program</strong><p>A guided program you walk through to a confident handoff, on your terms. Find your clarity, name what you refuse to lose, and weigh the successors who fit your values, not only the highest bidder. It grows as you prepare.</p><button type="button" className="offerCta" onClick={() => buy("report")} disabled={busy}>Start the program</button></article>
          <article><span>$1,500</span><strong>Concierge package</strong><p>A guided check, a private review with a real person, and help getting ready for the talks ahead. You show up to the lawyer and accountant organized, which cuts their hours.</p><button type="button" className="offerCta" onClick={() => buy("concierge")} disabled={busy}>Get the concierge package</button></article>
          <article><span>$199/mo</span><strong>Advisor pilot</strong><p>For CPAs, exit planners, and advisors guiding up to ten owner clients. Each one arrives prepared.</p><button type="button" className="offerCta" onClick={() => buy("advisor")} disabled={busy}>Start the advisor pilot</button></article>
        </div>
        {payStatus ? <p className="leadStatus" style={{ marginTop: 20 }}>{payStatus}</p> : null}
      </section>
    </main>
  );
}
