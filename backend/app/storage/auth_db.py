"""SQLite-backed store for passwordless email auth.

Holds the security-sensitive state that the file-based ``ProjectStore`` should
not: owner identities, short-lived sign-in challenges, owner-to-project links,
and active sessions. SQLite gives us atomic single-use enforcement (the consume
is an ``UPDATE ... WHERE consumed_at IS NULL`` guarded by row count), which a
JSON file cannot do safely under concurrent requests.

We never store a raw code, token, or session id. Every secret is kept as a
keyed HMAC-SHA256 digest, so a database leak alone cannot brute-force a 6-digit
code offline without the server secret. Comparison uses ``hmac.compare_digest``.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
from pathlib import Path
import sqlite3
from typing import Iterator
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass(frozen=True)
class ConsumeResult:
    """Outcome of verifying a code or magic-link token."""

    ok: bool
    reason: str  # ok | not_found | expired | too_many_attempts | already_used | mismatch
    email: str | None = None
    gate: str | None = None
    project_id: str | None = None
    attempts_remaining: int | None = None


class AuthStore:
    """All auth state for StewardPath, in one SQLite database."""

    def __init__(self, db_path: Path, secret_key: str) -> None:
        self.db_path = Path(db_path)
        self._secret = secret_key.encode("utf-8")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------- connection
    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS owners (
                    owner_id   TEXT PRIMARY KEY,
                    email      TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS owner_projects (
                    owner_id   TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    linked_at  TEXT NOT NULL,
                    PRIMARY KEY (owner_id, project_id)
                );

                CREATE TABLE IF NOT EXISTS auth_challenges (
                    id           TEXT PRIMARY KEY,
                    email        TEXT NOT NULL,
                    code_hash    TEXT NOT NULL,
                    token_hash   TEXT NOT NULL,
                    gate         TEXT NOT NULL,
                    project_id   TEXT,
                    created_at   TEXT NOT NULL,
                    expires_at   TEXT NOT NULL,
                    consumed_at  TEXT,
                    attempts     INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 5,
                    request_ip   TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_challenges_email ON auth_challenges (email);

                CREATE TABLE IF NOT EXISTS sessions (
                    session_hash TEXT PRIMARY KEY,
                    owner_id     TEXT NOT NULL,
                    created_at   TEXT NOT NULL,
                    expires_at   TEXT NOT NULL,
                    last_seen    TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS entitlements (
                    owner_id          TEXT NOT NULL,
                    product           TEXT NOT NULL,
                    status            TEXT NOT NULL,
                    granted_at        TEXT NOT NULL,
                    stripe_session_id TEXT,
                    PRIMARY KEY (owner_id, product)
                );
                """
            )

    # --------------------------------------------------------------- hashing
    def _digest(self, value: str) -> str:
        return hmac.new(self._secret, value.encode("utf-8"), hashlib.sha256).hexdigest()

    # ------------------------------------------------------------ challenges
    def create_challenge(
        self,
        *,
        email: str,
        code: str,
        token: str,
        gate: str,
        project_id: str | None,
        ttl_minutes: int,
        request_ip: str | None = None,
        max_attempts: int = 5,
        now: datetime | None = None,
    ) -> str:
        """Store one sign-in challenge. Returns its id. Code/token kept as hashes."""

        moment = now or _now()
        challenge_id = str(uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_challenges
                    (id, email, code_hash, token_hash, gate, project_id,
                     created_at, expires_at, consumed_at, attempts, max_attempts, request_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?)
                """,
                (
                    challenge_id,
                    email.strip().lower(),
                    self._digest(code),
                    self._digest(token),
                    gate,
                    project_id,
                    _iso(moment),
                    _iso(moment + timedelta(minutes=ttl_minutes)),
                    max_attempts,
                    request_ip,
                ),
            )
        return challenge_id

    def recent_challenge_count(self, email: str, *, within_minutes: int, now: datetime | None = None) -> int:
        """How many challenges this email requested in the window. Drives per-email rate limiting."""

        moment = now or _now()
        since = _iso(moment - timedelta(minutes=within_minutes))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM auth_challenges WHERE email = ? AND created_at >= ?",
                (email.strip().lower(), since),
            ).fetchone()
        return int(row["n"])

    def recent_attempt_total(self, email: str, *, within_minutes: int, now: datetime | None = None) -> int:
        """Total verification attempts against this email's challenges in the window.

        Summing across challenges (not per-row) closes the reset loophole where an
        attacker mints a fresh challenge to get a new attempt budget.
        """

        moment = now or _now()
        since = _iso(moment - timedelta(minutes=within_minutes))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(attempts), 0) AS n FROM auth_challenges WHERE email = ? AND created_at >= ?",
                (email.strip().lower(), since),
            ).fetchone()
        return int(row["n"])

    def verify_code(self, email: str, code: str, *, now: datetime | None = None) -> ConsumeResult:
        """Check a one-time code against the newest open challenge for this email."""

        moment = now or _now()
        normalized = email.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM auth_challenges
                WHERE email = ? AND consumed_at IS NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                (normalized,),
            ).fetchone()
            if row is None:
                return ConsumeResult(False, "not_found", email=normalized)
            if _parse(row["expires_at"]) <= moment:
                return ConsumeResult(False, "expired", email=normalized)
            if row["attempts"] >= row["max_attempts"]:
                return ConsumeResult(False, "too_many_attempts", email=normalized)

            # Count this attempt before checking the code.
            conn.execute("UPDATE auth_challenges SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
            remaining = row["max_attempts"] - (row["attempts"] + 1)

            if not hmac.compare_digest(row["code_hash"], self._digest(code)):
                return ConsumeResult(False, "mismatch", email=normalized, attempts_remaining=remaining)

            # Atomic single-use: only the first writer to flip consumed_at wins.
            cursor = conn.execute(
                "UPDATE auth_challenges SET consumed_at = ? WHERE id = ? AND consumed_at IS NULL",
                (_iso(moment), row["id"]),
            )
            if cursor.rowcount != 1:
                return ConsumeResult(False, "already_used", email=normalized)
            return ConsumeResult(True, "ok", email=normalized, gate=row["gate"], project_id=row["project_id"])

    def consume_token(self, token: str, *, now: datetime | None = None) -> ConsumeResult:
        """Single-use magic-link token consume. Looks up by token hash."""

        moment = now or _now()
        token_hash = self._digest(token)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM auth_challenges WHERE token_hash = ? LIMIT 1",
                (token_hash,),
            ).fetchone()
            if row is None:
                return ConsumeResult(False, "not_found")
            if row["consumed_at"] is not None:
                return ConsumeResult(False, "already_used", email=row["email"])
            if _parse(row["expires_at"]) <= moment:
                return ConsumeResult(False, "expired", email=row["email"])

            cursor = conn.execute(
                "UPDATE auth_challenges SET consumed_at = ? WHERE id = ? AND consumed_at IS NULL",
                (_iso(moment), row["id"]),
            )
            if cursor.rowcount != 1:
                return ConsumeResult(False, "already_used", email=row["email"])
            return ConsumeResult(True, "ok", email=row["email"], gate=row["gate"], project_id=row["project_id"])

    # --------------------------------------------------------------- owners
    def find_or_create_owner(self, email: str, *, now: datetime | None = None) -> str:
        """Return the owner_id for an email, creating the owner on first sign-in."""

        moment = now or _now()
        normalized = email.strip().lower()
        with self._connect() as conn:
            row = conn.execute("SELECT owner_id FROM owners WHERE email = ?", (normalized,)).fetchone()
            if row is not None:
                return row["owner_id"]
            owner_id = str(uuid4())
            conn.execute(
                "INSERT INTO owners (owner_id, email, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (owner_id, normalized, _iso(moment), _iso(moment)),
            )
            return owner_id

    def owner_email(self, owner_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT email FROM owners WHERE owner_id = ?", (owner_id,)).fetchone()
        return row["email"] if row else None

    def link_project(self, owner_id: str, project_id: str, *, now: datetime | None = None) -> None:
        moment = now or _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO owner_projects (owner_id, project_id, linked_at) VALUES (?, ?, ?)
                ON CONFLICT (owner_id, project_id) DO NOTHING
                """,
                (owner_id, project_id, _iso(moment)),
            )

    def projects_for_owner(self, owner_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT project_id FROM owner_projects WHERE owner_id = ? ORDER BY linked_at",
                (owner_id,),
            ).fetchall()
        return [row["project_id"] for row in rows]

    def owner_for_project(self, project_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT owner_id FROM owner_projects WHERE project_id = ? LIMIT 1",
                (project_id,),
            ).fetchone()
        return row["owner_id"] if row else None

    # ---------------------------------------------------------- entitlements
    def grant_entitlement(
        self,
        owner_id: str,
        product: str,
        *,
        stripe_session_id: str = "",
        status: str = "active",
        now: datetime | None = None,
    ) -> None:
        """Record that an owner has paid for a product. Idempotent per (owner, product)."""

        moment = now or _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO entitlements (owner_id, product, status, granted_at, stripe_session_id)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (owner_id, product) DO UPDATE SET
                    status = excluded.status,
                    granted_at = excluded.granted_at,
                    stripe_session_id = excluded.stripe_session_id
                """,
                (owner_id, product, status, _iso(moment), stripe_session_id),
            )

    def entitlements_for_owner(self, owner_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT product, status, granted_at FROM entitlements WHERE owner_id = ? ORDER BY granted_at",
                (owner_id,),
            ).fetchall()
        return [
            {"product": row["product"], "status": row["status"], "grantedAt": row["granted_at"]}
            for row in rows
        ]

    def has_entitlement(self, owner_id: str, product: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM entitlements WHERE owner_id = ? AND product = ? AND status = 'active' LIMIT 1",
                (owner_id, product),
            ).fetchone()
        return row is not None

    # -------------------------------------------------------------- sessions
    def create_session(self, owner_id: str, session_token: str, *, ttl_days: int = 30, now: datetime | None = None) -> None:
        moment = now or _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_hash, owner_id, created_at, expires_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self._digest(session_token),
                    owner_id,
                    _iso(moment),
                    _iso(moment + timedelta(days=ttl_days)),
                    _iso(moment),
                ),
            )

    def read_session(self, session_token: str, *, now: datetime | None = None) -> str | None:
        """Return the owner_id for a live session, or None if missing/expired."""

        moment = now or _now()
        session_hash = self._digest(session_token)
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_hash = ?", (session_hash,)).fetchone()
            if row is None:
                return None
            if _parse(row["expires_at"]) <= moment:
                conn.execute("DELETE FROM sessions WHERE session_hash = ?", (session_hash,))
                return None
            conn.execute(
                "UPDATE sessions SET last_seen = ? WHERE session_hash = ?",
                (_iso(moment), session_hash),
            )
            return row["owner_id"]

    def delete_session(self, session_token: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE session_hash = ?", (self._digest(session_token),))
