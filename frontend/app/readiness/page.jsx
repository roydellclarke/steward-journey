"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBaseUrl, apiFetch, toSnakeProfile } from "../../lib/api";
import "../styles.css";

const initialProfile = {
  businessName: "Harbor Tool & Die",
  industry: "specialty manufacturing",
  yearsOperating: 34,
  employees: 28,
  revenueRange: "$5M-$10M",
  profitMargin: "12-15%",
  ownerDependency: "medium - owner still owns key customer relationships",
  timeline: "2-4 years",
  ownerGoal: "step back while protecting employees and customer trust",
  fears: "a buyer will cut staff, erase the company name, or disappoint longtime customers",
  nonNegotiables: "keep the local team and preserve customer service standards",
  familyContext: "children are supportive but do not want to operate the company",
  nextOwnerTraits: "patient operator, local credibility, manufacturing experience",
  debt: "manageable equipment loan; no urgent lender pressure",
  customerConcentration: "top 3 customers are important but not the whole business",
  recurringRevenue: "repeat customers, limited formal contracts",
  ownerCompensationDependency: "some personal expenses and owner compensation need cleanup",
  sopsDocumented: "some core processes documented; customer handoff still mostly in owner's head",
  keyEmployeeRisk: "two senior employees are critical to continuity",
  financialStatementsCurrent: "monthly books are current; tax returns available",
  informationToWithhold: "customer names, exact margins, debt details, and employee compensation until buyer fit is proven"
};

const designModes = {
  advisor: {
    label: "Advisor",
    description: "Quiet, evidence-heavy, boardroom credible."
  },
  legacy: {
    label: "Legacy",
    description: "Warmer language for founders, family, and employees."
  },
  operator: {
    label: "Operator",
    description: "Transferability, risks, and next actions first."
  },
  premium: {
    label: "Premium",
    description: "Concierge report style for high-trust conversations."
  }
};

