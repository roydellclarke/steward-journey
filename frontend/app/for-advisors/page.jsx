import CopyLine from "../components/CopyLine";
import { MOMENTS } from "../../lib/content";
import { SITE_URL } from "../../lib/site";
import "./advisors.css";

// The advisor door. Most owners in this market do not find a product and then
// tell their CPA. They ask their CPA, and the CPA decides what to hand them.
// This page is written for that person: third person about the owner, no
// owner-facing second person, and the proof (a finished report) one click away.
const TITLE = "For CPAs, attorneys, and planners";
const DESCRIPTION =
  "StewardPath prepares an owner before the transition conversation starts: a readiness score across five areas, what they refuse to lose in their own words, and a brief you can read in five minutes. No commission, no brokerage, no competing for your client.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/for-advisors" },
  openGraph: { title: TITLE, description: DESCRIPTION, url: `${SITE_URL}/for-advisors`, type: "website" }
};

const CLIENT_MESSAGE =
  "Before we talk again about the transition, I would like you to look at something on your own time. " +
  "It is a private readiness check built for owners in your position: thirty-eight plain questions, at your pace, " +
  "and it gives you a score across five areas with the reasoning behind each one. Nothing is shared with me or with " +
  "anyone else unless you decide to share it. It is preparation, not advice, and it does not replace the work we do " +
  "together. It gives us a better starting point. Here it is: {url}";

const value = [
  [
    "The client arrives with the work done",
    "The owner answers thirty-eight questions in private and brings a readiness score across five areas, each one explained. The hour you would have spent assembling the picture goes to judgment instead."
  ],
  [
    "You see what they refuse to lose",
    "Most transition conversations stall on something the owner never said out loud. The program asks for it directly and writes it down in their words, before price enters the room."
  ],
  [
    "The successor question is already weighed",
    "Family, a key employee, a manager, an outside buyer: each is scored against the owner's own criteria, and anyone who crosses a stated non-negotiable is ruled out."
  ],
  [
    "Nothing competes with you",
    "StewardPath takes no commission and runs no deals. It does not give legal, tax, valuation, investment, or brokerage advice, and it routes regulated work to the qualified person. That is you."
  ]
];

export default function ForAdvisors() {
  return (
    <main className="publicShell advisorsShell">
      <section className="publicBand advisorsHead">
        <p className="publicEyebrow">{TITLE}</p>
        <h1>Your client arrives prepared, and you bill for judgment instead of assembly.</h1>
        <p className="advisorsLede">
          An owner facing a sale or a succession usually asks their accountant first. By the
          time the question reaches you it is vague, late, and tangled up with feelings nobody
          has named. StewardPath does the naming, in private, before the meeting.
        </p>
        <p className="advisorsActions">
          <a className="primaryCta" href="/sample">Read a finished report</a>
          <a className="quickGhost" href="/#pricing">See the advisor pilot</a>
        </p>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">What it does for your practice</p>
        <h2>Four things that change in the first meeting.</h2>
        <div className="advisorsGrid">
          {value.map(([title, body]) => (
            <article key={title}>
              <strong>{title}</strong>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">Send it to a client</p>
        <h2>A note you can paste, written for an owner to read.</h2>
        <p className="advisorsLede">
          It says what the program is, what it is not, and that you will not see their answers
          unless they choose to show you. That last part is why owners finish it.
        </p>
        <CopyLine
          template={CLIENT_MESSAGE}
          fallbackOrigin={SITE_URL}
          label="Copy the note"
        />
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">Or send the page that fits their situation</p>
        <h2>Four moments, four plain pages.</h2>
        <ul className="advisorsMoments">
          {MOMENTS.map((moment) => (
            <li key={moment.slug}>
              <a href={`/content/${moment.slug}`}>{moment.title}</a>
            </li>
          ))}
        </ul>
      </section>

      <section className="publicBand advisorsClose">
        <p className="publicEyebrow">What the owner controls</p>
        <h2>Their answers stay theirs.</h2>
        <p className="advisorsLede">
          Everything an owner enters is private by default. It is never shared with family,
          employees, or a buyer unless they choose it, and it is never used to train AI. They
          can export it or delete it on any day. When they want you to see a brief, they send
          it to you themselves.
        </p>
      </section>
    </main>
  );
}
