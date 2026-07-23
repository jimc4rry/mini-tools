import base64
import re
from io import BytesIO

import barcode as barcode_lib
from barcode.writer import ImageWriter
from django.shortcuts import render

from apps.core.ratelimit import is_rate_limited

# Payload lengths (barcode minus its own check digit) for the formats this
# tool understands. Full-number lengths are these + 1.
FORMAT_PAYLOAD_LENGTHS = {
    "ean8": 7,
    "upca": 11,
    "ean13": 12,
}
FORMAT_LABELS = {
    "ean8": "EAN-8",
    "upca": "UPC-A",
    "ean13": "EAN-13",
}


class BarcodeInputError(Exception):
    """Raised when the submitted digits can't be validated/encoded - message shown as-is."""


def gs1_check_digit(payload_digits):
    """
    Standard GS1 mod-10 check digit, used by EAN-8, UPC-A, EAN-13, and
    GTIN-14 alike: starting from the rightmost payload digit, alternate
    weights 3, 1, 3, 1... Working right-to-left like this (rather than
    hardcoding "odd positions get 3" per format) gives the correct answer
    for any of these payload lengths without special-casing each one.
    """
    total = 0
    weight = 3
    for digit in reversed(payload_digits):
        total += int(digit) * weight
        weight = 1 if weight == 3 else 3
    return (10 - (total % 10)) % 10


def _clean_digits(raw):
    return re.sub(r"[\s-]", "", raw or "")


def _format_for_length(payload_length):
    for fmt, length in FORMAT_PAYLOAD_LENGTHS.items():
        if length == payload_length:
            return fmt
    return None


def _validate(code):
    digits = _clean_digits(code)
    if not digits.isdigit():
        raise BarcodeInputError("Enter digits only (spaces and dashes are fine, letters aren't).")

    payload_length = len(digits) - 1
    fmt = _format_for_length(payload_length)
    if fmt is None:
        raise BarcodeInputError(
            f"{len(digits)} digits isn't a length this tool recognizes — "
            "expected 8 (EAN-8), 12 (UPC-A), or 13 (EAN-13)."
        )

    payload, check_digit = digits[:-1], digits[-1]
    expected = gs1_check_digit(payload)
    is_valid = expected == int(check_digit)
    return {
        "format_label": FORMAT_LABELS[fmt],
        "digits": digits,
        "is_valid": is_valid,
        "expected_check_digit": expected,
        "corrected_code": payload + str(expected),
    }


def _generate(code, fmt):
    digits = _clean_digits(code)
    if not digits.isdigit():
        raise BarcodeInputError("Enter digits only (spaces and dashes are fine, letters aren't).")

    expected_length = FORMAT_PAYLOAD_LENGTHS.get(fmt)
    if expected_length is None:
        raise BarcodeInputError("Unknown barcode format.")

    # Accept either just the payload, or the payload + an existing (possibly
    # wrong) check digit - either way we (re)compute the real check digit
    # rather than trust one that was typed in.
    if len(digits) == expected_length:
        payload = digits
    elif len(digits) == expected_length + 1:
        payload = digits[:-1]
    else:
        raise BarcodeInputError(
            f"{FORMAT_LABELS[fmt]} needs {expected_length} payload digits "
            f"(you entered {len(digits)})."
        )

    check_digit = gs1_check_digit(payload)
    full_code = payload + str(check_digit)

    barcode_class = barcode_lib.get_barcode_class(fmt)
    instance = barcode_class(payload, writer=ImageWriter())
    buffer = BytesIO()
    instance.write(buffer, options={"write_text": True, "quiet_zone": 2})
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {
        "full_code": full_code,
        "image_data_uri": f"data:image/png;base64,{encoded}",
    }


GENERATE_RATE_LIMIT_WINDOW_SECONDS = 300
GENERATE_RATE_LIMIT_MAX_REQUESTS = 30


def index(request):
    """
    Public, no-login barcode checksum validator + generator for EAN-8/
    UPC-A/EAN-13. Stateless: nothing is saved server-side, the barcode
    image is rendered in-memory and returned as a data URI.
    """
    mode = request.POST.get("mode") or request.GET.get("mode", "validate")
    if mode not in ("validate", "generate"):
        mode = "validate"
    result = None
    error = None
    fmt = request.POST.get("format", "ean13")

    if request.method == "POST" and is_rate_limited(
        request, "barcode_tool", GENERATE_RATE_LIMIT_MAX_REQUESTS, GENERATE_RATE_LIMIT_WINDOW_SECONDS
    ):
        error = "Too many requests from this network. Please try again in a few minutes."
    elif request.method == "POST":
        code = request.POST.get("code", "")
        try:
            if mode == "generate":
                result = _generate(code, fmt)
            else:
                result = _validate(code)
        except BarcodeInputError as e:
            error = str(e)

    return render(
        request,
        "barcode_tool/index.html",
        {
            "mode": mode,
            "format": fmt,
            "result": result,
            "error": error,
            "code": request.POST.get("code", ""),
        },
    )
