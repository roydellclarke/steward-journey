"""Pydantic schemas for the StewardPath API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OwnerProfileRequest(BaseModel):
    business_name: str = ""
    industry: str = ""
    years_operating: int = 0
    employees: int = 0
    revenue_range: str = ""
    profit_margin: str = ""
    owner_dependency: str = ""
    timeline: str = ""
    owner_goal: str = ""
    fears: str = ""
    non_negotiables: str = ""
    family_context: str = ""
    next_owner_traits: str = ""


class ProjectCreateRequest(BaseModel):
    name: str = ""
    profile: dict[str, Any] = Field(default_factory=dict)
    intake_state: dict[str, Any] | None = Field(default=None, alias="intakeState")

    model_config = {"populate_by_name": True}


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    profile: dict[str, Any] | None = None
    intake_state: dict[str, Any] | None = Field(default=None, alias="intakeState")

    model_config = {"populate_by_name": True}


class AnalysisCreateRequest(BaseModel):
    profile_snapshot: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    intake_snapshot: dict[str, Any] | None = Field(default=None, alias="intakeSnapshot")

    model_config = {"populate_by_name": True}


class RunAnalysisRequest(BaseModel):
    profile: OwnerProfileRequest
    project_id: str | None = None
    intake_state: dict[str, Any] | None = Field(default=None, alias="intakeState")

    model_config = {"populate_by_name": True}


class LeadCreateRequest(BaseModel):
    name: str = ""
    email: str = ""
    businessType: str = ""
    timeline: str = ""
    role: str = ""
    intent: str = "general"


# ---------------------------------------------------------------- intake upgrade
class IntakeStateBody(BaseModel):
    """A bare IntakeState (or partial) for stateless intake operations."""

    intake_state: dict[str, Any] = Field(default_factory=dict, alias="intakeState")
    readiness_score: int | None = Field(default=None, alias="readinessScore")

    model_config = {"populate_by_name": True}


class IntakePatchRequest(BaseModel):
    """A partial IntakeState patch to merge onto a project's durable record."""

    intake_state: dict[str, Any] = Field(default_factory=dict, alias="intakeState")

    model_config = {"populate_by_name": True}


class ReflectRequest(BaseModel):
    intake_state: dict[str, Any] = Field(default_factory=dict, alias="intakeState")
    completed_section: str | None = Field(default=None, alias="completedSection")
    next_question_id: str | None = Field(default=None, alias="nextQuestionId")

    model_config = {"populate_by_name": True}


# ----------------------------------------------------------- passwordless auth
class AuthRequestBody(BaseModel):
    """Ask for a sign-in code + link at one of the two intake gates."""

    email: str = ""
    project_id: str | None = Field(default=None, alias="projectId")
    gate: Literal["save", "report", "checkout"] = "save"

    model_config = {"populate_by_name": True}


class AuthVerifyBody(BaseModel):
    """Verify a one-time code the owner typed in."""

    email: str = ""
    code: str = ""


class AuthConfirmBody(BaseModel):
    """Confirm a magic link after the explicit click on the landing page."""

    token: str = ""


class CheckoutRequest(BaseModel):
    """Start a Stripe Checkout for one of the three paid products."""

    product: Literal["report", "concierge", "advisor"]
    project_id: str | None = Field(default=None, alias="projectId")

    model_config = {"populate_by_name": True}


class SuccessorCandidate(BaseModel):
    """One candidate weighed on the successor-fit scorecard."""

    id: str = ""
    name: str = ""
    kind: str = "outside_buyer"
    ratings: dict[str, int] = Field(default_factory=dict)
    offer_strength: int = Field(default=3, alias="offerStrength")
    dealbreaker: bool = False
    notes: str = ""

    model_config = {"populate_by_name": True}


class SuccessorsBody(BaseModel):
    candidates: list[SuccessorCandidate] = Field(default_factory=list)


class BookReviewRequest(BaseModel):
    """Request a human readiness review (single human touchpoint)."""

    name: str = ""
    email: str = ""
    preferred_time: str = Field(default="", alias="preferredTime")
    note: str = ""

    model_config = {"populate_by_name": True}
