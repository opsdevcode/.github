# DNS architecture — mint.opsdevco.de

Org record of how Mint language docs are named. This repository does **not**
contain Pulumi programs, Terraform, or Route53 apply scripts. Live DNS is
owned by Pulumi in `opsdevcode/repave-aws-infra`. This file does **not**
authorize `pulumi up`. Do not purchase `mintlang.dev`. Do not use the
Route53 console.

## HOSTING_DECISION

GitHub Pages from `opsdevcode/specmint-language` (Actions static site).
Commercial funnel stays `https://opsdevco.de/products/mint` on the company
Netlify site. Mint is not a fifth SKU.

Fallback until the custom hostname returns anonymous HTTP 200:
`https://opsdevcode.github.io/specmint-language/`.

## Pulumi implementation intent (`repave-aws-infra`)

Bind to the **existing** public hosted zone `opsdevco.de` (Route53 nameservers
already `awsdns-*`). Do not create a new zone. Do not ALIAS or A/AAAA this
name onto CloudFront, Netlify, or a Repave origin.

| Field | Value |
| --- | --- |
| Stack / repo | Pulumi in `opsdevcode/repave-aws-infra` |
| Zone | existing public `opsdevco.de` |
| Record name | `mint` (FQDN `mint.opsdevco.de`) |
| Type | `CNAME` |
| TTL | `300` |
| Target | `opsdevcode.github.io` |

That CNAME is the entire DNS change for this hostname. GitHub Pages
requires the GitHub Pages hostname as the CNAME target so it can issue
the custom-domain certificate.

After Pages custom-domain setup, GitHub may display a TXT challenge at
`_github-pages-challenge-opsdevcode.mint.opsdevco.de`. Add that TXT in
the same Pulumi zone **only** when GitHub shows the token. Do not invent
a challenge value.

HTTPS: GitHub Pages already enforces HTTPS on the project site.
Custom-domain certificates are issued by GitHub after the CNAME answers.

## What this org repo must not contain

- Pulumi Python/TypeScript/YAML
- Terraform HCL
- `pulumi up` / `pulumi preview` wrappers
- AWS credentials or zone IDs

## OWNER_ACTION_REQUIRED

1. Merge the `specmint-language` Pages PR (CNAME file in the published `site/`).
2. In `opsdevcode/specmint-language` Settings → Pages: custom domain
   `mint.opsdevco.de`, wait for DNS check, enable Enforce HTTPS.
3. In `repave-aws-infra`, add the Pulumi `aws.route53.Record` that matches
   the table above, then `pulumi up` **only after explicit owner
   authorization**. This document does not authorize apply.
4. Do not merge DNS apply from an agent. Do not tag.

## Probe after apply (owner)

Anonymous `GET https://mint.opsdevco.de/` must return HTTP 200 before README
and company-site links switch off the `github.io` fallback.
