# Repository governance

Engineering source of truth for how OpsDevCode GitHub repositories are
classified and what controls they are **supposed** to have.

This repository (`opsdevcode/.github`) owns the model. Product repos do not.
Nothing here enables rulesets, security features, or visibility changes.
`scripts/audit-github-governance.sh` is **read-only**.

## Purpose

Answer, for any repo:

1. Which profile applies?
2. Which controls are required?
3. Which controls are not migrated yet (`NOT_YET_ENFORCED`)?
4. Which controls drifted after adoption (`DRIFT`)?
5. Which exceptions are recorded?

## Repository profiles

| Profile | File | Applies to |
| --- | --- | --- |
| product | `profiles/product.json` | Repave, Overpass, Toll, Dispatch, Relay |
| infra | `profiles/infra.json` | `repave-aws-infra` |
| web | `profiles/web.json` | `opdevcode-website` |
| docs | `profiles/docs.json` | Convergence |
| org-meta | `profiles/org-meta.json` | this repo |
| generated | `profiles/generated.json` | Repave-emitted bootstrap/demo modules |

Mapping: `profiles/repos.json`. Unmapped org repos are **UNCLASSIFIED** (never
silently treated as product or generated).

Generated repos are **not** audited by default. Optional:
`./scripts/audit-github-governance.sh --include-generated`.

Do not classify side OSS (`kubesnooze`, `cursor-rules`, …) as generated.

Domain-specific CI stays in the product repo (Repave chart smoke, operator
tests, Backstage audit, language CodeQL, integration suites). Governance
standardizes the baseline only.

## Visibility policy

| Visibility | Repositories |
| --- | --- |
| private | Repave, Overpass, Toll, Dispatch, Relay, `repave-aws-infra` |
| public | `opdevcode-website`, Convergence, `.github` |
| private by default | generated (profile `generated`) |

Intent:

- Public source is **not** required for product GTM.
- Commercial runtime/source stays private (Relay included: internal service).
- Convergence stays public as a body of knowledge.
- Company website may stay public.
- `.github` stays public (org profile / community files).
- Existing public generated examples may need a later review; they are not
  automatically commercial products.

Matching this table is **policy**, not drift.

## Branch / ruleset policy

Target on the default branch (`main`):

- pull request required
- force push denied
- branch deletion denied
- conversation resolution required
- required CI checks
- no unconditional admin bypass

This file does **not** create rulesets.

## Review / approval policy

| Profile | Target |
| --- | --- |
| infra | 1 approval |
| product | target 1 approval |
| web | 1 approval and/or CODEOWNERS when maintainers exist |
| docs / org-meta | PR required; 0 approvals acceptable |

Solo-operator **temporary** `0` approval is allowed **only** when all of:

- required CI exists
- direct push to default branch remains blocked
- admin bypass is **not** `always`
- the exception is recorded on the repo mapping

## Bypass policy

Avoid `RepositoryRole` admin bypass = `always`.

Preferred: no bypass. If required: explicit actor, pull-request bypass only,
narrow emergency scope.

Current always-on admin bypass (Repave, Convergence, satellites) and
user-specific bypass (Relay) is **debt**, not the standard. Not changed here.

## Required checks and CI naming

New workflows use:

- `quality`, `test`, `security`
- optional: `build`, `integration`, `release-check`

**Do not rename existing Repave required checks** until a dedicated
workflow+ruleset migration (dual-name / staged). Legacy protected names stay
authoritative until that slice.

`required_checks: any` means “at least one required status check”, not a
fixed job list. Product-specific jobs remain local.

## Security baseline

Required (when the GitHub plan exposes the control):

- secret scanning
- push protection
- Dependabot alerts
- default workflow `permissions: contents: read`

Recommended for product repos: dependency-review.

CodeQL: only where Advanced Security / repo capability supports it. Do not
require it where it cannot run.

Org “GitHub recommended” configuration may exist **unenforced**. Org **2FA**
may be off. Those are **ORG SECURITY GAP** items, not repository `DRIFT`.
Do not enable them from this repo.

