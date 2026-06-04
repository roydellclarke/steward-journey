"""Transactional email for passwordless sign-in.

Delivery goes through Postmark in production. Tests and local runs without a
Postmark token use ``RecordingEmailSender``, which keeps messages in memory so
no real mail is ever sent during a test. Nothing here logs the code or link.

Copy follows the StewardPath writing laws: warm, plain, no em-dashes. The note
frames the account as a security feature, not a marketing ask.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AuthEmail:
    to: str
    subject: str
    text_body: str
    html_body: str


def _gate_intro(gate: str) -> str:
    if gate == "report":
        return "Here is your secure code to open your readiness report."
    return "Here is your secure code to pick your StewardPath answers back up."


def build_auth_email(*, to: str, code: str, link: str, gate: str) -> AuthEmail:
    """Compose the sign-in email carrying both the code and the link."""

    intro = _gate_intro(gate)
    text_body = (
        f"{intro}\n\n"
        f"Your code: {code}\n\n"
        "Enter it on the StewardPath page you came from. The code works once and "
        "expires in a few minutes.\n\n"
        "Prefer a link? Open this, then click the button to confirm it is you:\n"
        f"{link}\n\n"
        "Your answers stay private to you. If you did not ask to sign in, you can "
        "ignore this email and nothing changes.\n"
    )
    html_body = (
        f"<p>{intro}</p>"
        f'<p style="font-size:28px;letter-spacing:4px;font-weight:600;margin:24px 0">{code}</p>'
        "<p>Enter it on the StewardPath page you came from. The code works once and "
        "expires in a few minutes.</p>"
        f'<p>Prefer a link? <a href="{link}">Open StewardPath</a>, then click the '
        "button to confirm it is you.</p>"
        "<p>Your answers stay private to you. If you did not ask to sign in, you can "
        "ignore this email and nothing changes.</p>"
    )
    subject = "Your StewardPath sign-in code"
    return AuthEmail(to=to, subject=subject, text_body=text_body, html_body=html_body)


class EmailSender(Protocol):
    def send(self, message: AuthEmail) -> None: ...


@dataclass
class RecordingEmailSender:
    """In-memory sender for tests and local dev. Never touches the network."""

    sent: list[AuthEmail] = field(default_factory=list)

    def send(self, message: AuthEmail) -> None:
        self.sent.append(message)


@dataclass
class PostmarkEmailSender:
    """Sends via the Postmark transactional API.

    Click tracking is left off so single-use magic links are never pre-fetched
    by a scanner. Postmark defaults tracking to off; we do not enable it.
    """

    token: str
    sender: str
    timeout_seconds: float = 10.0
    api_url: str = "https://api.postmarkapp.com/email"

    def send(self, message: AuthEmail) -> None:
        import httpx  # imported here so offline test envs without httpx still load this module

        response = httpx.post(
            self.api_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.token,
            },
            json={
                "From": self.sender,
                "To": message.to,
                "Subject": message.subject,
                "TextBody": message.text_body,
                "HtmlBody": message.html_body,
                "MessageStream": "outbound",
                "TrackOpens": False,
                "TrackLinks": "None",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()


def build_email_sender(*, postmark_token: str, postmark_from: str) -> EmailSender:
    """Pick a sender from config: Postmark when wired up, recording fake otherwise."""

    if postmark_token and postmark_from:
        return PostmarkEmailSender(token=postmark_token, sender=postmark_from)
    return RecordingEmailSender()
