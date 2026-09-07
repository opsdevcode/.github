# Company engineering foundations

How OpsDevCode operates as one engineering organization. Not a product
roadmap. Not Convergence.

Canonical contribution path: [`CONTRIBUTING.md`](../CONTRIBUTING.md).
GitHub controls: [`GOVERNANCE.md`](../GOVERNANCE.md).

## First-class repositories

`opsdevcode/.github`, `repave`, `overpass`, `toll`, `dispatch`, `relay`,
`repave-aws-infra`, `opdevcode-website`, `convergence`.

Generated / goldpath repos are **not** first-class company repos.

## CI vocabulary

**New** workflows should name jobs:

- `quality`
- `test`
- `security`

Optional: `build`, `integration`, `release-check`.

Do **not** rename existing Repave required checks until a dedicated
workflow+ruleset migration. New repos use the vocabulary above. Existing repos
migrate gradually. Required ruleset checks must name jobs that actually exist.

## Release / versioning

Do not force one release engine.

| Repo | Engine | Production identity |
| --- | --- | --- |
| Repave | python-semantic-release | Engine tags; infra pins chart/image SHA |
| Overpass | merge-to-main image publish | `ghcr.io/opsdevcode/overpass:<git-sha>` |
| Company site | release-please | Netlify production from `main` |
| Relay | existing release workflow | Internal; not a public SKU |

Company invariants:

- Production artifacts are immutable
- Production deployments use full SHA or digest
- `:latest` is never production source of truth
- Product repos build, test, publish, and **dispatch**
- Infra repo **deploys** production
- Conventional commits on first-class repos

## Deployment authority

Product repo: build, test, publish, dispatch release.

Infra (`repave-aws-infra`): cluster, namespaces, runtime manifests, ingress,
secret plumbing. No product workflow runs broad production Terraform/Pulumi
against the cluster.

Toll and Dispatch identity surfaces are **not** independently deployed
production runtimes until they satisfy the production-readiness checklist.

## GitHub Environments

Named environments are for **actual** hosted runtimes (for example
`repave-production`, `overpass-production` when Overpass is customer-critical).

Do not create fake production environments for Toll/Dispatch while they remain
identity or transitional. Do not require environment reviewers that deadlock
solo operation.

## Secret handling

- No secrets in git, READMEs, or examples
- Narrow, rotatable tokens
- Production secrets live in AWS Secrets Manager (cluster) via External Secrets
  Operator, plus GitHub Actions secrets for CI/dispatch only
- Product owns product-specific secret **names**
- Shared secret only for genuinely shared infrastructure (example:
  `INFRA_DEPLOY_TOKEN` dispatching to infra)
- Local developer secrets stay in ignored `.env` files copied from examples
- Auth0 and GHCR credentials are infra/product-owned as documented in the
  owning repo; do not copy them into sibling repos

## Backup / recovery

Do not invent backup programs for services that do not own customer state.

| State | Owner | Notes |
| --- | --- | --- |
| Repave Postgres | Repave + infra | See Repave `docs/operations/postgres-backup-restore.md` |
| Overpass hosted state | Overpass + infra | Customer-critical only after restore is rehearsed |
| Toll FOCUS tables (today) | Repave durability (transitional) | Not independently protected Toll state |
| Dispatch | none (no domain DB) | — |
| Company site | Netlify / git | Static; restore = redeploy `main` |

Document data owner, mechanism, RPO/RTO, and restore verification in the
**owning** runtime repo. No separate backup platform.

## Production-readiness (hosted runtime)

A runtime may claim production readiness only if it has:

- clear owner
- health endpoint
- readiness semantics
- immutable release identity
- deployment owner (infra)
- secret ownership
- persistence ownership
- backup expectation if stateful
- logging
- basic metrics where justified
- runbook pointer
- rollback procedure
- no sibling DB coupling
- no sibling implementation imports

Checklist, not a committee. Toll/Dispatch are **not** marked ready until they
satisfy this.

## Observability

No custom telemetry store. For production runtimes: structured logs,
health/readiness, request/error visibility, deployment/release identity,
service-level metrics where justified. Use existing cluster tooling.

## Incident ownership

Founder-led. No artificial on-call rotation.

Current operational owner: **OpsDevCode** (maintainers of the owning runtime
repo). Escalation: GitHub Security Advisories or `security@opsdevcode.com` for
security; product issues via the owning repository.

Customer-impacting incidents should be recorded in the owning repo (issue or
ops note). Team handles replace an individual when they exist.

Runbooks live in the runtime repo (`docs/operations/` on Repave).

## ADR standard

Required for durable decisions on product boundaries, persistence, APIs,
security, deployment architecture, major capability contracts, irreversible
infra.

| Kind | Location |
| --- | --- |
| Product domain | `docs/adr/` in that product repo |
| Org GitHub / governance | this repository |
| Convergence methodology | Convergence RFCs — **not** OpsDevCode ADRs |

## Generated repositories

Repave-emitted goldpath/bootstrap repos must **not** automatically inherit
every first-class requirement (CODEOWNERS teams, product rulesets, org PR
theater).

GitHub may still inherit org community files (`CONTRIBUTING`, `SECURITY`) from
this repository when a generated repo has no override. That inheritance is
acceptable. Do not copy first-class rulesets onto generated repos.

## New first-class repository baseline

Start with:

- README (name, one-sentence role, maturity, ownership, docs pointer, local
  test pointer, link to this CONTRIBUTING)
- LICENSE decision (do not invent a legal entity)
- SECURITY pointer (this file or identical reporting address)
- CODEOWNERS (`@erskaggs` until teams exist; do not require code-owner review
  while approvals are 0)
- CI with `permissions: contents: read` by default
- Actions pinned to SHAs from `opsdevcode/repave` `.github/action-pins.json`
  (single pin registry — do not fork a second JSON)
- Dependabot for ecosystems the repo actually uses
- Profile assignment in `profiles/repos.json`
- PR + ruleset baseline from [`GOVERNANCE.md`](../GOVERNANCE.md)
- Architecture/docs pointer

No Cursor/tool authorship, no generic AI boilerplate, no copied Repave product
identity, no unprotected `main`, no write-all workflow permissions.

Prefer org community files plus this checklist. Do not build a new repository
generator unless Repave already provides the correct mechanism.
