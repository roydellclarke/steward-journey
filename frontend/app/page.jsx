"use client";

import { useState } from "react";
import { apiFetch } from "../lib/api";

// What you actually get, reframed around the concierge upgrade: something that
// listens and stays with you, not a one-time report.
const sampleSections = [
  ["A guided intake that listens", "Answer at your pace. StewardPath reflects back what you've shared, so it feels like being heard, not filling in a form."],
  ["A readiness score you understand", "One clear number across five areas, with the plain-language reason behind every part of it. No black box."],
  ["What must be protected", "Name the employees, customers, standards, and reputation you want to carry through, and we keep it private by default."],
  ["Successor fit, weighed your way", "Compare paths by continuity, financial outcome, and emotional fit, and exclude the ones you'd never accept."],
  ["Briefs you can actually use", "Advisor-ready summary, family-conversation guide, and a successor-fit brief, grounded only in what you said."],
  ["Progress over time", "Save and return whenever you like. Your readiness updates as you prepare, so you can see yourself moving forward."]
];

// The JTBD outcomes from the product brief, in the owner's own language.
const outcomes = [
  ["Feel heard, less alone", "Every step reflects back what you've shared, so it feels like someone's listening, not like using software."],
  ["In control of what's shared", "Private by default. You decide what, if anything, leaves this space, and with whom."],
  ["Less overwhelmed", "A staged plan and a score you can read turn a heavy decision into clear next steps."],
  ["More confident with advisors", "Walk into the CPA or attorney conversation already prepared, with a brief you can hand over."],
  ["Supported, not abandoned", "When you want a person, a private readiness review is one click away."],
  ["Clear on where you stand", "An honest readiness score across five areas, with the reasoning behind it, so you always know where you are today."]
];

const journeySteps = [
  ["1", "Begin privately", "A short trust step first: what we collect, why, and your control over it. Then start whenever you're ready."],
  ["2", "Share at your pace", "Easy questions first, sensitive ones later, with reassurance before each. “I don't know” is always a fine answer."],
  ["3", "See where you stand", "A readiness score with the reasoning behind it, your biggest opportunities, and successor paths weighed your way."],
  ["4", "Bring in a person when ready", "Book a private readiness review. A human picks up exactly where you left off, with only what you chose to share."]
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

  function updateLead(field, value) {
    setLead((current) => ({ ...current, [field]: value }));
  }

  async function submitLead(intent) {
    setStatus("Saving your request...");
    try {
      await apiFetch("/leads", {
        method: "POST",
        body: JSON.stringify({ ...lead, intent })
      });
      setStatus("Saved. You can start privately now, or use this request for follow-up.");
    } catch (error) {
      setStatus(`Could not save yet: ${error.message}`);
    }
  }

  const advisorMessage = `I am looking at StewardPath because I want to prepare before any buyer defines the terms. I want help understanding what must be protected, where the business may depend too much on me, and what information should stay private until there is real successor fit.`;

  return (
    <main className="publicShell">
      <section className="publicHero">
        <p className="publicEyebrow">Private, guided transition readiness for founder-led businesses</p>
        <h1>Before you sell, decide what must be protected.</h1>
        <div className="heroLower">
          <div className="heroLead">
            <p>
              You built more than an asset. You built trust with employees,
              customers, family, and your community. StewardPath walks with you
              through a once-in-a-lifetime decision: what could be lost, what to
              prepare, and what kind of next owner would protect it. You won't do
              this alone, and nothing is shared unless you choose to.
            </p>
            <div className="publicActions">
              <a href="/intake" className="primaryCta">Start private readiness check</a>
              <button type="button" onClick={() => submitLead("sample_report")}>Request sample report</button>
              <button type="button" onClick={() => submitLead("readiness_call")}>Book a readiness review</button>
            </div>
            <p className="heroAlt">
              Prefer the classic workbench? <a href="/readiness">Open it here</a>.
            </p>
          </div>
          <aside className="heroReport">
            <span>StewardPath helps you answer</span>
            <strong>What should not be lost if you step back?</strong>
            <ul>
              <li>Where the business still depends on you</li>
              <li>What a careful buyer may question</li>
              <li>Which successor paths fit your values</li>
              <li>What to keep private until fit is real</li>
              <li>What to prepare before advisor conversations</li>
            </ul>
          </aside>
        </div>
      </section>

      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Who this is for</p>
          <h2>You may not be ready to “sell.” You may be ready to protect the handoff.</h2>
        </div>
        <div className="publicGrid three">
          <article><strong>You have no clear successor.</strong><p>Your children may not want the business, employees may not be ready, and outside buyers may not understand the culture.</p></article>
          <article><strong>You worry about the wrong buyer.</strong><p>You want a fair price, but not at the cost of staff, customer trust, service standards, or the company name.</p></article>
          <article><strong>You need a cleaner advisor conversation.</strong><p>You want your CPA, attorney, banker, or planner to see the full picture before a broker or buyer frames it for you.</p></article>
        </div>
      </section>

      <section className="publicBand" id="how-it-works">
        <div>
          <p className="publicEyebrow">How it works</p>
          <h2>We stay with you, it's not just a report.</h2>
          <p>StewardPath is something you can come back to, a guided check, a plan, and a readiness picture that updates as you prepare, not a one-time report you file away.</p>
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
          <h2>A readiness program that turns private worry into clear next steps.</h2>
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
          <p className="publicEyebrow">What owners tell us they want to feel</p>
          <h2>The point isn't a document. It's how the decision finally feels.</h2>
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
          <h2>You choose what stays private until successor fit is real.</h2>
          <p>
            Share ranges and your own words, never exact figures. Revenue band,
            customer concentration, owner dependency, key-employee risk, whether
            procedures are documented. Everything is private by default; mark
            anything advisor-only, or share later with a serious match.
          </p>
        </div>
        <div className="privacyBox">
          <strong>This is not a broker pitch.</strong>
          <p>Private by default. Never shared with employees, family, or buyers unless you choose to. Never used to train AI. Export or permanently delete your data anytime. StewardPath is preparation support, not legal, tax, investment, valuation, or brokerage advice.</p>
        </div>
      </section>

      <section className="publicBand leadPanel">
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
            <button type="button" onClick={() => submitLead("sample_report")}>Request sample report</button>
            <button type="button" onClick={() => navigator.clipboard?.writeText(advisorMessage)}>Copy advisor message</button>
          </div>
        </form>
        {status ? <p className="leadStatus">{status}</p> : null}
      </section>

      <section className="publicBand offerBand">
        <article><span>Free</span><strong>Sample report</strong><p>See the questions, the score, and the kind of next steps StewardPath prepares.</p></article>
        <article><span>$249</span><strong>Owner readiness report</strong><p>Your private, guided readiness, with the reasoning behind every score, to review before advisor or buyer conversations.</p></article>
        <article><span>$1,500</span><strong>Concierge readiness package</strong><p>Guided intake plus a private readiness review with a person, and transition-conversation prep. Supported, not left to software.</p></article>
        <article><span>$199/mo</span><strong>Advisor pilot</strong><p>For CPAs, exit planners, and advisors supporting up to 10 owner clients.</p></article>
      </section>
    </main>
  );
}
