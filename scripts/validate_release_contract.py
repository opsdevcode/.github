#!/usr/bin/env python3
"""Validate opsdevcode.release/v0 contracts and org classification.

Expected failures return structured results. Messages name the field to change.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "opsdevcode.release/v0"
CLASSIFICATION_ID = "opsdevcode.release-classification/v0"
REPO_RE = re.compile(r"^opsdevcode/(\.github|[A-Za-z0-9._-]+)$")

PROFILES = frozenset(
    {
        "mint-language",
        "mint-platform",
        "mint-integration",
        "mint-internal",
        "product",
        "product-slice",
        "infra",
        "web",
        "docs",
        "org-meta",
        "generated",
        "side-oss",
    }
)
CANONICAL = frozenset({"github-release", "none"})
ENGINES = frozenset({"release-please", "python-semantic-release", "none"})
CHANNEL_ROLES = frozenset({"mirror", "deferred", "none"})
UNPUBLISHED_ROLES = frozenset({"deferred", "none"})
ARTIFACTS = frozenset(
    {"wheel", "sdist", "vsix", "sha256sums", "sbom", "image", "notes"}
)
ENFORCEMENT = frozenset({"adopted", "pending", "out-of-scope"})
COVERAGE = frozenset({"complete", "notes", "none", "historical-gap"})
GAP_STATUS = frozenset({"unproven", "accidental-1x", "leave-in-place"})
GAP_ACTION = frozenset({"do-not-synthesize", "leave-in-place"})
GITHUB_CANONICAL_PROFILES = frozenset(
    {
        "mint-language",
        "mint-platform",
        "mint-integration",
        "mint-internal",
        "product",
        "infra",
        "web",
    }
)
NONE_PROFILES = frozenset({"org-meta", "generated", "side-oss", "product-slice"})
ALLOWED_KEYS = frozenset(
    {
        "schema",
        "repository",
        "profile",
        "canonical",
        "engine",
        "tagPolicy",
        "prerelease",
        "downstream",
        "artifacts",
        "provenance",
        "notes",
    }
)


@dataclass(frozen=True)
class GateResult:
    passed: bool
    skipped: bool
    message: str


def _error(path: str, fix: str) -> str:
    return f"{path}: {fix}"


def _is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def validate_contract(data: Any, *, source: str = "contract") -> list[str]:
    if not _is_mapping(data):
        return [_error(source, "must be a JSON object")]

    errors: list[str] = []
    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        errors.append(
            _error(source, f"remove unknown keys {unknown}; allowed {sorted(ALLOWED_KEYS)}")
        )

    if data.get("schema") != SCHEMA_ID:
        errors.append(_error(f"{source}.schema", f"set to {SCHEMA_ID!r}"))

    repository = data.get("repository")
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        errors.append(
            _error(
                f"{source}.repository",
                "set to opsdevcode/<name> or opsdevcode/.github",
            )
        )

    profile = data.get("profile")
    if profile not in PROFILES:
        errors.append(
            _error(f"{source}.profile", f"set to one of {sorted(PROFILES)}")
        )

    canonical = data.get("canonical")
    if canonical not in CANONICAL:
        errors.append(
            _error(f"{source}.canonical", "set to 'github-release' or 'none'")
        )

    engine = data.get("engine")
    if engine not in ENGINES:
        errors.append(
            _error(
                f"{source}.engine",
                "set to 'release-please', 'python-semantic-release', or 'none'",
            )
        )

    errors.extend(_validate_tag_policy(data.get("tagPolicy"), source=source))
    errors.extend(_validate_prerelease(data.get("prerelease"), source=source))
    errors.extend(_validate_downstream(data.get("downstream"), source=source))
    errors.extend(_validate_artifacts(data.get("artifacts"), source=source))
    errors.extend(_validate_provenance(data.get("provenance"), source=source))

    if "notes" in data and not isinstance(data.get("notes"), str):
        errors.append(_error(f"{source}.notes", "set to a string or omit"))

    if errors:
        return errors

    assert isinstance(profile, str)
    assert isinstance(canonical, str)
    assert isinstance(engine, str)
    errors.extend(
        _validate_profile_invariants(
            profile=profile,
            canonical=canonical,
            engine=engine,
            downstream=data["downstream"],
            source=source,
        )
    )
    return errors


def _validate_tag_policy(value: Any, *, source: str) -> list[str]:
    path = f"{source}.tagPolicy"
    if not _is_mapping(value):
        return [_error(path, "set to an object with manualTags=false and retag=false")]
    errors: list[str] = []
    extra = sorted(set(value) - {"manualTags", "retag", "pattern"})
    if extra:
        errors.append(_error(path, f"remove unknown keys {extra}"))
    if value.get("manualTags") is not False:
        errors.append(_error(f"{path}.manualTags", "set to false; do not create tags by hand"))
    if value.get("retag") is not False:
        errors.append(_error(f"{path}.retag", "set to false; do not move published tags"))
    if "pattern" in value and (
        not isinstance(value.get("pattern"), str) or not value["pattern"]
    ):
        errors.append(_error(f"{path}.pattern", "set to a non-empty string or omit"))
    return errors


def _validate_prerelease(value: Any, *, source: str) -> list[str]:
    path = f"{source}.prerelease"
    if not _is_mapping(value):
        return [_error(path, "set to an object with githubMakeLatest=false")]
    errors: list[str] = []
    extra = sorted(set(value) - {"githubMakeLatest"})
    if extra:
        errors.append(_error(path, f"remove unknown keys {extra}"))
    if value.get("githubMakeLatest") is not False:
        errors.append(
            _error(
                f"{path}.githubMakeLatest",
                "set to false; never mark a prerelease as GitHub latest",
            )
        )
    return errors


def _validate_channel(value: Any, *, path: str, roles: frozenset[str]) -> list[str]:
    if not _is_mapping(value):
        return [_error(path, f"set to an object with role in {sorted(roles)}")]
    errors: list[str] = []
    extra = sorted(set(value) - {"role"})
    if extra:
        errors.append(_error(path, f"remove unknown keys {extra}"))
    if value.get("role") not in roles:
        errors.append(_error(f"{path}.role", f"set to one of {sorted(roles)}"))
    return errors


def _validate_downstream(value: Any, *, source: str) -> list[str]:
    path = f"{source}.downstream"
    if not _is_mapping(value):
        return [_error(path, "set pypi, ghcr, marketplace, openvsx, and pages")]
    errors: list[str] = []
    required = ("pypi", "ghcr", "marketplace", "openvsx", "pages")
    extra = sorted(set(value) - set(required))
    if extra:
        errors.append(_error(path, f"remove unknown keys {extra}"))
    missing = [key for key in required if key not in value]
    if missing:
        errors.append(_error(path, f"add missing channels {missing}"))
    errors.extend(
        _validate_channel(value.get("pypi"), path=f"{path}.pypi", roles=CHANNEL_ROLES)
    )
    errors.extend(
        _validate_channel(
            value.get("marketplace"),
            path=f"{path}.marketplace",
            roles=UNPUBLISHED_ROLES,
        )
    )
    errors.extend(
        _validate_channel(
            value.get("openvsx"), path=f"{path}.openvsx", roles=UNPUBLISHED_ROLES
        )
    )
    errors.extend(
        _validate_channel(value.get("pages"), path=f"{path}.pages", roles=CHANNEL_ROLES)
    )
    ghcr = value.get("ghcr")
    ghcr_path = f"{path}.ghcr"
    if not _is_mapping(ghcr):
        errors.append(
            _error(
                ghcr_path,
                "set to an object with role, latest=false, visibilityChange=false",
            )
        )
        return errors
    extra_ghcr = sorted(set(ghcr) - {"role", "latest", "visibilityChange"})
    if extra_ghcr:
        errors.append(_error(ghcr_path, f"remove unknown keys {extra_ghcr}"))
    if ghcr.get("role") not in CHANNEL_ROLES:
        errors.append(_error(f"{ghcr_path}.role", f"set to one of {sorted(CHANNEL_ROLES)}"))
    if ghcr.get("latest") is not False:
        errors.append(_error(f"{ghcr_path}.latest", "set to false; never publish :latest"))
    if ghcr.get("visibilityChange") is not False:
        errors.append(
            _error(
                f"{ghcr_path}.visibilityChange",
                "set to false; do not change GHCR package visibility here",
            )
        )
    return errors


def _validate_artifacts(value: Any, *, source: str) -> list[str]:
    path = f"{source}.artifacts"
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return [_error(path, f"set to a list of {sorted(ARTIFACTS)}")]
    errors: list[str] = []
    if len(value) != len(set(value)):
        errors.append(_error(path, "remove duplicate artifact names"))
    unknown = sorted(set(value) - ARTIFACTS)
    if unknown:
        errors.append(_error(path, f"remove unknown artifacts {unknown}"))
    return errors


def _validate_provenance(value: Any, *, source: str) -> list[str]:
    path = f"{source}.provenance"
    if not _is_mapping(value):
        return [_error(path, "set to an object with synthesize=false")]
    errors: list[str] = []
    extra = sorted(set(value) - {"synthesize"})
    if extra:
        errors.append(_error(path, f"remove unknown keys {extra}"))
    if value.get("synthesize") is not False:
        errors.append(
            _error(
                f"{path}.synthesize",
                "set to false; never invent provenance or retag to fill gaps",
            )
        )
    return errors


def _validate_profile_invariants(
    *,
    profile: str,
    canonical: str,
    engine: str,
    downstream: dict[str, Any],
    source: str,
) -> list[str]:
    errors: list[str] = []
    if profile in GITHUB_CANONICAL_PROFILES and canonical != "github-release":
        errors.append(
            _error(
                f"{source}.canonical",
                f"set to 'github-release' for profile {profile}",
            )
        )
    if profile in NONE_PROFILES and canonical != "none":
        errors.append(
            _error(f"{source}.canonical", f"set to 'none' for profile {profile}")
        )
    if canonical == "none" and engine != "none":
        errors.append(
            _error(f"{source}.engine", "set to 'none' when canonical is 'none'")
        )
    if profile == "mint-language" and downstream["pypi"].get("role") != "mirror":
        errors.append(
            _error(
                f"{source}.downstream.pypi.role",
                "set to 'mirror'; Mint language PyPI publishes the GitHub artifact bytes",
            )
        )
    if profile == "mint-integration" and downstream["pypi"].get("role") != "deferred":
        errors.append(
            _error(
                f"{source}.downstream.pypi.role",
                "set to 'deferred'; mint integration PyPI stays deferred",
            )
        )
    if profile == "mint-platform" and downstream["ghcr"].get("role") != "mirror":
        errors.append(
            _error(
                f"{source}.downstream.ghcr.role",
                "set to 'mirror'; GHCR is a GitHub Release mirror, visibility unchanged",
            )
        )
    if profile in {"mint-language", "mint-platform", "mint-integration"}:
        if engine != "release-please":
            errors.append(
                _error(
                    f"{source}.engine",
                    "set to 'release-please' for Mint family repos",
                )
            )
        if downstream["marketplace"].get("role") != "deferred":
            errors.append(
                _error(
                    f"{source}.downstream.marketplace.role",
                    "set to 'deferred'; do not publish Marketplace from this program",
                )
            )
        if downstream["openvsx"].get("role") != "deferred":
            errors.append(
                _error(
                    f"{source}.downstream.openvsx.role",
                    "set to 'deferred'; do not publish Open VSX from this program",
                )
            )
    return errors


def validate_classification(data: Any, *, source: str = "classification") -> list[str]:
    if not _is_mapping(data):
        return [_error(source, "must be a JSON object")]
    errors: list[str] = []
    allowed = {"schema", "organization", "canonicalChannel", "policy", "repos"}
    extra = sorted(set(data) - allowed)
    if extra:
        errors.append(_error(source, f"remove unknown keys {extra}"))
    if data.get("schema") != CLASSIFICATION_ID:
        errors.append(_error(f"{source}.schema", f"set to {CLASSIFICATION_ID!r}"))
    if data.get("organization") != "opsdevcode":
        errors.append(_error(f"{source}.organization", "set to 'opsdevcode'"))
    if data.get("canonicalChannel") != "github-release":
        errors.append(
            _error(
                f"{source}.canonicalChannel",
                "set to 'github-release'; downstream registries are mirrors",
            )
        )
    if data.get("policy") != "docs/github-releases.md":
        errors.append(_error(f"{source}.policy", "set to docs/github-releases.md"))
    repos = data.get("repos")
    if not isinstance(repos, list) or not repos:
        errors.append(_error(f"{source}.repos", "add at least one classified repository"))
        return errors

    seen: dict[str, int] = {}
    for index, row in enumerate(repos):
        row_path = f"{source}.repos[{index}]"
        errors.extend(_validate_classified_row(row, source=row_path, seen=seen, index=index))
    return errors


def _validate_classified_row(
    row: Any, *, source: str, seen: dict[str, int], index: int
) -> list[str]:
    if not _is_mapping(row):
        return [_error(source, "set to an object with contract, enforcementState, coverage")]
    errors: list[str] = []
    extra = sorted(set(row) - {"contract", "enforcementState", "coverage", "historicalGaps"})
    if extra:
        errors.append(_error(source, f"remove unknown keys {extra}"))
    errors.extend(validate_contract(row.get("contract"), source=f"{source}.contract"))
    if row.get("enforcementState") not in ENFORCEMENT:
        errors.append(
            _error(f"{source}.enforcementState", f"set to one of {sorted(ENFORCEMENT)}")
        )
    if row.get("coverage") not in COVERAGE:
        errors.append(_error(f"{source}.coverage", f"set to one of {sorted(COVERAGE)}"))
    gaps = row.get("historicalGaps", [])
    if "historicalGaps" in row and not isinstance(gaps, list):
        errors.append(_error(f"{source}.historicalGaps", "set to a list or omit"))
        gaps = []
    if row.get("coverage") == "historical-gap" and not gaps:
        errors.append(
            _error(
                f"{source}.historicalGaps",
                "record the unproven tag; do not synthesize a GitHub Release",
            )
        )
    for gap_index, gap in enumerate(gaps):
        gap_path = f"{source}.historicalGaps[{gap_index}]"
        if not _is_mapping(gap):
            errors.append(_error(gap_path, "set to {tag, status, action}"))
            continue
        extra_gap = sorted(set(gap) - {"tag", "status", "action"})
        if extra_gap:
            errors.append(_error(gap_path, f"remove unknown keys {extra_gap}"))
        if not isinstance(gap.get("tag"), str) or not gap["tag"]:
            errors.append(_error(f"{gap_path}.tag", "set to the existing git tag"))
        if gap.get("status") not in GAP_STATUS:
            errors.append(_error(f"{gap_path}.status", f"set to one of {sorted(GAP_STATUS)}"))
        if gap.get("action") not in GAP_ACTION:
            errors.append(_error(f"{gap_path}.action", f"set to one of {sorted(GAP_ACTION)}"))
        if gap.get("status") == "unproven" and gap.get("action") != "do-not-synthesize":
            errors.append(
                _error(
                    f"{gap_path}.action",
                    "set to 'do-not-synthesize' when tag/SHA/artifacts are unproven",
                )
            )
    contract = row.get("contract")
    if _is_mapping(contract) and isinstance(contract.get("repository"), str):
        name = contract["repository"]
        if name in seen:
            errors.append(
                _error(
                    f"{source}.contract.repository",
                    f"duplicate of repos[{seen[name]}]; keep one row per repository",
                )
            )
        else:
            seen[name] = index
    return errors


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing JSON file: set {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc.msg} at line {exc.lineno}") from exc


def validate_paths(
    *,
    contract: Path | None = None,
    classification: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if contract is not None:
        errors.extend(validate_contract(load_json(contract), source=str(contract)))
    if classification is not None:
        errors.extend(
            validate_classification(load_json(classification), source=str(classification))
        )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        help="path to opsdevcode-release.json",
    )
    parser.add_argument(
        "--classification",
        type=Path,
        help="path to profiles/releases.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.contract is None and args.classification is None:
        parser.error("set --contract and/or --classification")
    try:
        errors = validate_paths(
            contract=args.contract,
            classification=args.classification,
        )
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    print("validate-release-contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
