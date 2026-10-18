"use client";

import { useState } from "react";
import { QUICK_QUESTIONS, readFrom } from "../../lib/quickread";
import { bandWord } from "../../lib/labels";
import "./quickread.css";

// Three questions, one screen each, then an honest partial read. Nothing is
// stored, nothing is sent, and no account is asked for. The owner gets
// something true about their own business before StewardPath asks for
// anything at all.
export default function QuickRead() {
  const [answers, setAnswers] = useState({});
  const [index, setIndex] = useState(0);

  const question = QUICK_QUESTIONS[index];
  const read = readFrom(answers);
  const done = index >= QUICK_QUESTIONS.length;

  function choose(value) {
    setAnswers((current) => ({ ...current, [question.id]: value }));
    setIndex((current) => current + 1);
  }

  function restart() {
    setAnswers({});
    setIndex(0);
  }

  if (done && read) {
    return (
      <section className="quickRead quickRead--result" aria-live="polite">
        <p className="quickEyebrow">What three answers show</p>
        <h3 className="quickHeadline">{read.headline}</h3>
        <p className="quickBody">{read.body}</p>

        <ul className="quickAreas">
          {read.areas.map((area) => (
            <li key={area.area} className={area.isPressure ? "isPressure" : ""}>
              <span className="quickAreaName">{area.area}</span>
              <span className="quickAreaBand">{bandWord(area.weight)}</span>
              <span className="quickAreaAnswer">{area.answer}</span>
            </li>
          ))}
        </ul>

        <div className="quickLimits">
          <strong>What three answers cannot tell you</strong>
          <ul>
            {read.unseen.map((item) => <li key={item}>{item}</li>)}
          </ul>
          <p>The full check asks 38 questions and scores five areas. This one asked three.</p>
        </div>

        <div className="quickActions">
          <a className="primaryCta" href="/intake">Start the full check</a>
          <a className="quickGhost" href="/sample">Read a finished report first</a>
          <button type="button" className="quickRestart" onClick={restart}>Start over</button>
        </div>
        <p className="quickFine">Free to start. Private by default. Stop whenever you want.</p>
      </section>
    );
  }

  return (
    <section className="quickRead">
      <div className="quickTop">
        <p className="quickEyebrow">Free, no account</p>
        <span className="quickCount">Question {index + 1} of {QUICK_QUESTIONS.length}</span>
      </div>
      <h3 className="quickPrompt">{question.prompt}</h3>
      <p className="quickWhy">{question.why}</p>
      <div className="quickOptions" role="group" aria-label={question.prompt}>
        {question.options.map((option) => (
          <button key={option.value} type="button" onClick={() => choose(option.value)}>
            {option.label}
          </button>
        ))}
      </div>
      {index > 0 ? (
        <button type="button" className="quickBack" onClick={() => setIndex(index - 1)}>
          Back
        </button>
      ) : null}
    </section>
  );
}
