"""
Base settings shared by every environment.
Environment-specific values are read from the process environment
(loaded from a .env file in development, from Railway variables in production).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-local-dev-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Canonical site URL (e.g. https://minitoolshub.com) used to build canonical/
# og:url tags — see apps.core.context_processors.site_context. Without this,
# the app would self-canonicalize on whatever host served the request, which
# risks Railway's own *.up.railway.app domain and a custom domain both being
# indexed as duplicate content.
SITE_URL = env("SITE_URL", default="http://127.0.0.1:8000").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.docs",
    "apps.tools",
    "apps.tracker",
    "apps.qr_generator",
    "apps.barcode_tool",
    "apps.csv_cleaner",
    "apps.jira_helpers",
    "apps.feedback",
    "apps.og_image",
    "apps.newsletter",
    "apps.billing",
    "apps.platform_admin",
    "apps.vault",
    "apps.wellness",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.core.middleware.DefaultToEnglishMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_context",
                "apps.core.context_processors.current_tool_context",
                "apps.feedback.context_processors.unread_badge",
                "apps.vault.context_processors.vault_alerts",
                "apps.wellness.context_processors.wellness_alerts",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("el", "Ελληνικά"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Athens"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Protect against decompression-bomb / oversized-POST DoS attempts.
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# Email (console backend for dev; SMTP env vars for production)
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@minitools.local")

# Where apps.feedback emails a notification for each new submission.
# Left blank to skip sending (submissions are always saved to the Django admin
# regardless - see apps/feedback/views.py).
FEEDBACK_NOTIFY_EMAIL = env("FEEDBACK_NOTIFY_EMAIL", default="")

# Paddle billing, shared across every paid app on the Hub (see apps/billing/webhooks.py).
# Signature verification is skipped in dev until this is set.
PADDLE_WEBHOOK_SECRET = env("PADDLE_WEBHOOK_SECRET", default="")

# Paddle client-side token (Paddle dashboard -> Developer Tools -> Authentication -
# NOT the API key, this one is safe to expose in the browser) used to initialize
# Paddle.js on the checkout page (see apps/billing/views.py + templates/billing/upgrade.html).
PADDLE_CLIENT_TOKEN = env("PADDLE_CLIENT_TOKEN", default="")
# "sandbox" while testing with a Paddle sandbox account, "production" once live.
PADDLE_ENVIRONMENT = env("PADDLE_ENVIRONMENT", default="sandbox")

# Paddle Price IDs per paid product slug - create a Product + Price in the Paddle
# dashboard for each paid app, then set these. A product with a blank price ID
# has no working checkout yet: apps/billing/views.py returns 404 for it instead
# of opening a broken Paddle overlay.
PADDLE_PRICE_IDS = {
    "tracker": env("PADDLE_PRICE_ID_TRACKER", default=""),
    "vault": env("PADDLE_PRICE_ID_VAULT", default=""),
}

# Twilio WhatsApp notifications for the Expiration Tracker app (see
# apps/tracker/management/commands/send_whatsapp_notifications.py).
# Left blank until a Twilio account is set up.
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_WHATSAPP_FROM = env("TWILIO_WHATSAPP_FROM", default="")

# Field-level encryption key for apps.vault (License & Subscription Vault) -
# encrypts secret_value at rest via Fernet (see apps/vault/fields.py).
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Blank only works in dev (see config/settings/prod.py's startup guard).
VAULT_FIELD_ENCRYPTION_KEY = env("VAULT_FIELD_ENCRYPTION_KEY", default="")
