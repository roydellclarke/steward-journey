import QuickRead from "../components/QuickRead";
import StewardCard from "../components/StewardCard";
import { STEWARD_READY } from "../../lib/steward";
import { MOMENTS } from "../../lib/content";
import "./preview.css";

// A second front door, built beside the current homepage rather than on top of
// it. Both stay reachable so they can be compared side by side.
//
// What changes here, and why:
//  - One thing to do above the fold, not three buttons where two only scroll.
//  - The owner gets something true about their own business before anyone asks
//    who they are.
//  - The finished report is a page you can read, not a form that promises one.
//  - The person behind the promise appears on the page (lib/steward.js).
export const metadata = {
  title: "See where you stand, in three questions",
  description:
    "A private way for a founder-led or family business owner to see where they stand before a buyer or broker frames the choice. Three questions, no account, no email.",
  // Not indexed while this sits beside the live homepage, so the two never
  // compete for the same search result.
  robots: { index: false, follow: false }
};

const promises = [
  [
    "It asks, then it listens",
    "The full check asks 38 questions, a few at a time. Easy ones first. \"I don't know\" is a fine answer, and you can stop whenever you want."
  ],
  [
    "You see the reason, not just a number",
    "A score across five areas, each one explained in the words you would use yourself. No jargon, no grading, no lecture."
  ],
  [
    "You leave with something to hand over",
    "A summary for your advisor, a guide for the family talk, a note on the right next owner. Every line comes from what you told us."
  ]
];

export default function PreviewHome() {
  return (
    <main className="publicShell previewShell">
      <section className="previewHero">
        <p className="publicEyebrow">Private, and free to look around</p>
        <h1>Someone will make you an offer. Decide what you protect before they do.</h1>
        <div className="previewHeroBody">
          <div className="previewHeroWords">
            <p>
              You built more than a business. You built trust with the people who work
              for you, the customers who count on you, and a town that knows your name.
            </p>
            <p>
              Start with three questions. You will see where you stand in about a minute.
              Nothing is saved, nothing is sent, and nobody is told.
            </p>
            <p className="previewAside">
              Rather read one first? <a href="/sample">See a finished report, start to finish.</a>
            </p>
          </div>
          <QuickRead />
        </div>
      </section>

      <section className="publicBand previewDoors">
        <p className="publicEyebrow">Start where you actually are</p>
        <h2>Which one sounds like you right now?</h2>
        <ul className="previewMoments">
          {MOMENTS.map((moment) => (
            <li key={moment.slug}>
              <a href={`/content/${moment.slug}`}>
                <strong>{moment.door}</strong>
                <span>{moment.title}</span>
              </a>
            </li>
          ))}
        </ul>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">If you keep going</p>
        <h2>The full check, in three plain promises.</h2>
        <div className="previewGrid">
          {promises.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      {STEWARD_READY ? (
        <section className="publicBand">
          <p className="publicEyebrow">Who you are dealing with</p>
          <h2>A person, not a company voice.</h2>
          <StewardCard />
        </section>
      ) : null}

      <section className="publicBand previewSplit">
        <div>
          <p className="publicEyebrow">Privacy first</p>
          <h2>You decide what leaves this page, and when.</h2>
          <p>
            Share ranges and your own words, never exact numbers. Your answers stay
            private by default: not your family, not your employees, not a buyer, unless
            you choose. You can export everything or delete it for good, any day you like.
          </p>
        </div>
        <div className="privacyBox">
          <strong>This is not a broker pitch.</strong>
          <p>
            Nobody calls you because you read this page. Your answers are never used to
            train AI. StewardPath prepares you for the conversations ahead. It does not
            give legal, tax, valuation, investment, or brokerage advice, and it sends that
            work to qualified people.
          </p>
        </div>
      </section>

      <section className="publicBand previewClose">
        <p className="publicEyebrow">When you are ready</p>
        <h2>The check is free to start. You keep what it builds.</h2>
        <p>
          The Owner Readiness Program costs $249 and stays with you: your answers, your
          plan, and a score that climbs as you get ready. A concierge package and an
          advisor plan sit alongside it.
        </p>
        <div className="previewActions">
          <a className="primaryCta" href="/intake">Start the private check</a>
          <a className="quickGhost" href="/sample">Read a finished report</a>
        </div>
      </section>
    </main>
  );
}
