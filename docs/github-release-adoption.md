# Adopt `opsdevcode.release/v0`

Org source of truth: this repository. Product repos copy a contract and call
the reusable validator after this file exists on `opsdevcode/.github@main`.

## Contract

Add `opsdevcode-release.json` at the repository root. Copy the matching
`contract` object from [`profiles/releases.json`](../profiles/releases.json).
Do not weaken invariants (`manualTags`, `retag`, `githubMakeLatest`,
`provenance.synthesize`, GHCR `latest` / `visibilityChange`).

Validate locally:

```bash
python3 /path/to/opsdevcode/.github/scripts/validate_release_contract.py \
  --contract opsdevcode-release.json
```

## CI

After the reusable workflow is on `main`:

```yaml
jobs:
  release-check:
    uses: opsdevcode/.github/.github/workflows/validate-release-contract.yml@main
```

Until then, product repos may copy the workflow file the same way they copied
Conventional Commits.

## Engines

Keep the engine the repo already uses. Do not swap Release Please and
python-semantic-release in an adoption PR. Do not add a second tagger.

| Profile | Engine | Canonical |
| --- | --- | --- |
| mint-language / mint-platform / mint-integration | release-please | GitHub Release |
| product / infra / mint-internal | python-semantic-release | GitHub Release |
| web | release-please | GitHub Release |
| org-meta / product-slice / generated / side-oss | none | none |

## Merge

Squash-merge when required checks are green. Tags come from the release
engine after merge, never from the adoption PR.
