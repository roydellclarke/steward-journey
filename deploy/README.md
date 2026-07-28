# Deploying StewardPath

One server hosts both sites. DNS already points `stewardpathfinder.com` and
`api.stewardpathfinder.com` at it. Caddy terminates TLS and routes by hostname:
the site to the frontend container, the API subdomain to the backend container.

## Before you start

- A Linux server you control, with Docker and the Compose plugin installed.
- Ports 80 and 443 open to the internet (Caddy needs them for Let's Encrypt).
- The DNS A records live (done: both resolve to your server).
- A GitHub token with `read:packages` to pull the private images.

## Files to place in one directory on the server

1. `docker-compose.prod.yml`  (from this `deploy/` folder)
2. `Caddyfile`  (from this `deploy/` folder)
3. `.env.production`  (you create it, see below; never commit it)

## Every value `.env.production` needs

Copy `/.env.production.example` to `.env.production` and fill these in.

### Required to boot and sign in
| Variable | What it is | Where to get it |
|---|---|---|
| `STEWARDPATH_SECRET_KEY` | Signs sessions and magic links. Keep stable. | Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `STEWARDPATH_COOKIE_SECURE` | Must be `true` in production. | Set to `true` |
| `STEWARDPATH_FRONTEND_ORIGIN` | Exact site origin, for CORS + link base. | `https://stewardpathfinder.com` |
| `STEWARDPATH_DATA_ROOT` | Where owner data + auth.db live. | `/data/stewardpath` (backed by the volume) |
| `STEWARDPATH_AUTH_DB_PATH` | Auth database path. | `/data/stewardpath/auth/auth.db` |
| `STEWARDPATH_RESEND_API_KEY` | Sends sign-in codes. | resend.com dashboard |
| `STEWARDPATH_RESEND_FROM` | From address on a verified domain. | `StewardPath <no-reply@stewardpathfinder.com>` |

Verify `stewardpathfinder.com` in Resend (resend.com/domains) and add the SPF/DKIM
DNS records it gives you, or emails will not reach owners.

### Required to take payments
| Variable | What it is | Where to get it |
|---|---|---|
| `STEWARDPATH_STRIPE_SECRET_KEY` | Live secret key. | Stripe dashboard, starts with `sk_live_` |
| `STEWARDPATH_STRIPE_WEBHOOK_SECRET` | Confirms payments reliably. | Stripe webhook (see step 4), starts with `whsec_` |
| `STEWARDPATH_STRIPE_PRICE_*` | Optional pre-made Price IDs. | Blank is fine; the app prices inline. |

### Optional
| Variable | What it is |
|---|---|
| `STEWARDPATH_ADMIN_TOKEN` | Strong random token to reach `/orders` and `/leads`. Unset = closed. |
| `STEWARDPATH_USE_LLM` + `DEEPSEEK_API_KEY` + `MOONSHOT_API_KEY` | Turn on wording augmentation. App works fully without it. |
| `STEWARDPATH_MAGIC_LINK_TTL_MINUTES` | Save-and-resume link life. Default `20160` (14 days). |

## Bring it up (in order)

```bash
# 1. Authenticate to pull the private images
docker login ghcr.io -u roydellclarke        # paste the read:packages token

# 2. Start everything (from the directory with the three files)
docker compose -f docker-compose.prod.yml up -d

# 3. Watch the logs until Caddy reports certificates obtained
docker compose -f docker-compose.prod.yml logs -f caddy
```

## Step 4: register the Stripe webhook

In the Stripe dashboard, add a webhook endpoint:

```
https://api.stewardpathfinder.com/stripe/webhook
```

Copy its signing secret into `STEWARDPATH_STRIPE_WEBHOOK_SECRET`, then restart the
backend so it picks it up:

```bash
docker compose -f docker-compose.prod.yml up -d backend
```

## Verify

```bash
curl https://api.stewardpathfinder.com/health          # -> {"ok":true,...}
```

Then in a browser:
- `https://stewardpathfinder.com` loads over HTTPS (valid padlock).
- Start a check, answer a few, refresh: your progress is still there.
- Save and finish later: a real sign-in email arrives; the code works.
- A test purchase in live mode confirms, and you get exactly one receipt.

## Updating to a new version

```bash
# Build + push a new tag from your dev machine
VERSION=v0.3.0 ./scripts/build-and-push-ghcr.sh

# On the server, point the compose file at the new tag and roll:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Images are tagged by semver (never `:latest`), so rolling back is just pointing
the compose file at the previous tag and running `up -d` again.

## Back up

The only stateful thing is the `stewardpath-data` volume (owner data + auth.db).
Snapshot it on a schedule:

```bash
docker run --rm -v stewardpath-data:/data -v "$PWD":/backup alpine \
  tar czf /backup/stewardpath-data-$(date +%F).tar.gz -C /data .
```
