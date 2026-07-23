# Minitools Hub

A Django project that hosts a hub of small, independent products under one
domain: internal/external documentation, a marketplace of free mini-tools,
and full standalone apps — each reachable as a subpath of the same site,
sharing one design system.

**Live**: https://web-production-c2e12.up.railway.app/
(Railway project `minitools-hub` — entirely separate from any other
Django+Postgres project/deployment on this account: own codebase, own
database, own env vars.)

## What's actually in it

### The Hub itself (`apps/core`, `apps/docs`, `apps/tools`)

The landing page (`/`) shows two things side by side:

- **Applications** (left sidebar, `apps/docs`'s `Project` model) — a list of
  products this Hub fronts. Each one gets its own page (`/p/<slug>/`) with a
  description and an "Open the app" link. A project can be:
  - **doc-only**, just a home for its support/policy pages (e.g. **LiteQA**,
    a Jira Marketplace test-management app — its Privacy Policy, Terms, and
    Support pages live here at stable URLs so they can be submitted to the
    Marketplace listing even before the project is public)
  - **hosted inside this same Django project** via `Project.url_name` (e.g.
    **Expiration Tracker**, see below)
  - **hosted on a completely separate site** via `Project.external_url`
    (e.g. **MenuHub**, linking out to `getmenuhub.com`)

  A project can be marked `is_public = False` to hide it from the sidebar
  and its own `/p/<slug>/` page while its *individual* documents stay
  reachable by direct link — for a project pending external approval
  (Marketplace review, etc.) whose legal pages need to be live now, without
  the project being publicly browsable yet.

- **Documents** (`/docs/`) — a flat list of every published `Document`,
  each with a slug meant to be linked from external systems (Jira, a
  Marketplace listing, etc.). Once a slug's been shared externally, treat
  it as permanent — the slug is the public identifier.

- **Tools** (`/tools/`) — a marketplace of small, self-contained, public
  utilities. Each tool is its own Django app that registers a `Tool` row
  (name, description, an icon, `url_name` pointing at its entry view) so it
  shows up in the catalog, optionally under a `ToolCategory`. `is_free` /
  `price_cents` already exist on the model for when a tool needs to be
  paywalled (see "Billing" below — not wired up yet).
  - **Free QR Code Generator** (`apps/qr_generator`, `/qr-code-generator/`)
    is the first one live: no login, no database writes — it renders the
    QR code in-memory and returns it as a data URI. Ported from a
    different, unrelated project (a QR-menu SaaS), stripped of that
    project's own branding/upsell.

### Expiration Tracker (`apps/tracker`, `/expiration-tracker/`)

A full multi-tenant inventory-tracking app for small businesses (pharmacies,
mini markets, cafes, delis): track product batches and expiration dates,
barcode scanning, low-stock alerts, a waste log, CSV export, and scheduled
email/WhatsApp digests of what's expiring soon. Ported in from what was
originally its own standalone Django project.

- **Real user accounts**: signup creates a `Business` tied to the Django
  user, with a 14-day free trial (50-product cap). Uses the site's single
  shared `django.contrib.auth` — same login system as the Django admin.
  (Decision: **future** apps that need login should each get their own,
  separate account table instead of sharing this one — see the note below.
  Tracker is grandfathered in on shared auth since it already shipped this
  way.)
- **Fully bilingual** (English + Greek) — see "Internationalization" below.
- **Same visual design as the rest of the Hub** — it used to have its own
  separate look; it now extends the shared `templates/base.html` and just
  swaps in its own sidebar (Dashboard / Categories / Waste log / Settings /
  Log out) instead of the Applications list.
- **Billing scaffolding**: `apps/tracker/billing.py` has a Paddle webhook
  handler (HMAC signature verification + a logging-only cross-check against
  Paddle's published webhook IP ranges) ready for when there's a real Paddle
  account — currently inert (`PADDLE_WEBHOOK_SECRET` unset).
- **Signup hardening**: per-IP rate limit (5/hour) + an invisible honeypot
  field, since free-trial signup with no email verification is an obvious
  abuse target.

### Django admin (`/admin/`)

Same admin as always (manages every model above), just re-themed with the
Hub's own dark/gradient design system instead of Django's default
blue-and-white — see `templates/admin/base_site.html` and
`apps/core/apps.py`'s `site_header`/`site_title`.

## Design system

One shared `templates/base.html`: a violet→cyan gradient accent, Inter/Sora
(Google Fonts), a sticky header + left sidebar, glassy blurred cards, and a
small set of reusable classes (`.card`, `.btn-primary`/`.btn-secondary`/
`.btn-danger`, `.data-table`, `.chip-*` status pills, `.stat-tile`,
`.form-field`) that every app in the Hub — including Expiration Tracker and
the QR generator — builds its pages out of. Change it once in `base.html`
and it cascades everywhere.

## Internationalization

The whole project is set up for English + Greek (`LANGUAGES` in
`config/settings/base.py`, `LocaleMiddleware`, a language switcher). Right
now the *translated* content is Expiration Tracker specifically (every
template, form, view message, and model choice there goes through
`{% trans %}`/`gettext`) — the rest of the Hub's own copy is English-only
until/unless that's asked for too. Source strings are English; Greek
translations live in `locale/el/LC_MESSAGES/django.po` (compiled `.mo` is
committed alongside it, since Railway's build image has no `gettext` tools
to compile it at deploy time — if you add/change translatable strings,
run `python manage.py compilemessages -l el` locally before committing).

## Security & SEO

Ported over after reviewing a more mature sibling Django project for
practices worth adopting here:

- `SECURE_CONTENT_TYPE_NOSNIFF`, `FILE_UPLOAD_MAX_MEMORY_SIZE` /
  `DATA_UPLOAD_MAX_MEMORY_SIZE`, the usual HSTS/SSL-redirect/secure-cookie
  set in `config/settings/prod.py`.
- `SITE_URL` setting + `apps.core.context_processors.site_context`, so
  canonical/`og:url` tags always point at the real domain instead of
  self-canonicalizing on Railway's own `*.up.railway.app` subdomain
  (duplicate-content risk otherwise).
- Hand-rolled `robots.txt` / `sitemap.xml` (`apps/core/views.py`), listing
  public docs/projects/tools/qr-generator pages and disallowing `/admin/`,
  `/accounts/`, `/expiration-tracker/`.
- Meta description, Open Graph tags, Twitter card, and a favicon on every
  Hub page.

## Architecture

```
config/
  settings/base.py   shared settings, reads everything from env via django-environ
  settings/dev.py     local development (DEBUG=True, sqlite fallback)
  settings/prod.py    production hardening (HSTS, secure cookies, Railway domain)
  urls.py, wsgi.py, asgi.py
apps/
  core/          home page, health check, robots.txt/sitemap.xml
  docs/          Document + Project models, markdown rendering, admin
  tools/         Tool + ToolCategory registry, marketplace landing page
  qr_generator/  Free QR Code Generator (stateless, no login)
  tracker/       Expiration Tracker: full app, its own auth, models, templates
templates/base.html              shared layout + design system
templates/admin/base_site.html   Django admin re-themed to match
locale/el/                       Greek translations (Expiration Tracker)
static/, staticfiles/            served via whitenoise
```

Adding a new mini-tool: create `apps/<toolname>/`, add it to
`INSTALLED_APPS`, wire its URLs in `config/urls.py`, and add a `Tool` row
(via `/admin/`) pointing `url_name` at its entry view.

Adding a new full application (with its own login): give it its own
account/credentials model rather than reusing `django.contrib.auth`'s
shared `User` table, so its users can't log into another app in the Hub
with the same credentials. The Django admin itself stays shared across
every app.

## Local development

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate.ps1 in PowerShell
pip install -r requirements-dev.txt
cp .env.example .env             # then set a real SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Without a `DATABASE_URL` set, it falls back to a local `db.sqlite3` — no
Postgres needed for local dev.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: `manage.py
check`, `manage.py makemigrations --check` (catches missing migrations),
and `manage.py test`.

## Deploying to Railway

Already set up as its own Railway project (`minitools-hub`), with the web
service auto-deploying from this repo's `main` branch on every push, plus
its own Postgres plugin. To reproduce this setup elsewhere:

1. Push this repo to its own GitHub repository.
2. `railway init --name <name>` to create a new, separate project.
3. `railway add --database postgres` for the database.
4. `railway add --repo <owner>/<repo> --branch main --service web` to
   create the web service sourced from GitHub (continuous deployment).
5. Set env vars on the web service:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `SECRET_KEY` — generate one, e.g.
     `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}` (references the Postgres
     service's own variable)
   - `SITE_URL` — set once you have a domain (`railway domain` generates a
     Railway one to start with)
   - `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` — only needed for a custom
     domain; `RAILWAY_PUBLIC_DOMAIN` is auto-detected otherwise
6. Railway's Nixpacks/Railpack builder doesn't run a Heroku-style
   `release:` Procfile process type, so `migrate` + `collectstatic` are
   chained directly into the `web:` start command instead (before
   `gunicorn`) — they run once per deploy/restart, harmless since both are
   idempotent.
7. `railway domain --service web` to get a public URL.
8. `railway ssh`, then `python manage.py createsuperuser` from inside the
   container — `railway run` won't work for this since it executes locally
   against Railway's *internal* `DATABASE_URL` hostname, which only
   resolves from inside Railway's own network.

### Custom domain

`railway domain <yourdomain.com> --service web` to get the DNS record to
add at your registrar, then update `SITE_URL` (and `ALLOWED_HOSTS`/
`CSRF_TRUSTED_ORIGINS` if set) to match.

## Billing (not wired up yet)

Both places this matters have the data model ready but no live payment
processor connected:

- **Tools**: `Tool.is_free` / `Tool.price_cents` exist; add an
  `apps/billing` app (Stripe or similar) plus a purchase/subscription
  record to gate a paid tool's view, when there's a real product to charge
  for.
- **Expiration Tracker**: `apps/tracker/billing.py` already has a working
  Paddle webhook handler (signature verification, IP cross-check logging)
  — it just needs `PADDLE_API_KEY`/`PADDLE_WEBHOOK_SECRET`/price IDs from a
  real Paddle account, and a checkout flow (Paddle.js) to actually start
  subscriptions.
