import re

from django.shortcuts import render
from django.utils.text import slugify

from apps.core.ratelimit import is_rate_limited

JIRA_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-\d+$")

BRANCH_TYPES = ("feature", "bugfix", "hotfix", "chore", "release")


class HelperInputError(Exception):
    """Raised when the submitted fields can't produce output - message shown as-is."""


def _clean_jira_key(raw):
    key = (raw or "").strip().upper()
    if not key:
        raise HelperInputError("Enter a Jira issue key (e.g. PROJ-123).")
    if not JIRA_KEY_RE.match(key):
        raise HelperInputError("That doesn't look like a Jira issue key (expected e.g. PROJ-123).")
    return key


def _generate_branch(post):
    key = _clean_jira_key(post.get("jira_key"))
    branch_type = post.get("branch_type", "feature")
    if branch_type not in BRANCH_TYPES:
        branch_type = "feature"
    summary = (post.get("summary") or "").strip()
    slug = slugify(summary)[:50].strip("-")
    branch = f"{branch_type}/{key}"
    if slug:
        branch += f"-{slug}"
    return {"branch_name": branch}


def _generate_smart_commit(post):
    key = _clean_jira_key(post.get("jira_key"))
    comment = (post.get("comment") or "").strip()
    time_spent = (post.get("time_spent") or "").strip()
    transition = (post.get("transition") or "").strip()

    if not (comment or time_spent or transition):
        raise HelperInputError("Fill in at least one of comment, time spent, or transition.")

    parts = [key]
    if comment:
        parts.append(f"#comment {comment}")
    if time_spent:
        parts.append(f"#time {time_spent}")
    if transition:
        # Jira smart commits require quoting a transition name that contains spaces.
        parts.append(f'#"{transition}"' if " " in transition else f"#{transition}")

    return {"smart_commit": " ".join(parts)}


def _generate_gherkin(post):
    feature = (post.get("feature") or "").strip()
    role = (post.get("role") or "").strip()
    goal = (post.get("goal") or "").strip()
    benefit = (post.get("benefit") or "").strip()
    scenario = (post.get("scenario") or "").strip()
    given = (post.get("given") or "").strip()
    when = (post.get("when") or "").strip()
    then = (post.get("then") or "").strip()

    if not feature:
        raise HelperInputError("Enter a feature name.")
    if not (given and when and then):
        raise HelperInputError("Fill in Given, When, and Then.")

    lines = [f"Feature: {feature}"]
    if role or goal or benefit:
        lines.append(f"  As a {role or '...'}")
        lines.append(f"  I want {goal or '...'}")
        lines.append(f"  So that {benefit or '...'}")
    lines.append("")
    lines.append(f"  Scenario: {scenario or 'Happy path'}")
    for keyword, text in (("Given", given), ("When", when), ("Then", then)):
        for i, line in enumerate(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            lines.append(f"    {keyword if i == 0 else 'And'} {line}")

    return {"gherkin": "\n".join(lines)}


GENERATORS = {
    "branch": _generate_branch,
    "smart_commit": _generate_smart_commit,
    "gherkin": _generate_gherkin,
}

RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_REQUESTS = 60


def index(request):
    """
    Public, no-login generators for a few small Jira/Git text snippets:
    branch names, Jira smart-commit syntax, and a Gherkin/BDD scenario
    skeleton. Pure text templating - no state, nothing saved.
    """
    mode = request.POST.get("mode", "branch")
    if mode not in GENERATORS:
        mode = "branch"
    result = None
    error = None

    if request.method == "POST":
        if is_rate_limited(request, "jira_helpers", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS):
            error = "Too many requests from this network. Please try again in a few minutes."
        else:
            try:
                result = GENERATORS[mode](request.POST)
            except HelperInputError as e:
                error = str(e)

    return render(
        request,
        "jira_helpers/index.html",
        {"mode": mode, "result": result, "error": error, "form": request.POST},
    )
