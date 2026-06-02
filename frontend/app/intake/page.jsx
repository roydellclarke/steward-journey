"use client";

import { useEffect, useMemo, useState } from "react";
import { intakeApi, fieldPatch, prettify } from "../../lib/intake";
import "./intake.css";

const STORAGE_KEY = "stewardpath.intake.projectId";

// Plain-language labels for the five readiness drivers, shown in the report.
// The underlying score keys are unchanged (the backend and classic page use them).
const DRIVER_LABELS = {
  financial_clarity: "Financial clarity",
  operational_transferability: "How well it runs without you",
  process_documentation: "What's written down",
  family_alignment: "Family on the same page",
  owner_emotional_readiness: "Your readiness to step back"
};

export default function IntakePage() {
  const [step, setStep] = useState("trust"); // trust | intake | report
  const [projectId, setProjectId] = useState("");
  const [intakeState, setIntakeState] = useState(null);
  const [plan, setPlan] = useState(null);
  const [score, setScore] = useState(null);
  const [sectionIndex, setSectionIndex] = useState(0);
  const [drafts, setDrafts] = useState({}); // questionId -> {value, status}
  const [reflection, setReflection] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [showData, setShowData] = useState(false);
  const [resumeId, setResumeId] = useState("");

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : "";
    if (saved) setResumeId(saved);
  }, []);

  const sections = plan?.sections || [];
  const activeSection = sections[sectionIndex];
  const completion = intakeState?.meta?.completionPct ?? 0;

  async function begin(existingId) {
    setBusy(true);
    setStatus("Setting up your private space…");
    try {
      let pid = existingId;
      if (!pid) {
        const created = await intakeApi.createProject("My readiness");
        pid = created.project.id;
      }
      const loaded = await intakeApi.getIntake(pid);
      setProjectId(pid);
      if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, pid);
      applyLoaded(loaded);
      // Resume at the first section that still has an open question.
      const idx = Math.max(0, (loaded.plan.sections || []).findIndex((s) => !s.complete));
      setSectionIndex(idx === -1 ? 0 : idx);
      setStep("intake");
      setStatus("");
    } catch (error) {
      setStatus(`Could not start: ${error.message}. Is the backend running on the API URL?`);
    } finally {
      setBusy(false);
    }
  }

  function applyLoaded(payload) {
    setIntakeState(payload.intakeState);
    setPlan(payload.plan);
    if (payload.score) setScore(payload.score);
    setDrafts({});
  }

  function setDraft(questionId, value, statusOverride) {
    setDrafts((current) => ({
      ...current,
      [questionId]: { value, status: statusOverride || "answered" }
    }));
  }

  function mergePatches() {
    let patch = {};
    (activeSection?.questions || []).forEach((q) => {
      const draft = drafts[q.id];
      if (!draft) return;
      const single = fieldPatch(q.section, q.field, draft.value, draft.status);
      // deep-merge section objects
      Object.entries(single).forEach(([sectionKey, sectionValue]) => {
        patch[sectionKey] = { ...(patch[sectionKey] || {}), ...sectionValue };
      });
    });
    // record where the owner is, for resume
    patch.meta = { lastSection: activeSection?.key };
    return patch;
  }

  async function saveAndContinue() {
    if (!activeSection) return;
    setBusy(true);
    setStatus("Saving privately…");
    try {
      const patch = mergePatches();
      const saved = await intakeApi.putIntake(projectId, patch);
      applyLoaded(saved);
      // Reflective-summary moment grounded in what was just shared.
      const next = saved.plan.nextQuestionId;
      const ref = await intakeApi.reflect(saved.intakeState, activeSection.key, next);
      setReflection(ref.reflection);
      setStatus("");
    } catch (error) {
      setStatus(`Could not save: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  function advanceAfterReflection() {
    setReflection(null);
    if (sectionIndex < sections.length - 1) {
      setSectionIndex(sectionIndex + 1);
    } else {
      finish();
    }
  }

  async function finish() {
    setBusy(true);
    setStatus("Preparing your readiness…");
    try {
      const result = await intakeApi.analyze(projectId);
      const handoff = await intakeApi.handoff(projectId);
      setReport({ ...result, handoff: handoff.handoff });
      setScore(result.score);
      setStep("report");
      setStatus("");
    } catch (error) {
      setStatus(`Could not prepare report: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  if (step === "trust") {
    return <TrustScreen onBegin={() => begin("")} onResume={resumeId ? () => begin(resumeId) : null} busy={busy} status={status} />;
  }

  if (step === "report" && report) {
    return (
      <ReportView
        report={report}
        score={score}
        projectId={projectId}
        onBackToIntake={() => { setStep("intake"); setReport(null); }}
      />
    );
  }

  return (
    <main className="conciergeShell">
      <div className="conciergeMain">
        <ProgressHeader completion={completion} score={score} />
        {reflection ? (
          <ReflectionMoment reflection={reflection} onContinue={advanceAfterReflection} busy={busy} />
        ) : activeSection ? (
          <SectionView
            section={activeSection}
            drafts={drafts}
            onAnswer={setDraft}
            onContinue={saveAndContinue}
            onBack={sectionIndex > 0 ? () => setSectionIndex(sectionIndex - 1) : null}
            busy={busy}
            isLast={sectionIndex === sections.length - 1}
          />
        ) : (
          <p>Loading…</p>
        )}
        {status ? <p className="conciergeStatus" role="status">{status}</p> : null}
      </div>
      <ReadinessSidebar
        score={score}
        completion={completion}
        snapshots={intakeState?.meta?.snapshots || []}
        onOpenData={() => setShowData(true)}
        onSeeReadiness={finish}
        busy={busy}
      />
      {showData ? (
        <DataControlCenter projectId={projectId} onClose={() => setShowData(false)} />
      ) : null}
    </main>
  );
}

function TrustScreen({ onBegin, onResume, busy, status }) {
  return (
    <main className="conciergeShell single">
      <section className="trustCard">
        <p className="conciergeEyebrow">Private readiness</p>
        <h1>First, how this stays private.</h1>
        <ul className="trustList">
          <li><strong>What we collect:</strong> ranges and your own words. Never exact figures.</li>
          <li><strong>Why:</strong> so your plan fits your situation and protects what you name.</li>
          <li><strong>Private by default:</strong> no one sees this. Not family, not employees, not buyers. Not unless you choose.</li>
          <li><strong>You hold the keys:</strong> you decide later what to share, and with whom.</li>
          <li><strong>Never used to train AI:</strong> your answers stay yours. We do not feed them to any system.</li>
          <li><strong>Yours to erase:</strong> export your data or delete it for good, anytime.</li>
        </ul>
        <p className="trustScope">StewardPath prepares you. It does not give legal, tax, valuation, or investment advice. Stop, skip, or come back whenever you need.</p>
        <div className="trustActions">
          <button type="button" className="primaryCta" onClick={onBegin} disabled={busy}>
            {busy ? "Setting up…" : "Begin privately"}
          </button>
          {onResume ? <button type="button" onClick={onResume} disabled={busy}>Resume where I left off</button> : null}
        </div>
        {status ? <p className="conciergeStatus" role="status">{status}</p> : null}
      </section>
    </main>
  );
}

function ProgressHeader({ completion, score }) {
  return (
    <header className="progressHeader">
      <div>
        <p className="conciergeEyebrow">Your readiness, taking shape</p>
        <h2>Move at your pace. You can stop and resume anytime.</h2>
      </div>
      <div className="progressMeta">
        <span>{completion}% complete</span>
        <div className="progressRail"><i style={{ width: `${completion}%` }} /></div>
        {score ? <small>Readiness so far: {score.overall}/100</small> : null}
      </div>
    </header>
  );
}

function SectionView({ section, drafts, onAnswer, onContinue, onBack, busy, isLast }) {
  return (
    <section className="sectionCard">
      <p className="conciergeEyebrow">{section.title}</p>
      <p className="sectionIntro">{section.intro}</p>
      {section.securityGate && section.reassurance ? (
        <div className="reassureBanner">
          <span aria-hidden="true">🔒</span>
          <p>{section.reassurance}</p>
        </div>
      ) : null}
      <div className="questionList">
        {section.questions.map((q) => (
          <QuestionInput key={q.id} question={q} draft={drafts[q.id]} onAnswer={onAnswer} />
        ))}
      </div>
      <div className="sectionActions">
        {onBack ? <button type="button" onClick={onBack} disabled={busy}>Back</button> : <span />}
        <button type="button" className="primaryCta" onClick={onContinue} disabled={busy}>
          {busy ? "Saving…" : isLast ? "Finish & see readiness" : "Continue"}
        </button>
      </div>
    </section>
  );
}

function QuestionInput({ question, draft, onAnswer }) {
  const [showWhy, setShowWhy] = useState(false);
  // Existing stored value/status shown if no fresh draft.
  const current = draft ?? (question.value != null
    ? { value: question.value, status: question.status }
    : { value: question.kind === "multi" ? [] : "", status: question.status });
  const value = current.value;
  const skipped = current.status === "skipped";
  const unknown = current.status === "unknown" && (value == null || value === "" || (Array.isArray(value) && !value.length));

  function setValue(next) {
    onAnswer(question.id, next, "answered");
  }
  function toggleMulti(optionValue) {
    const list = Array.isArray(value) ? value : [];
    const next = list.includes(optionValue) ? list.filter((v) => v !== optionValue) : [...list, optionValue];
    onAnswer(question.id, next, "answered");
  }

  return (
    <div className={`questionBlock${question.sensitive ? " sensitive" : ""}`}>
      <div className="questionPrompt">
        <label>{question.prompt}</label>
        {question.why ? (
          <button type="button" className="whyLink" onClick={() => setShowWhy((s) => !s)}>
            {showWhy ? "Hide" : "Why we ask"}
          </button>
        ) : null}
      </div>
      {showWhy && question.why ? <p className="whyText">{question.why}</p> : null}
      {question.helpText ? <p className="helpText">{question.helpText}</p> : null}

      {(question.kind === "text") && (
        <input value={value || ""} placeholder={question.placeholder} onChange={(e) => setValue(e.target.value)} />
      )}
      {(question.kind === "longtext") && (
        <textarea value={value || ""} placeholder={question.placeholder} onChange={(e) => setValue(e.target.value)} />
      )}
      {question.kind === "boolean" && (
        <div className="choiceRow">
          {[["yes", true], ["no", false]].map(([label, v]) => (
            <button type="button" key={label} className={value === v ? "choice active" : "choice"} onClick={() => setValue(v)}>
              {label === "yes" ? "Yes" : "No"}
            </button>
          ))}
        </div>
      )}
      {(question.kind === "single" || question.kind === "band") && (
        <div className="choiceWrap">
          {question.options.map((opt) => (
            <button type="button" key={opt.value} className={value === opt.value ? "choice active" : "choice"} onClick={() => setValue(opt.value)}>
              {opt.label}
            </button>
          ))}
        </div>
      )}
      {question.kind === "multi" && (
        <div className="choiceWrap">
          {question.options.map((opt) => {
            const list = Array.isArray(value) ? value : [];
            return (
              <button type="button" key={opt.value} className={list.includes(opt.value) ? "choice active" : "choice"} onClick={() => toggleMulti(opt.value)}>
                {opt.label}
              </button>
            );
          })}
        </div>
      )}
      {question.kind === "scale" && (
        <div className="choiceRow scale">
          {[1, 2, 3, 4, 5].map((n) => (
            <button type="button" key={n} className={value === n ? "choice active" : "choice"} onClick={() => setValue(n)}>{n}</button>
          ))}
        </div>
      )}

      <div className="skipRow">
        {question.allowUnknown ? (
          <button type="button" className={unknown ? "softBtn active" : "softBtn"} onClick={() => onAnswer(question.id, null, "unknown")}>
            I don't know
          </button>
        ) : null}
        {question.allowSkip ? (
          <button type="button" className={skipped ? "softBtn active" : "softBtn"} onClick={() => onAnswer(question.id, null, "skipped")}>
            Skip for now
          </button>
        ) : null}
      </div>
    </div>
  );
}

function ReflectionMoment({ reflection, onContinue, busy }) {
  return (
    <section className="reflectionCard">
      <p className="conciergeEyebrow">A moment to take stock</p>
      <p className="reflectionText">{reflection.text}</p>
      <button type="button" className="primaryCta" onClick={onContinue} disabled={busy}>Continue</button>
    </section>
  );
}

function ReadinessSidebar({ score, completion, snapshots, onOpenData, onSeeReadiness, busy }) {
  return (
    <aside className="readinessSidebar">
      <div className="sidebarScore">
        <span>Readiness so far</span>
        <strong>{score ? `${score.overall}/100` : ", "}</strong>
        <small>{completion}% of intake complete</small>
      </div>
      {score?.topGaps?.length ? (
        <div className="sidebarGaps">
          <span>Biggest opportunities</span>
          <ul>{score.topGaps.slice(0, 3).map((g) => <li key={g.gap}>{g.gap}</li>)}</ul>
        </div>
      ) : null}
      {snapshots.length > 1 ? (
        <div className="sidebarTrend">
          <span>Your progress over time</span>
          <div className="trendBars">
            {snapshots.slice(-8).map((s, i) => (
              <i key={i} style={{ height: `${Math.max(6, s.readinessScore)}%` }} title={`${s.readinessScore}/100`} />
            ))}
          </div>
        </div>
      ) : null}
      <div className="sidebarActions">
        <button type="button" className="primaryCta" onClick={onSeeReadiness} disabled={busy}>See my readiness</button>
        <button type="button" onClick={onOpenData}>Your data &amp; privacy</button>
      </div>
      <p className="sidebarPrivacy">Private by default. Not legal, tax, valuation, or investment advice.</p>
    </aside>
  );
}

function DataControlCenter({ projectId, onClose }) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    intakeApi.exportData(projectId).then(setData).catch((e) => setStatus(e.message));
  }, [projectId]);

  function download() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "stewardpath-your-data.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function remove() {
    if (!window.confirm("Permanently delete everything stored for this readiness? This cannot be undone.")) return;
    try {
      await intakeApi.deleteProject(projectId);
      if (typeof window !== "undefined") window.localStorage.removeItem(STORAGE_KEY);
      setStatus("Deleted. Reloading…");
      setTimeout(() => window.location.reload(), 900);
    } catch (e) {
      setStatus(e.message);
    }
  }

  const analyses = data?.analyses?.length || 0;
  const events = data?.auditEvents || [];

  return (
    <div className="dataOverlay" role="dialog" aria-modal="true">
      <div className="dataPanel">
        <div className="dataHead">
          <h2>Your data &amp; privacy</h2>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <p>Everything here stays private by default. Nothing is shared unless you choose to, and your answers are never used to train AI.</p>
        <ul className="dataStats">
          <li><strong>Your answers</strong><span>{data ? `${data.intakeState?.meta?.completionPct || 0}% filled in` : "…"}</span></li>
          <li><strong>Saved readiness reports</strong><span>{analyses}</span></li>
          <li><strong>Who can see this</strong><span>{(data?.intakeState?.disclosureControls?.defaultVisibility || "private") === "private" ? "Only you" : data.intakeState.disclosureControls.defaultVisibility}</span></li>
        </ul>
        {events.length ? (
          <div className="auditList">
            <span>Activity log</span>
            <ul>{events.slice(0, 6).map((e) => <li key={e.id}>{new Date(e.at).toLocaleString()} · {prettify(e.action)}</li>)}</ul>
          </div>
        ) : null}
        <div className="dataActions">
          <button type="button" onClick={download} disabled={!data}>Export my data</button>
          <button type="button" className="danger" onClick={remove}>Delete everything</button>
        </div>
        {status ? <p className="conciergeStatus">{status}</p> : null}
      </div>
    </div>
  );
}

