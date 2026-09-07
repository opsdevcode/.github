#!/usr/bin/env python3
"""Offline tests for governance profiles and classification."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import github_governance_audit as audit  # noqa: E402


class ProfileTests(unittest.TestCase):
    def test_json_parses_and_profiles_exist(self) -> None:
        profiles = audit.load_profiles()
        mapping = audit.load_repos()
        errors = audit.validate_mapping(profiles, mapping)
        self.assertEqual(errors, [])
        required = {
            "opsdevcode/repave",
            "opsdevcode/overpass",
            "opsdevcode/toll",
            "opsdevcode/dispatch",
            "opsdevcode/relay",
            "opsdevcode/repave-aws-infra",
            "opsdevcode/opdevcode-website",
            "opsdevcode/convergence",
            "opsdevcode/.github",
        }
        names = {row["repo"] for row in mapping["repos"]}
        self.assertTrue(required <= names)

    def test_no_duplicate_repos(self) -> None:
        mapping = audit.load_repos()
        names = [row["repo"] for row in mapping["repos"]]
        self.assertEqual(len(names), len(set(names)))

    def test_unknown_profile_fails_validation(self) -> None:
        profiles = audit.load_profiles()
        mapping = {
            "repos": [
                {
                    "repo": "opsdevcode/example",
                    "profile": "not-a-profile",
                    "enforcement_state": "pending",
                }
            ]
        }
        errors = audit.validate_mapping(profiles, mapping)
        self.assertTrue(any("unknown profile" in e for e in errors))


class ClassificationTests(unittest.TestCase):
    def test_pending_mismatch_is_not_yet_enforced(self) -> None:
        self.assertEqual(
            audit.classify_control(
                expected="present", actual="absent", enforcement_state="pending"
            ),
            "NOT_YET_ENFORCED",
        )

    def test_adopted_mismatch_is_drift(self) -> None:
        self.assertEqual(
            audit.classify_control(
                expected="present", actual="absent", enforcement_state="adopted"
            ),
            "DRIFT",
        )

    def test_evaluate_pending_missing_ruleset(self) -> None:
        profile = audit.load_profiles()["product"]
        assignment = {
            "repo": "opsdevcode/overpass",
            "profile": "product",
            "enforcement_state": "pending",
        }
        live = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "gate": "no",
            "checks": "no",
            "secret_scan": "no",
            "push_protection": "no",
            "dependabot": "no",
        }
        judged = audit.evaluate_repo(profile, assignment, live)
        self.assertEqual(judged["status"], "NOT_YET_ENFORCED")
        classes = {f["control"]: f["classification"] for f in judged["findings"]}
        self.assertEqual(classes["visibility"], "COMPLIANT")
        self.assertEqual(classes["ruleset_or_branch_protection"], "NOT_YET_ENFORCED")

    def test_evaluate_adopted_missing_ruleset_is_drift(self) -> None:
        profile = audit.load_profiles()["product"]
        assignment = {
            "repo": "opsdevcode/overpass",
            "profile": "product",
            "enforcement_state": "adopted",
        }
        live = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "gate": "no",
            "checks": "yes",
            "secret_scan": "yes",
            "push_protection": "yes",
            "dependabot": "yes",
        }
        judged = audit.evaluate_repo(profile, assignment, live)
        self.assertEqual(judged["status"], "DRIFT")

    def test_partial_adopted_controls_drift_only_those_controls(self) -> None:
        profile = audit.load_profiles()["product"]
        assignment = {
            "repo": "opsdevcode/overpass",
            "profile": "product",
            "enforcement_state": "pending",
            "adopted_controls": ["ruleset_or_branch_protection", "required_checks"],
        }
        live = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "gate": "no",
            "checks": "yes",
            "secret_scan": "no",
            "push_protection": "no",
            "dependabot": "no",
        }
        judged = audit.evaluate_repo(profile, assignment, live)
        classes = {f["control"]: f["classification"] for f in judged["findings"]}
        self.assertEqual(classes["ruleset_or_branch_protection"], "DRIFT")
        self.assertEqual(classes["required_checks"], "COMPLIANT")
        self.assertEqual(classes["secret_scanning"], "NOT_YET_ENFORCED")
        self.assertEqual(judged["status"], "DRIFT")

    def test_partial_adopted_controls_compliant_gate_still_pending_security(
        self,
    ) -> None:
        profile = audit.load_profiles()["product"]
        assignment = {
            "repo": "opsdevcode/overpass",
            "profile": "product",
            "enforcement_state": "pending",
            "adopted_controls": ["ruleset_or_branch_protection", "required_checks"],
        }
        live = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "gate": "yes",
            "checks": "yes",
            "secret_scan": "no",
            "push_protection": "no",
            "dependabot": "no",
        }
        judged = audit.evaluate_repo(profile, assignment, live)
        classes = {f["control"]: f["classification"] for f in judged["findings"]}
        self.assertEqual(classes["ruleset_or_branch_protection"], "COMPLIANT")
        self.assertEqual(classes["required_checks"], "COMPLIANT")
        self.assertEqual(classes["secret_scanning"], "NOT_YET_ENFORCED")
        self.assertEqual(judged["status"], "NOT_YET_ENFORCED")


    def test_evaluate_adopted_product_baseline_compliant(self) -> None:
        profile = audit.load_profiles()["product"]
        assignment = {
            "repo": "opsdevcode/overpass",
            "profile": "product",
            "enforcement_state": "adopted",
        }
        live = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "gate": "yes",
            "checks": "yes",
            "secret_scan": "yes",
            "push_protection": "yes",
            "dependabot": "yes",
        }
        judged = audit.evaluate_repo(profile, assignment, live)
        self.assertEqual(judged["status"], "COMPLIANT")


class ScriptSafetyTests(unittest.TestCase):
    def test_shell_syntax(self) -> None:
        script = ROOT / "scripts" / "audit-github-governance.sh"
        subprocess.run(["bash", "-n", str(script)], check=True)

    def test_no_mutation_commands(self) -> None:
        paths = [
            ROOT / "scripts" / "audit-github-governance.sh",
            ROOT / "scripts" / "github_governance_audit.py",
        ]
        needles = (
            "-X POST",
            "-X PUT",
            "-X PATCH",
            "-X DELETE",
            "--method POST",
            "--method PUT",
            "--method PATCH",
            "--method DELETE",
            "gh repo edit",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for needle in needles:
                self.assertNotIn(needle, text, msg=f"{path} contains {needle}")


class FoundationFilesTests(unittest.TestCase):
    def test_required_company_files_exist(self) -> None:
        for rel in (
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODEOWNERS",
            "docs/engineering-foundations.md",
        ):
            self.assertTrue((ROOT / rel).is_file(), msg=rel)

    def test_contributing_forbids_tool_vendor_authorship(self) -> None:
        text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("Tool-vendor or AI authorship footers are not used", text)
        self.assertIn("security@opsdevcode.com", text)


if __name__ == "__main__":
    unittest.main()
