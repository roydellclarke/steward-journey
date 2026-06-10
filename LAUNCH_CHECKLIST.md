# StewardPath launch checklist

What must be true before letting real users in. Grouped by who does it.

## Code and product (done in-repo)

- [x] Per-owner auth with access checks on every data route
- [x] Default-private data, export and delete, append-only audit log
- [x] Payments via Stripe Checkout (no card data on our servers)
- [x] Purchases tied to the owner's account; per-product routing on return
- [x] Subscription lifecycle: access revoked on cancel and failed renewal, restored on recovery
- [x] Sign-in code failures surfaced to the owner (no silent dead end)
- [x] Privacy Policy and Terms pages, linked in the footer, with a visible "preparation, not advice" disclaimer
- [x] Per-page titles, one h1 per page, favicon
- [x] Unit suite (backend) and Puppeteer UI suite green

## You own (external, before launch)

- [ ] **Persistent storage.** Point `STEWARDPATH_DATA_ROOT` and the auth DB at a durable, backed-up volume. Not `/tmp`.
- [ ] **Domain + HTTPS/TLS.** Register the domain, serve over HTTPS, terminate TLS at your proxy.
- [ ] **Strong secret + secure cookies.** Set a unique `STEWARDPATH_SECRET_KEY` and `STEWARDPATH_COOKIE_SECURE=true`.
- [ ] **Email delivery.** Verify a domain in Resend and set `STEWARDPATH_RESEND_FROM` on it. Without this, owners cannot sign in.
- [ ] **Live Stripe.** Swap to `sk_live_` keys, register the webhook, set `STEWARDPATH_STRIPE_WEBHOOK_SECRET`. Point the webhook at `https://api.yourdomain.com/stripe/webhook` and subscribe to `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.updated`, and `invoice.payment_failed`.
- [ ] **Rotate the test Stripe key** that was shared in chat.
- [ ] **Production config.** Set `STEWARDPATH_FRONTEND_ORIGIN`, `NEXT_PUBLIC_API_BASE_URL`, and `NEXT_PUBLIC_SITE_URL` to the real domains. Remove the dev `frontend/.env.local`.
- [ ] **Production build.** Deploy the frontend with `next build` + `next start`, not `next dev`.
- [ ] **Admin token.** Set a strong `STEWARDPATH_ADMIN_TOKEN`.
- [ ] **Legal review.** Have counsel review the Privacy and Terms pages and fill the `[BRACKETED]` placeholders (company name, jurisdiction, contact, refund window, effective date).

## Nice soon after

- [ ] Error monitoring and uptime alerts
- [ ] Backup + restore drill for the file-backed store
- [ ] Stripe customer portal for self-serve subscription management
- [ ] Accessibility pass and real device testing