function ReportView({ report, score, projectId, onBackToIntake }) {
  const synthesis = report.analysis;
  const handoff = report.handoff;
  const [showBook, setShowBook] = useState(false);

  return (
    <main className="conciergeShell single report">
      <header className="reportHead">
        <div>
          <p className="conciergeEyebrow">Your readiness</p>
          <h1>{score.overall}/100</h1>
          <p>{score.interpretation}</p>
        </div>
        <button type="button" onClick={onBackToIntake}>Keep refining</button>
      </header>

      <section className="reportSection">
        <h3>Why your score looks like this</h3>
        <div className="driverGrid">
          {Object.entries(score.dimensions).map(([key, value]) => (
            <DriverCard key={key} label={DRIVER_LABELS[key] || prettify(key)} value={value} rationale={synthesis.scoreRationale?.[key]} />
          ))}
        </div>
      </section>

      {score.topGaps?.length ? (
        <section className="reportSection">
          <h3>Where to focus next</h3>
          <ol className="gapList">
            {score.topGaps.map((g) => (
              <li key={g.gap}><strong>{g.gap}</strong><p>{g.nextStep}</p></li>
            ))}
          </ol>
        </section>
      ) : null}

      <section className="reportSection">
        <h3>Successor paths, weighed against what you value</h3>
        <div className="pathGrid">
          {synthesis.buyerFit?.paths?.map((p) => (
            <article key={p.key} className={p.preferred ? "pathCard preferred" : "pathCard"}>
              <div className="pathHead"><strong>{p.path}</strong>{p.preferred ? <span>Your preference</span> : null}</div>
              <p>{p.summary}</p>
              <small>Trade-off: {p.tradeoff}</small>
            </article>
          ))}
        </div>
        {synthesis.buyerFit?.excluded?.length ? (
          <p className="excludedNote">Excluded at your request: {synthesis.buyerFit.excluded.map((e) => e.path).join(", ")}.</p>
        ) : null}
      </section>

      <section className="reportSection">
        <h3>Briefs you can use</h3>
        {Object.entries(synthesis.narratives || {}).map(([key, body]) => (
          <article key={key} className="briefCard">
            <div><span>{prettify(key)}</span><p>{body}</p></div>
            <button type="button" onClick={() => navigator.clipboard?.writeText(body)}>Copy</button>
          </article>
        ))}
      </section>

      <section className="reportSection routing">
        <h3>{handoff?.routing?.headline || "Your next step"}</h3>
        <p>{handoff?.routing?.body}</p>
        <button type="button" className="primaryCta" onClick={() => setShowBook(true)}>{handoff?.routing?.cta || "Book a private readiness review"}</button>
      </section>

      <section className="disclaimerBand">
        {(synthesis.disclaimers || []).map((d) => <span key={d}>{d}</span>)}
      </section>

      {showBook ? <BookReview projectId={projectId} onClose={() => setShowBook(false)} /> : null}
    </main>
  );
}

