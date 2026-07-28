"""Canonical StewardPath IntakeState schema, lossless migration, and helpers.

This module is the single source of truth for the structured intake-state object
described in the Concierge-Experience upgrade brief. It is intentionally pure
Python (no FastAPI / Pydantic) so the deterministic logic stays importable and
testable without cloud or web dependencies.

Every owner-supplied value is wrapped in a ``Field`` shape::

    {"value": <T> | None, "status": FieldStatus, "confidence": ..., "updatedAt": ..., "note": ...}

``status`` carries meaning: "answered", "estimated", "unknown" (a readiness gap,
not an error), "skipped" (deferred), "pending_document". ``unknown``/``skipped``
are signals that feed scoring and the roadmap; they never block the flow.

Upgrade note: ``migrate_profile_to_intake_state`` is now LOSSLESS. When an
existing record is passed in, its answered fields are preserved and only missing
structure is filled. Older records are migrated forward by ``schemaVersion``.
"""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any
from uuid import uuid4


INTAKE_SCHEMA_VERSION = 4

FIELD_STATUSES = {"answered", "estimated", "unknown", "skipped", "pending_document"}

# Section -> ordered field names. Drives lossless rebuilds and completion math.
SECTION_FIELDS: dict[str, list[str]] = {
    "business": [
        "category",
        "industry",
        "region",
        "yearsOperating",
        "employeeBand",
        "revenueBand",
        "customerConcentration",
    ],
    "owner": ["isFounder", "role", "ageBand", "identityTiedToBusiness"],
    "financialClarity": [
        "booksUpToDate",
        "financialsDocumented",
        "revenueTrend",
        "profitabilityClear",
        "ownerCompNormalized",
    ],
    "operationalTransferability": [
        "functionsDependentOnOwner",
        "keyPersonRisk",
        "managementDepth",
        "systemsDocumented",
    ],
    "processDocumentation": ["sopsExist", "documentedAreas", "tribalKnowledgeRisk"],
    "familyAlignment": [
        "familyInBusiness",
        "expectationsKnown",
        "alignmentLevel",
        "conflictRisk",
    ],
    "emotionalReadiness": [
        "primaryMotivation",
        "urgencyDrivers",
        "readinessToLetGo",
        "topConcerns",
    ],
    "protectedInterests": ["employeeConcerns", "customerContinuityConcerns"],
    "successorPreferences": [
        "acceptablePaths",
        "unacceptablePaths",
        "idealBuyerTraits",
        "dealbreakers",
    ],
}

# Section order = emotional sequencing: easy/neutral first, sensitive later.
SECTION_ORDER = [
    "business",
    "owner",
    "operationalTransferability",
    "processDocumentation",
    "financialClarity",
    "successorPreferences",
    "protectedInterests",
    "familyAlignment",
    "emotionalReadiness",
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _field(
    value: Any,
    status: str = "answered",
    confidence: str = "medium",
    note: str = "",
) -> dict[str, Any]:
    empty = value is None or value == "" or value == []
    return {
        "value": None if empty else value,
        "status": "unknown" if empty else status,
        "confidence": confidence,
        "updatedAt": _now(),
        "note": note,
    }


def is_field(value: Any) -> bool:
    return isinstance(value, dict) and "status" in value and "value" in value


def normalize_field(raw: Any) -> dict[str, Any]:
    """Coerce arbitrary client input into a valid Field, preserving meaning."""

    if not is_field(raw):
        return _field(raw)
    value = raw.get("value")
    status = raw.get("status")
    empty = value is None or value == "" or value == []
    if status not in FIELD_STATUSES:
        status = "unknown" if empty else "answered"
    # An "answered" field with no value is really a gap; keep the explicit
    # "skipped"/"pending_document" signals the owner chose.
    if empty and status not in {"unknown", "skipped", "pending_document"}:
        status = "unknown"
    return {
        "value": None if empty else value,
        "status": status,
        "confidence": raw.get("confidence") or "medium",
        "updatedAt": raw.get("updatedAt") or _now(),
        "note": raw.get("note") or "",
    }


def _split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if item]
    return [item.strip() for item in str(value or "").replace(";", ",").split(",") if item.strip()]


def _employee_band(value: Any) -> str | None:
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        return None
    if count <= 0:
        return None
    if count <= 9:
        return "1-9"
    if count <= 25:
        return "10-25"
    if count <= 50:
        return "26-50"
    if count <= 100:
        return "51-100"
    return "100+"


def _revenue_band(value: Any) -> str | None:
    text = str(value or "").lower()
    if not text:
        return None
    # Try to extract the largest "<n>m" magnitude (handles "$3M", "$5M-$10M").
    millions = [float(match) for match in re.findall(r"(\d+(?:\.\d+)?)\s*m", text)]
    if millions:
        top = max(millions)
        if top >= 20:
            return "20m+"
        if top >= 5:
            return "5m-20m"
        if top >= 1:
            return "1m-5m"
        return "250k-1m"
    if "250" in text or "k" in text:
        return "250k-1m"
    return None


