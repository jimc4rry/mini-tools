# Minitools Hub

A Django project that hosts a hub of small, independent products under one
domain: internal/external documentation, a marketplace of free mini-tools,
and full standalone apps — each reachable as a subpath of the same site,
sharing one design system, one login, and one bilingual (EN/EL) UI.

**Live**: https://web-production-c2e12.up.railway.app/
(Railway project `minitools-hub` — entirely separate from any other
Django+Postgres project/deployment on this account: own codebase, own
database, own env vars.)

## What's actually in it

### The Hub itself (`apps/core`, `apps/docs`, `apps/tools`)

The landing page (`/`) shows:

- **Applications** (left sidebar, `apps/docs`'s `Project` model) — a list of
  products this Hub fronts. Each one gets its own page (`/p/<slug>/`) with a
  description and an "Open the app" link. A project can be:
  - **doc-only**, just a home for its support/policy pages (e.g. **LiteQA**,
    a Jira Marketplace test-management app — its Privacy Policy, Terms,
    Support, and Security Policy pages live here at stable URLs so they can
    be submitted to the Marketplace listing even before the project is
    public)
  - **hosted inside this same Django project** via `Project.url_name` (e.g.
    Expiration Tracker, Vault, Wellness, Invoicing, Tickets — see "Full
    applications" below)
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
  utilities, no login required. Each tool is its own Django app that
  registers a `Tool` row (name, description, icon, `url_name`) to show up in
  the catalog:
  - **QR Code Generator** (`apps/qr_generator`, `/qr-code-generator/`) — no
    database writes, renders in-memory and returns a data URI.
  - **Barcode / EAN-13 Validator** (`apps/barcode_tool`, `/barcode-validator/`)
    — checks or generates a valid check digit for EAN-8/UPC-A/EAN-13.
  - **Bulk Inventory CSV Cleaner** (`apps/csv_cleaner`, `/csv-cleaner/`) —
    trims whitespace, normalizes dates, drops exact-duplicate rows.
  - **Jira Smart Commit & Branch Name Generator** (`apps/jira_helpers`,
    `/jira-helpers/`) — branch names, smart-commit syntax, Gherkin skeletons.
  - **Embeddable QR widget** — an `<iframe>`-friendly variant of the QR
    generator for embedding elsewhere.

  `Tool.is_free` / `Tool.price_cents` exist on the model for a future paid
  tool; nothing in the marketplace is actually paywalled yet.

### Full applications (own login-gated area, each with a paid tier)

All five share the same account system and the same generic billing model
(see "Accounts & billing" below) rather than each inventing its own:

- **Expiration Tracker** (`apps/tracker`, `/expiration-tracker/`) — multi-
  tenant inventory tracking for small businesses (pharmacies, mini markets,
  cafes, delis): product batches, expiration dates, barcode scanning,
  low-stock alerts, a waste log, CSV export, scheduled email/WhatsApp
  digests. The oldest app here — predates the shared `Subscription` model,
  so it keeps its own `Business.plan_status`/`trial_ends_at`/`paddle_*`
  fields in sync via `apps.billing.webhooks.sync_tracker_business()`.
- **License & Subscription Vault** (`apps/vault`, `/vault/`) — encrypted
  storage for API keys, license keys, and SSL certificates, with a Master
  PIN gate before any secret is revealed/copied (rate-limited against
  brute-force), expiry alerts, and a daily scheduled job
  (`check_ssl_expiry` management command) that checks a domain's real TLS
  certificate and keeps the expiry date in sync automatically. Field-level
  encryption via `cryptography`'s Fernet — see `VAULT_FIELD_ENCRYPTION_KEY`
  below.
- **Wellness** (`apps/wellness`, `/wellness/`) — a weight-loss consistency
  tracker that deliberately isn't a calorie counter: three small daily
  missions (seeded, rotated per user/day via a deterministic random seed,
  no cron needed), a weekly no-guilt "Joker" day, and a weeks-to-goal
  estimate derived from the user's own logged weigh-in trend (not a
  theoretical BMR/calorie-deficit guess, since intake is never tracked).
  UI is deliberately red-free — only green/blue/orange "energy" colors.
- **Invoicing** (`apps/invoicing`, `/invoicing/`) — clients, invoices and
  quotes with line items, auto-numbering per type (`INV-0001`/`QUO-0001`),
  a Draft/Sent/Paid/Cancelled lifecycle with overdue auto-detection, and a
  print-ready standalone page for saving straight to PDF via the browser
  (no PDF library dependency).
- **Tickets** (`apps/tickets`, `/tickets/`) — a Jira-lite ticketing system:
  Boards with an owner plus invited members (the first genuinely
  multi-user, shared-access feature in this codebase — every other app is
  single-owner-per-record), a drag-and-drop Kanban board (plain HTML5
  Drag-and-Drop, no JS framework anywhere in this project), comments, and
  assignment. Object-level permission check returns 404 (not 403) to
  non-members, so a board's existence isn't revealed to outsiders.

### Accounts & billing (`apps/billing`, `apps/platform_admin`)

- **One shared login for the whole Hub.** Signup (`apps/core/forms.py`'s
  `PlatformSignupForm`) just creates a `django.contrib.auth.User` — no
  app-specific fields. Each full app then does its own lightweight
  onboarding the first time a logged-in user visits it: Vault/Wellness ask
  a couple of setup questions (Master PIN; age/height/goal), Tracker/
  Invoicing/Tickets need nothing extra and create their state on first use.
  *(This reverses an earlier, since-abandoned decision that each app should
  get an isolated account table — that turned out to be worse for a user
  who wants access to more than one app.)*
- **`apps.billing.Subscription`** — one row per `(user, product)`, `product`
  being a simple slug (`"tracker"`, `"vault"`, `"wellness"`, `"invoicing"`,
  `"tickets"`). `Subscription.is_active_for(user, product)` is the one
  check every app uses to gate a paid feature — new apps should read this
  directly rather than inventing their own plan-status fields (Tracker's
  own denormalized `Business.plan_status` predates this model and is a
  documented exception, not the pattern to copy).
- **Upgrade/checkout** (`apps/billing/views.py`, `/billing/upgrade/<product>/`)
  — a Paddle Checkout overlay (Paddle.js, loaded site-wide in
  `templates/base.html`). Gracefully 404s instead of opening a broken
  overlay for any product without a configured `PADDLE_PRICE_IDS` entry
  (all blank by default — see below).
- **Platform Admin** (`apps/platform_admin`, `/platform-admin/`, superuser-
  only) — a cross-app console modeled on a sibling project's own admin UI:
  every subscription across every app in one searchable/filterable table,
  a manual plan-override form (for support cases outside the Paddle flow),
  and a Feedback inbox (see below) with an unread-count badge.

### Feedback, newsletter, and other small pieces

- **Feedback** (`apps/feedback`, floating "Feedback" button on every page)
  — rate-limited + honeypotted submission form; unread submissions badge on
  both the Django admin sidebar and Platform Admin's own dashboard/detail
  view.
- **Newsletter** (`apps/newsletter`) — a simple email-capture footer form
  for "notify me when new free tools launch."
- **OG image generator** (`apps/og_image`) — generates the Open Graph
  preview image used by every page's `og:image` tag on the fly (Pillow),
  rather than a single static banner for the whole site.
- **RSS/Atom feed**, **Ctrl+K global search**, **recently-used tools**
  (localStorage), a public **"build in public" stats widget**, and a
  **dark/light theme toggle** round out the Hub-level (not app-specific)
  features.

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
`.form-field`, `.badge-count`) that every app in the Hub builds its pages
out of. Change it once in `base.html` and it cascades everywhere. No
front-end framework or bundler anywhere — every bit of interactivity
(theme toggle, Ctrl+K search, Vault's reveal/copy, Tickets' drag-and-drop)
is a plain inline `<script>` block using `fetch` + a CSRF cookie header.

