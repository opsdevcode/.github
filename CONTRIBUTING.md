# Contributing (OpsDevCode GitHub)

Normal path for every first-class repository:

1. Branch from `main`
2. Make a focused change
3. Run the repo’s local checks
4. Push the branch
5. Open a pull request
6. Required CI must pass
7. Resolve review conversations
8. Squash-merge
9. GitHub deletes the head branch

You should not need a different process per product. Differences are **profile
plus required check names**, not ad-hoc branch protection.

## Profiles

| Profile | Repos | Approvals (solo now) | Target |
| --- | --- | --- | --- |
| product | Repave, Overpass, Toll, Dispatch, Relay | 0 | 1 when a second maintainer exists |
| infra | `repave-aws-infra` | 0 | 1 |
| web | `opdevcode-website` | 0 | CODEOWNERS *request* reviews; review is not a merge deadlock |
| docs | Convergence | 0 | PR + CI |
| org-meta | `.github` | 0 | PR + `validate` |

Generated repos are **not** in this path. Do not copy these rules onto them.

## Merge

Squash only. Merge commits and rebase merges are disabled so one PR is one
mainline change. Auto-merge **capability** is on; do not enable auto-merge on
a PR unless you intend it.

## Bypass

No `RepositoryRole` admin `always` bypass. Direct pushes to `main` are not the
workflow.

Automation that previously pushed `main` (Repave Release changelog, infra
`DEPLOY_BUMP_TOKEN` image pins) must open a PR or use a **dedicated GitHub App**
installed on the org. GitHub Actions cannot be added as a ruleset bypass actor
in this org (API 422).

## Source of truth

[`GOVERNANCE.md`](GOVERNANCE.md) and [`profiles/`](profiles/).
