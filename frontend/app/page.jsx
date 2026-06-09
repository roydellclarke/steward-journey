"use client";

import { useState } from "react";
import { apiFetch, startCheckout } from "../lib/api";

// What you get. Same strategy (JTBD + loss aversion), tighter prose, varied rhythm.
const sampleSections = [
  ["A guided check that listens", "It asks at your pace and reflects back what you said. No blank forms. No jargon."],
  ["A readiness score you can read", "One number across five areas, each with the reason behind it. You see exactly where you stand."],
  ["What you refuse to lose", "Name the people, standards, and reputation that must survive the handoff. We keep it private."],
  ["Successor paths, your way", "Weigh family, employees, managers, and outside buyers against what you value. Rule out the ones you would never accept."],
  ["Briefs you can hand over", "An advisor summary, a family guide, a successor brief. Drawn only from what you told us."],
  ["A plan you return to", "Save it. Come back. Watch the score climb as you prepare."]
];

// The JTBD outcomes, owner's language, deliberately uneven lengths.
const outcomes = [
  ["Heard, not processed", "Every step reflects your words back. You are talked with, not handed software."],
  ["In control of what's shared", "Private by default. You decide what leaves this space, and who ever sees it."],
  ["Less overwhelmed", "A staged plan and a score you can read turn a heavy decision into a next step."],
  ["Ready for the advisor", "Walk into the CPA or attorney meeting prepared, with a brief in hand."],
  ["Not left to software", "When you want a person, a private review is one click away."],
  ["Clear on where you stand", "An honest score across five areas, and the reasoning behind each one."]
];

const journeySteps = [
  ["1", "Begin privately", "A short trust step comes first: what we collect, why, and how you stay in control. Then you start when you are ready."],
  ["2", "Share at your pace", "Easy questions first. The hard ones come later, with a word of reassurance before each. \"I don't know\" counts as an answer."],
  ["3", "See where you stand", "A readiness score with its reasoning, your biggest openings, and successor paths weighed your way."],
  ["4", "Bring in a person", "Book a private review. A human picks up where you left off, with only what you chose to share."]
];

const advisorTypes = ["Owner", "CPA", "Exit planner", "Wealth advisor", "Estate attorney", "Community bank", "Other advisor"];

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
      <section className="publicHero">
        <p className="publicEyebrow">Private, guided transition readiness for founder-led businesses</p>
        <h1>Decide what you protect before a buyer decides for you.</h1>
        <div className="heroLower">
          <div className="heroLead">
            <p>
              You built more than an asset. You built trust with the people who
              work for you, the customers who count on you, and the town that
              knows your name. StewardPath walks you through the decision before
              anyone else frames it: what you could lose, what to fix first, and
              which kind of owner would carry it forward. You won't do this
              alone. Nothing leaves this space unless you say so.
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
              <li>Where the business still leans on you</li>
              <li>What a careful buyer will question</li>
              <li>Which successor paths fit your values</li>
              <li>What to keep private until fit is real</li>
              <li>What to prepare before the advisor call</li>
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
          <article><strong>Your advisor needs the full picture.</strong><p>Give your CPA, attorney, or banker the whole story before a broker tells it for them.</p></article>
        </div>
      </section>

      <section className="publicBand" id="how-it-works">
        <div>
          <p className="publicEyebrow">How it works</p>
          <h2>We stay with you. It is not just a report.</h2>
          <p>StewardPath is something you return to: a guided check, a plan, and a score that moves as you prepare. Not a report you file and forget.</p>
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
            Share ranges and your own words, never exact figures. Revenue band,
            customer concentration, how much rides on you, whether the work is
            written down. It all starts private. Mark anything advisor-only, or
            share it later with a buyer who has proven they fit.
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
            Your answers, your progress, and your plan stay private and move as
            you prepare. Get ready now and the legal, tax, and accounting work
            later runs faster, which can mean fewer billable hours. The real
            return is peace of mind for whatever you choose next.
          </p>
        </div>
        <div className="offerBand">
          <article><span>Free</span><strong>Sample report</strong><p>See the questions, the score, and the plan StewardPath builds with you.</p><button type="button" className="offerCta ghost" onClick={scrollToRequest}>Start free</button></article>
          <article><span>$249</span><strong>Owner readiness report</strong><p>Your private readiness, with the reasoning behind every score. It moves as you prepare, so the advisor or buyer call finds you ready.</p><button type="button" className="offerCta" onClick={() => buy("report")} disabled={busy}>Buy the report</button></article>
          <article><span>$1,500</span><strong>Concierge package</strong><p>A guided intake, a private review with a real person, and help preparing the conversations ahead. You reach the lawyer and accountant organized, which trims their hours.</p><button type="button" className="offerCta" onClick={() => buy("concierge")} disabled={busy}>Get the concierge package</button></article>
          <article><span>$199/mo</span><strong>Advisor pilot</strong><p>For CPAs, exit planners, and advisors guiding up to ten owner clients. Each one arrives prepared.</p><button type="button" className="offerCta" onClick={() => buy("advisor")} disabled={busy}>Start the advisor pilot</button></article>
        </div>
        {payStatus ? <p className="leadStatus" style={{ marginTop: 20 }}>{payStatus}</p> : null}
      </section>
    </main>
  );
}