## Internationalization

The **entire Hub is bilingual** (English + Greek): every app, every
template, every form/view message goes through `{% trans %}`/`gettext`,
with a language switcher in the header (top-left) and English as the
default for a first-time visitor regardless of browser locale
(`apps.core.middleware.DefaultToEnglishMiddleware`). Two deliberate,
consistent exceptions stay English-only everywhere: page `<title>` tags/
OG-image titles (SEO metadata, not visible page content), and app/product
names used as short nav labels (e.g. "Vault", "Wellness", "Dashboard").
Source strings are English; Greek translations live in
`locale/el/LC_MESSAGES/django.po` (compiled `.mo` is committed alongside
it, since Railway's build image has no `gettext` tools to compile it at
deploy time — if you add/change translatable strings, run
`python manage.py compilemessages -l el` locally before committing).

**Recurring gotcha**: `makemessages` fuzzy-matches new strings against
similar-looking existing ones and can silently carry over a *wrong*
translation (e.g. a new "Edit invoice" string matching old "Edit item"'s
Greek text). After every `makemessages -l el` run, grep for `#, fuzzy`
markers and check for blank `msgstr ""` entries before compiling — this has
bitten every single app added to this project so far.

## Security & SEO

- `SECURE_CONTENT_TYPE_NOSNIFF`, `FILE_UPLOAD_MAX_MEMORY_SIZE` /
  `DATA_UPLOAD_MAX_MEMORY_SIZE`, the usual HSTS/SSL-redirect/secure-cookie
  set in `config/settings/prod.py` — including a startup `RuntimeError` if
  `ALLOWED_HOSTS` or `VAULT_FIELD_ENCRYPTION_KEY` end up empty in
  production, rather than silently running insecurely.
