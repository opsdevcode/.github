# opsdevcode/.github

The organization Overview README lives in [`profile/README.md`](profile/README.md).

Company and product-portfolio semantics: [`portfolio/README.md`](portfolio/README.md)
([`portfolio/products.json`](portfolio/products.json),
[`portfolio/public-content.md`](portfolio/public-content.md),
[`portfolio/visual-family.md`](portfolio/visual-family.md)).

Visual family grammar: [`brand/README.md`](brand/README.md).

Repository governance (engineering, not the org Overview): [`GOVERNANCE.md`](GOVERNANCE.md),
[`CONTRIBUTING.md`](CONTRIBUTING.md),
[`docs/engineering-foundations.md`](docs/engineering-foundations.md),
[`docs/github-releases.md`](docs/github-releases.md),
[`SECURITY.md`](SECURITY.md).

Org-wide pull request template: [`PULL_REQUEST_TEMPLATE.md`](PULL_REQUEST_TEMPLATE.md)
(used when a repo has no template of its own).

```bash
./scripts/audit-github-governance.sh
./scripts/audit-github-governance.sh --offline
tests/validate-governance.sh
python3 scripts/validate_release_contract.py --contract opsdevcode-release.json --classification profiles/releases.json
```
