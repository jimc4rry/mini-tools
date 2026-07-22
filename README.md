# Minitools Hub

Django project that hosts:

- **Documents** (`apps/docs`) — support & policy documents with stable slugs,
  meant to be linked from external systems (Jira, wikis, etc.). Once a slug
  has been shared externally, treat it as permanent.
- **Tools** (`apps/tools`) — a registry/marketplace of standalone mini-tools.
  Each tool is its own Django app; it registers a `Tool` row (name, slug,
  description, `url_name` pointing at its entry view) so it shows up on the
  landing page. Free/paid fields already exist on the model; the actual
  billing flow (Stripe checkout + webhook) is intentionally not wired up yet
  — add it as its own app (e.g. `apps/billing`) when there's a real product
  to charge for.
- **Core** (`apps/core`) — landing page + `/healthz` for Railway's health
  check.

This is a separate project from the existing Django+Postgres app — separate
codebase, separate Railway project/service, separate database.

## Architecture

```
config/
  settings/base.py   shared settings, reads everything from env via django-environ
  settings/dev.py     local development (DEBUG=True, sqlite fallback)
  settings/prod.py    production hardening (HSTS, secure cookies, Railway domain)
  urls.py, wsgi.py, asgi.py
apps/
  core/    home page, health check
  docs/    Document/Category models, markdown rendering, admin
  tools/   Tool registry model, marketplace landing page, admin
templates/base.html   shared layout
static/, staticfiles/  served via whitenoise
```

Adding a new mini-tool later: create `apps/<toolname>/`, add it to
`INSTALLED_APPS`, wire its URLs in `config/urls.py`, and add a `Tool` row
(via `/admin/`) pointing `url_name` at its entry view.

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

## Deploying to Railway (as its own project)

1. Push this repo to its own GitHub repository (separate from the existing
   Django+Postgres project).
2. In Railway: **New Project → Deploy from GitHub repo**, pick this repo.
   This creates an isolated project — it will not share database or env
   vars with the other Django app.
3. **Add a PostgreSQL plugin** to this new project. Railway sets
   `DATABASE_URL` on the web service automatically.
4. On the web service, set environment variables:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `SECRET_KEY` — generate one, e.g.
     `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
   - `ALLOWED_HOSTS` — leave unset if you're fine relying on
     `RAILWAY_PUBLIC_DOMAIN` (auto-detected in `prod.py`), or set explicitly
     if you attach a custom domain.
   - `CSRF_TRUSTED_ORIGINS` — same idea, needed if using a custom domain.
5. Railway auto-detects the `Procfile`:
   - `release` runs `migrate` + `collectstatic` before each deploy.
   - `web` runs `gunicorn` bound to Railway's `$PORT`.
6. Deploy. Then run `railway run python manage.py createsuperuser` to get
   into `/admin/` and start adding documents/tools.

### Custom domain

Add the domain in Railway's service settings, then add it to both
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` env vars (comma-separated).

## Next steps for the "sell mini-tools" part

The `Tool` model already has `is_free` / `price_cents`. When you're ready to
charge for a tool:

1. Add an `apps/billing` app with a `stripe` dependency.
2. Add a Stripe Checkout session view + webhook endpoint (verify webhook
   signatures — don't trust unsigned payloads).
3. Gate the paid tool's view behind a check for an existing purchase/
   subscription record tied to the logged-in user.

This is deliberately not scaffolded yet since it depends on real Stripe
account details and pricing decisions.