export default function StewardPathMvp() {
  const [profile, setProfile] = useState(initialProfile);
  const [analysis, setAnalysis] = useState(() => analyze(profile));
  const [status, setStatus] = useState("Sample report loaded. Adjust your situation and prepare a fresh report.");
  const [source, setSource] = useState("Sample report");
  const [busy, setBusy] = useState(false);
  const [designMode, setDesignMode] = useState("advisor");
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState("");
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [intakeState, setIntakeState] = useState(null);

  const sections = [
    ["Readiness", "readiness"],
    ["What Matters", "jtbd"],
    ["Business Quality", "buffett"],
    ["Buyer Fit", "buyer-fit"],
    ["Your Next Steps", "roadmap"],
    ["When To Act", "growth"],
    ["Briefs", "narratives"]
  ];
  const lowestDimension = useMemo(() => {
    const entries = readinessDimensionEntries(analysis.readiness.dimensions);
    return entries.sort((a, b) => a[1] - b[1])[0] || ["financialClarity", 0];
  }, [analysis]);
  const recommendedMode = useMemo(() => recommendDesignMode(analysis, profile), [analysis, profile]);
  const activeProject = projects.find((project) => project.id === activeProjectId);

  useEffect(() => {
    loadProjects();
  }, []);

  function updateField(field, value) {
    setProfile((current) => ({ ...current, [field]: value }));
    setStatus("Draft changed. Run analysis to refresh the report.");
  }

  async function loadProjects(selectProjectId = "") {
    const payload = await apiFetch("/projects");
    setProjects(payload.projects || []);
    const nextProjectId = selectProjectId || activeProjectId || payload.projects?.[0]?.id || "";
    if (nextProjectId) {
      await loadProject(nextProjectId, payload.projects || []);
    }
  }

  async function createProject() {
    setBusy(true);
    setStatus("Creating project workspace...");
    try {
      const payload = await apiFetch("/projects", {
        method: "POST",
        body: JSON.stringify({ name: profile.businessName || "Untitled StewardPath project", profile, intakeState })
      });
      setProjects((current) => [payload.project, ...current.filter((project) => project.id !== payload.project.id)]);
      setActiveProjectId(payload.project.id);
      setIntakeState(payload.project.intakeState || null);
      setAnalysisHistory([]);
      setStatus(`Project created: ${payload.project.name}`);
      return payload.project;
    } catch (error) {
      setStatus(`Project was not created: ${error.message}`);
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function saveProjectDraft() {
    const project = activeProjectId ? activeProject : await createProject();
    if (!project) return null;
    setBusy(true);
    setStatus("Saving project draft...");
    try {
      const payload = await apiFetch(`/projects/${project.id}`, {
        method: "PATCH",
        body: JSON.stringify({ name: profile.businessName || project.name, profile, intakeState })
      });
      setProjects((current) => [payload.project, ...current.filter((item) => item.id !== payload.project.id)]);
      setActiveProjectId(payload.project.id);
      setIntakeState(payload.project.intakeState || null);
      setStatus("Project draft saved.");
      return payload.project;
    } catch (error) {
      setStatus(`Project draft was not saved: ${error.message}`);
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function loadProject(projectId, projectList = projects) {
    setBusy(true);
    setStatus("Loading project...");
    try {
      const payload = await apiFetch(`/projects/${projectId}`);
      setActiveProjectId(projectId);
      setProfile({ ...initialProfile, ...(payload.project.profile || {}) });
      setIntakeState(payload.project.intakeState || null);
      setProjects(projectList.map((project) => project.id === projectId ? payload.project : project));
      await loadAnalysisHistory(projectId);
      const latestResponse = await fetch(`${apiBaseUrl}/projects/${projectId}/analyses/latest`);
      if (latestResponse.ok) {
        const latestPayload = await latestResponse.json();
        setAnalysis(normalizeAnalysis(latestPayload.analysisEntry.analysis));
        setSource(sourceLabelFor(latestPayload.analysisEntry.analysis));
        setStatus(`Loaded latest saved analysis for ${payload.project.name}.`);
      } else {
        setAnalysis(analyze({ ...initialProfile, ...(payload.project.profile || {}) }));
        setSource("Draft report");
        setStatus(`Loaded project draft: ${payload.project.name}`);
      }
    } catch (error) {
      setStatus(`Project could not be loaded: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function loadAnalysisHistory(projectId) {
    const payload = await apiFetch(`/projects/${projectId}/analyses`);
    setAnalysisHistory(payload.analyses || []);
  }

  async function loadSavedAnalysis(entry) {
    setProfile({ ...initialProfile, ...(entry.profileSnapshot || {}) });
    setIntakeState(entry.intakeSnapshot || intakeState);
    setAnalysis(normalizeAnalysis(entry.analysis));
    setSource(sourceLabelFor(entry.analysis));
    setStatus(`Loaded saved analysis from ${new Date(entry.createdAt).toLocaleString()}.`);
  }

  async function ensureProjectForAnalysis() {
    if (activeProjectId) {
      await saveProjectDraft();
      return activeProjectId;
    }
    const project = await createProject();
    return project?.id || "";
  }

  async function runAnalysis() {
    setBusy(true);
    setStatus("Preparing and saving your report...");
    try {
      const projectId = await ensureProjectForAnalysis();
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST",
        credentials: "include", // carry the session cookie if the project is claimed
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: toSnakeProfile(profile), project_id: projectId || null, intake_state: intakeState })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Report preparation failed");
      }
      setAnalysis(normalizeAnalysis(payload.analysis));
      const llmStatus = payload.analysis?.llm_status || "unknown";
      setSource(sourceLabelFor(payload.analysis));
      if (payload.savedAnalysis) {
        setAnalysisHistory((current) => [payload.savedAnalysis, ...current]);
        await loadProjects(projectId);
      }
      setStatus(llmStatus === "ok"
        ? "Your report is ready and saved to this project."
        : llmStatus === "partial"
          ? "Your report is ready and saved. Some deeper checks were limited."
        : "Your report is ready and saved."
      );
    } catch (error) {
      setAnalysis(analyze(profile));
      setSource("Draft report");
      setStatus(`We prepared a draft report on this device. ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={`mvpShell mode-${designMode}`}>
      <section className="heroBand">
        <div className="heroCopy">
          <p className="mvpEyebrow">StewardPath Readiness · classic workbench</p>
          <h1>Before you sell, decide what must be protected.</h1>
          <p>
            You spent years building trust with employees, customers, family,
            and your community. This workbench shows what could be lost, what to
            prepare, and what kind of next owner can protect what you built,             with the reasoning behind every score. Prefer to be guided, at your
            pace, with privacy reassurance at each step? <a href="/intake">Try the
            concierge readiness program</a>.
          </p>
        </div>
        <div className="heroSignal">
          <span>Your progress</span>
          <strong>A clearer transfer plan before buyers define the terms</strong>
        </div>
      </section>

      <section className="mvpGrid">
        <aside className="intakePanel">
          <ProjectWorkspace
            projects={projects}
            activeProjectId={activeProjectId}
            activeProject={activeProject}
            analysisHistory={analysisHistory}
            busy={busy}
            onCreate={createProject}
            onSave={saveProjectDraft}
            onLoad={loadProject}
            onLoadAnalysis={loadSavedAnalysis}
          />
          <div className="panelTitle">
            <h2>Your Situation</h2>
            <button type="button" onClick={runAnalysis} disabled={busy}>
              {busy ? "Preparing..." : "Prepare My Report"}
            </button>
          </div>
          <p className="statusLine" role="status">{status}</p>
          {busy ? (
            <div className="progressRail" aria-hidden="true">
              <i />
            </div>
          ) : null}
          <p className="sourceLine">Report status: <strong>{source}</strong></p>
          <Field label="Business name" value={profile.businessName} onChange={(value) => updateField("businessName", value)} />
          <Field label="Industry" value={profile.industry} onChange={(value) => updateField("industry", value)} />
          <div className="twoCol">
            <Field label="Years operating" type="number" value={profile.yearsOperating} onChange={(value) => updateField("yearsOperating", Number(value))} />
            <Field label="Employees" type="number" value={profile.employees} onChange={(value) => updateField("employees", Number(value))} />
          </div>
          <div className="twoCol">
            <Field label="Revenue range" value={profile.revenueRange} onChange={(value) => updateField("revenueRange", value)} />
            <Field label="Profit margin" value={profile.profitMargin} onChange={(value) => updateField("profitMargin", value)} />
          </div>
          <Field label="Where the business still depends on you" value={profile.ownerDependency} onChange={(value) => updateField("ownerDependency", value)} />
          <Field label="When you want change" value={profile.timeline} onChange={(value) => updateField("timeline", value)} />
          <Area label="What you want to happen next" value={profile.ownerGoal} onChange={(value) => updateField("ownerGoal", value)} />
          <Area label="What you are afraid could be lost" value={profile.fears} onChange={(value) => updateField("fears", value)} />
          <Area label="What a buyer must not change" value={profile.nonNegotiables} onChange={(value) => updateField("nonNegotiables", value)} />
          <Area label="What your family needs to understand" value={profile.familyContext} onChange={(value) => updateField("familyContext", value)} />
          <Area label="Ideal next owner traits" value={profile.nextOwnerTraits} onChange={(value) => updateField("nextOwnerTraits", value)} />
          <div className="intakeDivider">
            <span>Financial clarity</span>
            <p>Share enough to prepare. Keep sensitive details private until successor fit is real.</p>
          </div>
          <Area label="Debt or lender pressure" value={profile.debt} onChange={(value) => updateField("debt", value)} />
          <Area label="Customer concentration" value={profile.customerConcentration} onChange={(value) => updateField("customerConcentration", value)} />
          <Area label="Recurring revenue or repeat customers" value={profile.recurringRevenue} onChange={(value) => updateField("recurringRevenue", value)} />
          <Area label="Owner compensation or personal expenses to clean up" value={profile.ownerCompensationDependency} onChange={(value) => updateField("ownerCompensationDependency", value)} />
          <Area label="SOPs and process documentation" value={profile.sopsDocumented} onChange={(value) => updateField("sopsDocumented", value)} />
          <Area label="Key employee risk" value={profile.keyEmployeeRisk} onChange={(value) => updateField("keyEmployeeRisk", value)} />
          <Area label="Are financial statements current?" value={profile.financialStatementsCurrent} onChange={(value) => updateField("financialStatementsCurrent", value)} />
          <Area label="Information to keep private until buyer fit is proven" value={profile.informationToWithhold} onChange={(value) => updateField("informationToWithhold", value)} />
          <div className="intakeActionBar">
            <div>
              <strong>Ready to see what this changes?</strong>
              <span>Your report can still keep sensitive details private.</span>
            </div>
            <button type="button" onClick={runAnalysis} disabled={busy}>
              {busy ? "Preparing..." : "Prepare My Report"}
            </button>
          </div>
        </aside>

        <section className="analysisPanel">
          <div className="designModePanel">
            <div>
              <p className="mvpEyebrow">Adaptive Design Layer</p>
              <h2>{designModes[designMode].label} mode</h2>
              <p>{designModes[designMode].description}</p>
            </div>
            <div className="modePicker" aria-label="Design mode">
              {Object.entries(designModes).map(([id, mode]) => (
                <button
                  type="button"
                  key={id}
                  className={designMode === id ? "active" : ""}
                  onClick={() => setDesignMode(id)}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <p className="modeHint">
              Suggested: <button type="button" onClick={() => setDesignMode(recommendedMode)}>{designModes[recommendedMode].label}</button>
            </p>
          </div>

          <div className="scoreHeader">
            <div>
              <p className="mvpEyebrow">Your Transfer Readiness</p>
              <h2>{analysis.readiness.overall}/100</h2>
              <p>{analysis.readiness.interpretation}</p>
            </div>
            <div className="riskBox">
              <span>Current bottleneck</span>
              <strong>{prettify(lowestDimension[0])}</strong>
            </div>
          </div>

          <nav className="mvpTabs" aria-label="Readiness report sections">
            {sections.map(([label, id]) => (
              <a href={`#${id}`} key={id}>
                {label}
              </a>
            ))}
          </nav>

          <div className="analysisSections">
            <section id="readiness" className="analysisSection">
              <h3>Readiness</h3>
              <Readiness analysis={analysis} />
            </section>
            <section id="jtbd" className="analysisSection">
              <h3>What Matters Most</h3>
              <Jtbd analysis={analysis} mode={designMode} />
            </section>
            <section id="buffett" className="analysisSection">
              <h3>Business Quality</h3>
              <Buffett analysis={analysis} />
            </section>
            <section id="buyer-fit" className="analysisSection">
              <h3>Buyer Fit</h3>
              <BuyerFit analysis={analysis} />
            </section>
            <section id="roadmap" className="analysisSection">
              <h3>Your Next Steps</h3>
              <Roadmap analysis={analysis} />
            </section>
            <section id="growth" className="analysisSection">
              <h3>When To Act</h3>
              <Growth analysis={analysis} />
            </section>
            <section id="narratives" className="analysisSection">
              <h3>Briefs You Can Use</h3>
              <Narratives analysis={analysis} profile={profile} />
            </section>
          </div>
        </section>
      </section>

      <section className="disclaimerBand">
        {analysis.disclaimers.map((item) => <span key={item}>{item}</span>)}
      </section>
    </main>
  );
}

function ProjectWorkspace({
  projects,
  activeProjectId,
  activeProject,
  analysisHistory,
  busy,
  onCreate,
  onSave,
  onLoad,
  onLoadAnalysis
}) {
  return (
    <section className="projectWorkspace">
      <div className="panelTitle">
        <div>
          <p className="mvpEyebrow">Project Workspace</p>
          <h2>{activeProject?.name || "No project selected"}</h2>
        </div>
      </div>
      <div className="projectActions">
        <button type="button" onClick={onCreate} disabled={busy}>New Project</button>
        <button type="button" onClick={onSave} disabled={busy}>Save Draft</button>
      </div>
      <label className="mvpField">
        <span>Saved projects</span>
        <select value={activeProjectId} onChange={(event) => onLoad(event.target.value)} disabled={busy || !projects.length}>
          <option value="">Select a project</option>
          {projects.map((project) => (
            <option value={project.id} key={project.id}>
              {project.name} ({project.analysisCount || 0})
            </option>
          ))}
        </select>
      </label>
      <div className="historyList">
        <span>Analysis history</span>
        {analysisHistory.length ? (
          analysisHistory.slice(0, 5).map((entry) => (
            <button type="button" key={entry.analysisId} onClick={() => onLoadAnalysis(entry)} disabled={busy}>
              {new Date(entry.createdAt).toLocaleString()} · {entry.analysisSource.replaceAll("_", " ")}
            </button>
          ))
        ) : (
          <p>No saved analyses yet.</p>
        )}
      </div>
    </section>
  );
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="mvpField">
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Area({ label, value, onChange }) {
  return (
    <label className="mvpField">
      <span>{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Readiness({ analysis }) {
  const entries = readinessDimensionEntries(analysis.readiness.dimensions);
  return (
    <div className="readinessDrivers">
      <article className="readinessSummary">
        <span>Unified readiness score</span>
        <p>
          The headline score is normalized from these drivers and weighted
          toward the weakest areas, so one strong area cannot hide the work
          that still needs attention.
        </p>
      </article>
      <div className="readinessMatrix">
        {entries.map(([label, score]) => (
          <article className="readinessTile" key={label}>
            <span>{prettify(label)}</span>
            <div className="bar"><i style={{ width: `${score * 20}%` }} /></div>
            <small>{readinessDriverLabel(score)}</small>
          </article>
        ))}
      </div>
    </div>
  );
}

function Jtbd({ analysis, mode }) {
  const jtbd = analysis.jtbd;
  return (
    <div className={`jtbdCanvas ${mode === "legacy" ? "storyWeighted" : ""}`}>
      <article className="strugglePanel">
        <span>What is on the owner’s mind</span>
        <h4>{jtbd.firstThought || "The owner needs a transfer plan that protects what matters."}</h4>
        <p>{jtbd.strugglingMoment}</p>
      </article>
      <ForceColumn title="Why this matters now" items={jtbd.pushForces} tone="push" />
      <ForceColumn title="What a good transition could protect" items={jtbd.pullForces} tone="pull" />
      <ForceColumn title="What the owner is worried about" items={jtbd.anxietyForces} tone="anxiety" />
      <ForceColumn title="Why this keeps getting delayed" items={jtbd.habitForces} tone="habit" />
      <JobBand title="Practical next steps" items={jtbd.functionalJobs} />
      <JobBand title="Personal reassurance" items={jtbd.emotionalJobs} />
      <JobBand title="Family, team, and community" items={jtbd.socialJobs} />
    </div>
  );
}

function Buffett({ analysis }) {
  const scores = Object.entries(analysis.buffettQuality.scores);
  return (
    <div className="buffettBoard">
      <article className="qualityMemo">
        <span>Quality lens</span>
        <p>{analysis.buffettQuality.summary}</p>
      </article>
      <div className="scoreDialGrid">
        {scores.map(([label, score]) => (
          <ScoreDial key={label} label={prettify(label)} score={score} />
        ))}
      </div>
      <ListCard title="Questions to answer before a buyer controls the conversation" items={analysis.buffettQuality.questionsToAnswer} className="buyerQuestions" />
    </div>
  );
}

function BuyerFit({ analysis }) {
  return (
    <div className="buyerMap">
      {analysis.buyerPaths.map((path) => (
        <article className="buyerCard" key={path.path}>
          <div>
            <span>{path.legacyPreservation >= 4 ? "High continuity" : path.financialPotential >= 5 ? "Price-forward" : "Conditional fit"}</span>
            <h3>{path.path}</h3>
          </div>
          <p>{path.notes}</p>
          <div className="fitBars">
            <MetricBar label="Legacy" value={path.legacyPreservation} />
            <MetricBar label="Financial" value={path.financialPotential} />
            <MetricBar label="Emotional" value={path.emotionalFit} />
          </div>
       </article>
      ))}
    </div>
  );
}

function Roadmap({ analysis }) {
  return (
    <ol className="roadmap">
      {analysis.roadmap.map((step, index) => (
        <li key={step.phase}>
          <span>{String(index + 1).padStart(2, "0")}</span>
          <div>
            <strong>{step.phase.replace(/^\d+\.\s*/, "")}</strong>
            <p>{step.action}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function Growth({ analysis }) {
  const growth = analysis.growthDiscovery;
  return (
    <div className="growthLab">
      <article className="northStarCard">
        <span>The moment to watch for</span>
        <h3>{growth.northStarMetric}</h3>
        <p>{growth.activationEvent}</p>
      </article>
      <div className="growthColumns">
        <ListCard title="Signs you should not keep waiting" items={growth.locksmithMoments} />
        <ListCard title="Proof you are making progress" items={growth.keyDrivers} />
      </div>
      <article className="hypothesisStrip">
        <span>What may be holding you back</span>
        <p>{growth.rateLimitingStepHypothesis}</p>
      </article>
      <div className="experimentGrid">
        {growth.growthLevers.map((lever) => (
          <article className="experimentCard" key={lever.idea}>
            <h3>{lever.idea}</h3>
            <p>{lever.riskyAssumption}</p>
            <div className="pathScores">
              <span>{lever.keyDriver}</span>
              <span>Impact {lever.impact}/5</span>
              <span>Effort {lever.effort}/5</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function Narratives({ analysis, profile }) {
  const exports = buildExports(analysis, profile);
  return (
    <div className="narrativeDesk">
      <ReportImage analysis={analysis} profile={profile} />
      <ExportCenter exports={exports} />
      {Object.entries(analysis.narratives).map(([label, body]) => (
        <article className="narrativeSheet" key={label}>
          <div>
            <span>{prettify(label)}</span>
            <p>{body}</p>
          </div>
          <button type="button" onClick={() => navigator.clipboard?.writeText(body)}>Copy</button>
        </article>
      ))}
    </div>
  );
}

function ReportImage({ analysis, profile }) {
  const svg = buildReportSvg(analysis, profile);
  const href = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  const filename = `${slugify(profile.businessName || "stewardpath")}-readiness-card.svg`;
  return (
    <article className="reportImageCard">
      <div>
        <span>Downloadable report image</span>
        <h4>A shareable readiness card for your advisor conversation</h4>
        <p>
          Download a polished image summary you can keep with your notes or
          share when you are ready. It does not include private financial detail.
        </p>
      </div>
      <div className="reportImagePreview" dangerouslySetInnerHTML={{ __html: svg }} />
      <a href={href} download={filename}>Download image</a>
    </article>
  );
}

function ExportCenter({ exports }) {
  return (
    <article className="exportCenter">
      <span>Copyable exports</span>
      <div>
        {exports.map((item) => (
          <section key={item.title}>
            <h4>{item.title}</h4>
            <p>{item.body}</p>
            <button type="button" onClick={() => navigator.clipboard?.writeText(`${item.title}\n\n${item.body}`)}>Copy</button>
          </section>
        ))}
      </div>
    </article>
  );
}

function ForceColumn({ title, items, tone }) {
  return (
    <article className={`forceColumn ${tone}`}>
      <span>{title}</span>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </article>
  );
}

function JobBand({ title, items }) {
  return (
    <article className="jobBand">
      <span>{title}</span>
      <div>{items.map((item) => <p key={item}>{item}</p>)}</div>
    </article>
  );
}

function ScoreDial({ label, score }) {
  return (
    <article className="scoreDial">
      <strong>{score}</strong>
      <span>{label}</span>
      <div className="bar"><i style={{ width: `${score * 20}%` }} /></div>
    </article>
  );
}

function MetricBar({ label, value }) {
  return (
    <div className="metricBar">
      <span>{label}</span>
      <div className="bar"><i style={{ width: `${value * 20}%` }} /></div>
      <strong>{value}/5</strong>
    </div>
  );
}

function ListCard({ title, items, className = "" }) {
  return (
    <article className={`mvpCard wide ${className}`}>
      <span>{title}</span>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </article>
  );
}

function normalizeAnalysis(raw) {
  const fallback = analyze(initialProfile);
  const readiness = raw.readiness || fallback.readiness;
  const dimensions = canonicalizeReadinessDimensions({
    ...fallback.readiness.dimensions,
    ...(readiness.dimensions || {})
  });
  const overall = computeUnifiedReadinessScore(dimensions);
  const jtbd = normalizeKeys(raw.jtbd || fallback.jtbd);
  const buffettQuality = normalizeKeys(raw.buffett_quality || raw.buffettQuality || fallback.buffettQuality);
  const growthDiscovery = normalizeKeys(raw.growth_discovery || raw.growthDiscovery || fallback.growthDiscovery);
  const narratives = normalizeKeys(raw.narratives || fallback.narratives);
  return {
    analysisSource: raw.analysis_source || "deterministic",
    llmStatus: raw.llm_status || "disabled",
    llmModels: raw.llm_models || {},
    llmErrors: raw.llm_errors || [],
    readiness: {
      ...fallback.readiness,
      ...readiness,
      overall,
      interpretation: readinessLabel(overall),
      dimensions
    },
    jtbd: { ...fallback.jtbd, ...jtbd },
    buffettQuality: {
      ...fallback.buffettQuality,
      ...buffettQuality,
      scores: {
        ...fallback.buffettQuality.scores,
        ...(buffettQuality.scores || {})
      },
      questionsToAnswer: buffettQuality.questionsToAnswer || fallback.buffettQuality.questionsToAnswer
    },
    buyerPaths: (raw.buyer_paths || raw.buyerPaths || fallback.buyerPaths).map(normalizeKeys),
    roadmap: raw.roadmap || fallback.roadmap,
    growthDiscovery: { ...fallback.growthDiscovery, ...growthDiscovery },
    narratives: { ...fallback.narratives, ...narratives },
    disclaimers: raw.disclaimers || fallback.disclaimers
  };
}

function normalizeKeys(value) {
  if (Array.isArray(value)) {
    return value.map(normalizeKeys);
  }
  if (!value || typeof value !== "object") {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [snakeToCamel(key), normalizeKeys(entry)])
  );
}

function snakeToCamel(value) {
  return value.replace(/_([a-z])/g, (_match, letter) => letter.toUpperCase());
}

function canonicalizeReadinessDimensions(dimensions = {}) {
  const canonical = {
    financialClarity: 0,
    operationalTransferability: 0,
    processDocumentation: 0,
    familyAlignment: 0,
    ownerEmotionalReadiness: 0
  };
  Object.entries(dimensions).forEach(([key, value]) => {
    const normalizedKey = snakeToCamel(key);
    if (Object.prototype.hasOwnProperty.call(canonical, normalizedKey)) {
      canonical[normalizedKey] = clampReadinessScore(value);
    }
  });
  return canonical;
}

function readinessDimensionEntries(dimensions = {}) {
  return Object.entries(canonicalizeReadinessDimensions(dimensions));
}

function clampReadinessScore(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) return 0;
  return Math.min(5, Math.max(0, score));
}

function computeUnifiedReadinessScore(dimensions = {}) {
  const scores = Object.values(canonicalizeReadinessDimensions(dimensions));
  if (!scores.length) return 0;
  const weights = scores.map((score) => Math.exp(5 - score));
  const totalWeight = weights.reduce((total, weight) => total + weight, 0);
  const weightedScore = scores.reduce((total, score, index) => total + score * weights[index], 0) / totalWeight;
  return Math.round((weightedScore / 5) * 100);
}

function readinessDriverLabel(score) {
  if (score >= 4.5) return "Strong";
  if (score >= 3.5) return "Stable";
  if (score >= 2.5) return "Needs work";
  return "Risk area";
}

function sourceLabelFor(analysis) {
  return analysis?.analysis_source === "llm_augmented"
    ? "Enhanced report"
    : analysis?.analysis_source === "llm_partial"
      ? "Enhanced report"
      : analysis?.analysis_source === "deterministic_with_llm_errors"
        ? "Draft report"
        : "Prepared report";
}

function buildExports(analysis, profile) {
  const business = profile.businessName || "the business";
  const privateInfo = profile.informationToWithhold || "sensitive customer, margin, debt, and employee details";
  return [
    {
      title: "Advisor-ready summary",
      body: `${business} is preparing for a thoughtful transition. Current readiness is ${analysis.readiness.overall}/100. The owner wants to protect ${profile.nonNegotiables || "employees, customers, and company reputation"}. Before any buyer conversation, review founder dependency, customer concentration, debt, current financial statements, SOP documentation, and what should stay private: ${privateInfo}.`
    },
    {
      title: "Family conversation guide",
      body: `I am not just deciding whether to sell ${business}. I am deciding what must not be lost. I want the family aligned on the people, standards, name, customer trust, and community reputation that matter beyond price. The next step is to prepare before buyers or timing pressure define the terms.`
    },
    {
      title: "Successor-fit brief",
      body: `The right next owner should be ${profile.nextOwnerTraits || "patient, capable, and respectful of the team"}. Price matters, but fit must include employee continuity, customer service standards, operational competence, and willingness to preserve what made ${business} worth buying.`
    }
  ];
}

function buildReportSvg(analysis, profile) {
  const business = escapeXml(profile.businessName || "Your business");
  const readiness = Number(analysis.readiness.overall || 0);
  const protectedText = escapeXml(profile.nonNegotiables || "employees, customers, standards, and reputation");
  const successor = escapeXml(profile.nextOwnerTraits || "a patient operator who respects the team");
  const bottleneck = prettify(readinessDimensionEntries(analysis.readiness.dimensions).sort((a, b) => a[1] - b[1])[0]?.[0] || "transfer readiness");
  const steps = [
    `Protect: ${protectedText}`,
    `Prepare: ${escapeXml(bottleneck)}`,
    `Match: ${successor}`
  ];
  const stepLines = steps.flatMap((step) => wrapSvgText(step, 44));
  const color = readiness >= 75 ? "#315b45" : readiness >= 50 ? "#7a5a2b" : "#8d4646";
  return `
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-label="StewardPath readiness report image">
  <rect width="1200" height="675" fill="#f4f1ea"/>
  <rect x="42" y="42" width="1116" height="591" rx="28" fill="#fffdf8" stroke="#d8d1c5" stroke-width="3"/>
  <rect x="42" y="42" width="1116" height="154" rx="28" fill="#203a2e"/>
  <text x="84" y="100" fill="#cfe1c9" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="800" letter-spacing="2">STEWARDPATH READINESS CARD</text>
  <text x="84" y="158" fill="#fffaf0" font-family="Arial, Helvetica, sans-serif" font-size="46" font-weight="800">${business}</text>
  <text x="84" y="260" fill="#5f665f" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="800">Before you sell, decide what must be protected.</text>
  <circle cx="950" cy="362" r="116" fill="#f3f7f1" stroke="${color}" stroke-width="16"/>
  <text x="950" y="350" text-anchor="middle" fill="${color}" font-family="Arial, Helvetica, sans-serif" font-size="72" font-weight="900">${readiness}</text>
  <text x="950" y="394" text-anchor="middle" fill="#5f665f" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800">/100 ready</text>
  <text x="84" y="322" fill="#203a2e" font-family="Arial, Helvetica, sans-serif" font-size="32" font-weight="900">Your next conversation should protect:</text>
  ${stepLines.map((line, index) => `<text x="112" y="${376 + index * 34}" fill="#17201b" font-family="Arial, Helvetica, sans-serif" font-size="26">${escapeXml(line)}</text>`).join("")}
  <rect x="84" y="548" width="1032" height="2" fill="#d8d1c5"/>
  <text x="84" y="594" fill="#5f665f" font-family="Arial, Helvetica, sans-serif" font-size="22">Private preparation support. Not legal, tax, investment, valuation, or brokerage advice.</text>
</svg>`.trim();
}

function wrapSvgText(text, maxLength) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = "";
  words.forEach((word) => {
    const next = line ? `${line} ${word}` : word;
    if (next.length > maxLength && line) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  });
  if (line) lines.push(line);
  return lines.slice(0, 5);
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function slugify(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "stewardpath";
}

function analyze(profile) {
  const dependency = dependencyScore(profile.ownerDependency);
  const financial = profile.revenueRange && profile.profitMargin ? 3 : 1;
  const family = profile.familyContext ? 4 : 2;
  const emotional = profile.fears && profile.nextOwnerTraits ? 4 : 2;
  const docs = profile.nonNegotiables ? 3 : 2;
  const dimensions = canonicalizeReadinessDimensions({
    financialClarity: financial,
    operationalTransferability: dependency,
    processDocumentation: docs,
    familyAlignment: family,
    ownerEmotionalReadiness: emotional
  });
  const overall = computeUnifiedReadinessScore(dimensions);
  return {
    readiness: {
      overall,
      interpretation: readinessLabel(overall),
      dimensions
    },
    jtbd: {
      strugglingMoment: `You may be ready to step back from ${profile.businessName || "the business"}, but you do not want buyers, brokers, or timing pressure to decide what your life's work becomes.`,
      pushForces: [`Your timeline is ${profile.timeline || "getting harder to ignore"}.`, "You may not want to remain the emergency backup for every hard decision.", "Your family, advisors, or employees may need clarity before uncertainty becomes risk."],
      pullForces: ["You can protect jobs, customer trust, and the company name before a buyer changes the story.", "You can make the business easier for a good successor to preserve.", "You can step back without feeling like you abandoned the people who helped you build it."],
      anxietyForces: [profile.fears || "You may worry the wrong buyer will damage the company, cut people, or disappoint customers.", "You may worry employees will see your transition as abandonment.", "You may worry brokers or buyers will only care about price, not what should be protected."],
      habitForces: ["It is easy to keep personally rescuing problems because that has always worked.", "It is easier to postpone the conversation than risk hearing the wrong answer.", "Advisor conversations can feel scattered until you have one clear story."],
      functionalJobs: ["See what must be fixed before you talk seriously with buyers.", "Compare transfer paths without being pushed toward one answer too soon.", "Prepare clear materials for your advisors, family, and eventual successor."],
      emotionalJobs: ["Feel that decades of work will not be casually undone.", "Replace dread with a plan you can explain.", "Make your next chapter feel like continuity, not disappearance."],
      socialJobs: ["Show employees you are trying to protect them, not surprise them.", "Give your family a clearer picture of what matters beyond price.", "Protect your reputation in the community after you step back."]
    },
    buffettQuality: {
      summary: "This is not a valuation. It shows where a careful buyer may see strength, risk, or dependency before those issues cost you leverage.",
      scores: {
        understandableBusiness: profile.yearsOperating >= 20 ? 5 : 3,
        founderIndependence: dependency,
        managementDepth: profile.employees >= 5 ? 4 : 2,
        durableCustomerValue: Math.round((dependency + 4 + (profile.yearsOperating >= 20 ? 5 : 3)) / 3),
        stewardshipFit: 4
      },
      questionsToAnswer: ["What would earnings look like if the owner stepped away for 90 days?", "Which customers buy because of the company, not only the founder?", "Where does the business have pricing power or repeat demand?", "What concentration, debt, or reinvestment risks would worry a patient buyer?"]
    },
    buyerPaths: buyerPaths(),
    roadmap: roadmap(overall),
    growthDiscovery: growthDiscovery(),
    narratives: narratives(profile),
    disclaimers: ["Not legal advice.", "Not tax advice.", "Not investment advice.", "Not a formal valuation."]
  };
}

function buyerPaths() {
  return [
    ["Family transfer", 5, 3, 4, "Best when family desire and capability are real, not assumed."],
    ["Employee ownership", 5, 3, 4, "Strong continuity path if leadership bench and financing can work."],
    ["Management buyout", 4, 4, 4, "Often preserves culture when managers can operate without founder rescue."],
    ["Independent entrepreneur buyer", 4, 4, 3, "Can fit legacy goals if buyer values stewardship and local trust."],
    ["Strategic buyer", 3, 5, 2, "May pay well but can create employee and culture-change risk."],
    ["Private equity buyer", 2, 5, 2, "Can be financially attractive but needs careful fit screening."]
  ].map(([path, legacyPreservation, financialPotential, emotionalFit, notes]) => ({ path, legacyPreservation, financialPotential, emotionalFit, notes }));
}

function roadmap(score) {
  return [
    ["1. Name the legacy job", "Write the owner goal, fears, non-negotiables, and successor traits in plain language."],
    ["2. Reduce founder dependency", "Document decisions, customer relationships, operating rhythms, and emergency procedures."],
    ["3. Prepare advisor evidence", "Gather financial clarity, customer concentration, management bench, and process documentation."],
    ["4. Compare transfer paths", "Screen family, employees, managers, local buyers, strategic buyers, and financial buyers against legacy criteria."],
    ["5. Communicate carefully", "Prepare separate family, employee, advisor, and buyer narratives."],
    ["6. Decide next step", `Current readiness is ${score}/100: focus on the lowest readiness dimension first.`]
  ].map(([phase, action]) => ({ phase, action }));
}

function growthDiscovery() {
  return {
    northStarMetric: "You have a written plan for what must be protected.",
    activationEvent: "You complete the intake, review your readiness report, and save at least one non-negotiable successor criterion.",
    locksmithMoments: ["A key employee leaves or hints they may leave.", "Your children make it clear they do not want to run the business.", "A buyer approaches before you are prepared.", "Your CPA or attorney asks what happens if you cannot work for 90 days.", "A peer owner sells and regrets what happened to the company."],
    keyDrivers: ["You can name what must be protected.", "You know where the business depends too much on you.", "You have a report you can share with advisors.", "You have at least one realistic successor path.", "You return to update the plan instead of avoiding it."],
    rateLimitingStepHypothesis: "The hardest part may not be finding a buyer. It may be admitting what could be lost if you wait too long.",
    growthLevers: [
      { idea: "Readiness check before a sale conversation", keyDriver: "You can name what must be protected.", impact: 5, effort: 2, riskyAssumption: "You are more likely to act when the report speaks to protection, not just valuation." },
      { idea: "Advisor briefing memo", keyDriver: "You have a report you can share with advisors.", impact: 4, effort: 3, riskyAssumption: "Your advisors can help more when your concerns are organized before the meeting." },
      { idea: "Successor-fit comparison", keyDriver: "You have at least one realistic successor path.", impact: 4, effort: 2, riskyAssumption: "You will make better progress when buyer fit is visible, not just price." }
    ]
  };
}

function narratives(profile) {
  const business = profile.businessName || "this business";
  const steward = profile.nextOwnerTraits || "someone who protects employees, customers, and community trust";
  return {
    legacyStatement: `${business} is more than an asset. It is a promise to customers, employees, family, and the community that the work will continue with care.`,
    buyerCriteriaMemo: `The right next owner should be ${steward}. Price matters, but fit, continuity, and employee trust are non-negotiable.`,
    familyConversationGuide: "Start with what must be preserved, what the owner wants life to look like next, and which decisions need professional advice.",
    advisorBrief: `The owner is exploring a legacy transfer on a ${profile.timeline || "thoughtful"} timeline and wants options that protect continuity as well as financial outcome.`
  };
}

function dependencyScore(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("low") || normalized.includes("team")) return 5;
  if (normalized.includes("medium") || normalized.includes("some")) return 3;
  if (normalized.includes("high") || normalized.includes("everything") || normalized.includes("me")) return 1;
  return 2;
}

function readinessLabel(score) {
  if (score >= 75) return "Transfer story is becoming credible; focus on buyer fit and advisor review.";
  if (score >= 50) return "Promising but not yet steward-ready; reduce founder dependency and clarify stakeholder alignment.";
  return "Early readiness; start with documentation, emotional goals, and advisor conversations.";
}

function recommendDesignMode(analysis, profile) {
  const fears = `${profile.fears || ""} ${profile.nonNegotiables || ""}`.toLowerCase();
  const dimensions = analysis.readiness.dimensions;
  const lowTransferability = dimensions.operationalTransferability <= 2 || dimensions.processDocumentation <= 2;
  if (analysis.readiness.overall >= 75) return "premium";
  if (lowTransferability) return "operator";
  if (fears.includes("family") || fears.includes("employees") || fears.includes("legacy") || fears.includes("name")) {
    return "legacy";
  }
  return "advisor";
}

function prettify(value) {
  return value.replace(/([A-Z])/g, " $1").replace(/_/g, " ").replace(/^./, (char) => char.toUpperCase());
}
