import { apiFetch } from "./api";

// Build a single-field IntakeState patch. nonNegotiables lives at the top level;
// every other field is nested under its section.
export function fieldPatch(section, field, value, status = "answered") {
  const entry = { value, status, updatedAt: new Date().toISOString() };
  if (section === "nonNegotiables") {
    return { nonNegotiables: entry };
  }
  return { [section]: { [field]: entry } };
}

export const intakeApi = {
  questions: () => apiFetch("/intake/questions"),
  plan: (intakeState, readinessScore) =>
    apiFetch("/intake/plan", { method: "POST", body: JSON.stringify({ intakeState, readinessScore }) }),
  reflect: (intakeState, completedSection, nextQuestionId) =>
    apiFetch("/intake/reflect", {
      method: "POST",
      body: JSON.stringify({ intakeState, completedSection, nextQuestionId })
    }),
  score: (intakeState) =>
    apiFetch("/intake/score", { method: "POST", body: JSON.stringify({ intakeState }) }),

  // project-scoped
  createProject: (name) =>
    apiFetch("/projects", { method: "POST", body: JSON.stringify({ name, profile: {} }) }),
  listProjects: () => apiFetch("/projects"),
  getIntake: (projectId) => apiFetch(`/projects/${projectId}/intake`),
  putIntake: (projectId, intakeState) =>
    apiFetch(`/projects/${projectId}/intake`, { method: "PUT", body: JSON.stringify({ intakeState }) }),
  analyze: (projectId) =>
    apiFetch(`/projects/${projectId}/intake/analyze`, { method: "POST" }),
  handoff: (projectId) => apiFetch(`/projects/${projectId}/handoff`),
  actionPlan: (projectId) => apiFetch(`/projects/${projectId}/action-plan`),
  completeAction: (projectId, actionId) =>
    apiFetch(`/projects/${projectId}/action-plan/${actionId}/complete`, { method: "POST" }),
  bookReview: (projectId, payload) =>
    apiFetch(`/projects/${projectId}/book-review`, { method: "POST", body: JSON.stringify(payload) }),
  exportData: (projectId) => apiFetch(`/projects/${projectId}/export`),
  deleteProject: (projectId) => apiFetch(`/projects/${projectId}`, { method: "DELETE" })
};

export function prettify(value = "") {
  return String(value)
    .replace(/([A-Z])/g, " $1")
    .replace(/_/g, " ")
    .replace(/^./, (c) => c.toUpperCase())
    .trim();
}