## Release / CD ownership

Every product owns an independent release lifecycle, even on shared infra.

Product repo owns: source, tests, artifact/container build, publish, immutable
release identity, deployment **trigger**.

Infra repo owns: cluster, namespace, runtime manifests, ingress, secret
plumbing, infrastructure resources.

A Repave release deploys Repave only. An Overpass release deploys Overpass
only. Future Toll/Dispatch the same. No family-wide deploy train.

Transitional (not fixed here): Toll/Dispatch publish without a complete
deploy owner; Relay is not yet the hosted runtime.

## Immutable release policy

Production uses immutable identity: full git SHA tag and/or digest.

`:latest` may exist for browsing. It must not be the production pin.
Do not remove current `:latest` publishing in this slice.

## Drift detection and adoption state

The checker is advisory until a control is **adopted**. First-class mapped
repos are `enforcement_state: adopted` for the evaluated baseline (ruleset
or branch protection, required checks, secret scanning, push protection,
Dependabot alerts). Disabling those is `DRIFT` (audit exit 1).

| Status | Meaning |
| --- | --- |
| `COMPLIANT` | Evaluable controls match the profile |
| `PARTIAL` | Matches where known; some controls `UNKNOWN` |
| `NOT_YET_ENFORCED` | Profile assigned; migration not started (`enforcement_state: pending`) |
| `DRIFT` | `enforcement_state: adopted` and live state diverged |
| `EXCEPTION` | Documented temporary deviation |
| `UNCLASSIFIED` | No mapping |
| `ERROR` | Audit/API failure |

`UNKNOWN` is **not** compliant. It is reported per control. During `pending`
it does not fail the run.

Optional `adopted_controls` on a mapping row marks individual controls as
adopted while the repo stays `enforcement_state: pending`. A mismatch on an
adopted control is `DRIFT`. Remaining profile controls stay
`NOT_YET_ENFORCED`. Do not set whole-repo `adopted` until secret scanning,
push protection, and Dependabot match the profile.

## Exceptions (current debt, not the standard)

Recorded on `profiles/repos.json`; not remediated here.

- Repave: legacy required-check names; admin bypass `always` (Release admin
  merge); solo `0` approvals
- Overpass / Toll / Dispatch / Relay / infra / Convergence / `.github`:
  temporary solo `0` approvals
- Website: CODEOWNERS plus 1 approval with explicit `erskaggs` review bypass;
  admins are enforced
- Infra: ARC cluster-admin on deploy runners (separate P1; not GitHub rulesets)

## Reusable workflows

Not in this slice. Later, small callables only: Python quality, Python tests,
commitlint, optional container publish. No internal CI framework.

## Migration strategy

1. Foundation (profiles + read-only audit) — done
2. Minimal rulesets: Overpass, Toll, Dispatch, `repave-aws-infra` — done
3. Secret scanning, push protection, Dependabot alerts on **product** repos — done
4. Remaining first-class repos (infra/web/docs/org-meta) security + `.github`
   ruleset; infra required check is Pulumi job `check` (not a compile-only
   GitHub Action)
5. Lightweight reusable CI for thin products — optional later
6. Optional Repave check-name transition — optional later
7. Generated-repo governance — opt-in audit only
8. Org 2FA and org code-security configuration attach/enforce — **blocked**
   without owner UI / security-admin API rights (still `ORG SECURITY GAP`)
9. `GOVERNANCE_AUDIT_TOKEN` on `.github` for scheduled live audit

Do not remove Repave `RepositoryRole` admin bypass `always` until Release is
proven to merge without it.

## Audit

```bash
./scripts/audit-github-governance.sh
./scripts/audit-github-governance.sh --offline
./scripts/audit-github-governance.sh --json
```

Exit codes:

- `0` — no `DRIFT` and no `ERROR` (`NOT_YET_ENFORCED` / `EXCEPTION` / `PARTIAL` do not fail)
- `1` — one or more adopted-policy `DRIFT`
- `2` — tool/API/`ERROR` failure

GET-only `gh api`. No settings mutation.
