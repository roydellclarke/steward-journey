"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useModalA11y } from "./useModalA11y";
import { intakeApi, fieldPatch, prettify } from "../../lib/intake";
import { authApi } from "../../lib/auth";
import AuthGate from "./AuthGate";
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
  const [authGate, setAuthGate] = useState(null); // null | "save" | "report"
  const [account, setAccount] = useState({ authenticated: false, email: "", entitlements: [] });
  const [pendingResume, setPendingResume] = useState(""); // a claimed project awaiting sign-in
  const [showBook, setShowBook] = useState(false);
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : "";
    if (saved) setResumeId(saved);
    // Restore any existing session so we can greet a returning owner by email.
    authApi.me().then((me) => {
      if (me.authenticated) setAccount({ authenticated: true, email: me.email, entitlements: me.entitlements || [] });
    }).catch(() => {});
  }, []);

  // Concierge buyers paid for a private review with a person. Surface it as a
  // clear step inside the program, not just a line on the receipt.
  const hasConcierge = (account.entitlements || []).some((e) => e.product === "concierge" && e.status === "active");

  // After a gate passes we have a live session but not the owner's paid
  // entitlements. Pull them so concierge/advisor features survive sign-in
  // (the verify result carries only the email).
  function refreshEntitlements(email) {
    authApi.me().then((me) => {
      if (me.authenticated) {
        setAccount({ authenticated: true, email: me.email || email, entitlements: me.entitlements || [] });
      }
    }).catch(() => {});
  }

  function onSaveGatePassed(result) {
    setAccount((a) => ({ ...a, authenticated: true, email: result.email }));
    refreshEntitlements(result.email);
    setAuthGate(null);
    if (pendingResume) {
      // Signing in to resume a claimed project: retry the load, now with a session.
      const id = pendingResume;
      setPendingResume("");
      begin(id, true);
      return;
    }
    setStatus(`Saved. We emailed ${result.email} a secure link to pick this back up anytime.`);
  }

  function onReportGatePassed(result) {
    setAccount((a) => ({ ...a, authenticated: true, email: result.email }));
    refreshEntitlements(result.email);
    setAuthGate(null);
    setStep("report");
  }

  const sections = plan?.sections || [];
  const activeSection = sections[sectionIndex];

  // Live completion: the saved percent, nudged by the answers in progress so the
  // bar moves as the owner picks, not only after Continue saves. It uses the same
  // field counts the backend computes (meta.completeFields/totalFields), so the
  // number never snaps back once the section saves. Falls back to the saved
  // percent for older records that predate the counts.
  const completion = useMemo(() => {
    const meta = intakeState?.meta;
    if (!meta) return 0;
    const total = meta.totalFields || 0;
    if (!total) return meta.completionPct ?? 0;
    const done = new Set(["answered", "estimated", "skipped"]);
    let complete = meta.completeFields || 0;
    (activeSection?.questions || []).forEach((q) => {
      const draft = drafts[q.id];
      if (!draft) return;
      const was = done.has(q.status);
      const now = done.has(draft.status);
      if (now && !was) complete += 1;
      else if (!now && was) complete -= 1;
    });
    complete = Math.max(0, Math.min(total, complete));
    return Math.round((complete / total) * 100);
  }, [intakeState, drafts, activeSection]);

  async function begin(existingId, afterAuth = false) {
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
      // A saved project that is claimed needs the owner's session. If resuming
      // fails and we have not just signed in, prompt sign-in and retry once.
      if (existingId && !afterAuth) {
        setPendingResume(existingId);
        setAuthGate("save");
        setStatus("");
      } else {
        setStatus(`Could not open this readiness: ${error.message}. You may need the secure link from your email.`);
      }
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
    // A fresh answer means there is unsaved work; the debounce will save it.
    setSaveState("saving");
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
      setSaveState("saved");
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

  // Autosave: persist answers in the background so closing the tab mid-section
  // never loses work. It keeps the drafts (so the fields being edited are not
  // disturbed) and refreshes score/plan; the completion delta lands at zero
  // because the saved plan now marks these answered. Explicit Continue still
  // drives the reflection and section advance.
  async function autosave() {
    if (busy || !projectId || !activeSection) return;
    if (!Object.keys(drafts).length) return;
    setSaveState("saving");
    try {
      const saved = await intakeApi.putIntake(projectId, mergePatches());
      setIntakeState(saved.intakeState);
      setPlan(saved.plan);
      if (saved.score) setScore(saved.score);
      setSaveState("saved");
    } catch {
      // Silent: the owner can still click Continue to save explicitly.
      setSaveState("idle");
    }
  }

  // Debounce: save 1.5s after the last change, resetting on each new answer.
  useEffect(() => {
    if (step !== "intake" || reflection) return;
    if (!Object.keys(drafts).length) return;
    const timer = setTimeout(() => { autosave(); }, 1500);
    return () => clearTimeout(timer);
    // autosave is intentionally excluded; the effect re-runs on every draft
    // change, which is exactly when a fresh save should be scheduled.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drafts, step, reflection]);

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
      // Gate 2: an owner signs in before viewing the report. Already-signed-in
      // owners go straight through; everyone else passes the report gate first.
      if (account.authenticated) {
        setStep("report");
      } else {
        setAuthGate("report");
      }
      setStatus("");
    } catch (error) {
      setStatus(`Could not prepare report: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  // One auth modal, reused across every step (trust screen resume, save, report).
  const authGateEl = authGate ? (
    <AuthGate
      gate={authGate}
      projectId={projectId || pendingResume}
      knownEmail={account.email}
      onClose={() => { setAuthGate(null); setPendingResume(""); }}
      onAuthenticated={authGate === "report" ? onReportGatePassed : onSaveGatePassed}
    />
  ) : null;

  if (step === "trust") {
    return (
      <>
        <TrustScreen onBegin={() => begin("")} onResume={resumeId ? () => begin(resumeId) : null} busy={busy} status={status} />
        {authGateEl}
      </>
    );
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
      <ProgressHeader completion={completion} score={score} />
      {hasConcierge ? (
        <div className="conciergeBanner">
          <span>Your concierge package includes a private review with a real person.</span>
          <button type="button" className="primaryCta" onClick={() => setShowBook(true)}>Book your review</button>
        </div>
      ) : null}
      <div className="conciergeGrid">
        <div className="conciergeMain">
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
              saveState={saveState}
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
          onSaveForLater={() => setAuthGate("save")}
          account={account}
          busy={busy}
        />
      </div>
      {showData ? (
        <DataControlCenter projectId={projectId} onClose={() => setShowData(false)} />
      ) : null}
      {showBook ? <BookReview projectId={projectId} onClose={() => setShowBook(false)} /> : null}
      {authGateEl}
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
          <li><strong>What we collect:</strong> ranges and your own words. Never exact numbers.</li>
          <li><strong>Why:</strong> so your plan fits you and guards what you name.</li>
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

function SectionView({ section, drafts, onAnswer, onContinue, onBack, busy, saveState, isLast }) {
  // Live per-section count so the owner sees each answer register right away.
  const done = new Set(["answered", "estimated", "skipped"]);
  const total = section.questions.length;
  const answered = section.questions.filter((q) => {
    const status = drafts[q.id]?.status ?? q.status;
    return done.has(status);
  }).length;
  const saveNote = saveState === "saving"
    ? "Saving…"
    : saveState === "saved"
      ? "Saved. Your answers save as you go."
      : "Your answers save as you go, so you can stop anytime.";
  return (
    <section className="sectionCard">
      <p className="conciergeEyebrow">{section.title}</p>
      <p className="sectionIntro">{section.intro}</p>
      <p className="sectionProgress" aria-live="polite">{answered} of {total} answered in this section</p>
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
      <p className="autosaveNote" aria-live="polite">{saveNote}</p>
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
        <label id={`${question.id}-label`} htmlFor={question.id}>{question.prompt}</label>
        {question.why ? (
          <button type="button" className="whyLink" onClick={() => setShowWhy((s) => !s)}>
            {showWhy ? "Hide" : "Why we ask"}
          </button>
        ) : null}
      </div>
      {showWhy && question.why ? <p className="whyText">{question.why}</p> : null}
      {question.helpText ? <p className="helpText">{question.helpText}</p> : null}

      {(question.kind === "text") && (
        <input id={question.id} value={value || ""} placeholder={question.placeholder} onChange={(e) => setValue(e.target.value)} />
      )}
      {(question.kind === "longtext") && (
        <textarea id={question.id} value={value || ""} placeholder={question.placeholder} onChange={(e) => setValue(e.target.value)} />
      )}
      {question.kind === "boolean" && (
        <div className="choiceRow" role="group" aria-labelledby={`${question.id}-label`}>
          {[["yes", true], ["no", false]].map(([label, v]) => (
            <button type="button" key={label} className={value === v ? "choice active" : "choice"} onClick={() => setValue(v)}>
              {label === "yes" ? "Yes" : "No"}
            </button>
          ))}
        </div>
      )}
      {(question.kind === "single" || question.kind === "band") && (
        <div className="choiceWrap" role="group" aria-labelledby={`${question.id}-label`}>
          {question.options.map((opt) => (
            <button type="button" key={opt.value} className={value === opt.value ? "choice active" : "choice"} onClick={() => setValue(opt.value)}>
              {opt.label}
            </button>
          ))}
        </div>
      )}
      {question.kind === "multi" && (
        <div className="choiceWrap" role="group" aria-labelledby={`${question.id}-label`}>
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
        <div className="choiceRow scale" role="group" aria-labelledby={`${question.id}-label`}>
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

function ReadinessSidebar({ score, completion, snapshots, onOpenData, onSeeReadiness, onSaveForLater, account, busy }) {
  return (
    <aside className="readinessSidebar">
      <div className="sidebarScore">
        <span>Readiness so far</span>
        <strong>{score ? `${score.overall}/100` : "Not yet"}</strong>
        <small>{completion}% of intake complete</small>
        <small className="scoreHint">This score climbs as you answer the questions about your money and how the business runs.</small>
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
        <button type="button" onClick={onSaveForLater} disabled={busy}>Save &amp; finish later</button>
        <button type="button" onClick={onOpenData}>Your data &amp; privacy</button>
      </div>
      {account?.authenticated ? (
        <p className="sidebarSaved">Saved to {account.email}. Resume anytime from the secure link we sent.</p>
      ) : null}
      <p className="sidebarPrivacy">Private by default. Not legal, tax, valuation, or investment advice.</p>
    </aside>
  );
}

function DataControlCenter({ projectId, onClose }) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("");
  const panelRef = useRef(null);
  useModalA11y(panelRef, onClose);

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
    <div className="dataOverlay" role="dialog" aria-modal="true" aria-label="Your data and privacy" ref={panelRef}>
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
          <p className="reportSubnote">This is not a one-time report. Your readiness stays private and saved, and it moves as you prepare.</p>
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

      <ActionPlan projectId={projectId} onBackToIntake={onBackToIntake} />

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

      <SuccessorScorecard projectId={projectId} />

      <section className="reportSection">
        <h3>Briefs you can use</h3>
        <p className="reportLead">Hand these to your advisor or your family. Arriving organized makes their work faster, and lighter on the bill.</p>
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

// Weigh real candidates against what the owner values. Ranked by fit, never by
// offer. A blank rating starts neutral (3); the owner adjusts what matters.
const FIT_CRITERIA = [
  ["keepsPeople", "Protects your employees"],
  ["keepsCustomers", "Keeps customers cared for"],
  ["keepsName", "Honors your name"],
  ["readyToLead", "Ready to lead"],
  ["sharesValues", "Shares your values"],
  ["acceptsTerms", "Accepts your terms"]
];
const KINDS = [
  ["family", "Family member"],
  ["employee", "Key employee"],
  ["manager", "Manager / team"],
  ["outside_buyer", "Outside buyer"],
  ["other", "Other"]
];
const blankCandidate = () => ({
  name: "", kind: "outside_buyer",
  ratings: Object.fromEntries(FIT_CRITERIA.map(([k]) => [k, 3])),
  offerStrength: 3, dealbreaker: false
});

function SuccessorScorecard({ projectId }) {
  const [card, setCard] = useState(null);
  const [draft, setDraft] = useState(blankCandidate());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    intakeApi.successors(projectId).then(setCard).catch(() => setError("Could not load your scorecard."));
  }, [projectId]);

  async function save(nextCandidates) {
    setBusy(true);
    setError("");
    try {
      setCard(await intakeApi.saveSuccessors(projectId, nextCandidates));
    } catch (e) {
      setError(e.message || "Could not save.");
    } finally {
      setBusy(false);
    }
  }

  function addCandidate() {
    if (!draft.name.trim()) { setError("Give the candidate a name first."); return; }
    const existing = (card?.candidates || []).map((c) => ({
      name: c.name, kind: c.kind, ratings: c.ratings, offerStrength: c.offerStrength, dealbreaker: c.dealbreaker, id: c.id
    }));
    save([...existing, { ...draft, name: draft.name.trim() }]);
    setDraft(blankCandidate());
  }

  function removeCandidate(id) {
    const kept = (card?.candidates || []).filter((c) => c.id !== id).map((c) => ({
      name: c.name, kind: c.kind, ratings: c.ratings, offerStrength: c.offerStrength, dealbreaker: c.dealbreaker, id: c.id
    }));
    save(kept);
  }

  return (
    <section className="reportSection">
      <h3>Weigh your successors, on your terms</h3>
      <p className="reportLead">
        Rate each candidate on what matters to you. We rank by fit, not by the size of the offer.
      </p>
      {error ? <p className="conciergeStatus" role="alert">{error}</p> : null}

      {card?.candidates?.length ? (
        <ol className="scoreList">
          {card.candidates.map((c) => (
            <li key={c.id} className={c.ruledOut ? "scoreCard ruled" : "scoreCard"}>
              <div className="scoreHead">
                <div>
                  <strong>{c.name}</strong>
                  <span className="scoreKind">{(KINDS.find((k) => k[0] === c.kind) || [])[1] || c.kind}</span>
                </div>
                <div className="scoreNums">
                  {c.ruledOut ? <span className="ruledTag">Ruled out</span> : <span className="fitTag">Fit {c.fitScore}</span>}
                  <span className="offerTag">Offer {c.offerStrength}/5</span>
                  <button type="button" className="softBtn" onClick={() => removeCandidate(c.id)} disabled={busy}>Remove</button>
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="reportLead">No candidates yet. Add the people, or buyers, you are weighing.</p>
      )}

      <div className="scoreForm">
        <div className="scoreFormRow">
          <input placeholder="Candidate name" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          <select value={draft.kind} onChange={(e) => setDraft({ ...draft, kind: e.target.value })}>
            {KINDS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
        </div>
        <div className="scoreRatings">
          {FIT_CRITERIA.map(([k, label]) => (
            <label key={k} className="ratingField">
              <span>{label}</span>
              <select value={draft.ratings[k]} onChange={(e) => setDraft({ ...draft, ratings: { ...draft.ratings, [k]: Number(e.target.value) } })}>
                {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          ))}
          <label className="ratingField">
            <span>Offer strength</span>
            <select value={draft.offerStrength} onChange={(e) => setDraft({ ...draft, offerStrength: Number(e.target.value) })}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        </div>
        <label className="scoreDealbreaker">
          <input type="checkbox" checked={draft.dealbreaker} onChange={(e) => setDraft({ ...draft, dealbreaker: e.target.checked })} />
          This candidate crosses a non-negotiable (rule them out)
        </label>
        <button type="button" className="primaryCta" onClick={addCandidate} disabled={busy}>{busy ? "Saving…" : "Add candidate"}</button>
      </div>
    </section>
  );
}

// The loop that turns the score into progress. Each open step points at one
// answer; finishing it saves and moves the readiness number on the spot.
function ActionPlan({ projectId, onBackToIntake }) {
  const [plan, setPlan] = useState(null);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    intakeApi.actionPlan(projectId).then(setPlan).catch(() => setError("Could not load your plan."));
  }, [projectId]);

  async function done(action) {
    if (!action.quickComplete) { onBackToIntake?.(); return; }
    setBusyId(action.id);
    setError("");
    try {
      setPlan(await intakeApi.completeAction(projectId, action.id));
    } catch (e) {
      setError(e.message || "Could not update that step.");
    } finally {
      setBusyId("");
    }
  }

  if (!plan) {
    return (
      <section className="reportSection">
        <h3>Your plan</h3>
        <p>{error || "Loading your steps…"}</p>
      </section>
    );
  }

  const open = plan.actions.filter((a) => a.status === "open");
  const finished = plan.actions.filter((a) => a.status === "done");

  return (
    <section className="reportSection">
      <h3>Your plan to a confident handoff</h3>
      <p className="reportLead">
        {plan.summary.done} of {plan.summary.total} steps done. Readiness {plan.summary.readiness}/100.
        Each step you finish moves the number. Work at your pace.
      </p>
      {error ? <p className="conciergeStatus" role="alert">{error}</p> : null}
      <ol className="planList">
        {open.map((a) => (
          <li key={a.id} className="planStep">
            <div className="planStepBody">
              <span className="planDriver">{a.driverLabel}</span>
              <strong>{a.title}</strong>
              <p className="planWhy">{a.why}</p>
              <p className="planGuide">{a.guidance}</p>
            </div>
            <button type="button" onClick={() => done(a)} disabled={busyId === a.id}>
              {a.quickComplete ? (busyId === a.id ? "Saving…" : "I've done this") : "Update in your answers"}
            </button>
          </li>
        ))}
      </ol>
      {finished.length ? (
        <details className="planDone">
          <summary>{finished.length} done</summary>
          <ul>{finished.map((a) => <li key={a.id}>{a.title}</li>)}</ul>
        </details>
      ) : null}
    </section>
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
  const panelRef = useRef(null);
  useModalA11y(panelRef, onClose);

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
    <div className="dataOverlay" role="dialog" aria-modal="true" aria-label="Private readiness review" ref={panelRef}>
      <div className="dataPanel">
        <div className="dataHead"><h2>Private readiness review</h2><button type="button" onClick={onClose} aria-label="Close">×</button></div>
        <p>A real person reviews what you've prepared and helps shape a clear, paced plan. You reach your lawyer and accountant organized, which lightens their work. We see only what you choose to share, and your progress stays here, private and saved.</p>
        <input aria-label="Your name" placeholder="Your name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input aria-label="Email" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input aria-label="Preferred time" placeholder="Preferred time, e.g. next week mornings" value={form.preferredTime} onChange={(e) => setForm({ ...form, preferredTime: e.target.value })} />
        <textarea aria-label="Anything you'd like us to know first" placeholder="Anything you'd like us to know first (optional)" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        <div className="dataActions">
          <button type="button" className="primaryCta" onClick={submit}>Request review</button>
        </div>
        {status ? <p className="conciergeStatus">{status}</p> : null}
      </div>
    </div>
  );
}
