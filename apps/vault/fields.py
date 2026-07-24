from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    return Fernet(settings.VAULT_FIELD_ENCRYPTION_KEY.encode())


class EncryptedTextField(models.TextField):
    """
    Transparently encrypts/decrypts using a server-held Fernet key
    (settings.VAULT_FIELD_ENCRYPTION_KEY). This protects data at rest (DB
    dumps/backups) but the app itself can always decrypt - it is not
    zero-knowledge/client-derived encryption. The Master PIN gate (see
    apps/vault/views.py) is a separate, UI-level re-auth step before a
    value is revealed, not part of the encryption key itself.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return ""
