# First-class governance mutations (2026-09-07)

Live GitHub settings. Not generated-repo work.

## Merge ergonomics (all nine first-class repos)

| Setting | Before (typical) | After |
| --- | --- | --- |
| squash | true | true |
| merge commit | true | false |
| rebase | true | false |
| delete_branch_on_merge | false (Repave already true) | true |
| allow_auto_merge | false | true (capability only) |

Reason: one PR process — squash, then delete the branch.

## Rulesets

Updated in place (`main branch`) except website (created `opsdevcode-main`).

Common PR rule:

- approvals: 0 (solo-operable)
- conversation resolution: true
- dismiss stale reviews: true
- code owners required: false
- allowed merge methods: squash
- force push blocked (`non_fast_forward`)
- branch deletion blocked

Bypass: empty on all nine. Removed Repave `RepositoryRole` admin `always`.

Required checks unchanged except website `version` now via ruleset.

## Classic branch protection

| Repo | Action |
| --- | --- |
| `opdevcode-website` | deleted after ruleset create (had 1 approval + CODEOWNERS + user bypass) |
| `repave` | deleted leftover classic protection (ruleset is the gate) |

## GitHub Actions integration bypass

Attempted `actor_id` 15368 (`Integration`) on infra. GitHub returned 422:
actor must belong to the ruleset source/org. **UNSUPPORTED** here. Recorded as
debt: Release / `DEPLOY_BUMP_TOKEN` must PR or use an org-installed App.

## Security

Secret scanning, push protection, Dependabot alerts: already enabled on all
nine. No visibility changes.
