"""Stripe payments for the three StewardPath offerings.

We use Stripe Checkout (Stripe-hosted pages), so no card data ever reaches our
servers and PCI scope stays minimal. The browser asks the backend for a
Checkout Session, redirects to Stripe to pay, then returns to a success page.
Payment is confirmed server-side two ways: the success page calls
``finalize_session`` (a direct retrieve from Stripe), and Stripe's webhook calls
the same path. Both are idempotent, so an order is finalized exactly once.

The catalog below is the single source of truth for what each product costs.
The frontend pricing copy must match these amounts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json


def _as_dict(stripe_object) -> dict:
    """Convert a Stripe SDK object to a plain, fully-nested dict.

    Stripe's objects do not expose dict's ``.get``/iteration the way plain
    dicts do (attribute access routes through ``__getattr__``), so we serialize
    to JSON and back. That gives callers ordinary dicts with normal ``.get``.
    """

    return json.loads(str(stripe_object))


@dataclass(frozen=True)
class Product:
    key: str
    name: str
    description: str
    amount_cents: int
    # "payment" for a one-time charge, "subscription" for recurring billing.
    mode: str
    # For subscriptions only: the billing interval Stripe should use.
    interval: str | None = None

    @property
    def amount_display(self) -> str:
        dollars = self.amount_cents / 100
        whole = f"${dollars:,.0f}" if dollars == int(dollars) else f"${dollars:,.2f}"
        return f"{whole}/mo" if self.mode == "subscription" else whole


# Keys are stable identifiers the frontend sends; amounts mirror the pricing
# band in frontend/app/page.jsx. Change a price here and there together.
CATALOG: dict[str, Product] = {
    "report": Product(
        key="report",
        name="Owner Readiness Program",
        description="A guided program you walk through to a confident handoff on your terms, with the reasoning behind every score.",
        amount_cents=24900,
        mode="payment",
    ),
    "concierge": Product(
        key="concierge",
        name="Concierge package",
        description="A guided intake and a private review with a real person.",
        amount_cents=150000,
        mode="payment",
    ),
    "advisor": Product(
        key="advisor",
        name="Advisor pilot",
        description="For advisors guiding up to ten owner clients. Billed monthly.",
        amount_cents=19900,
        mode="subscription",
        interval="month",
    ),
}


class PaymentsError(RuntimeError):
    """Raised when Stripe is not configured or a Stripe call fails."""


@dataclass
class StripePayments:
    """Thin wrapper over the Stripe SDK, configured from settings.

    ``stripe`` is imported lazily inside methods so the module still loads in
    offline test environments that do not install the SDK (mirrors how the
    email senders import httpx).
    """

    secret_key: str
    webhook_secret: str = ""
    # Optional pre-created Stripe Price IDs, one per product key. When a key is
    # present we use it; otherwise we price the line item inline from CATALOG.
    price_ids: dict[str, str] | None = None

    @property
    def configured(self) -> bool:
        return bool(self.secret_key)

    def _client(self):
        if not self.secret_key:
            raise PaymentsError(
                "Stripe is not configured. Set STEWARDPATH_STRIPE_SECRET_KEY in the backend .env."
            )
        import stripe  # lazy: keeps offline test envs importable without the SDK

        stripe.api_key = self.secret_key
        return stripe

    def _line_item(self, product: Product) -> dict:
        configured_price = (self.price_ids or {}).get(product.key)
        if configured_price:
            return {"price": configured_price, "quantity": 1}
        price_data: dict = {
            "currency": "usd",
            "product_data": {"name": product.name, "description": product.description},
            "unit_amount": product.amount_cents,
        }
        if product.mode == "subscription":
            price_data["recurring"] = {"interval": product.interval or "month"}
        return {"price_data": price_data, "quantity": 1}

    def create_checkout_session(
        self,
        product: Product,
        *,
        success_url: str,
        cancel_url: str,
        client_reference_id: str | None = None,
    ):
        """Create a Stripe Checkout Session and return the Stripe session object."""

        stripe = self._client()
        params: dict = {
            "mode": product.mode,
            "line_items": [self._line_item(product)],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {"product": product.key},
        }
        if client_reference_id:
            params["client_reference_id"] = client_reference_id
        # Stripe collects the buyer's email on the hosted page; we read it back
        # from the session to send our own confirmation. customer_creation is
        # only valid in payment mode (subscriptions always create a customer).
        if product.mode == "payment":
            params["customer_creation"] = "always"
        try:
            return _as_dict(stripe.checkout.Session.create(**params))
        except Exception as exc:  # noqa: BLE001 - surface any Stripe failure as ours
            raise PaymentsError(f"Could not start checkout: {exc}") from exc

    def retrieve_session(self, session_id: str):
        """Fetch a Checkout Session from Stripe (the trustworthy paid-state)."""

        stripe = self._client()
        try:
            return _as_dict(stripe.checkout.Session.retrieve(session_id))
        except Exception as exc:  # noqa: BLE001
            raise PaymentsError(f"Could not load checkout session: {exc}") from exc

    def parse_webhook_event(self, payload: bytes, signature: str):
        """Verify a webhook signature and return the parsed Stripe event."""

        if not self.webhook_secret:
            raise PaymentsError(
                "Webhook secret is not set. Set STEWARDPATH_STRIPE_WEBHOOK_SECRET to verify events."
            )
        stripe = self._client()
        try:
            return _as_dict(stripe.Webhook.construct_event(payload, signature, self.webhook_secret))
        except Exception as exc:  # noqa: BLE001 - includes signature failures
            raise PaymentsError(f"Invalid webhook signature: {exc}") from exc
