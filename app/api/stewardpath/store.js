import { mkdir, readFile, readdir, writeFile, appendFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { appendSnapshot, migrateProfileToIntakeState } from "./intake_state";

const repoRoot = process.cwd();
const storeRoot = path.join(repoRoot, "workspace", "stewardpath", "projects");
const leadRoot = path.join(repoRoot, "workspace", "stewardpath", "leads");
const leadLogPath = path.join(leadRoot, "leads.jsonl");

function nowIso() {
  return new Date().toISOString();
}

function assertProjectId(projectId) {
  if (!/^[a-zA-Z0-9_-]+$/.test(projectId || "")) {
    throw new Error("Invalid project id.");
  }
}

async function ensureDir(dir) {
  await mkdir(dir, { recursive: true });
}

async function readJson(filePath, fallback = null) {
  try {
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return fallback;
    throw error;
  }
}

async function writeJson(filePath, value) {
  await ensureDir(path.dirname(filePath));
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function projectDir(projectId) {
  assertProjectId(projectId);
  return path.join(storeRoot, projectId);
}

function projectPath(projectId) {
  return path.join(projectDir(projectId), "project.json");
}

function profilePath(projectId) {
  return path.join(projectDir(projectId), "profile.json");
}

function intakeStatePath(projectId) {
  return path.join(projectDir(projectId), "intake_state.json");
}

function latestAnalysisPath(projectId) {
  return path.join(projectDir(projectId), "latest_analysis.json");
}

function analysesPath(projectId) {
  return path.join(projectDir(projectId), "analyses.jsonl");
}

export async function listProjects() {
  await ensureDir(storeRoot);
  const entries = await readdir(storeRoot, { withFileTypes: true });
  const projects = await Promise.all(
    entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => getProject(entry.name).catch(() => null))
  );
  return projects.filter(Boolean).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export async function createProject({ name, profile, intakeState }) {
  const timestamp = nowIso();
  const nextIntakeState = migrateProfileToIntakeState(profile || {}, intakeState || null);
  const project = {
    id: randomUUID(),
    name: name?.trim() || profile?.businessName || "Untitled StewardPath project",
    createdAt: timestamp,
    updatedAt: timestamp,
    schemaVersion: nextIntakeState.meta.schemaVersion,
    latestAnalysisId: null,
    analysisCount: 0
  };
  await writeJson(projectPath(project.id), project);
  await writeJson(profilePath(project.id), profile || {});
  await writeJson(intakeStatePath(project.id), nextIntakeState);
  await ensureDir(path.join(projectDir(project.id), "exports"));
  return { ...project, profile: profile || {}, intakeState: nextIntakeState };
}

export async function getProject(projectId) {
  const project = await readJson(projectPath(projectId));
  if (!project) return null;
  const profile = await readJson(profilePath(projectId), {});
  const existingIntakeState = await readJson(intakeStatePath(projectId), null);
  const intakeState = migrateProfileToIntakeState(profile, existingIntakeState);
  if (!existingIntakeState || existingIntakeState?.meta?.schemaVersion !== intakeState.meta.schemaVersion) {
    await writeJson(intakeStatePath(projectId), intakeState);
  }
  return { ...project, schemaVersion: intakeState.meta.schemaVersion, profile, intakeState };
}

export async function updateProject(projectId, updates) {
  const current = await getProject(projectId);
  if (!current) return null;
  const updatedProfile = updates.profile || current.profile || {};
  const updatedIntakeState = migrateProfileToIntakeState(updatedProfile, updates.intakeState || current.intakeState || null);
  const updatedProject = {
    id: current.id,
    name: updates.name?.trim() || current.name,
    createdAt: current.createdAt,
    updatedAt: nowIso(),
    schemaVersion: updatedIntakeState.meta.schemaVersion,
    latestAnalysisId: current.latestAnalysisId || null,
    analysisCount: current.analysisCount || 0
  };
  await writeJson(projectPath(projectId), updatedProject);
  await writeJson(profilePath(projectId), updatedProfile);
  await writeJson(intakeStatePath(projectId), updatedIntakeState);
  return { ...updatedProject, profile: updatedProfile, intakeState: updatedIntakeState };
}

export async function appendAnalysis(projectId, { profileSnapshot, intakeSnapshot: providedIntakeSnapshot, analysis }) {
  const current = await getProject(projectId);
  if (!current) return null;
  const intakeSnapshot = appendSnapshot(
    migrateProfileToIntakeState(profileSnapshot || current.profile || {}, providedIntakeSnapshot || current.intakeState || null),
    analysis?.readiness?.overall
  );
  const entry = {
    analysisId: randomUUID(),
    projectId,
    createdAt: nowIso(),
    profileSnapshot: profileSnapshot || current.profile || {},
    intakeSnapshot,
    analysis,
    analysisSource: analysis?.analysis_source || analysis?.analysisSource || "unknown",
    llmModels: analysis?.llm_models || analysis?.llmModels || {},
    llmErrors: analysis?.llm_errors || analysis?.llmErrors || [],
    version: "stewardpath-concierge-3"
  };
  await ensureDir(projectDir(projectId));
  await appendFile(analysesPath(projectId), `${JSON.stringify(entry)}\n`, "utf8");
  await writeJson(latestAnalysisPath(projectId), entry);
  await updateProject(projectId, {
    name: current.name,
    profile: profileSnapshot || current.profile || {},
    intakeState: intakeSnapshot
  });
  const updated = await getProject(projectId);
  const project = {
    ...updated,
    latestAnalysisId: entry.analysisId,
    analysisCount: (current.analysisCount || 0) + 1,
    updatedAt: entry.createdAt
  };
  await writeJson(projectPath(projectId), {
    id: project.id,
    name: project.name,
    createdAt: project.createdAt,
    updatedAt: project.updatedAt,
    schemaVersion: intakeSnapshot.meta.schemaVersion,
    latestAnalysisId: project.latestAnalysisId,
    analysisCount: project.analysisCount
  });
  return entry;
}

export async function listAnalyses(projectId) {
  assertProjectId(projectId);
  try {
    const lines = (await readFile(analysesPath(projectId), "utf8"))
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    return lines.map((line) => JSON.parse(line)).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}

export async function getLatestAnalysis(projectId) {
  return readJson(latestAnalysisPath(projectId), null);
}

export async function appendLead(lead) {
  const entry = {
    id: randomUUID(),
    createdAt: nowIso(),
    name: lead.name || "",
    email: lead.email || "",
    businessType: lead.businessType || "",
    timeline: lead.timeline || "",
    role: lead.role || "",
    intent: lead.intent || "general"
  };
  await ensureDir(leadRoot);
  await appendFile(leadLogPath, `${JSON.stringify(entry)}\n`, "utf8");
  return entry;
}

export async function listLeads() {
  try {
    const lines = (await readFile(leadLogPath, "utf8"))
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    return lines.map((line) => JSON.parse(line)).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}
