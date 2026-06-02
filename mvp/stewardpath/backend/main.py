"""FastAPI app for StewardPath MVP."""

from __future__ import annotations

from dataclasses import asdict

from mvp.stewardpath.backend.reasoning import OwnerProfile, analyze_owner_profile


try:  # FastAPI remains optional for offline harness tests.
    from fastapi import FastAPI
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    FastAPI = None
    BaseModel = object


class OwnerProfileRequest(BaseModel):  # type: ignore[misc]
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


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install the API dependencies first.")

    app = FastAPI(title="StewardPath API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/analyze")
    def analyze(request: OwnerProfileRequest) -> dict:
        profile = OwnerProfile(**request.model_dump())
        return analyze_owner_profile(profile)

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
        return {"request": asdict(profile), "analysis": analyze_owner_profile(profile)}

    return app


app = create_app() if FastAPI is not None else None