function DriverCard({ label, value, rationale }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="driverCard">
      <div className="driverTop">
        <span>{label}</span>
        <strong>{value}/5</strong>
      </div>
      <div className="bar"><i style={{ width: `${(value / 5) * 100}%` }} /></div>
      <button type="button" className="whyLink" onClick={() => setOpen((o) => !o)}>{open ? "Hide why" : "Why?"}</button>
      {open ? <p className="driverWhy">{rationale}</p> : null}
    </article>
  );
}

function BookReview({ projectId, onClose }) {
  const [form, setForm] = useState({ name: "", email: "", preferredTime: "", note: "" });
  const [status, setStatus] = useState("");

  async function submit() {
    setStatus("Requesting your review…");
    try {
      await intakeApi.bookReview(projectId, form);
      setStatus("Requested. We'll be in touch privately to confirm a time.");
    } catch (e) {
      setStatus(e.message);
    }
  }

  return (
    <div className="dataOverlay" role="dialog" aria-modal="true">
      <div className="dataPanel">
        <div className="dataHead"><h2>Private readiness review</h2><button type="button" onClick={onClose} aria-label="Close">×</button></div>
        <p>A person reviews what you've prepared and helps you turn it into a clear, paced plan. We only see what you've chosen to share.</p>
        <input placeholder="Your name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input placeholder="Preferred time, e.g. next week mornings" value={form.preferredTime} onChange={(e) => setForm({ ...form, preferredTime: e.target.value })} />
        <textarea placeholder="Anything you'd like us to know first (optional)" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        <div className="dataActions">
          <button type="button" className="primaryCta" onClick={submit}>Request review</button>
        </div>
        {status ? <p className="conciergeStatus">{status}</p> : null}
      </div>
    </div>
  );
}
