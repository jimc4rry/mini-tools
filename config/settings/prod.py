from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# Railway injects the public domain of the service; trust it automatically
# so ALLOWED_HOSTS/CSRF don't need to be kept in sync by hand on every deploy.
_railway_domain = env("RAILWAY_PUBLIC_DOMAIN", default=None)
if _railway_domain:
    ALLOWED_HOSTS.append(_railway_domain)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_domain}")

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS is empty in production. Set the ALLOWED_HOSTS env var "
        "(comma-separated) or ensure RAILWAY_PUBLIC_DOMAIN is available."
    )

if not VAULT_FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "VAULT_FIELD_ENCRYPTION_KEY is empty in production - apps.vault "
        "would crash the moment it tries to encrypt/decrypt a secret. "
        "Generate one with: python -c \"from cryptography.fernet import "
        "Fernet; print(Fernet.generate_key().decode())\" and set it as an env var."
    )

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
