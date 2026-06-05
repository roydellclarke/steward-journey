"""Shared session-cookie handling for the HttpOnly passwordless session.

Both the auth router (which issues and clears the cookie) and the project
routes (which enforce it) need the same view of a session, so the signing
salt, cookie name, and TTL live here in one place to avoid drift.
"""

from __future__ import annotations

import secrets

from fastapi import Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.storage.auth_db import AuthStore


COOKIE_NAME = "sp_session"
SESSION_TTL_DAYS = 30
_MAX_AGE = SESSION_TTL_DAYS * 24 * 3600


class SessionCookie:
    """Issues, reads, and clears the signed HttpOnly session cookie."""

    def __init__(self, secret_key: str, cookie_secure: bool) -> None:
        self._serializer = URLSafeTimedSerializer(secret_key, salt="sp-session")
        self._secure = cookie_secure

    def read_owner(self, request: Request, auth_store: AuthStore) -> str | None:
        """Resolve the owner_id for a live session, or None if absent/invalid."""

        raw = request.cookies.get(COOKIE_NAME)
        if not raw:
            return None
        try:
            token = self._serializer.loads(raw, max_age=_MAX_AGE)
        except (BadSignature, SignatureExpired):
            return None
        return auth_store.read_session(token)

    def issue(self, response: Response, auth_store: AuthStore, owner_id: str) -> None:
        """Mint a fresh session for the owner and set the cookie."""

        token = secrets.token_urlsafe(32)
        auth_store.create_session(owner_id, token, ttl_days=SESSION_TTL_DAYS)
        # Cross-site (prod, separate subdomains) needs SameSite=None + Secure.
        # Local http dev runs same-site across ports, so Lax works without TLS.
        response.set_cookie(
            key=COOKIE_NAME,
            value=self._serializer.dumps(token),
            max_age=_MAX_AGE,
            httponly=True,
            secure=self._secure,
            samesite="none" if self._secure else "lax",
            path="/",
        )

    def clear(self, request: Request, response: Response, auth_store: AuthStore) -> None:
        """Delete the server-side session and expire the cookie."""

        raw = request.cookies.get(COOKIE_NAME)
        if raw:
            try:
                token = self._serializer.loads(raw, max_age=_MAX_AGE)
                auth_store.delete_session(token)
            except (BadSignature, SignatureExpired):
                pass
        response.delete_cookie(COOKIE_NAME, path="/")
