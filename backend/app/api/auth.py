"""Passwordless email auth: the two intake gates.

Owners never set a password. They prove control of an email with a one-time
code (primary) or a magic link (fallback). Both arrive in the same message.
This router wires the HTTP surface; the security-sensitive state lives in
``AuthStore`` and token signing/expiry is handled by ``itsdangerous``.

Gate 1 ("save"): pause and resume the intake later.
Gate 2 ("report"): open the finished readiness report.

On the first successful sign-in we tie the in-progress (anonymous) intake
project to a durable per-owner record and hand back a session cookie.
"""

from __future__ import annotations

import re
import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import Settings
from app.models.schemas import AuthConfirmBody, AuthRequestBody, AuthVerifyBody
from app.services.email import EmailSender, build_auth_email
from app.storage.auth_db import AuthStore
from app.storage.projects import ProjectStore


COOKIE_NAME = "sp_session"
SESSION_TTL_DAYS = 30
MAX_CODE_ATTEMPTS = 5
EMAIL_RATE_MAX = 5  # sign-in requests per email...
EMAIL_RATE_WINDOW_MIN = 15  # ...within this window
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Deliberately generic. Never tell the caller why a code or link failed, so it
# cannot become an oracle for which emails exist or which codes are close.
_GENERIC_FAILURE = "That code or link did not work. It may have expired or already been used. Please request a new one."


def build_auth_router(
    *,
    settings: Settings,
    project_store: ProjectStore,
    auth_store: AuthStore,
    email_sender: EmailSender,
    limiter,
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    link_serializer = URLSafeTimedSerializer(settings.secret_key, salt="sp-magic-link")
    session_serializer = URLSafeTimedSerializer(settings.secret_key, salt="sp-session")
    ttl_seconds = settings.otp_ttl_minutes * 60

    def _set_session_cookie(response: Response, signed_value: str) -> None:
        # Cross-site (prod, separate subdomains) needs SameSite=None + Secure.
        # Local http dev runs same-site across ports, so Lax works without TLS.
        samesite = "none" if settings.cookie_secure else "lax"
        response.set_cookie(
            key=COOKIE_NAME,
            value=signed_value,
            max_age=SESSION_TTL_DAYS * 24 * 3600,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=samesite,
            path="/",
        )

    def _owner_from_request(request: Request) -> str | None:
        raw_cookie = request.cookies.get(COOKIE_NAME)
        if not raw_cookie:
            return None
        try:
            session_token = session_serializer.loads(raw_cookie, max_age=SESSION_TTL_DAYS * 24 * 3600)
        except (BadSignature, SignatureExpired):
            return None
        return auth_store.read_session(session_token)

    def _complete_auth(*, email: str, gate: str | None, project_id: str | None, response: Response) -> dict:
        """Find-or-create the owner, claim the intake project, issue a session."""

        owner_id = auth_store.find_or_create_owner(email)
        claimed = False
        if project_id and project_store.get_project(project_id):
            auth_store.link_project(owner_id, project_id)
            # Audit stores metadata only, never the email itself.
            project_store.audit.record("owner_authenticated", project_id=project_id, detail={"gate": gate})
            claimed = True

        session_token = secrets.token_urlsafe(32)
        auth_store.create_session(owner_id, session_token, ttl_days=SESSION_TTL_DAYS)
        _set_session_cookie(response, session_serializer.dumps(session_token))

        return {
            "authenticated": True,
            "email": email,
            "gate": gate,
            "projectId": project_id if claimed else None,
            "projects": auth_store.projects_for_owner(owner_id),
        }

    # -------------------------------------------------------------- request
    @router.post("/request")
    @limiter.limit("15/minute")
    def request_code(body: AuthRequestBody, request: Request) -> dict:
        email = body.email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise HTTPException(status_code=400, detail="Please enter a valid email address.")

        # Per-email throttle. Over the cap we still answer the same way, we just
        # do not mint or send anything. Combined with the uniform response, a
        # caller cannot tell an existing owner from a new one, or a sent code
        # from a skipped one.
        recent = auth_store.recent_challenge_count(email, within_minutes=EMAIL_RATE_WINDOW_MIN)
        if recent < EMAIL_RATE_MAX:
            code = f"{secrets.randbelow(10**6):06d}"
            token = secrets.token_urlsafe(32)
            auth_store.create_challenge(
                email=email,
                code=code,
                token=token,
                gate=body.gate,
                project_id=body.project_id,
                ttl_minutes=settings.otp_ttl_minutes,
                request_ip=request.client.host if request.client else None,
                max_attempts=MAX_CODE_ATTEMPTS,
            )
            signed = link_serializer.dumps({"t": token, "g": body.gate, "p": body.project_id})
            link = f"{settings.frontend_origin}/auth/confirm?token={signed}"
            email_sender.send(build_auth_email(to=email, code=code, link=link, gate=body.gate))

        # Uniform response regardless of existence, rate state, or send outcome.
        return {"ok": True, "ttlMinutes": settings.otp_ttl_minutes}

    # --------------------------------------------------------------- verify
    @router.post("/verify")
    @limiter.limit("30/minute")
    def verify_code(body: AuthVerifyBody, request: Request, response: Response) -> dict:
        result = auth_store.verify_code(body.email, body.code)
        if not result.ok:
            raise HTTPException(status_code=400, detail=_GENERIC_FAILURE)
        return _complete_auth(email=result.email, gate=result.gate, project_id=result.project_id, response=response)

    # ----------------------------------------------- magic-link confirmation
    @router.get("/confirm")
    @limiter.limit("30/minute")
    def peek_link(token: str, request: Request) -> dict:
        """Landing-page peek. Validates the signature but does NOT consume it,
        so an email scanner that pre-fetches the link cannot burn it. The owner
        must POST an explicit confirmation to sign in."""

        try:
            payload = link_serializer.loads(token, max_age=ttl_seconds)
        except (BadSignature, SignatureExpired):
            raise HTTPException(status_code=400, detail=_GENERIC_FAILURE)
        return {"ok": True, "gate": payload.get("g", "save")}

    @router.post("/confirm")
    @limiter.limit("30/minute")
    def confirm_link(body: AuthConfirmBody, request: Request, response: Response) -> dict:
        try:
            payload = link_serializer.loads(body.token, max_age=ttl_seconds)
        except (BadSignature, SignatureExpired):
            raise HTTPException(status_code=400, detail=_GENERIC_FAILURE)
        result = auth_store.consume_token(payload.get("t", ""))
        if not result.ok:
            raise HTTPException(status_code=400, detail=_GENERIC_FAILURE)
        return _complete_auth(email=result.email, gate=result.gate, project_id=result.project_id, response=response)

    # --------------------------------------------------------- session state
    @router.get("/me")
    def me(request: Request) -> dict:
        owner_id = _owner_from_request(request)
        if not owner_id:
            return {"authenticated": False}
        return {
            "authenticated": True,
            "email": auth_store.owner_email(owner_id),
            "projects": auth_store.projects_for_owner(owner_id),
        }

    @router.post("/logout")
    def logout(request: Request, response: Response) -> dict:
        raw_cookie = request.cookies.get(COOKIE_NAME)
        if raw_cookie:
            try:
                session_token = session_serializer.loads(raw_cookie, max_age=SESSION_TTL_DAYS * 24 * 3600)
                auth_store.delete_session(session_token)
            except (BadSignature, SignatureExpired):
                pass
        response.delete_cookie(COOKIE_NAME, path="/")
        return {"ok": True}

    return router
