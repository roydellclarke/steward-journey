import { AREA_LABELS, BUYER_VIEW_LABELS, bandWord } from "../../lib/labels";
import { SITE_URL } from "../../lib/site";
import QuickRead from "../components/QuickRead";
import "./sample.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const TITLE = "A finished readiness report, start to finish";
const DESCRIPTION =
  "The whole report StewardPath builds with an owner, shown on a made-up machine shop: the readiness score across five areas, what a careful buyer would question, the transfer paths weighed, the plan, and the briefs. No sign-up, no email.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/sample" },
  openGraph: { title: TITLE, description: DESCRIPTION, url: `${SITE_URL}/sample`, type: "article" },
  twitter: { card: "summary_large_image", title: TITLE, description: DESCRIPTION }
};

// The sample is deterministic and cheap to build, so it renders fresh on each
// request rather than baking at build time. That keeps a backend that is down
// during a build from freezing the fallback into a static page.
async function loadSample() {
  try {
    const response = await fetch(`${API_BASE}/sample`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

function Bar({ score }) {
  return (
    <span className="sampleBar" aria-hidden="true">
      {[1, 2, 3, 4, 5].map((step) => (
        <i key={step} className={step <= score ? "on" : ""} />
      ))}
    </span>
  );
}

function ScoreRow({ label, score }) {
  return (
    <li>
      <span className="sampleRowLabel">{label}</span>
      <Bar score={score} />
      <span className="sampleRowBand">{bandWord(score)}</span>
    </li>
  );
}

export default async function SamplePage() {
  const data = await loadSample();

  if (!data) {
    return (
      <main className="publicShell">
        <section className="publicBand">
          <p className="publicEyebrow">Sample report</p>
          <h1>The sample is not loading right now.</h1>
          <p className="sampleLede">
            Nothing is wrong with your account, because you do not need one to read this.
            Try again in a minute, or start your own private check and see the real thing.
          </p>
          <p><a className="primaryCta" href="/intake">Start the private check</a></p>
        </section>
      </main>
    );
  }

  const { request: profile, analysis } = data;
  const { jtbd, readiness, buffett_quality: buyerView, buyer_paths: paths, roadmap, narratives, disclaimers } = analysis;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": `${SITE_URL}/sample#article`,
    headline: TITLE,
    description: DESCRIPTION,
    mainEntityOfPage: `${SITE_URL}/sample`,
    inLanguage: "en-US",
    author: { "@id": `${SITE_URL}/#organization` },
    publisher: { "@id": `${SITE_URL}/#organization` }
  };

  return (
    <main className="publicShell sampleShell">
      <section className="publicBand sampleHead">
        <p className="publicEyebrow">Sample report</p>
        <h1>Read a finished one before you answer a single question.</h1>
        <p className="sampleLede">
          This is the whole report, end to end. It belongs to an owner who does not exist,
          so you can read every part of it without anyone asking who you are.
        </p>
        <p className="sampleNotice">
          <strong>Harbor Tool &amp; Die is made up.</strong> The business, the numbers, and the
          worries are invented to show the shape of a real report. A real one is built only
          from what you tell us, and it stays private.
        </p>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">The owner</p>
        <h2>Who this report belongs to</h2>
        <dl className="sampleFacts">
          <div><dt>Business</dt><dd>{profile.business_name}</dd></div>
          <div><dt>Trade</dt><dd>{profile.industry}</dd></div>
          <div><dt>Years running</dt><dd>{profile.years_operating}</dd></div>
          <div><dt>People</dt><dd>{profile.employees}</dd></div>
          <div><dt>Sales</dt><dd>{profile.revenue_range}</dd></div>
          <div><dt>Timeline</dt><dd>{profile.timeline}</dd></div>
        </dl>
        <blockquote className="sampleQuote">{jtbd.struggling_moment}</blockquote>
        <p className="sampleAttrib">The moment this report was built for.</p>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">Where this owner stands</p>
        <h2>One number, five areas, and the reason behind each.</h2>
        <div className="sampleScore">
          <div className="sampleOverall">
            <strong>{readiness.overall}</strong>
            <span>out of 100</span>
          </div>
          <ul className="sampleRows">
            {Object.entries(readiness.dimensions).map(([key, score]) => (
              <ScoreRow key={key} label={AREA_LABELS[key] || key} score={score} />
            ))}
          </ul>
        </div>
        <p className="sampleInterpretation">{readiness.interpretation}</p>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">Through a buyer's eyes</p>
        <h2>What a careful buyer will look at first.</h2>
        <p className="sampleLede">{buyerView.summary}</p>
        <ul className="sampleRows">
          {Object.entries(buyerView.scores).map(([key, score]) => (
            <ScoreRow key={key} label={BUYER_VIEW_LABELS[key] || key} score={score} />
          ))}
        </ul>
        <div className="sampleAsk">
          <strong>The questions they will ask out loud</strong>
          <ul>
            {buyerView.questions_to_answer.map((question) => <li key={question}>{question}</li>)}
          </ul>
        </div>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">The paths</p>
        <h2>Six ways out, weighed against what this owner refuses to lose.</h2>
        <div className="sampleTableWrap">
          <table className="sampleTable">
            <thead>
              <tr>
                <th scope="col">Path</th>
                <th scope="col">Protects the legacy</th>
                <th scope="col">Money on the table</th>
                <th scope="col">Feels right</th>
              </tr>
            </thead>
            <tbody>
              {paths.map((path) => (
                <tr key={path.path}>
                  <th scope="row">
                    {path.path}
                    <span>{path.notes}</span>
                  </th>
                  <td><Bar score={path.legacy_preservation} /></td>
                  <td><Bar score={path.financial_potential} /></td>
                  <td><Bar score={path.emotional_fit} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">The plan</p>
        <h2>What this owner does next, in order.</h2>
        <ol className="sampleSteps">
          {roadmap.map((step) => (
            <li key={step.phase}>
              <strong>{step.phase.replace(/^\d+\.\s*/, "")}</strong>
              <p>{step.action}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="publicBand">
        <p className="publicEyebrow">The briefs</p>
        <h2>Four pages this owner can hand to someone else.</h2>
        <div className="sampleBriefs">
          <article>
            <strong>What must not be lost</strong>
            <p>{narratives.legacy_statement}</p>
          </article>
          <article>
            <strong>The right next owner</strong>
            <p>{narratives.buyer_criteria_memo}</p>
          </article>
          <article>
            <strong>For the family talk</strong>
            <p>{narratives.family_conversation_guide}</p>
          </article>
          <article>
            <strong>For the advisor</strong>
            <p>{narratives.advisor_brief}</p>
          </article>
        </div>
      </section>

      <section className="publicBand sampleClose">
        <p className="publicEyebrow">Your turn</p>
        <h2>Three questions, and you will know where you stand.</h2>
        <p className="sampleLede">
          No account. No email. Nothing saved until you ask for it.
        </p>
        <QuickRead />
      </section>

      <section className="publicBand sampleLegal">
        <ul>
          {disclaimers.map((line) => <li key={line}>{line}</li>)}
        </ul>
      </section>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    </main>
  );
}
