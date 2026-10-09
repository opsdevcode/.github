# GitHub Releases are canonical

GitHub Releases are the organization release record. Downstream registries
are mirrors of those releases. Do not rewrite published history.

This file is policy. Schema: [`schemas/opsdevcode.release.v0.json`](../schemas/opsdevcode.release.v0.json)
(`opsdevcode.release/v0`). Classification:
[`profiles/releases.json`](../profiles/releases.json). Adoption:
[`github-release-adoption.md`](github-release-adoption.md).

## Rules

1. **Canonical channel is GitHub Releases.** PyPI, GHCR, Marketplace, Open VSX,
   and Pages are mirrors or deferred. They must not invent a version that
   GitHub does not already have.
2. **No manual tags.** Release Please or python-semantic-release creates the
   tag after a green squash-merge. Do not `git tag` or `gh release create`.
3. **No retag.** Published tags stay on the SHA that created them.
4. **No fake provenance.** Repair a historical gap only when the tag, SHA, and
   artifacts are proven. Unproven tags stay recorded as gaps.
5. **No `latest` on prereleases.** GitHub `make_latest` stays false on
   prereleases. GHCR `:latest` is never a production pin and is never published
   for alpha/prerelease images.
6. **No GHCR visibility change** from this program.
7. **No Marketplace / Open VSX** from this program.
8. **No `mint apply`.**
9. **Mint integration PyPI stays deferred.** Mint language PyPI remains a
   mirror of the GitHub Release artifact bytes.

## Ownership

Each repository owns its engine, artifacts, and deploy trigger. There is no
family-wide release train. Infra deploys; product repos publish.

## Historical gaps

A git tag without a GitHub Release is a gap, not a license to mint a release.
Record it on the classification row. Do not synthesize assets, attestations,
or a GitHub Release for an unproven tag.

Accidental `v1.0.0-alpha.1` tags stay in place. Do not retag them onto a later
SHA and do not treat them as a 1.0 claim.
