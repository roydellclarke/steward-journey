"""Tests for Stripe payments: catalog pricing, order store, and the routes.

Stripe itself is never called: a fake payments object stands in for the SDK, so
these tests are hermetic and need no API key. API tests skip without FastAPI,
matching the rest of the suite.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest


try:
    from fastapi.testclient import TestClient  # noqa: F401
    import slowapi  # noqa: F401
    import itsdangerous  # noqa: F401
    HAS_STACK = True
except Exception:  # pragma: no cover
    HAS_STACK = False


from app.services.payments import CATALOG
from app.storage.projects import ProjectStore


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


@unittest.skipUnless(HAS_STACK, "FastAPI/slowapi/itsdangerous not installed in this environment")
class CheckoutApiTestCase(unittest.TestCase):
    def setUp(self):
        self.main = _reload_app()
        self.main.payments = _FakePayments()
        self.client = TestClient(self.main.app)

    def test_products_lists_three(self):
        body = self.client.get("/products").json()
        self.assertEqual(len(body["products"]), 3)

    def test_checkout_creates_session_and_records_pending_order(self):
        response = self.client.post("/checkout", json={"product": "report"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["url"], "https://stripe.test/checkout/cs_test_123")
        orders = self.main.store.list_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["status"], "pending")
        self.assertEqual(orders[0]["product"], "report")

    def test_checkout_rejects_unknown_product(self):
        response = self.client.post("/checkout", json={"product": "nope"})
        self.assertEqual(response.status_code, 422)  # Literal validation fails

    def test_success_finalize_marks_paid_and_emails_once(self):
        self.client.post("/checkout", json={"product": "report"})
        status = self.client.get("/checkout/session/cs_test_123").json()
        self.assertTrue(status["paid"])
        self.assertEqual(self.main.store.get_order_by_session("cs_test_123")["status"], "paid")
        # RecordingEmailSender captured exactly one confirmation.
        self.assertEqual(len(self.main.email_sender.sent), 1)
        self.assertEqual(self.main.email_sender.sent[0].to, "buyer@example.com")
        # A second visit to the success page must not send another receipt.
        self.client.get("/checkout/session/cs_test_123")
        self.assertEqual(len(self.main.email_sender.sent), 1)

    def test_checkout_503_when_payments_unconfigured(self):
        self.main.payments.configured = False
        response = self.client.post("/checkout", json={"product": "report"})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