def _bool_from_text(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value or "").lower()
    if not text:
        return None
    if "no " in text or "none" in text or "not " in text or text in {"no", "false"}:
        return False
    return True


# "answered"/"estimated" count toward completion. "skipped" counts too: the
# owner made a decision, the flow can proceed. "unknown" is an open gap.
_COMPLETE_STATUSES = {"answered", "estimated", "skipped"}


def _completion_counts(state: dict[str, Any]) -> tuple[int, int]:
    """Return (complete, total) fields, the basis for the completion percent.

    ``total`` counts every defined field, including ones branching has not
    surfaced yet; ``complete`` counts those answered, estimated, or skipped.
    """

    fields: list[dict[str, Any]] = []

    def collect(value: Any) -> None:
        if not isinstance(value, dict):
            return
        if is_field(value):
            fields.append(value)
            return
        for child in value.values():
            collect(child)

    for section in list(SECTION_FIELDS.keys()) + ["nonNegotiables"]:
        collect(state.get(section))
    complete = len([item for item in fields if item.get("status") in _COMPLETE_STATUSES])
    return complete, len(fields)


def _completion_pct(state: dict[str, Any]) -> int:
    complete, total = _completion_counts(state)
    if not total:
        return 0
    return round((complete / total) * 100)


def _set_completion(state: dict[str, Any]) -> None:
    """Write the completion percent plus the raw counts into meta.

    Exposing ``completeFields``/``totalFields`` lets the UI show live progress
    against the same denominator the backend uses, so the number does not
    snap back when the answers save.
    """

    complete, total = _completion_counts(state)
    meta = state.setdefault("meta", {})
    meta["completionPct"] = round((complete / total) * 100) if total else 0
    meta["completeFields"] = complete
    meta["totalFields"] = total


