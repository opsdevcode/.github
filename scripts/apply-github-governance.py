#!/usr/bin/env python3
"""Apply first-class OpsDevCode PR/ruleset/merge baseline (gh api mutations)."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

GITHUB_ACTIONS_APP_ID = 15368  # github-actions[bot]

REPOS: dict[str, dict[str, Any]] = {
    "opsdevcode/.github": {
        "checks": ["validate"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/overpass": {
        "checks": ["test"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/toll": {
        "checks": ["test"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/dispatch": {
        "checks": ["test"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/relay": {
        "checks": [
            "test",
            "Code quality (Ruff + mypy)",
            "Security (Bandit + pip-audit)",
            "commitlint",
            "semantic-pull-request",
        ],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
        "note": "Target 1 approval when a second maintainer exists; 0 keeps solo path live.",
    },
    "opsdevcode/repave-aws-infra": {
        "checks": ["check"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/repave": {
        "checks": [
            "engine-unit",
            "engine-portal",
            "engine-slow",
            "Python quality and security",
            "commitlint",
            "semantic-pull-request",
            "operator-test",
            "operator-e2e",
            "chart-validate",
            "chart-smoke",
            "chart-smoke-decomposed",
            "chart-smoke-multi-replica",
            "chart-smoke-backstage",
            "CodeQL (python)",
            "CodeQL (javascript-typescript)",
            "CodeQL (go)",
            "dependency review",
            "backstage-audit",
        ],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/convergence": {
        "checks": ["commitlint", "semantic-pull-request"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": False,
    },
    "opsdevcode/opdevcode-website": {
        "checks": ["version"],
        "approvals": 0,
        "codeowners": False,
        "actions_bypass": False,
        "create_if_missing": True,
        "delete_classic_protection": True,
    },
}

MUTATIONS: list[dict[str, Any]] = []


def gh(method: str, path: str, body: Any | None = None) -> tuple[int, Any]:
    cmd = ["gh", "api", "-X", method, path]
    if body is not None:
        cmd.extend(["--input", "-"])
    proc = subprocess.run(
        cmd,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
    )
    parsed: Any
    try:
        parsed = json.loads(proc.stdout) if proc.stdout else {}
    except json.JSONDecodeError:
        parsed = {"_raw": proc.stdout, "_err": proc.stderr}
    if proc.returncode != 0 and not parsed:
        parsed = {"_err": proc.stderr.strip()}
    return proc.returncode, parsed


def log(repo: str, control: str, before: Any, after: Any, reason: str) -> None:
    MUTATIONS.append(
        {
            "repository": repo,
            "setting": control,
            "before": before,
            "after": after,
            "reason": reason,
        }
    )
    print(f"{repo}: {control}\n  before={before!r}\n  after={after!r}\n  reason={reason}")


def apply_repo_merge(full: str) -> None:
    code, repo = gh("GET", f"repos/{full}")
    if code != 0:
        raise SystemExit(f"GET {full} failed: {repo}")
    before = {
        "allow_squash_merge": repo.get("allow_squash_merge"),
        "allow_merge_commit": repo.get("allow_merge_commit"),
        "allow_rebase_merge": repo.get("allow_rebase_merge"),
        "delete_branch_on_merge": repo.get("delete_branch_on_merge"),
        "allow_auto_merge": repo.get("allow_auto_merge"),
    }
    after = {
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "delete_branch_on_merge": True,
        "allow_auto_merge": True,
        "squash_merge_commit_title": "PR_TITLE",
        "squash_merge_commit_message": "COMMIT_MESSAGES",
    }
    if before != {k: after[k] for k in before}:
        code, resp = gh("PATCH", f"repos/{full}", after)
        if code != 0:
            raise SystemExit(f"PATCH merge {full} failed: {resp}")
        log(full, "merge_ergonomics", before, {k: after[k] for k in before}, "squash-only + auto-delete + auto-merge capability")
    else:
        print(f"{full}: merge ergonomics already target")


def ruleset_payload(cfg: dict[str, Any], *, name: str = "opsdevcode-main") -> dict[str, Any]:
    bypass = []
    if cfg.get("actions_bypass"):
        bypass.append(
            {
                "actor_id": GITHUB_ACTIONS_APP_ID,
                "actor_type": "Integration",
                "bypass_mode": "always",
            }
        )
    return {
        "name": name,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": bypass,
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": cfg["approvals"],
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": cfg["codeowners"],
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": True,
                    "allowed_merge_methods": ["squash"],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [{"context": c} for c in cfg["checks"]],
                },
            },
            {"type": "non_fast_forward"},
            {"type": "deletion"},
        ],
    }


def apply_ruleset(full: str, cfg: dict[str, Any]) -> None:
    code, listing = gh("GET", f"repos/{full}/rulesets")
    if code != 0:
        raise SystemExit(f"list rulesets {full}: {listing}")
    existing = listing if isinstance(listing, list) else []
    payload = ruleset_payload(cfg)
    if not existing:
        if not cfg.get("create_if_missing"):
            raise SystemExit(f"{full}: no ruleset and create_if_missing is false")
        code, resp = gh("POST", f"repos/{full}/rulesets", payload)
        if code != 0:
            raise SystemExit(f"POST ruleset {full}: {resp}")
        log(full, "ruleset", None, {"id": resp.get("id"), "name": payload["name"]}, "create opsdevcode-main")
        return
    # Prefer updating the existing 'main branch' ruleset in place (keep name).
    rs = existing[0]
    code, detail = gh("GET", f"repos/{full}/rulesets/{rs['id']}")
    if code != 0:
        raise SystemExit(f"GET ruleset {full}: {detail}")
    before = {
        "bypass_actors": detail.get("bypass_actors"),
        "rules": detail.get("rules"),
    }
    update = ruleset_payload(cfg, name=str(detail.get("name") or "main branch"))
    code, resp = gh("PUT", f"repos/{full}/rulesets/{rs['id']}", update)
    if code != 0:
        raise SystemExit(f"PUT ruleset {full}: {resp}")
    log(
        full,
        "ruleset",
        {"bypass": before["bypass_actors"], "pr": _pr_summary(before["rules"]), "checks": _check_summary(before["rules"])},
        {
            "bypass": update["bypass_actors"],
            "approvals": cfg["approvals"],
            "dismiss_stale": True,
            "merge_methods": ["squash"],
            "checks": cfg["checks"],
        },
        "align PR baseline; no RepositoryRole admin always-bypass",
    )


def _pr_summary(rules: Any) -> Any:
    for rule in rules or []:
        if rule.get("type") == "pull_request":
            p = rule.get("parameters") or {}
            return {
                "approvals": p.get("required_approving_review_count"),
                "threads": p.get("required_review_thread_resolution"),
                "codeowners": p.get("require_code_owner_review"),
                "dismiss_stale": p.get("dismiss_stale_reviews_on_push"),
                "merge_methods": p.get("allowed_merge_methods"),
            }
    return None


def _check_summary(rules: Any) -> Any:
    for rule in rules or []:
        if rule.get("type") == "required_status_checks":
            return [c.get("context") for c in (rule.get("parameters") or {}).get("required_status_checks") or []]
    return None


def delete_classic_protection(full: str) -> None:
    code, _ = gh("GET", f"repos/{full}/branches/main/protection")
    if code != 0:
        print(f"{full}: no classic branch protection")
        return
    code, resp = gh("DELETE", f"repos/{full}/branches/main/protection")
    # DELETE may return 204 empty
    log(full, "classic_branch_protection", "present", "deleted", "ruleset is the single protection path")


def enable_dependabot(full: str) -> None:
    code, _ = gh("GET", f"repos/{full}/vulnerability-alerts")
    if code == 0:
        print(f"{full}: Dependabot alerts already enabled")
        return
    code, resp = gh("PUT", f"repos/{full}/vulnerability-alerts")
    log(full, "dependabot_alerts", "disabled_or_unknown", "enabled" if code == 0 else resp, "security baseline")


def main() -> int:
    if "--apply" not in sys.argv:
        print("Refusing to mutate. Re-run with --apply after reviewing REPOS.", file=sys.stderr)
        return 2
    order = [
        "opsdevcode/.github",
        "opsdevcode/overpass",
        "opsdevcode/toll",
        "opsdevcode/dispatch",
        "opsdevcode/repave-aws-infra",
        "opsdevcode/repave",
        "opsdevcode/relay",
        "opsdevcode/opdevcode-website",
        "opsdevcode/convergence",
    ]
    for full in order:
        print(f"\n=== {full} ===")
        apply_repo_merge(full)
        apply_ruleset(full, REPOS[full])
        if REPOS[full].get("delete_classic_protection"):
            delete_classic_protection(full)
        enable_dependabot(full)
    Path = __import__("pathlib").Path
    out = Path("/tmp/opsdevcode-governance-mutations.json")
    out.write_text(json.dumps(MUTATIONS, indent=2), encoding="utf-8")
    print(f"\nWrote {out} ({len(MUTATIONS)} mutations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
