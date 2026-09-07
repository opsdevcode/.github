#!/usr/bin/env python3
"""Read-only GitHub governance audit (GET via `gh api` only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILES = {
    "product": "product.json",
    "infra": "infra.json",
    "web": "web.json",
    "docs": "docs.json",
    "org-meta": "org-meta.json",
    "generated": "generated.json",
}

STATUS_RANK = {
    "COMPLIANT": 0,
    "PARTIAL": 1,
    "NOT_YET_ENFORCED": 2,
    "EXCEPTION": 3,
    "UNCLASSIFIED": 4,
    "DRIFT": 5,
    "ERROR": 6,
}


class AuditError(Exception):
    """Tool or API failure."""


def load_profiles() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, filename in PROFILE_FILES.items():
        path = ROOT / "profiles" / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("profile") != key:
            raise AuditError(f"{filename} profile field must be {key!r}")
        out[key] = data
    return out


def load_repos() -> dict[str, Any]:
    return json.loads((ROOT / "profiles" / "repos.json").read_text(encoding="utf-8"))


def validate_mapping(profiles: dict[str, Any], mapping: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for row in mapping.get("repos") or []:
        name = str(row.get("repo") or "")
        profile = str(row.get("profile") or "")
        if not name:
            errors.append("repo mapping missing repo")
            continue
        if name in seen:
            errors.append(f"duplicate assignment: {name}")
        seen.add(name)
        if profile not in profiles:
            errors.append(f"unknown profile {profile!r} for {name}")
        state = str(row.get("enforcement_state") or "")
        if state not in {"pending", "adopted", "exception"}:
            errors.append(f"invalid enforcement_state {state!r} for {name}")
    gen = mapping.get("generated") or {}
    if gen.get("profile") and gen["profile"] not in profiles:
        errors.append("generated.profile is unknown")
    return errors


def classify_control(
    *,
    expected: Any,
    actual: Any,
    enforcement_state: str,
    unknown_is_match: bool = False,
) -> str:
    """Return COMPLIANT, DRIFT, NOT_YET_ENFORCED, EXCEPTION, or PARTIAL."""
    if actual == "UNKNOWN":
        return "PARTIAL"
    match = expected == actual
    if match:
        return "COMPLIANT"
    if enforcement_state == "exception":
        return "EXCEPTION"
    if enforcement_state == "adopted":
        return "DRIFT"
    return "NOT_YET_ENFORCED"


def rollup(statuses: list[str]) -> str:
    if not statuses:
        return "COMPLIANT"
    return max(statuses, key=lambda s: STATUS_RANK.get(s, 0))


def evaluate_repo(
    profile: dict[str, Any],
    assignment: dict[str, Any],
    live: dict[str, Any],
) -> dict[str, Any]:
    state = str(assignment.get("enforcement_state") or "pending")
    findings: list[dict[str, str]] = []

    def add(control: str, expected: str, actual: str, classification: str) -> None:
        findings.append(
            {
                "control": control,
                "expected": expected,
                "actual": actual,
                "classification": classification,
            }
        )

    if not live.get("exists"):
        cls = "DRIFT" if state == "adopted" else "NOT_YET_ENFORCED"
        return {
            "status": cls,
            "findings": [
                {
                    "control": "repository",
                    "expected": "exists",
                    "actual": "absent",
                    "classification": cls,
                }
            ],
        }

    want_vis = profile["visibility"]
    actual_vis = str(live.get("visibility") or "UNKNOWN")
    if actual_vis == "UNKNOWN":
        vis_class = "PARTIAL"
    elif actual_vis == want_vis:
        vis_class = "COMPLIANT"
    else:
        vis_class = "DRIFT"
    add("visibility", want_vis, actual_vis, vis_class)

    want_branch = profile.get("default_branch", "main")
    actual_branch = str(live.get("default_branch") or "UNKNOWN")
    if actual_branch == "UNKNOWN":
        bclass = "PARTIAL"
    elif actual_branch == want_branch:
        bclass = "COMPLIANT"
    else:
        bclass = classify_control(
            expected=want_branch, actual=actual_branch, enforcement_state=state
        )
    add("default_branch", want_branch, actual_branch, bclass)

    gate_expected = "required" if profile.get("pull_request_required") else "optional"
    gate_flag = str(live.get("gate") or "UNKNOWN")
    if gate_flag == "yes":
        gate_actual = "present"
    elif gate_flag == "no":
        gate_actual = "absent"
    else:
        gate_actual = "UNKNOWN"
    if gate_expected == "required":
        if gate_actual == "UNKNOWN":
            gclass = "PARTIAL"
        elif gate_actual == "present":
            gclass = "COMPLIANT"
        else:
            gclass = classify_control(
                expected="present", actual=gate_actual, enforcement_state=state
            )
    else:
        gclass = "COMPLIANT"
    add("ruleset_or_branch_protection", gate_expected, gate_actual, gclass)

    checks_mode = profile.get("required_checks")
    checks_actual = str(live.get("checks") or "UNKNOWN")
    if checks_mode == "any":
        if checks_actual == "UNKNOWN":
            cclass = "PARTIAL"
        elif checks_actual == "yes":
            cclass = "COMPLIANT"
        else:
            cclass = classify_control(
                expected="yes", actual=checks_actual, enforcement_state=state
            )
        add("required_checks", "at-least-one", checks_actual, cclass)

    for live_key, control, want in (
        ("secret_scan", "secret_scanning", profile.get("secret_scanning")),
        ("push_protection", "push_protection", profile.get("push_protection")),
        ("dependabot", "dependabot_alerts", profile.get("dependabot_alerts")),
    ):
        expected = "enabled" if want else "disabled"
        actual_flag = str(live.get(live_key) or "UNKNOWN")
        actual = (
            "enabled"
            if actual_flag == "yes"
            else "disabled"
            if actual_flag == "no"
            else "UNKNOWN"
        )
        if actual == "UNKNOWN":
            sclass = "PARTIAL"
        elif actual == expected:
            sclass = "COMPLIANT"
        else:
            sclass = classify_control(
                expected=expected, actual=actual, enforcement_state=state
            )
        add(control, expected, actual, sclass)

    status = rollup([f["classification"] for f in findings])
    return {"status": status, "findings": findings}


def gh_get(path: str) -> tuple[int, str]:
    result = subprocess.run(
        ["gh", "api", "-i", path],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and not result.stdout:
        err = (result.stderr or "gh api failed").strip()
        if "401" in err or "403" in err or "auth" in err.lower():
            raise AuditError(f"insufficient credentials for GET {path}")
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


def flag(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).lower()
    if text in {"enabled", "true", "yes"}:
        return "yes"
    if text in {"disabled", "false", "no"}:
        return "no"
    return "UNKNOWN"


def inspect_repo(full_name: str) -> dict[str, Any]:
    status, data = gh_json(f"repos/{full_name}")
    if status == 404:
        return {"exists": False}
    if status >= 400 or not isinstance(data, dict):
        raise AuditError(f"GET repos/{full_name} HTTP {status}")
    default_branch = str(data.get("default_branch") or "")
    vis = str(data.get("visibility") or ("private" if data.get("private") else "public"))
    security = data.get("security_and_analysis") or {}
    secret = (security.get("secret_scanning") or {}).get("status")
    push = (security.get("secret_scanning_push_protection") or {}).get("status")

    rs_status, rules = gh_json(f"repos/{full_name}/rulesets")
    rulesets = rules if isinstance(rules, list) else []
    has_ruleset = rs_status == 200 and bool(rulesets)
    check_names: list[str] = []
    if rs_status == 200:
        for item in rulesets:
            rid = item.get("id") if isinstance(item, dict) else None
            if rid is None:
                continue
            st, detail = gh_json(f"repos/{full_name}/rulesets/{rid}")
            if st != 200 or not isinstance(detail, dict):
                continue
            for rule in detail.get("rules") or []:
                if not isinstance(rule, dict):
                    continue
                if rule.get("type") != "required_status_checks":
                    continue
                params = rule.get("parameters") or {}
                for chk in params.get("required_status_checks") or []:
                    if isinstance(chk, dict) and chk.get("context"):
                        check_names.append(str(chk["context"]))

    prot_status, prot = gh_json(
        f"repos/{full_name}/branches/{default_branch}/protection"
    )
    has_protection = prot_status == 200
    if prot_status == 200 and isinstance(prot, dict):
        rsc = prot.get("required_status_checks")
        if isinstance(rsc, dict):
            check_names.extend(str(c) for c in (rsc.get("contexts") or []))

    if rs_status not in {200, 404} and prot_status not in {200, 404}:
        gate = "UNKNOWN"
    elif has_ruleset or has_protection:
        gate = "yes"
    else:
        gate = "no"

    if gate == "UNKNOWN":
        checks = "UNKNOWN"
    elif check_names:
        checks = "yes"
    else:
        checks = "no"

    dep_status, _ = gh_get(f"repos/{full_name}/vulnerability-alerts")
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
        "gate": gate,
        "checks": checks,
        "secret_scan": flag(secret),
        "push_protection": flag(push),
        "dependabot": dependabot,
    }


def inspect_org(org: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    status, data = gh_json(f"orgs/{org}")
    if status == 200 and isinstance(data, dict) and "two_factor_requirement_enabled" in data:
        enabled = bool(data.get("two_factor_requirement_enabled"))
        findings.append(
            {
                "control": "org_2fa",
                "expected": "enabled",
                "actual": "enabled" if enabled else "disabled",
                "classification": "ORG_SECURITY_GAP" if not enabled else "COMPLIANT",
            }
        )
    else:
        findings.append(
            {
                "control": "org_2fa",
                "expected": "enabled",
                "actual": "UNKNOWN",
                "classification": "UNKNOWN",
            }
        )

    cs_status, configs = gh_json(f"orgs/{org}/code-security/configurations")
    if cs_status == 200 and isinstance(configs, list) and configs:
        enforced = any(
            isinstance(c, dict) and str(c.get("enforcement") or "").lower() == "enforced"
            for c in configs
        )
        findings.append(
            {
                "control": "org_code_security_enforcement",
                "expected": "enforced",
                "actual": "enforced" if enforced else "unenforced",
                "classification": "ORG_SECURITY_GAP" if not enforced else "COMPLIANT",
            }
        )
    else:
        findings.append(
            {
                "control": "org_code_security_enforcement",
                "expected": "enforced",
                "actual": "UNKNOWN",
                "classification": "UNKNOWN",
            }
        )
    return {"findings": findings}


def pad(value: Any, width: int) -> str:
    text = str(value)
    if len(text) > width:
        return text[: max(1, width - 1)] + "…"
    return text.ljust(width)


def generated_candidates(org: str, mapping: dict[str, Any]) -> list[str]:
    cfg = mapping.get("generated") or {}
    prefixes = tuple(cfg.get("description_prefixes") or [])
    exclude = set(cfg.get("exclude_names") or [])
    assigned = {str(r["repo"]).split("/", 1)[-1] for r in mapping.get("repos") or []}
    status, repos = gh_json(f"orgs/{org}/repos?per_page=100")
    if status != 200 or not isinstance(repos, list):
        raise AuditError("cannot list organization repositories")
    names: list[str] = []
    for item in repos:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name or name in exclude or name in assigned:
            continue
        desc = str(item.get("description") or "")
        if any(desc.startswith(p) for p in prefixes):
            names.append(f"{org}/{name}")
    return names


def run_audit(argv: list[str]) -> int:
    offline = "--offline" in argv
    as_json = "--json" in argv
    include_generated = "--include-generated" in argv
    try:
        profiles = load_profiles()
        mapping = load_repos()
        errors = validate_mapping(profiles, mapping)
    except (OSError, json.JSONDecodeError, AuditError) as exc:
        print(f"failed to load policy: {exc}", file=sys.stderr)
        return 2
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2
    if offline:
        print("offline: profiles and repo mapping OK")
        print(f"mapped repos: {len(mapping.get('repos') or [])}")
        return 0

    org = str(mapping.get("organization") or "opsdevcode")
    rows: list[dict[str, Any]] = []
    api_fail = False

    assignments = list(mapping.get("repos") or [])
    if include_generated:
        try:
            for full in generated_candidates(org, mapping):
                assignments.append(
                    {
                        "repo": full,
                        "profile": "generated",
                        "enforcement_state": "pending",
                        "exceptions": [],
                    }
                )
        except AuditError as exc:
            print(f"generated discovery failed: {exc}", file=sys.stderr)
            return 2

    if not as_json:
        print(f"{pad('REPO', 34)} {pad('PROFILE', 12)} STATUS")

    for item in assignments:
        full = str(item["repo"])
        profile_name = str(item["profile"])
        profile = profiles[profile_name]
        try:
            live = inspect_repo(full)
            judged = evaluate_repo(profile, item, live)
        except AuditError as exc:
            api_fail = True
            judged = {
                "status": "ERROR",
                "findings": [
                    {
                        "control": "api",
                        "expected": "readable",
                        "actual": str(exc),
                        "classification": "ERROR",
                    }
                ],
            }
        row = {
            "repo": full,
            "profile": profile_name,
            "enforcement_state": item.get("enforcement_state"),
            "exceptions": item.get("exceptions") or [],
            "status": judged["status"],
            "findings": judged["findings"],
        }
        rows.append(row)
        if not as_json:
            print(f"{pad(full, 34)} {pad(profile_name, 12)} {judged['status']}")
            interesting = [
                f
                for f in judged["findings"]
                if f["classification"] not in {"COMPLIANT"}
            ]
            for finding in interesting:
                print(f"  {finding['control']}")
                print(f"    expected: {finding['expected']}")
                print(f"    actual: {finding['actual']}")
                print(f"    classification: {finding['classification']}")

    org_block: dict[str, Any] = {"findings": []}
    try:
        org_block = inspect_org(org)
    except AuditError as exc:
        org_block = {
            "findings": [
                {
                    "control": "org",
                    "expected": "readable",
                    "actual": str(exc),
                    "classification": "UNKNOWN",
                }
            ]
        }

    if not as_json:
        print()
        print("ORG")
        for finding in org_block["findings"]:
            print(f"  {finding['control']}")
            print(f"    expected: {finding['expected']}")
            print(f"    actual: {finding['actual']}")
            print(f"    classification: {finding['classification']}")

    if as_json:
        json.dump({"repos": rows, "org": org_block}, sys.stdout, indent=2)
        print()

    if api_fail:
        return 2
    if any(r["status"] == "DRIFT" for r in rows):
        return 1
    return 0


def main(argv: list[str]) -> int:
    if "--validate" in argv:
        try:
            profiles = load_profiles()
            mapping = load_repos()
            errors = validate_mapping(profiles, mapping)
        except (OSError, json.JSONDecodeError, AuditError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 2
        print("validate: OK")
        return 0
    return run_audit(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
