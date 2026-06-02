import { randomUUID } from "node:crypto";

export const INTAKE_SCHEMA_VERSION = 3;

function nowIso() {
  return new Date().toISOString();
}

function field(value, status = "answered", confidence = "medium", note = "") {
  const empty = value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length);
  return {
    value: empty ? null : value,
    status: empty ? "unknown" : status,
    confidence,
    updatedAt: nowIso(),
    note
  };
}

function splitList(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  return String(value || "")
    .split(/[,;\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function employeeBandFromCount(value) {
  const count = Number(value || 0);
  if (!count) return null;
  if (count <= 9) return "1-9";
  if (count <= 25) return "10-25";
  if (count <= 50) return "26-50";
  if (count <= 100) return "51-100";
  return "100+";
}

function revenueBandFromText(value) {
  const text = String(value || "").toLowerCase();
  if (!text) return null;
  if (text.includes("20m") || text.includes("20 m")) return "20m+";
  if (text.includes("5m") || text.includes("10m") || text.includes("5 m") || text.includes("10 m")) return "5m-20m";
  if (text.includes("1m") || text.includes("1 m")) return "1m-5m";
  if (text.includes("250")) return "250k-1m";
  return null;
}

function concentrationFromText(value) {
  const text = String(value || "").toLowerCase();
  if (!text) return null;
  if (text.includes("top 3") || text.includes("few") || text.includes("high")) return "high_few_clients";
  if (text.includes("moderate") || text.includes("important")) return "moderate";
  return "diversified";
}

function keyPersonRiskFromText(value) {
  const text = String(value || "").toLowerCase();
  if (!text) return null;
  if (text.includes("critical") || text.includes("high")) return "high";
  if (text.includes("medium") || text.includes("some")) return "medium";
  return "low";
}

function managementDepthFromEmployees(value) {
  const count = Number(value || 0);
  if (!count) return null;
  if (count < 5) return "none";
  if (count < 25) return "thin";
  return "solid";
}

function boolFromText(value) {
  const text = String(value || "").toLowerCase();
  if (!text) return null;
  if (text.includes("no ") || text.includes("none") || text.includes("not ")) return false;
  return true;
}

function functionsFromDependency(value) {
  const text = String(value || "").toLowerCase();
  const functions = [];
  if (text.includes("sales")) functions.push("sales");
  if (text.includes("customer") || text.includes("relationship")) functions.push("key relationships");
  if (text.includes("decision")) functions.push("major decisions");
  if (text.includes("owner") || text.includes("me")) functions.push("daily oversight");
  return functions;
}

export function migrateProfileToIntakeState(profile = {}, existing = null) {
  if (existing?.meta?.schemaVersion >= INTAKE_SCHEMA_VERSION) {
    return existing;
  }
  const timestamp = nowIso();
  const state = {
    meta: {
      ownerRecordId: existing?.meta?.ownerRecordId || randomUUID(),
      schemaVersion: INTAKE_SCHEMA_VERSION,
      createdAt: existing?.meta?.createdAt || timestamp,
      updatedAt: timestamp,
      completionPct: 0,
      lastSection: existing?.meta?.lastSection || "business",
      snapshots: existing?.meta?.snapshots || []
    },
    business: {
      category: field(profile.category || "founder-led business"),
      industry: field(profile.industry),
      region: field(profile.region || null),
      yearsOperating: field(Number(profile.yearsOperating || profile.years_operating || 0) || null),
      employeeBand: field(profile.employeeBand || employeeBandFromCount(profile.employees)),
      revenueBand: field(profile.revenueBand || revenueBandFromText(profile.revenueRange)),
      customerConcentration: field(profile.customerConcentrationStatus || concentrationFromText(profile.customerConcentration))
    },
    owner: {
      isFounder: field(profile.isFounder ?? true),
      role: field(profile.ownerRole || "owner"),
      ageBand: field(profile.ageBand || null, profile.ageBand ? "answered" : "skipped"),
      identityTiedToBusiness: field(profile.identityTiedToBusiness || null, profile.identityTiedToBusiness ? "answered" : "unknown")
    },
    financialClarity: {
      booksUpToDate: field(boolFromText(profile.financialStatementsCurrent)),
      financialsDocumented: field(boolFromText(profile.financialStatementsCurrent)),
      revenueTrend: field(profile.revenueTrend || null),
      profitabilityClear: field(Boolean(profile.profitMargin), profile.profitMargin ? "estimated" : "unknown"),
      ownerCompNormalized: field(boolFromText(profile.ownerCompensationDependency))
    },
    operationalTransferability: {
      functionsDependentOnOwner: field(functionsFromDependency(profile.ownerDependency)),
      keyPersonRisk: field(keyPersonRiskFromText(profile.keyEmployeeRisk)),
      managementDepth: field(profile.managementDepth || managementDepthFromEmployees(profile.employees)),
      systemsDocumented: field(boolFromText(profile.sopsDocumented))
    },
    processDocumentation: {
      sopsExist: field(boolFromText(profile.sopsDocumented)),
      documentedAreas: field(splitList(profile.sopsDocumented)),
      tribalKnowledgeRisk: field(String(profile.sopsDocumented || "").toLowerCase().includes("head") ? "high" : "medium")
    },
    familyAlignment: {
      familyInBusiness: field(profile.familyInBusiness ?? null, profile.familyInBusiness === undefined ? "unknown" : "answered"),
      expectationsKnown: field(Boolean(profile.familyContext), profile.familyContext ? "answered" : "unknown"),
      alignmentLevel: field(profile.familyContext ? "partial" : "unknown"),
      conflictRisk: field(profile.conflictRisk || null)
    },
    emotionalReadiness: {
      primaryMotivation: field(profile.ownerGoal),
      urgencyDrivers: field(splitList(profile.timeline)),
      readinessToLetGo: field(profile.readinessToLetGo || null, profile.readinessToLetGo ? "answered" : "unknown"),
      topConcerns: field(splitList(profile.fears))
    },
    protectedInterests: {
      employeeConcerns: field(splitList(profile.nonNegotiables || profile.fears)),
      customerContinuityConcerns: field(splitList(profile.nonNegotiables || profile.customerConcentration))
    },
    successorPreferences: {
      acceptablePaths: field(profile.acceptablePaths || []),
      unacceptablePaths: field(profile.unacceptablePaths || []),
      idealBuyerTraits: field(splitList(profile.nextOwnerTraits)),
      dealbreakers: field(splitList(profile.nonNegotiables))
    },
    nonNegotiables: field(splitList(profile.nonNegotiables)),
    disclosureControls: {
      defaultVisibility: "private",
      sectionOverrides: {},
      fieldOverrides: {}
    },
    uploads: existing?.uploads || [],
    derived: existing?.derived || undefined
  };
  state.meta.completionPct = completionPct(state);
  return state;
}

export function completionPct(intakeState) {
  const fields = [];
  function collect(value) {
    if (!value || typeof value !== "object") return;
    if ("status" in value && "value" in value) {
      fields.push(value);
      return;
    }
    Object.values(value).forEach(collect);
  }
  collect(intakeState);
  if (!fields.length) return 0;
  const complete = fields.filter((item) => ["answered", "estimated"].includes(item.status)).length;
  return Math.round((complete / fields.length) * 100);
}

export function appendSnapshot(intakeState, readinessScore) {
  if (!intakeState) return intakeState;
  return {
    ...intakeState,
    meta: {
      ...intakeState.meta,
      updatedAt: nowIso(),
      completionPct: completionPct(intakeState),
      snapshots: [
        ...(intakeState.meta?.snapshots || []),
        { takenAt: nowIso(), readinessScore: Number(readinessScore || 0) }
      ].slice(-24)
    }
  };
}
