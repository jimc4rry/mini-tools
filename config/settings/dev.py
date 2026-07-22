from .base import *  # noqa: F401,F403

DEBUG = True
# Wide open on purpose: this only runs on your machine / LAN in development
# (e.g. start_server_lan.bat), never in production (prod.py is strict).
ALLOWED_HOSTS = ["*"]
