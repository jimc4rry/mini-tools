import base64
import re
from io import BytesIO
from urllib.parse import urlencode

import qrcode
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.shortcuts import render


class QRInputError(Exception):
    """Raised by an _encode_* function when the submitted fields can't be turned into a
    valid QR payload - the message is shown to the user as-is."""


def _encode_url(post):
    value = post.get("url", "").strip()
    if not value:
        raise QRInputError("Please enter a URL.")
    if "://" not in value:
        value = f"https://{value}"
    try:
        URLValidator()(value)
    except ValidationError:
        raise QRInputError("That doesn't look like a valid URL.")
    return value


def _encode_text(post):
    value = post.get("text", "").strip()
    if not value:
        raise QRInputError("Please enter some text.")
    return value


def _clean_phone(raw, error_message):
    digits = re.sub(r"[^\d+]", "", raw.strip())
    if not re.search(r"\d", digits):
        raise QRInputError(error_message)
    return digits


def _encode_phone(post):
    raw = post.get("phone", "")
    if not raw.strip():
        raise QRInputError("Please enter a phone number.")
    digits = _clean_phone(raw, "That doesn't look like a valid phone number.")
    return f"tel:{digits}"


def _encode_email(post):
    address = post.get("email", "").strip()
    if not address:
        raise QRInputError("Please enter an email address.")
    try:
        EmailValidator()(address)
    except ValidationError:
        raise QRInputError("That doesn't look like a valid email address.")
    params = {}
    subject = post.get("email_subject", "").strip()
    body = post.get("email_body", "").strip()
    if subject:
        params["subject"] = subject
    if body:
        params["body"] = body
    query = urlencode(params)
    return f"mailto:{address}" + (f"?{query}" if query else "")


def _encode_sms(post):
    raw = post.get("sms_phone", "")
    if not raw.strip():
        raise QRInputError("Please enter a phone number.")
    digits = _clean_phone(raw, "That doesn't look like a valid phone number.")
    message = post.get("sms_message", "").strip()
    return f"SMSTO:{digits}:{message}"


# Characters with special meaning in the WIFI: and VCARD: mini-formats below - a literal
# occurrence in a user-supplied value (e.g. a semicolon in a network name) would otherwise
# corrupt the format's field separators, so it must be backslash-escaped.
def _escape_special_chars(value, chars):
    for ch in chars:
        value = value.replace(ch, "\\" + ch)
    return value


def _encode_wifi(post):
    ssid = post.get("wifi_ssid", "").strip()
    if not ssid:
        raise QRInputError("Please enter a network name (SSID).")
    encryption = post.get("wifi_encryption", "WPA")
    if encryption not in ("WPA", "WEP", "nopass"):
        encryption = "WPA"
    ssid_escaped = _escape_special_chars(ssid, "\\;,:")
    if encryption == "nopass":
        return f"WIFI:T:nopass;S:{ssid_escaped};;"
    password_escaped = _escape_special_chars(post.get("wifi_password", ""), "\\;,:")
    return f"WIFI:T:{encryption};S:{ssid_escaped};P:{password_escaped};;"


def _encode_contact(post):
    name = post.get("vcard_name", "").strip()
    if not name:
        raise QRInputError("Please enter a name.")
    email = post.get("vcard_email", "").strip()
    if email:
        try:
            EmailValidator()(email)
        except ValidationError:
            raise QRInputError("That doesn't look like a valid email address.")

    escape = lambda v: _escape_special_chars(v, "\\;,")
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{escape(name)}"]
    org = post.get("vcard_org", "").strip()
    if org:
        lines.append(f"ORG:{escape(org)}")
    phone = post.get("vcard_phone", "").strip()
    if phone:
        lines.append(f"TEL:{_clean_phone(phone, 'That does not look like a valid phone number.')}")
    if email:
        lines.append(f"EMAIL:{email}")
    lines.append("END:VCARD")
    return "\n".join(lines)


QR_TYPES = ("url", "text", "phone", "email", "sms", "wifi", "contact")

_ENCODERS = {
    "url": _encode_url,
    "text": _encode_text,
    "phone": _encode_phone,
    "email": _encode_email,
    "sms": _encode_sms,
    "wifi": _encode_wifi,
    "contact": _encode_contact,
}


def index(request):
    """
    Public, no-login QR code generator. Stateless: nothing is saved
    server-side, the image is generated in-memory and returned as a data
    URI. Supports several QR payload types (a "type" is really just a
    different plain-text format convention - see the _encode_* functions -
    not a different underlying technology).
    """
    qr_image_data_uri = None
    error = None
    post = request.POST if request.method == "POST" else {}
    qr_type = post.get("qr_type", "url")
    if qr_type not in QR_TYPES:
        qr_type = "url"

    if request.method == "POST":
        try:
            payload = _ENCODERS[qr_type](post)
        except QRInputError as e:
            error = str(e)
        else:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, "PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            qr_image_data_uri = f"data:image/png;base64,{encoded}"

    context = {
        "qr_image_data_uri": qr_image_data_uri,
        "error": error,
        "qr_type": qr_type,
        "form": post,
    }
    return render(request, "qr_generator/index.html", context)