- `SITE_URL` setting + `apps.core.context_processors.site_context`, so
  canonical/`og:url` tags always point at the real domain instead of
  self-canonicalizing on Railway's own `*.up.railway.app` subdomain.
- Hand-rolled `robots.txt` / `sitemap.xml` (`apps/core/views.py`), listing
  every public doc/project/tool page and disallowing `/admin/`,
  `/accounts/`, and every login-gated app path.
- Meta description, Open Graph tags (dynamically generated preview image
  per page via `apps/og_image`), Twitter card, and a favicon on every page.
- Rate limiting + honeypot fields on every public POST endpoint that
  doesn't require login (signup, feedback, newsletter).

## Architecture

```
config/
  settings/base.py   shared settings, reads everything from env via django-environ
  settings/dev.py     local development (DEBUG=True, sqlite fallback)
  settings/prod.py    production hardening (HSTS, secure cookies, Railway domain)
  urls.py, wsgi.py, asgi.py
apps/
  core/            home page, universal signup, health check, robots.txt/sitemap.xml, search
  docs/            Document + Project models, markdown rendering, admin
  tools/           Tool + ToolCategory registry, marketplace landing page
  qr_generator/    Free QR Code Generator (stateless, no login)
  barcode_tool/    Barcode/EAN-13 validator & generator
  csv_cleaner/     Bulk inventory CSV cleaner
  jira_helpers/    Jira smart-commit / branch name / Gherkin generator
  feedback/        Feedback widget + admin inbox + unread badge
  og_image/        Dynamic Open Graph preview image generator
  newsletter/      Email-capture signup
  billing/         Shared Subscription model, Paddle webhook + checkout page
  platform_admin/  Superuser-only cross-app console
  tracker/         Expiration Tracker: full app (predates the shared billing model)
  vault/           License & Subscription Vault: encrypted secrets + expiry alerts
  wellness/        Weight-loss consistency tracker (missions, Joker, trend prediction)
  invoicing/       Invoices/quotes for freelancers
  tickets/         Jira-lite Kanban ticketing, the first multi-user/shared-access app
templates/base.html              shared layout + design system
templates/admin/base_site.html   Django admin re-themed to match
locale/el/                       Greek translations (whole Hub)
static/, staticfiles/            served via whitenoise
```

