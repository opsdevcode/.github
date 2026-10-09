#!/usr/bin/env python3
"""Offline tests for opsdevcode.release/v0 contracts and classification."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_release_contract as release  # noqa: E402

SCHEMA = ROOT / "schemas" / "opsdevcode.release.v0.json"
CLASS_SCHEMA = ROOT / "schemas" / "opsdevcode.release-classification.v0.json"
CONTRACT = ROOT / "opsdevcode-release.json"
CLASSIFICATION = ROOT / "profiles" / "releases.json"

AUDITED_REPOS = frozenset(
    {
        "opsdevcode/.github",
        "opsdevcode/specmint-language",
        "opsdevcode/specmint-platform",
        "opsdevcode/mint-integration-template",
        "opsdevcode/mint-integration-local",
        "opsdevcode/mint-integration-github",
        "opsdevcode/specmint",
        "opsdevcode/repave",
        "opsdevcode/repave-operator",
        "opsdevcode/repave-cli",
        "opsdevcode/repave-corpus",
        "opsdevcode/repave-aws-infra",
        "opsdevcode/overpass",
        "opsdevcode/toll",
        "opsdevcode/dispatch",
        "opsdevcode/relay",
        "opsdevcode/opdevcode-website",
        "opsdevcode/convergence",
        "opsdevcode/helm-payments-api",
        "opsdevcode/checkov-policy-platform-baseline",
        "opsdevcode/opa-policy-platform-guardrails",
        "opsdevcode/tf-azure-aks",
        "opsdevcode/tfm-azure-eventgrid-test",
        "opsdevcode/azure-policy-test-test",
        "opsdevcode/tf-aws-eks-demo",
        "opsdevcode/tf-aws-eks",
        "opsdevcode/ansible-role-hardening",
        "opsdevcode/ansible-role-webserver",
        "opsdevcode/gitops-dev-payments-api",
        "opsdevcode/tf-azure-networking-demo",
        "opsdevcode/tf-aws-vpc-demo",
        "opsdevcode/cloudopt",
        "opsdevcode/knode",
        "opsdevcode/talentlayer",
        "opsdevcode/terraform-aws-eks-karpenter",
        "opsdevcode/atx",
        "opsdevcode/kubesnooze",
        "opsdevcode/term-dx",
        "opsdevcode/eks-addons",
        "opsdevcode/shownodes",
        "opsdevcode/cursor-rules",
    }
)


def _blank_downstream() -> dict:
    return {
        "pypi": {"role": "none"},
        "ghcr": {"role": "none", "latest": False, "visibilityChange": False},
        "marketplace": {"role": "none"},
        "openvsx": {"role": "none"},
        "pages": {"role": "none"},
    }


def _contract(**overrides: object) -> dict:
    data: dict = {
        "schema": "opsdevcode.release/v0",
        "repository": "opsdevcode/.github",
        "profile": "org-meta",
        "canonical": "none",
        "engine": "none",
        "tagPolicy": {"manualTags": False, "retag": False},
        "prerelease": {"githubMakeLatest": False},
        "downstream": _blank_downstream(),
        "artifacts": [],
        "provenance": {"synthesize": False},
    }
    data.update(overrides)
    return data


class SchemaFileTests(unittest.TestCase):
    def test_schema_files_parse_and_ids_match(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        classification = json.loads(CLASS_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "opsdevcode.release/v0")
        self.assertEqual(schema["properties"]["schema"]["const"], "opsdevcode.release/v0")
        self.assertEqual(classification["$id"], "opsdevcode.release-classification/v0")
        self.assertEqual(set(schema["properties"]["profile"]["enum"]), release.PROFILES)
        self.assertFalse(schema["properties"]["tagPolicy"]["properties"]["manualTags"]["const"])
        self.assertFalse(schema["properties"]["prerelease"]["properties"]["githubMakeLatest"]["const"])


class ContractTests(unittest.TestCase):
    def test_org_meta_contract_passes(self) -> None:
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(release.validate_contract(data), [])
        self.assertEqual(data["repository"], "opsdevcode/.github")
        self.assertEqual(data["canonical"], "none")

    def test_manual_tag_names_the_fix(self) -> None:
        data = _contract()
        data["tagPolicy"]["manualTags"] = True
        errors = release.validate_contract(data)
        self.assertTrue(any("manualTags" in item and "false" in item for item in errors))

    def test_latest_on_prerelease_names_the_fix(self) -> None:
        data = _contract()
        data["prerelease"]["githubMakeLatest"] = True
        errors = release.validate_contract(data)
        self.assertTrue(any("githubMakeLatest" in item for item in errors))

    def test_synthesize_provenance_names_the_fix(self) -> None:
        data = _contract()
        data["provenance"]["synthesize"] = True
        errors = release.validate_contract(data)
        self.assertTrue(any("synthesize" in item for item in errors))

    def test_ghcr_latest_and_visibility_change_refused(self) -> None:
        data = _contract()
        data["downstream"]["ghcr"]["latest"] = True
        data["downstream"]["ghcr"]["visibilityChange"] = True
        errors = release.validate_contract(data)
        self.assertTrue(any("ghcr.latest" in item for item in errors))
        self.assertTrue(any("visibilityChange" in item for item in errors))

    def test_marketplace_cannot_be_mirror(self) -> None:
        data = _contract()
        data["downstream"]["marketplace"]["role"] = "mirror"
        errors = release.validate_contract(data)
        self.assertTrue(any("marketplace.role" in item for item in errors))

    def test_mint_integration_requires_deferred_pypi(self) -> None:
        data = _contract(
            repository="opsdevcode/mint-integration-local",
            profile="mint-integration",
            canonical="github-release",
            engine="release-please",
            downstream={
                "pypi": {"role": "mirror"},
                "ghcr": {"role": "none", "latest": False, "visibilityChange": False},
                "marketplace": {"role": "deferred"},
                "openvsx": {"role": "deferred"},
                "pages": {"role": "none"},
            },
        )
        errors = release.validate_contract(data)
        self.assertTrue(any("pypi.role" in item and "deferred" in item for item in errors))

    def test_mint_language_requires_pypi_mirror(self) -> None:
        data = _contract(
            repository="opsdevcode/specmint-language",
            profile="mint-language",
            canonical="github-release",
            engine="release-please",
            artifacts=["wheel", "sdist", "vsix", "sha256sums", "sbom"],
            downstream={
                "pypi": {"role": "none"},
                "ghcr": {"role": "none", "latest": False, "visibilityChange": False},
                "marketplace": {"role": "deferred"},
                "openvsx": {"role": "deferred"},
                "pages": {"role": "mirror"},
            },
        )
        errors = release.validate_contract(data)
        self.assertTrue(any("pypi.role" in item and "mirror" in item for item in errors))


class ClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
        cls.errors = release.validate_classification(cls.data)

    def test_classification_passes(self) -> None:
        self.assertEqual(self.errors, [])

    def test_every_audited_repo_is_classified(self) -> None:
        names = {row["contract"]["repository"] for row in self.data["repos"]}
        self.assertEqual(names, AUDITED_REPOS)

    def test_github_is_canonical_channel(self) -> None:
        self.assertEqual(self.data["canonicalChannel"], "github-release")
        self.assertEqual(self.data["policy"], "docs/github-releases.md")

    def test_org_meta_adopted_and_mint_pending(self) -> None:
        rows = {row["contract"]["repository"]: row for row in self.data["repos"]}
        self.assertEqual(rows["opsdevcode/.github"]["enforcementState"], "adopted")
        self.assertEqual(rows["opsdevcode/specmint-language"]["enforcementState"], "pending")
        self.assertEqual(rows["opsdevcode/mint-integration-local"]["contract"]["profile"], "mint-integration")
        self.assertEqual(
            rows["opsdevcode/mint-integration-local"]["contract"]["downstream"]["pypi"]["role"],
            "deferred",
        )

    def test_repave_historical_gap_is_not_synthesized(self) -> None:
        rows = {row["contract"]["repository"]: row for row in self.data["repos"]}
        repave = rows["opsdevcode/repave"]
        self.assertEqual(repave["coverage"], "historical-gap")
        gaps = repave["historicalGaps"]
        self.assertEqual(gaps[0]["tag"], "v2.48.0-rc.1")
        self.assertEqual(gaps[0]["action"], "do-not-synthesize")

    def test_accidental_1x_tags_left_in_place(self) -> None:
        rows = {row["contract"]["repository"]: row for row in self.data["repos"]}
        for name in ("opsdevcode/specmint-language", "opsdevcode/specmint-platform"):
            tags = {gap["tag"] for gap in rows[name]["historicalGaps"]}
            self.assertIn("v1.0.0-alpha.1", tags)
            for gap in rows[name]["historicalGaps"]:
                self.assertEqual(gap["action"], "leave-in-place")

    def test_generated_and_side_oss_are_out_of_scope(self) -> None:
        rows = {row["contract"]["repository"]: row for row in self.data["repos"]}
        self.assertEqual(rows["opsdevcode/tf-aws-eks"]["enforcementState"], "out-of-scope")
        self.assertEqual(rows["opsdevcode/kubesnooze"]["contract"]["profile"], "side-oss")
        self.assertEqual(rows["opsdevcode/kubesnooze"]["contract"]["canonical"], "none")

    def test_unproven_gap_without_do_not_synthesize_fails(self) -> None:
        data = deepcopy(self.data)
        data["repos"][0]["coverage"] = "historical-gap"
        data["repos"][0]["historicalGaps"] = [
            {"tag": "v0.0.0", "status": "unproven", "action": "leave-in-place"}
        ]
        errors = release.validate_classification(data)
        self.assertTrue(any("do-not-synthesize" in item for item in errors))


class ScriptTests(unittest.TestCase):
    def test_cli_accepts_org_files(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_release_contract.py"),
                "--contract",
                str(CONTRACT),
                "--classification",
                str(CLASSIFICATION),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("OK", completed.stdout)

    def test_cli_names_missing_path(self) -> None:
        missing = ROOT / "missing-opsdevcode-release.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_release_contract.py"),
                "--contract",
                str(missing),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(str(missing), completed.stderr)


class PolicyDocTests(unittest.TestCase):
    def test_policy_files_exist_and_forbid_manual_tags(self) -> None:
        policy = (ROOT / "docs" / "github-releases.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Releases are the organization release record", policy)
        self.assertIn("No manual tags", policy)
        self.assertIn("Mint integration PyPI stays deferred", policy)
        adoption = (ROOT / "docs" / "github-release-adoption.md").read_text(encoding="utf-8")
        self.assertIn("opsdevcode-release.json", adoption)
        self.assertIn("validate-release-contract.yml@main", adoption)


if __name__ == "__main__":
    unittest.main()
