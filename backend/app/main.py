"""Standalone StewardPath FastAPI application."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.auth import build_auth_router
from app.core.config import Settings
from app.intake import branching, questions as qbank
from app.intake.handoff import build_handoff
from app.intake.reflection import reflect as build_reflection
from app.models.schemas import (
    AnalysisCreateRequest,
    BookReviewRequest,
    IntakePatchRequest,
    IntakeStateBody,
    LeadCreateRequest,
    OwnerProfileRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ReflectRequest,
    RunAnalysisRequest,
)
from app.services.email import build_email_sender
from app.services.llm_reasoning import analyze_owner_profile_with_optional_llm
from app.services.reasoning import OwnerProfile
from app.services.scoring import score_intake
from app.services.synthesis import synthesize
from app.storage.auth_db import AuthStore
from app.storage.intake_state import merge_intake_patch, migrate_profile_to_intake_state
from app.storage.projects import ProjectStore


settings = Settings.from_env()
store = ProjectStore(settings.data_root)
auth_store = AuthStore(settings.auth_db_path, settings.secret_key)
email_sender = build_email_sender(postmark_token=settings.postmark_token, postmark_from=settings.postmark_from)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="StewardPath API", version="0.3.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Auth uses an HttpOnly session cookie, so the browser must be allowed to send
# credentials. That rules out the "*" origin: we name the exact frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    build_auth_router(
        settings=settings,
        project_store=store,
        auth_store=auth_store,
        email_sender=email_sender,
        limiter=limiter,
    )
)


def _profile_from_request(request: OwnerProfileRequest) -> OwnerProfile:
    return OwnerProfile(**request.model_dump())


def _camel_profile(profile: OwnerProfileRequest) -> dict:
    snake = profile.model_dump()
    return {
        "businessName": snake["business_name"],
        "industry": snake["industry"],
        "yearsOperating": snake["years_operating"],
        "employees": snake["employees"],
        "revenueRange": snake["revenue_range"],
        "profitMargin": snake["profit_margin"],
        "ownerDependency": snake["owner_dependency"],
        "timeline": snake["timeline"],
        "ownerGoal": snake["owner_goal"],
        "fears": snake["fears"],
        "nonNegotiables": snake["non_negotiables"],
        "familyContext": snake["family_context"],
        "nextOwnerTraits": snake["next_owner_traits"],
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "stewardpath-backend", "version": "0.3.0"}


@app.post("/analyze")
def analyze(request: RunAnalysisRequest) -> dict:
    profile = _profile_from_request(request.profile)
    analysis = analyze_owner_profile_with_optional_llm(profile, settings)
    saved_analysis = None
    if request.project_id:
        # Persist any intake-state edits the owner made before analyzing.
        if request.intake_state is not None:
            store.update_project(request.project_id, name=None, profile=None, intake_state=request.intake_state)
        saved_analysis = store.append_analysis(
            request.project_id,
            profile_snapshot=_camel_profile(request.profile),
            analysis=analysis,
        )
        if saved_analysis is None:
            raise HTTPException(status_code=404, detail="Project not found")
    return {"analysis": analysis, "savedAnalysis": saved_analysis}


@app.get("/sample")
def sample() -> dict:
    profile = OwnerProfile(
        business_name="Harbor Tool & Die",
        industry="specialty manufacturing",
        years_operating=34,
        employees=28,
        revenue_range="$5M-$10M",
        profit_margin="12-15%",
        owner_dependency="medium - owner still owns key customer relationships",
        timeline="2-4 years",
        owner_goal="step back while protecting employees and customer trust",
        fears="a buyer will cut staff or erase the company name",
        non_negotiables="keep the local team and preserve customer service standards",
        family_context="children are supportive but do not want to operate the company",
        next_owner_traits="patient operator, local credibility, manufacturing experience",
    )
    return {"request": asdict(profile), "analysis": analyze_owner_profile_with_optional_llm(profile, settings)}


# --------------------------------------------------------------------- projects
@app.get("/projects")
def list_projects() -> dict:
    return {"projects": store.list_projects()}


@app.post("/projects", status_code=201)
def create_project(request: ProjectCreateRequest) -> dict:
    return {"project": store.create_project(name=request.name, profile=request.profile, intake_state=request.intake_state)}


@app.get("/projects/{project_id}")
def get_project(project_id: str) -> dict:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": project}


@app.patch("/projects/{project_id}")
def update_project(project_id: str, request: ProjectUpdateRequest) -> dict:
    project = store.update_project(project_id, name=request.name, profile=request.profile, intake_state=request.intake_state)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": project}


@app.delete("/projects/{project_id}")
def delete_project(project_id: str) -> dict:
    """Hard delete — honors the owner's right to remove their data."""

    if not store.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "projectId": project_id}


@app.get("/projects/{project_id}/export")
def export_project(project_id: str) -> dict:
    """'Your data' export — everything stored for this project."""

    export = store.export_project(project_id)
    if not export:
        raise HTTPException(status_code=404, detail="Project not found")
    return export


