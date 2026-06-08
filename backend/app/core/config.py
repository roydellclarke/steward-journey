"""Runtime configuration for the StewardPath backend."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


# Placeholder secret. Usable for local http dev only; refused in production
# posture (see Settings.from_env). Never sign real sessions/links with this.
DEV_SECRET_KEY = "dev-only-insecure-secret-change-me"


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_env_file(path: Path | None = None) -> None:
    """Load simple KEY=value pairs from .env without overriding the process."""

    env_path = path or Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    data_root: Path
    use_llm: bool
    kimi_model: str
    deepseek_model: str
    kimi_temperature: float
    deepseek_temperature: float
    request_timeout_seconds: int
    # Passwordless email auth.
    secret_key: str
    frontend_origin: str
    auth_db_path: Path
    otp_ttl_minutes: int
    postmark_token: str
    postmark_from: str
    resend_api_key: str
    resend_from: str
    cookie_secure: bool
    admin_token: str
    log_auth_emails: bool
    # Stripe payments.
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_report: str
    stripe_price_concierge: str
    stripe_price_advisor: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        data_root = Path(os.getenv("STEWARDPATH_DATA_ROOT", "data/stewardpath")).resolve()
        auth_db_default = data_root / "auth" / "auth.db"
        secret_key = os.getenv("STEWARDPATH_SECRET_KEY", DEV_SECRET_KEY)
        cookie_secure = _bool_env("STEWARDPATH_COOKIE_SECURE", True)
        # Production posture (secure cookies) must not run on the placeholder
        # secret: it signs every session and magic link. Fail loudly at startup.
        if cookie_secure and (not secret_key or secret_key == DEV_SECRET_KEY):
            raise RuntimeError(
                "STEWARDPATH_SECRET_KEY must be set to a strong, unique value when "
                "STEWARDPATH_COOKIE_SECURE is true. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return cls(
            data_root=data_root,
            use_llm=_bool_env("STEWARDPATH_USE_LLM", False),
            kimi_model=os.getenv("STEWARDPATH_KIMI_MODEL", "moonshot/kimi-k2.5"),
            deepseek_model=os.getenv("STEWARDPATH_DEEPSEEK_MODEL", "deepseek/deepseek-reasoner"),
            kimi_temperature=float(os.getenv("STEWARDPATH_KIMI_TEMPERATURE", "1")),
            deepseek_temperature=float(os.getenv("STEWARDPATH_DEEPSEEK_TEMPERATURE", "0.15")),
            request_timeout_seconds=int(os.getenv("STEWARDPATH_LLM_TIMEOUT_SECONDS", "120")),
            secret_key=secret_key,
            frontend_origin=os.getenv("STEWARDPATH_FRONTEND_ORIGIN", "http://localhost:3000"),
            auth_db_path=Path(os.getenv("STEWARDPATH_AUTH_DB_PATH", str(auth_db_default))).resolve(),
            otp_ttl_minutes=int(os.getenv("STEWARDPATH_OTP_TTL_MINUTES", "10")),
            postmark_token=os.getenv("STEWARDPATH_POSTMARK_TOKEN", ""),
            postmark_from=os.getenv("STEWARDPATH_POSTMARK_FROM", ""),
            resend_api_key=os.getenv("STEWARDPATH_RESEND_API_KEY", ""),
            resend_from=os.getenv("STEWARDPATH_RESEND_FROM", ""),
            cookie_secure=cookie_secure,
            admin_token=os.getenv("STEWARDPATH_ADMIN_TOKEN", ""),
            log_auth_emails=_bool_env("STEWARDPATH_LOG_AUTH_EMAILS", False),
            stripe_secret_key=os.getenv("STEWARDPATH_STRIPE_SECRET_KEY", ""),
            stripe_webhook_secret=os.getenv("STEWARDPATH_STRIPE_WEBHOOK_SECRET", ""),
            stripe_price_report=os.getenv("STEWARDPATH_STRIPE_PRICE_REPORT", ""),
            stripe_price_concierge=os.getenv("STEWARDPATH_STRIPE_PRICE_CONCIERGE", ""),
            stripe_price_advisor=os.getenv("STEWARDPATH_STRIPE_PRICE_ADVISOR", ""),
        )
