"""Guarded Meta Pages publisher.

This module is intentionally conservative. It does not accept Facebook
passwords, does not scrape the UI, and defaults to dry-run. Real posting must
use an OAuth/Page access token referenced through the connector vault.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib import parse, request

from harness.connector_vault import Connector


@dataclass(frozen=True)
class PublishResult:
    status: str
    detail: str
    provider_response: dict | None = None


class MetaPagesPublisher:
    def __init__(self, connector: Connector, *, dry_run: bool = True) -> None:
        if connector.provider != "meta_pages":
            raise ValueError("MetaPagesPublisher requires a meta_pages connector.")
        self.connector = connector
        self.dry_run = dry_run

    def publish(self, payload: dict) -> str:
        post_text = str(payload.get("post_text") or payload.get("message") or "").strip()
        approved = bool(payload.get("approved", False))
        if not post_text:
            raise ValueError("Meta publish payload requires `post_text` or `message`.")
        if not approved:
            raise PermissionError("Meta publish jobs require explicit approval.")

        page_id = str(self.connector.config.get("page_id") or "").strip()
        token_env_var = self.connector.token_env_var
        token = os.getenv(token_env_var, "")
        if not page_id:
            raise ValueError("Meta connector is missing page_id.")
        if not token:
            raise RuntimeError(f"Missing OAuth token environment variable: {token_env_var}")

        if self.dry_run:
            result = PublishResult(
                status="DRY_RUN",
                detail=f"Would publish {len(post_text)} characters to Meta Page {page_id}.",
            )
            return json.dumps(result.__dict__, indent=2)

        data = parse.urlencode({"message": post_text, "access_token": token}).encode("utf-8")
        req = request.Request(
            f"https://graph.facebook.com/v20.0/{page_id}/feed",
            data=data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with request.urlopen(req, timeout=30) as response:  # nosec B310 - explicit user-configured connector.
            body = json.loads(response.read().decode("utf-8"))
        result = PublishResult(status="PUBLISHED", detail="Meta Page post published.", provider_response=body)
        return json.dumps(result.__dict__, indent=2)

