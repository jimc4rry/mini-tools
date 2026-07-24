from .base import *  # noqa: F401,F403

DEBUG = True
# Wide open on purpose: this only runs on your machine / LAN in development
# (e.g. start_server_lan.bat), never in production (prod.py is strict).
ALLOWED_HOSTS = ["*"]

# Insecure fixed key so local dev works without a .env entry - never used in
# prod (see prod.py's guard against a blank VAULT_FIELD_ENCRYPTION_KEY).
if not VAULT_FIELD_ENCRYPTION_KEY:
    VAULT_FIELD_ENCRYPTION_KEY = "SL8acUxcG5BIQrds7AEs8HDkVwp2SwFXJEF4pwdKZMU="
