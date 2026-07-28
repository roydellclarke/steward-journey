"""Tests for Stripe payments: catalog pricing, order store, and the routes.

Stripe itself is never called: a fake payments object stands in for the SDK, so
these tests are hermetic and need no API key. API tests skip without FastAPI,
matching the rest of the suite.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import importlib
import json
import os
import re
import tempfile
import unittest


_CODE_RE = re.compile(r"Your code: (\d{6})")


def _sign_in(client, main, email="buyer@example.com"):
    """Run the real passwordless flow so the TestClient holds a session cookie.

    Returns the owner_id for entitlement assertions. The RecordingEmailSender
    captures the code in the email body.
    """

    client.post("/auth/request", json={"email": email, "gate": "save"})
    code = _CODE_RE.search(main.email_sender.sent[-1].text_body).group(1)
    client.post("/auth/verify", json={"email": email, "code": code})
    return main.auth_store.find_or_create_owner(email)


try:
    from fastapi.testclient import TestClient  # noqa: F401
    import slowapi  # noqa: F401
    import itsdangerous  # noqa: F401
    HAS_STACK = True
except Exception:  # pragma: no cover
    HAS_STACK = False


from pathlib import Path

from app.services.payments import CATALOG
from app.storage.auth_db import AuthStore
from app.storage.projects import ProjectStore


class EntitlementLifecycleTestCase(unittest.TestCase):
    def setUp(self):
        self.auth = AuthStore(Path(tempfile.mkdtemp()) / "auth.db", "secret")

    def test_subscription_revoked_on_cancel(self):
        owner = self.auth.find_or_create_owner("advisor@example.com")
        self.auth.grant_entitlement(owner, "advisor", stripe_subscription_id="sub_123")
        self.assertTrue(self.auth.has_entitlement(owner, "advisor"))
        self.assertEqual(self.auth.set_status_by_subscription("sub_123", "canceled"), 1)
        self.assertFalse(self.auth.has_entitlement(owner, "advisor"))

    def test_failed_payment_suspends_then_recovers(self):
        owner = self.auth.find_or_create_owner("advisor2@example.com")
        self.auth.grant_entitlement(owner, "advisor", stripe_subscription_id="sub_9")
        self.auth.set_status_by_subscription("sub_9", "past_due")
        self.assertFalse(self.auth.has_entitlement(owner, "advisor"))
        self.auth.set_status_by_subscription("sub_9", "active")
        self.assertTrue(self.auth.has_entitlement(owner, "advisor"))


class CatalogTestCase(unittest.TestCase):
    def test_three_products_with_expected_pricing(self):
        self.assertEqual(set(CATALOG), {"report", "concierge", "advisor"})
        self.assertEqual(CATALOG["report"].amount_cents, 24900)
        self.assertEqual(CATALOG["report"].amount_display, "$249")
        self.assertEqual(CATALOG["concierge"].amount_display, "$1,500")
        self.assertEqual(CATALOG["advisor"].mode, "subscription")
        self.assertEqual(CATALOG["advisor"].amount_display, "$199/mo")


class OrderStoreTestCase(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        self.store = ProjectStore(Path(tempfile.mkdtemp()))

    def test_mark_paid_is_idempotent(self):
        self.store.append_order(
            {"product": "report", "amountCents": 24900, "mode": "payment", "stripeSessionId": "cs_test_1"}
        )
        order, newly = self.store.mark_order_paid("cs_test_1", email="a@b.com")
        self.assertIsNotNone(order)
        self.assertTrue(newly)
        self.assertEqual(self.store.get_order_by_session("cs_test_1")["status"], "paid")
        # A second confirmation must not re-fire (so the receipt sends once).
        _, newly_again = self.store.mark_order_paid("cs_test_1", email="a@b.com")
        self.assertFalse(newly_again)

    def test_mark_paid_unknown_session(self):
        order, newly = self.store.mark_order_paid("nope")
        self.assertIsNone(order)
        self.assertFalse(newly)


def _reload_app():
    root = tempfile.mkdtemp()
    os.environ["STEWARDPATH_DATA_ROOT"] = root
    os.environ["STEWARDPATH_AUTH_DB_PATH"] = os.path.join(root, "auth", "auth.db")
    # Never call real LLM providers from tests, even if backend/.env enables them.
    os.environ["STEWARDPATH_USE_LLM"] = "false"
    os.environ["STEWARDPATH_SECRET_KEY"] = "test-secret-key"
    os.environ["STEWARDPATH_COOKIE_SECURE"] = "false"
    os.environ["STEWARDPATH_FRONTEND_ORIGIN"] = "http://localhost:3000"
    for key in (
        "STEWARDPATH_RESEND_API_KEY",
        "STEWARDPATH_RESEND_FROM",
        "STEWARDPATH_POSTMARK_TOKEN",
        "STEWARDPATH_POSTMARK_FROM",
        "STEWARDPATH_STRIPE_SECRET_KEY",
        "STEWARDPATH_STRIPE_WEBHOOK_SECRET",
    ):
        os.environ[key] = ""
    os.environ["STEWARDPATH_LOG_AUTH_EMAILS"] = "false"
    import app.main as main_module

    importlib.reload(main_module)
    return main_module


class _FakeSession(dict):
    """A dict that also exposes Stripe-style .get for nested access."""


class _FakePayments:
    """Stand-in for StripePayments. Never touches the network."""

    configured = True

    def create_checkout_session(self, product, *, success_url, cancel_url, client_reference_id=None):
        return _FakeSession(id="cs_test_123", url="https://stripe.test/checkout/cs_test_123")

    def retrieve_session(self, session_id):
        return _FakeSession(
            id=session_id,
            payment_status="paid",
            status="complete",
            customer_details={"email": "buyer@example.com"},
            metadata={"product": "report"},
        )

    def parse_webhook_event(self, payload, signature):
        import json
        return json.loads(payload)


@unittest.skipUnless(HAS_STACK, "FastAPI/slowapi/itsdangerous not installed in this environment")
class CheckoutApiTestCase(unittest.TestCase):
    def setUp(self):
        self.main = _reload_app()
        self.main.payments = _FakePayments()
        self.client = TestClient(self.main.app)

    def test_products_lists_three(self):
        body = self.client.get("/products").json()
        self.assertEqual(len(body["products"]), 3)

    def test_checkout_requires_sign_in(self):
        response = self.client.post("/checkout", json={"product": "report"})
        self.assertEqual(response.status_code, 401)

    def test_checkout_creates_session_and_records_pending_order(self):
        owner_id = _sign_in(self.client, self.main)
        response = self.client.post("/checkout", json={"product": "report"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["url"], "https://stripe.test/checkout/cs_test_123")
        orders = self.main.store.list_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["status"], "pending")
        self.assertEqual(orders[0]["product"], "report")
        self.assertEqual(orders[0]["ownerId"], owner_id)

    def test_checkout_rejects_unknown_product(self):
        response = self.client.post("/checkout", json={"product": "nope"})
        self.assertEqual(response.status_code, 422)  # Literal validation fails

    def test_success_finalize_marks_paid_grants_entitlement_emails_once(self):
        owner_id = _sign_in(self.client, self.main)
        self.client.post("/checkout", json={"product": "report"})
        before = len(self.main.email_sender.sent)

        status = self.client.get("/checkout/session/cs_test_123").json()
        self.assertTrue(status["paid"])
        self.assertEqual(self.main.store.get_order_by_session("cs_test_123")["status"], "paid")
        # Entitlement is now recorded against the owner's account.
        self.assertTrue(self.main.auth_store.has_entitlement(owner_id, "report"))
        # Exactly one purchase confirmation went out (beyond the sign-in code).
        self.assertEqual(len(self.main.email_sender.sent), before + 1)
        self.assertIn("order is confirmed", self.main.email_sender.sent[-1].subject)
        # A second visit to the success page must not send another receipt.
        self.client.get("/checkout/session/cs_test_123")
        self.assertEqual(len(self.main.email_sender.sent), before + 1)

    def test_claim_finalization_is_exactly_once(self):
        # The atomic claim is what makes finalize safe when the webhook and the
        # success page race: the first caller wins, everyone after gets False,
        # so the receipt email and audit event fire exactly once.
        store = self.main.auth_store
        self.assertTrue(store.claim_finalization("cs_race"))
        self.assertFalse(store.claim_finalization("cs_race"))
        self.assertTrue(store.claim_finalization("cs_other"))
        self.assertFalse(store.claim_finalization(""))

    def test_me_exposes_entitlements_after_purchase(self):
        _sign_in(self.client, self.main)
        self.client.post("/checkout", json={"product": "report"})
        self.client.get("/checkout/session/cs_test_123")
        me = self.client.get("/auth/me").json()
        products = [e["product"] for e in me.get("entitlements", [])]
        self.assertIn("report", products)

    def test_checkout_503_when_payments_unconfigured(self):
        _sign_in(self.client, self.main)
        self.main.payments.configured = False
        response = self.client.post("/checkout", json={"product": "report"})
        self.assertEqual(response.status_code, 503)

    def test_webhook_cancellation_revokes_entitlement(self):
        owner = self.main.auth_store.find_or_create_owner("adv@example.com")
        self.main.auth_store.grant_entitlement(owner, "advisor", stripe_subscription_id="sub_abc")
        self.assertTrue(self.main.auth_store.has_entitlement(owner, "advisor"))
        body = json.dumps({"type": "customer.subscription.deleted", "data": {"object": {"id": "sub_abc"}}})
        resp = self.client.post("/stripe/webhook", content=body, headers={"stripe-signature": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.main.auth_store.has_entitlement(owner, "advisor"))


if __name__ == "__main__":
    unittest.main()
