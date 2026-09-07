#!/usr/bin/env python3
"""Read-only GitHub governance audit. Uses `gh api` GET only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class AuditError(Exception):
    """Tool or API failure (exit 2)."""


def load_policy() -> tuple[dict[str, Any], dict[str, Any]]:
    classes = json.loads((ROOT / "profiles" / "classes.json").read_text(encoding="utf-8"))
    assignments = json.loads((ROOT / "profiles" / "assignments.json").read_text(encoding="utf-8"))
    return classes, assignments


def gh_get(path: str) -> tuple[int, str]:
    """GET a GitHub API path via gh. Uses default GET only."""
    result = subprocess.run(
        ["gh", "api", "-i", path],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and not result.stdout:
        err = (result.stderr or result.stdout or "gh api failed").strip()
        if "HTTP 401" in err or "HTTP 403" in err or "auth" in err.lower():
            raise AuditError(
                "insufficient GitHub credentials for GET "
                f"{path}; run: gh auth status"
            )
        raise AuditError(err[:500])
    raw = result.stdout
    if "\r\n\r\n" in raw:
        header, body = raw.split("\r\n\r\n", 1)
    elif "\n\n" in raw:
        header, body = raw.split("\n\n", 1)
    else:
        header, body = raw, ""
    status = 0
    for line in header.splitlines():
        if line.startswith("HTTP/"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                status = int(parts[1])
    return status, body


def gh_json(path: str) -> tuple[int, Any]:
    status, body = gh_get(path)
    if not body.strip():
        return status, None
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, None


def bool_status(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).lower()
    if text in {"enabled", "true", "yes"}:
        return "yes"
    if text in {"disabled", "false", "no"}:
        return "no"
    return "UNKNOWN"


def expected_match(expected: str, actual: str) -> bool:
    if actual == "UNKNOWN":
        return True
    return expected == actual


def inspect_repo(org: str, name: str) -> dict[str, Any]:
    path = f"repos/{org}/{name}"
    status, data = gh_json(path)
    if status == 404:
        return {"exists": False}
    if status >= 400 or not isinstance(data, dict):
        raise AuditError(f"GET {path} failed HTTP {status}")
    default_branch = str(data.get("default_branch") or "")
    vis = str(data.get("visibility") or ("private" if data.get("private") else "public"))
    security = data.get("security_and_analysis") or {}
    secret = (security.get("secret_scanning") or {}).get("status")
    push = (security.get("secret_scanning_push_protection") or {}).get("status")

    rules_status, rules = gh_json(f"repos/{org}/{name}/rulesets")
    rulesets: list[Any] = rules if isinstance(rules, list) else []
    if rules_status not in {200, 404}:
        ruleset_present = "UNKNOWN"
        ruleset_reviews: int | None = None
        ruleset_checks: list[str] | None = None
    else:
        ruleset_present = "yes" if rulesets else "no"
        ruleset_reviews = None
        ruleset_checks = []
        for item in rulesets:
            rid = item.get("id")
            if rid is None:
                continue
            st, detail = gh_json(f"repos/{org}/{name}/rulesets/{rid}")
            if st != 200 or not isinstance(detail, dict):
                continue
            for rule in detail.get("rules") or []:
                if not isinstance(rule, dict):
                    continue
                rtype = rule.get("type")
                params = rule.get("parameters") or {}
                if rtype == "pull_request":
                    ruleset_reviews = int(params.get("required_approving_review_count") or 0)
                if rtype == "required_status_checks":
                    checks = params.get("required_status_checks") or []
                    for chk in checks:
                        if isinstance(chk, dict) and chk.get("context"):
                            ruleset_checks.append(str(chk["context"]))
        if ruleset_present == "no":
            ruleset_checks = []

    prot_status, prot = gh_json(f"repos/{org}/{name}/branches/{default_branch}/protection")
    if prot_status == 404:
        protection = "no"
        prot_reviews = None
        prot_checks: list[str] = []
    elif prot_status == 200 and isinstance(prot, dict):
        protection = "yes"
        reviews = prot.get("required_pull_request_reviews") or {}
        prot_reviews = reviews.get("required_approving_review_count")
        if prot_reviews is not None:
            prot_reviews = int(prot_reviews)
        rsc = prot.get("required_status_checks")
        if isinstance(rsc, dict):
            prot_checks = [str(c) for c in (rsc.get("contexts") or [])]
        else:
            prot_checks = []
    else:
        protection = "UNKNOWN"
        prot_reviews = None
        prot_checks = []

    if ruleset_present == "UNKNOWN" and protection == "UNKNOWN":
        gate = "UNKNOWN"
    elif ruleset_present == "yes" or protection == "yes":
        gate = "yes"
    else:
        gate = "no"

    reviews: int | str
    if ruleset_reviews is not None:
        reviews = ruleset_reviews
    elif prot_reviews is not None:
        reviews = prot_reviews
    elif gate == "no":
        reviews = 0
    else:
        reviews = "UNKNOWN"

    checks = ruleset_checks if ruleset_checks else prot_checks
    if gate == "UNKNOWN":
        checks_flag = "UNKNOWN"
    elif checks:
        checks_flag = "yes"
    else:
        checks_flag = "no"

    dep_status, _dep = gh_get(f"repos/{org}/{name}/vulnerability-alerts")
    if dep_status == 204:
        dependabot = "yes"
    elif dep_status == 404:
        dependabot = "no"
    else:
        dependabot = "UNKNOWN"

    return {
        "exists": True,
        "visibility": vis,
        "default_branch": default_branch,
        "ruleset": ruleset_present if ruleset_present != "UNKNOWN" else (
            "yes" if protection == "yes" else ruleset_present
        ),
        "gate": gate,
        "reviews": reviews,
        "checks": checks_flag,
        "check_names": checks,
        "secret_scan": bool_status(secret),
        "push_protection": bool_status(push),
        "dependabot": dependabot,
    }


def evaluate(assignment: dict[str, Any], klass: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if not live.get("exists"):
        return {"result": "DRIFT", "reasons": ["repository not found"]}

    want_vis = assignment.get("visibility") or klass["visibility"]
    if live["visibility"] != want_vis:
        reasons.append(f"visibility {live['visibility']} != {want_vis}")

    if live["default_branch"] != klass.get("default_branch", "main"):
        reasons.append(
            f"default_branch {live['default_branch']} != {klass.get('default_branch')}"
        )

    if klass.get("require_ruleset_or_branch_protection"):
        if live["gate"] == "no":
            reasons.append("no ruleset or branch protection")
        # UNKNOWN is not noncompliance

    reviews = live["reviews"]
    min_rev = int(klass.get("min_approving_reviews") or 0)
    solo = bool(klass.get("solo_operator_reviews_allowed"))
    if reviews == "UNKNOWN":
        pass
    elif klass.get("require_ruleset_or_branch_protection") and live["gate"] == "yes":
        if int(reviews) < min_rev and not solo:
            reasons.append(f"approving reviews {reviews} < {min_rev}")

    if klass.get("require_status_checks") and live["gate"] != "UNKNOWN":
        if live["checks"] == "no":
            reasons.append("no required status checks")

    for key, label, expected in (
        ("secret_scan", "secret scanning", klass.get("secret_scanning")),
        ("push_protection", "push protection", klass.get("push_protection")),
        ("dependabot", "Dependabot alerts", klass.get("dependabot_alerts")),
    ):
        actual = live[key]
        want = "yes" if expected == "enabled" else "no" if expected == "disabled" else expected
        if not expected_match(str(want), str(actual)):
            reasons.append(f"{label} {actual} != {want}")

    result = "OK" if not reasons else "DRIFT"
    return {"result": result, "reasons": reasons}


def pad(value: Any, width: int) -> str:
    text = str(value)
    if len(text) > width:
        return text[: width - 1] + "…"
    return text.ljust(width)


def main(argv: list[str]) -> int:
    offline = "--offline" in argv
    as_json = "--json" in argv
    try:
        classes_doc, assignments = load_policy()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to load profiles: {exc}", file=sys.stderr)
        return 2

    classes = classes_doc.get("classes") or {}
    org = str(assignments.get("organization") or "opsdevcode")
    rows: list[dict[str, Any]] = []
    api_fail = False

    if offline:
        for item in assignments.get("repos") or []:
            profile = item["profile"]
            if profile not in classes:
                print(f"unknown profile {profile} for {item.get('name')}", file=sys.stderr)
                return 2
        print("offline: profiles parse OK")
        print(f"assigned repos: {len(assignments.get('repos') or [])}")
        return 0

    header = (
        f"{pad('REPO', 22)} {pad('PROFILE', 8)} {pad('VISIBILITY', 12)} "
        f"{pad('RULESET', 8)} {pad('CHECKS', 8)} {pad('SECRET_SCAN', 12)} "
        f"{pad('DEPENDABOT', 12)} RESULT"
    )
    if not as_json:
        print(header)

    for item in assignments.get("repos") or []:
        name = str(item["name"])
        profile = str(item["profile"])
        klass = classes.get(profile)
        if not klass:
            print(f"unknown profile {profile} for {name}", file=sys.stderr)
            return 2
        try:
            live = inspect_repo(org, name)
            judged = evaluate(item, klass, live)
        except AuditError as exc:
            api_fail = True
            live = {
                "visibility": "UNKNOWN",
                "gate": "UNKNOWN",
                "checks": "UNKNOWN",
                "secret_scan": "UNKNOWN",
                "dependabot": "UNKNOWN",
            }
            judged = {"result": "ERROR", "reasons": [str(exc)]}

        row = {
            "repo": name,
            "profile": profile,
            "visibility": live.get("visibility", "UNKNOWN"),
            "ruleset": live.get("gate", "UNKNOWN"),
            "checks": live.get("checks", "UNKNOWN"),
            "secret_scan": live.get("secret_scan", "UNKNOWN"),
            "dependabot": live.get("dependabot", "UNKNOWN"),
            "result": judged["result"],
            "reasons": judged["reasons"],
        }
        rows.append(row)
        if not as_json:
            print(
                f"{pad(name, 22)} {pad(profile, 8)} {pad(row['visibility'], 12)} "
                f"{pad(row['ruleset'], 8)} {pad(row['checks'], 8)} "
                f"{pad(row['secret_scan'], 12)} {pad(row['dependabot'], 12)} "
                f"{row['result']}"
            )
            for reason in judged["reasons"]:
                print(f"  - {reason}")

    if as_json:
        json.dump({"repos": rows}, sys.stdout, indent=2)
        print()

    if api_fail:
        return 2
    if any(r["result"] == "DRIFT" for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