Adding a new **mini-tool** (free, no login): create `apps/<toolname>/`, add
it to `INSTALLED_APPS`, wire its URLs in `config/urls.py`, add a `Tool` row
(via `/admin/`) pointing `url_name` at its entry view.

Adding a new **full application** (login required, has a paid tier):
- Use the shared `django.contrib.auth.User` — don't invent a separate
  account table. Onboard the user the first time they visit (a short form
  if there's real profile data to collect, or nothing at all if there
  isn't — see Invoicing/Tickets for the no-onboarding-needed shape).
- Create an `apps.billing.Subscription(user=user, product="<slug>")` at
  onboarding time (or lazily on first visit); gate paid features with
  `Subscription.is_active_for(user, product)`.
- Namespace its `urls.py` (`app_name = "<slug>"`) — an early app
  (`apps/tracker`) doesn't, and that's a real footgun (bare URL names in a
  single global namespace can collide across apps); every app since has
  namespaced.
- Seed a `docs.Project` row (a small data migration, see any
  `apps/docs/migrations/00*_seed_*_project.py`) so it shows up in the
  Applications sidebar and gets a `/p/<slug>/` page.
- Wrap every string in `{% trans %}`/`gettext` from the start, run
  `makemessages -l el`, fill in real translations (checking for the fuzzy-
  match gotcha above), compile.

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
Postgres needed for local dev. `config/settings/dev.py` also fills in an
insecure fixed `VAULT_FIELD_ENCRYPTION_KEY` automatically so Vault works
locally without any extra setup.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: `manage.py
check`, `manage.py makemigrations --check` (catches missing migrations),
and `manage.py test`.

## Deploying to Railway

Already set up as its own Railway project (`minitools-hub`), with the `web`
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
   - `VAULT_FIELD_ENCRYPTION_KEY` — **required**, `prod.py` refuses to boot
     without it. Generate with
     `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
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
9. **Scheduled jobs** (e.g. Vault's `check_ssl_expiry`) run as a *second*
   Railway service pointed at the same repo, with its own Cron Schedule and
   Custom Start Command set in that service's Settings tab (the CLI doesn't
   expose either field) — copy over `DATABASE_URL` (as a variable reference
   to the same Postgres plugin), `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`,
   `VAULT_FIELD_ENCRYPTION_KEY`, and an explicit `ALLOWED_HOSTS` (this
   service has no public domain, so `RAILWAY_PUBLIC_DOMAIN` won't be set
   and `prod.py`'s empty-`ALLOWED_HOSTS` guard would otherwise fail every
   run). Don't create it via `railway add`/`service redeploy` before those
   fields are set — it'll deploy with the default `web:` start command
   (a second, unwanted full gunicorn instance) in the meantime.

### Custom domain

`railway domain <yourdomain.com> --service web` to get the DNS record to
add at your registrar, then update `SITE_URL` (and `ALLOWED_HOSTS`/
`CSRF_TRUSTED_ORIGINS` if set) to match.

## Billing

`apps/billing` is wired up end-to-end (webhook signature verification,
generic `Subscription` model, a Paddle Checkout overlay page) but has no
*real* Paddle account connected yet:

- `PADDLE_WEBHOOK_SECRET` — unset, so webhook signature verification is
  skipped in dev/until configured.
- `PADDLE_CLIENT_TOKEN` / `PADDLE_ENVIRONMENT` (`sandbox` by default) — the
  public client-side token Paddle.js needs to open a checkout overlay.
- `PADDLE_PRICE_ID_TRACKER` / `PADDLE_PRICE_ID_VAULT` / one per paid
  product — all blank by default, meaning `/billing/upgrade/<product>/`
  404s gracefully instead of opening a checkout overlay that couldn't
  actually charge anyone. Set them once there's a real Paddle Product +
  Price for that app.

Once those are set, the existing webhook (`apps/billing/webhooks.py`)
already knows how to flip a `Subscription` to active on successful
checkout — no new integration work needed, just real credentials.
