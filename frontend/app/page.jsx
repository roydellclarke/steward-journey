"use client";

import { useState } from "react";
import { apiFetch } from "../lib/api";

const sampleSections = [
  ["Readiness", "See where the business may lose value or trust if you wait too long."],
  ["What Matters", "Name the employees, customers, standards, and reputation you want protected."],
  ["Business Quality", "Spot the questions a careful buyer may ask before those questions cost you leverage."],
  ["Buyer Fit", "Compare successor paths by continuity, financial outcome, and emotional fit."],
  ["Your Next Steps", "Leave with a short preparation plan you can discuss with advisors and family."]
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
      const payload = await apiFetch("/leads", {
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
        <div>
          <p className="publicEyebrow">Private transition readiness for founder-led businesses</p>
          <h1>Before you sell, decide what must be protected.</h1>
          <p>
            You built more than an asset. You built trust with employees,
            customers, family, and your community. StewardPath helps you see
            what could be lost, what must be prepared, and what kind of next
            owner may actually protect what you built.
          </p>
          <div className="publicActions">
            <a href="/intake" className="primaryCta">Start private readiness check</a>
            <button type="button" onClick={() => submitLead("sample_report")}>Request sample report</button>
            <button type="button" onClick={() => submitLead("readiness_call")}>Book readiness call</button>
          </div>
          <p style={{ marginTop: "10px", fontSize: "0.85rem" }}>
            Prefer the classic workbench? <a href="/readiness">Open it here</a>.
          </p>
        </div>
        <aside className="heroReport">
          <span>Your report helps you answer</span>
          <strong>What should not be lost if you step back?</strong>
          <ul>
            <li>Where the business still depends on you</li>
            <li>What a buyer may question</li>
            <li>Which successor paths fit your values</li>
            <li>What to share with advisors first</li>
          </ul>
        </aside>
      </section>

      <section className="publicBand">
        <div>
          <p className="publicEyebrow">Who this is for</p>
          <h2>You may not be ready to “sell.” You may be ready to protect the handoff.</h2>
        </div>
        <div className="publicGrid three">
          <article><strong>You have no clear successor.</strong><p>Your children may not want the business, employees may not be ready, and outside buyers may not understand the culture.</p></article>
          <article><strong>You worry about the wrong buyer.</strong><p>You want price, but not at the cost of staff, customer trust, service standards, or the company name.</p></article>
          <article><strong>You need a cleaner advisor conversation.</strong><p>You want your CPA, attorney, banker, or planner to see the full picture before a broker or buyer frames it for you.</p></article>
        </div>
      </section>

      <section className="publicBand reportPreview">
        <div>
          <p className="publicEyebrow">What you get</p>
          <h2>A readiness report that turns private worry into next steps.</h2>
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

      <section className="publicBand split">
        <div>
          <p className="publicEyebrow">Financial clarity without oversharing</p>
          <h2>You choose what stays private until successor fit is real.</h2>
          <p>
            Add revenue range, margin, debt, customer concentration, recurring
            revenue, owner compensation, key employee risk, and whether SOPs
            are documented. Mark sensitive details as private, advisor-only,
            or share later with a serious match.
          </p>
        </div>
        <div className="privacyBox">
          <strong>This is not a broker pitch.</strong>
          <p>You control what gets shared. StewardPath is preparation support, not legal, tax, investment, valuation, or brokerage advice.</p>
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
        <article><span>Free</span><strong>Sample report</strong><p>See the kind of questions and next steps StewardPath prepares.</p></article>
        <article><span>$249</span><strong>Owner readiness report</strong><p>Prepare a private report you can review before advisor or buyer conversations.</p></article>
        <article><span>$1,500</span><strong>Concierge readiness package</strong><p>Guided intake, reviewed report, and transition conversation prep.</p></article>
        <article><span>$199/mo</span><strong>Advisor pilot</strong><p>For advisors serving up to 10 owner clients.</p></article>
      </section>
    </main>
  );
}