@app.get("/projects/{project_id}/analyses")
def list_analyses(project_id: str) -> dict:
    return {"analyses": store.list_analyses(project_id)}


@app.post("/projects/{project_id}/analyses", status_code=201)
def append_analysis(project_id: str, request: AnalysisCreateRequest) -> dict:
    entry = store.append_analysis(
        project_id,
        profile_snapshot=request.profile_snapshot,
        analysis=request.analysis,
        intake_snapshot=request.intake_snapshot,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"analysisEntry": entry}


@app.get("/projects/{project_id}/analyses/latest")
def latest_analysis(project_id: str) -> dict:
    entry = store.latest_analysis(project_id)
    if not entry:
        raise HTTPException(status_code=404, detail="No analysis has been saved for this project")
    return {"analysisEntry": entry}


@app.get("/projects/{project_id}/snapshots")
def project_snapshots(project_id: str) -> dict:
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"snapshots": store.snapshots(project_id)}


# ------------------------------------------------------- guided intake (stateless)
@app.get("/intake/questions")
def intake_questions() -> dict:
    """The curated question bank + section metadata for the guided flow."""

    return {
        "sections": qbank.all_sections(),
        "securityGatedSections": sorted(qbank.SECURITY_GATED_SECTIONS),
        "reassurance": qbank.SECTION_REASSURANCE,
    }


@app.post("/intake/plan")
def intake_plan(body: IntakeStateBody) -> dict:
    """Deterministic adaptive plan: next question, gates, reflections, routing."""

    state = migrate_profile_to_intake_state(None, body.intake_state)
    return {"intakeState": state, "plan": branching.build_intake_plan(state, body.readiness_score)}


@app.post("/intake/reflect")
def intake_reflect(body: ReflectRequest) -> dict:
    state = migrate_profile_to_intake_state(None, body.intake_state)
    reflection = build_reflection(
        state,
        completed_section=body.completed_section,
        next_question_id=body.next_question_id,
        settings=settings,
    )
    return {"reflection": reflection}


@app.post("/intake/score")
def intake_score(body: IntakeStateBody) -> dict:
    """Grounded readiness score + rationale + full synthesis from an IntakeState."""

    state = migrate_profile_to_intake_state(None, body.intake_state)
    return {
        "score": score_intake(state),
        "synthesis": synthesize(state, settings),
        "plan": branching.build_intake_plan(state, score_intake(state)["overall"]),
    }


# ------------------------------------------------- guided intake (project-scoped)
@app.get("/projects/{project_id}/intake")
def get_project_intake(project_id: str) -> dict:
    state = store.read_intake_state(project_id)
    if state is None:
        if not store.get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        state = migrate_profile_to_intake_state(None, None)
    scored = score_intake(state)
    return {"intakeState": state, "plan": branching.build_intake_plan(state, scored["overall"]), "score": scored}


@app.put("/projects/{project_id}/intake")
def put_project_intake(project_id: str, request: IntakePatchRequest) -> dict:
    project = store.update_project(project_id, name=None, profile=None, intake_state=request.intake_state)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    state = project["intakeState"]
    scored = score_intake(state)
    return {"intakeState": state, "plan": branching.build_intake_plan(state, scored["overall"]), "score": scored}


@app.post("/projects/{project_id}/intake/analyze", status_code=201)
def analyze_project_intake(project_id: str) -> dict:
    """Score the durable intake state, run grounded synthesis, and save it."""

    state = store.read_intake_state(project_id)
    if state is None:
        if not store.get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        state = migrate_profile_to_intake_state(None, None)
    bundle = synthesize(state, settings)
    saved = store.append_analysis(
        project_id,
        profile_snapshot=store.get_project(project_id).get("profile", {}),
        analysis=bundle,
        intake_snapshot=state,
    )
    return {"analysis": bundle, "savedAnalysis": saved, "score": score_intake(state)}


@app.get("/projects/{project_id}/handoff")
def project_handoff(project_id: str) -> dict:
    """The fully-prepped package for the single human readiness review."""

    state = store.read_intake_state(project_id)
    if state is None:
        if not store.get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        state = migrate_profile_to_intake_state(None, None)
    return {"handoff": build_handoff(state)}


@app.post("/projects/{project_id}/book-review", status_code=201)
def book_review(project_id: str, request: BookReviewRequest) -> dict:
    """Book the human readiness review; captures the lead and the handoff package."""

    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    lead = store.append_lead({**request.model_dump(), "intent": "readiness_review"})
    store.audit.record("review_requested", project_id=project_id, detail={"leadId": lead["id"]})
    state = store.read_intake_state(project_id) or migrate_profile_to_intake_state(None, None)
    return {"lead": lead, "handoff": build_handoff(state)}


# ----------------------------------------------------------------------- leads
@app.get("/leads")
def list_leads() -> dict:
    return {"leads": store.list_leads()}


@app.post("/leads", status_code=201)
def create_lead(request: LeadCreateRequest) -> dict:
    if not request.name and not request.email:
        raise HTTPException(status_code=400, detail="Please include at least a name or email.")
    return {"lead": store.append_lead(request.model_dump())}
