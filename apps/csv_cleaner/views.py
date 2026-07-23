import base64
import csv
import io
from datetime import datetime

from django.shortcuts import render

from apps.core.ratelimit import is_rate_limited

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB - matches DATA_UPLOAD_MAX_MEMORY_SIZE
MAX_ROWS = 20_000  # keeps in-memory processing fast; this is a quick-clean tool, not a bulk-ETL one

# Tried in order; the first one that parses wins. Day-first slash/dash dates
# are tried before month-first ones - an assumption (not every "DD/MM vs
# MM/DD" case is unambiguous), stated in the UI so it isn't a silent guess.
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%B %d %Y",
    "%b %d, %Y",
]


class CsvCleanError(Exception):
    """Raised when the upload can't be processed - message shown as-is."""


def _clean_cell(value):
    """Trims whitespace always; if what's left parses as one of DATE_FORMATS,
    normalizes it to YYYY-MM-DD - otherwise the trimmed text is kept as-is."""
    text = value.strip()
    if not text:
        return text
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d")
    return text


def _escape_formula(value):
    """
    CSV-injection guard: a cell starting with "=" is treated as a live
    formula by Excel/Sheets the moment the file is opened. Prefixing it
    with a single quote forces it to be read as plain text instead.
    Deliberately NOT escaping a leading "+"/"-"/"@" too - those are also
    formula triggers in some spreadsheet apps, but also completely normal
    prefixes for real data (negative numbers, phone numbers), so guarding
    them would corrupt more legitimate data than it protects.
    """
    if value.startswith("="):
        return "'" + value
    return value


def _decode(uploaded_file):
    raw = uploaded_file.read()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvCleanError("Couldn't read this file's text encoding. Please save it as UTF-8 CSV and try again.")


def _clean_csv(uploaded_file):
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise CsvCleanError(f"File is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")

    text = _decode(uploaded_file)
    try:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
    except csv.Error:
        raise CsvCleanError("Couldn't parse this as CSV. Check it's comma-separated and try again.")

    if not rows:
        raise CsvCleanError("That file is empty.")
    if len(rows) > MAX_ROWS:
        raise CsvCleanError(f"That's {len(rows)} rows — this tool handles up to {MAX_ROWS} at a time.")

    header, *body = rows
    header = [cell.strip() for cell in header]

    seen = set()
    cleaned_rows = []
    duplicates_removed = 0
    for row in body:
        cleaned = tuple(_escape_formula(_clean_cell(cell)) for cell in row)
        if cleaned in seen:
            duplicates_removed += 1
            continue
        seen.add(cleaned)
        cleaned_rows.append(cleaned)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(cleaned_rows)

    csv_bytes = ("﻿" + output.getvalue()).encode("utf-8")  # BOM so Excel opens it as UTF-8
    data_uri = "data:text/csv;base64," + base64.b64encode(csv_bytes).decode("ascii")

    return {
        "preview_rows": cleaned_rows[:10],
        "header": header,
        "download_uri": data_uri,
        "original_rows": len(body),
        "cleaned_rows": len(cleaned_rows),
        "duplicates_removed": duplicates_removed,
    }


CLEAN_RATE_LIMIT_WINDOW_SECONDS = 300
CLEAN_RATE_LIMIT_MAX_REQUESTS = 20


def index(request):
    """
    Public, no-login CSV cleaner: trims whitespace, normalizes common date
    formats to YYYY-MM-DD, drops exact-duplicate rows, and guards against
    CSV/formula injection in the output. Stateless — the uploaded file is
    read into memory, processed, and the result handed back; nothing is
    written to disk or a database.
    """
    error = None
    result = None

    if request.method == "POST":
        if is_rate_limited(
            request, "csv_cleaner", CLEAN_RATE_LIMIT_MAX_REQUESTS, CLEAN_RATE_LIMIT_WINDOW_SECONDS
        ):
            error = "Too many requests from this network. Please try again in a few minutes."
        elif "file" not in request.FILES:
            error = "Choose a CSV file first."
        else:
            try:
                result = _clean_csv(request.FILES["file"])
            except CsvCleanError as e:
                error = str(e)

    return render(request, "csv_cleaner/index.html", {"error": error, "result": result})
