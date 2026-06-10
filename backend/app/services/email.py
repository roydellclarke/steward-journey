"""Transactional email for passwordless sign-in.

Delivery goes through Postmark in production. Tests and local runs without a
Postmark token use ``RecordingEmailSender``, which keeps messages in memory so
no real mail is ever sent during a test. Nothing here logs the code or link.

Copy follows the StewardPath writing laws: warm, plain, no em-dashes. The note
frames the account as a security feature, not a marketing ask.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
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
    if gate == "checkout":
        return "Here is your secure code to sign in and continue to payment."
    return "Here is your secure code to pick your StewardPath answers back up."


def build_auth_email(*, to: str, code: str, link: str, gate: str) -> AuthEmail:
    """Compose the sign-in email carrying both the code and the link."""

    intro = _gate_intro(gate)
    # Escape everything interpolated into HTML. Today these are server-generated
    # (numeric code, signed link), but escaping keeps the template safe if a
    # user-influenced value is ever added.
    code_html = escape(code)
    link_html = escape(link, quote=True)
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
        f'<p style="font-size:28px;letter-spacing:4px;font-weight:600;margin:24px 0">{code_html}</p>'
        "<p>Enter it on the StewardPath page you came from. The code works once and "
        "expires in a few minutes.</p>"
        f'<p>Prefer a link? <a href="{link_html}">Open StewardPath</a>, then click the '
        "button to confirm it is you.</p>"
        "<p>Your answers stay private to you. If you did not ask to sign in, you can "
        "ignore this email and nothing changes.</p>"
    )
    subject = "Your StewardPath sign-in code"
    return AuthEmail(to=to, subject=subject, text_body=text_body, html_body=html_body)


def build_purchase_email(*, to: str, product_name: str, amount_display: str) -> AuthEmail:
    """Compose the receipt-style confirmation after a successful payment.

    AuthEmail is just an email envelope (to, subject, two bodies); reusing it
    keeps every sender working without new plumbing. Copy follows the writing
    laws: warm, plain, no em-dashes.
    """

    product_html = escape(product_name)
    amount_html = escape(amount_display)
    text_body = (
        f"Thank you. Your payment for {product_name} ({amount_display}) is confirmed.\n\n"
        "We have your order. A person will be in touch with the next step, and your "
        "answers stay private to you the whole way.\n\n"
        "If you have a question, just reply to this email.\n"
    )
    html_body = (
        f"<p>Thank you. Your payment for <strong>{product_html}</strong> "
        f"({amount_html}) is confirmed.</p>"
        "<p>We have your order. A person will be in touch with the next step, and your "
        "answers stay private to you the whole way.</p>"
        "<p>If you have a question, just reply to this email.</p>"
    )
    return AuthEmail(
        to=to,
        subject=f"Your StewardPath order is confirmed: {product_name}",
        text_body=text_body,
        html_body=html_body,
    )


class EmailSender(Protocol):
    def send(self, message: AuthEmail) -> None: ...


@dataclass
class RecordingEmailSender:
    """In-memory sender for tests and local dev. Never touches the network."""

    sent: list[AuthEmail] = field(default_factory=list)

    def send(self, message: AuthEmail) -> None:
        self.sent.append(message)


@dataclass
class ConsoleEmailSender:
    """Dev-only sender: prints the message to stdout instead of sending it.

    Lets you complete a real sign-in locally without wiring up Postmark. Never
    enabled by default, and the production-posture secret guard keeps the dev
    cookie setting (and thus this) out of a secure deployment.
    """

    def send(self, message: AuthEmail) -> None:
        print(f"\n[dev-auth-email] to={message.to}\n{message.text_body}\n", flush=True)


@dataclass
class ResendEmailSender:
    """Sends via the Resend transactional API.

    Resend does not rewrite links unless click tracking is enabled for the
    domain, so leave that off in the dashboard to keep single-use magic links
    from being pre-fetched by a scanner.
    """

    api_key: str
    sender: str
    timeout_seconds: float = 10.0
    api_url: str = "https://api.resend.com/emails"

    def send(self, message: AuthEmail) -> None:
        import httpx  # imported here so offline test envs without httpx still load this module

        response = httpx.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": self.sender,
                "to": [message.to],
                "subject": message.subject,
                "text": message.text_body,
                "html": message.html_body,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()


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


def build_email_sender(
    *,
    resend_api_key: str = "",
    resend_from: str = "",
    postmark_token: str = "",
    postmark_from: str = "",
    log_to_console: bool = False,
) -> EmailSender:
    """Pick a transactional sender from config.

    Priority: Resend, then Postmark, then (dev) console, then an in-memory fake.
    ``log_to_console`` prints the email (code + link) so you can sign in locally
    without a provider. Off by default. With no provider and no console flag,
    nothing is sent (tests, offline).
    """

    if resend_api_key and resend_from:
        return ResendEmailSender(api_key=resend_api_key, sender=resend_from)
    if postmark_token and postmark_from:
        return PostmarkEmailSender(token=postmark_token, sender=postmark_from)
    if log_to_console:
        return ConsoleEmailSender()
    return RecordingEmailSender()