def _legacy_profile_field(section: str, name: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Synthesize a Field from the legacy flat owner profile (back-compat seeding)."""

    p = profile
    seeders = {
        ("business", "category"): lambda: _field(p.get("category") or ("family" if p.get("familyInBusiness") else "founder-led business")),
        ("business", "industry"): lambda: _field(p.get("industry")),
        ("business", "region"): lambda: _field(p.get("region")),
        ("business", "yearsOperating"): lambda: _field(p.get("yearsOperating") or p.get("years_operating")),
        ("business", "employeeBand"): lambda: _field(p.get("employeeBand") or _employee_band(p.get("employees"))),
        ("business", "revenueBand"): lambda: _field(p.get("revenueBand") or _revenue_band(p.get("revenueRange") or p.get("revenue_range"))),
        ("business", "customerConcentration"): lambda: _field(p.get("customerConcentrationStatus") or _concentration_from_text(p.get("customerConcentration"))),
        ("owner", "isFounder"): lambda: _field(p.get("isFounder", True)),
        ("owner", "role"): lambda: _field(p.get("ownerRole") or "owner"),
        ("owner", "ageBand"): lambda: _field(p.get("ageBand"), status="skipped" if not p.get("ageBand") else "answered"),
        ("owner", "identityTiedToBusiness"): lambda: _field(p.get("identityTiedToBusiness")),
        ("financialClarity", "booksUpToDate"): lambda: _field(_bool_from_text(p.get("financialStatementsCurrent"))),
        ("financialClarity", "financialsDocumented"): lambda: _field(_bool_from_text(p.get("financialStatementsCurrent"))),
        ("financialClarity", "revenueTrend"): lambda: _field(p.get("revenueTrend")),
        ("financialClarity", "profitabilityClear"): lambda: _field(bool(p.get("profitMargin") or p.get("profit_margin")), status="estimated" if (p.get("profitMargin") or p.get("profit_margin")) else "unknown"),
        ("financialClarity", "ownerCompNormalized"): lambda: _field(_bool_from_text(p.get("ownerCompensationDependency"))),
        ("operationalTransferability", "functionsDependentOnOwner"): lambda: _field(_split_list(p.get("ownerDependency") or p.get("owner_dependency"))),
        ("operationalTransferability", "keyPersonRisk"): lambda: _field(p.get("keyPersonRisk") or _risk_from_text(p.get("keyEmployeeRisk"))),
        ("operationalTransferability", "managementDepth"): lambda: _field(p.get("managementDepth")),
        ("operationalTransferability", "systemsDocumented"): lambda: _field(_bool_from_text(p.get("sopsDocumented"))),
        ("processDocumentation", "sopsExist"): lambda: _field(_bool_from_text(p.get("sopsDocumented"))),
        ("processDocumentation", "documentedAreas"): lambda: _field(_split_list(p.get("sopsDocumented"))),
        ("processDocumentation", "tribalKnowledgeRisk"): lambda: _field("high" if "head" in str(p.get("sopsDocumented", "")).lower() else None),
        ("familyAlignment", "familyInBusiness"): lambda: _field(p.get("familyInBusiness")),
        ("familyAlignment", "expectationsKnown"): lambda: _field(bool(p.get("familyContext") or p.get("family_context")) or None),
        ("familyAlignment", "alignmentLevel"): lambda: _field("partial" if (p.get("familyContext") or p.get("family_context")) else None),
        ("familyAlignment", "conflictRisk"): lambda: _field(p.get("conflictRisk")),
        ("emotionalReadiness", "primaryMotivation"): lambda: _field(p.get("ownerGoal") or p.get("owner_goal")),
        ("emotionalReadiness", "urgencyDrivers"): lambda: _field(_split_list(p.get("timeline"))),
        ("emotionalReadiness", "readinessToLetGo"): lambda: _field(p.get("readinessToLetGo")),
        ("emotionalReadiness", "topConcerns"): lambda: _field(_split_list(p.get("fears"))),
        ("protectedInterests", "employeeConcerns"): lambda: _field(_split_list(p.get("nonNegotiables") or p.get("non_negotiables") or p.get("fears"))),
        ("protectedInterests", "customerContinuityConcerns"): lambda: _field(_split_list(p.get("nonNegotiables") or p.get("non_negotiables") or p.get("customerConcentration"))),
        ("successorPreferences", "acceptablePaths"): lambda: _field(p.get("acceptablePaths") or None),
        ("successorPreferences", "unacceptablePaths"): lambda: _field(p.get("unacceptablePaths") or None),
        ("successorPreferences", "idealBuyerTraits"): lambda: _field(_split_list(p.get("nextOwnerTraits") or p.get("next_owner_traits"))),
        ("successorPreferences", "dealbreakers"): lambda: _field(_split_list(p.get("nonNegotiables") or p.get("non_negotiables"))),
    }
    seeder = seeders.get((section, name))
    return seeder() if seeder else _field(None)


def _concentration_from_text(value: Any) -> str | None:
    text = str(value or "").lower()
    if not text:
        return None
    if "whole" in text or "few" in text or "top 1" in text or "one customer" in text:
        return "high_few_clients"
    if "top 3" in text or "important" in text or "moderate" in text:
        return "moderate"
    if "divers" in text or "spread" in text or "many" in text:
        return "diversified"
    return None


def _risk_from_text(value: Any) -> str | None:
    text = str(value or "").lower()
    if not text:
        return None
    if "critical" in text or "high" in text or "two senior" in text:
        return "high"
    if "some" in text or "medium" in text:
        return "medium"
    if "low" in text or "none" in text:
        return "low"
    return "medium"


def empty_state(owner_record_id: str | None = None) -> dict[str, Any]:
    """A fully-formed, empty IntakeState (every field present, status unknown)."""

    return migrate_profile_to_intake_state(
        {},
        {"meta": {"ownerRecordId": owner_record_id}} if owner_record_id else None,
    )


def migrate_profile_to_intake_state(
    profile: dict[str, Any] | None,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build/repair an IntakeState, LOSSLESSLY preserving any existing answers.

    - If ``existing`` already holds a field for a slot, that field is kept
      verbatim (answers are never overwritten by re-running migration).
    - Otherwise the legacy flat ``profile`` is used to seed a best-effort value.
    - Missing structure is always filled so the object is complete and valid.
    """

    profile = profile or {}
    existing = existing or {}
    existing_meta = existing.get("meta", {}) if isinstance(existing.get("meta"), dict) else {}
    timestamp = _now()

    def field_for(section: str, name: str) -> dict[str, Any]:
        prior = existing.get(section, {})
        if isinstance(prior, dict) and is_field(prior.get(name)):
            return normalize_field(prior[name])
        return _legacy_profile_field(section, name, profile)

    state: dict[str, Any] = {
        "meta": {
            "ownerRecordId": existing_meta.get("ownerRecordId") or str(uuid4()),
            "schemaVersion": INTAKE_SCHEMA_VERSION,
            "createdAt": existing_meta.get("createdAt") or timestamp,
            "updatedAt": timestamp,
            "completionPct": 0,
            "completeFields": 0,
            "totalFields": 0,
            "lastSection": existing_meta.get("lastSection") or SECTION_ORDER[0],
            "snapshots": list(existing_meta.get("snapshots", [])),
        },
    }

    for section, names in SECTION_FIELDS.items():
        state[section] = {name: field_for(section, name) for name in names}

    # Top-level nonNegotiables Field (list)
    if is_field(existing.get("nonNegotiables")):
        state["nonNegotiables"] = normalize_field(existing["nonNegotiables"])
    else:
        state["nonNegotiables"] = _field(_split_list(profile.get("nonNegotiables") or profile.get("non_negotiables")))

    prior_disclosure = existing.get("disclosureControls", {}) if isinstance(existing.get("disclosureControls"), dict) else {}
    state["disclosureControls"] = {
        "defaultVisibility": prior_disclosure.get("defaultVisibility") or "private",
        "sectionOverrides": dict(prior_disclosure.get("sectionOverrides", {})),
        "fieldOverrides": dict(prior_disclosure.get("fieldOverrides", {})),
    }

    state["uploads"] = list(existing.get("uploads", []))
    state["derived"] = existing.get("derived") if isinstance(existing.get("derived"), dict) else None

    _set_completion(state)
    return state


def merge_intake_patch(state: dict[str, Any], patch: dict[str, Any] | None) -> dict[str, Any]:
    """Apply a partial client update onto an IntakeState, field by field.

    ``patch`` may contain section dicts with partial fields, a top-level
    ``nonNegotiables`` field, ``disclosureControls``, ``uploads``, and
    ``meta.lastSection``. Unknown keys are ignored; existing answers outside the
    patch are preserved.
    """

    state = migrate_profile_to_intake_state({}, state)
    patch = patch or {}

    for section, names in SECTION_FIELDS.items():
        incoming = patch.get(section)
        if not isinstance(incoming, dict):
            continue
        for name in names:
            if name in incoming:
                state[section][name] = normalize_field(incoming[name])

    if "nonNegotiables" in patch:
        state["nonNegotiables"] = normalize_field(patch["nonNegotiables"])

    incoming_disclosure = patch.get("disclosureControls")
    if isinstance(incoming_disclosure, dict):
        controls = state["disclosureControls"]
        if "defaultVisibility" in incoming_disclosure:
            controls["defaultVisibility"] = incoming_disclosure["defaultVisibility"] or "private"
        if isinstance(incoming_disclosure.get("sectionOverrides"), dict):
            controls["sectionOverrides"].update(incoming_disclosure["sectionOverrides"])
        if isinstance(incoming_disclosure.get("fieldOverrides"), dict):
            controls["fieldOverrides"].update(incoming_disclosure["fieldOverrides"])

    if isinstance(patch.get("uploads"), list):
        state["uploads"] = patch["uploads"]

    patch_meta = patch.get("meta", {})
    if isinstance(patch_meta, dict) and patch_meta.get("lastSection"):
        state["meta"]["lastSection"] = patch_meta["lastSection"]

    state["meta"]["updatedAt"] = _now()
    _set_completion(state)
    return state


def _resolve_field(state: dict[str, Any], section: str, name: str) -> dict[str, Any] | None:
    node = state.get(section)
    # Top-level Fields (e.g. nonNegotiables) ARE the field — there is no nesting.
    if is_field(node):
        return node
    if isinstance(node, dict):
        candidate = node.get(name)
        if is_field(candidate):
            return candidate
    return None


def field_value(state: dict[str, Any], section: str, name: str) -> Any:
    field = _resolve_field(state, section, name)
    return field.get("value") if field else None


def field_status(state: dict[str, Any], section: str, name: str) -> str:
    field = _resolve_field(state, section, name)
    return field.get("status") if field else "unknown"


def iter_fields(state: dict[str, Any]):
    """Yield (section, name, field) for every owner-supplied field."""

    for section, names in SECTION_FIELDS.items():
        for name in names:
            field = (state.get(section, {}) or {}).get(name)
            if is_field(field):
                yield section, name, field
    if is_field(state.get("nonNegotiables")):
        yield "nonNegotiables", "nonNegotiables", state["nonNegotiables"]


def open_gaps(state: dict[str, Any]) -> list[str]:
    """Field paths the owner has not answered (unknown/skipped/pending)."""

    gaps = []
    for section, name, field in iter_fields(state):
        if field.get("status") in {"unknown", "skipped", "pending_document"}:
            gaps.append(f"{section}.{name}")
    return gaps


def set_derived(state: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    state = migrate_profile_to_intake_state({}, state)
    state["derived"] = derived
    state["meta"]["updatedAt"] = _now()
    return state


def append_snapshot(state: dict[str, Any], readiness_score: int | float | None) -> dict[str, Any]:
    state = migrate_profile_to_intake_state({}, state)
    state["meta"]["updatedAt"] = _now()
    _set_completion(state)
    snapshots = list(state["meta"].get("snapshots", []))
    snapshots.append({"takenAt": _now(), "readinessScore": int(readiness_score or 0)})
    state["meta"]["snapshots"] = snapshots[-24:]
    return state
