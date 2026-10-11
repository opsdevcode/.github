# DNS architecture — mint.opsdevco.de

Org record of how Mint language docs are named. This repository does **not**
contain Pulumi programs, Terraform, or Route53 apply scripts. Live DNS is
owned by Pulumi in `opsdevcode/repave-aws-infra` stack `domains`. This file
does **not** authorize `pulumi up`. Do not use the Route53 console.

## HOSTING_DECISION

Content: static site from `opsdevcode/specmint-language` (`scripts/build_docs_site.py`).
No second compiler. No Pages reverse proxy.

Serving (production pattern, same as overpass/toll/dispatch):

- Image `ghcr.io/opsdevcode/mint:<git-sha>`
- Workload `kubernetes/product-surfaces/mint.yaml` in `repave-aws-infra`
- Ingress-nginx + cert-manager `letsencrypt-prod`
- Pulumi `PRODUCT_HOSTS` alias to the existing ingress-nginx NLB

GitHub Pages on `specmint-language` stays a **fallback mirror** at
`https://opsdevcode.github.io/specmint-language/`. Do not enable Pages
`https_enforced` as production. After NLB cutover, remove the Pages custom
domain only (`scripts/remove_pages_custom_domain.sh`). Do not disable Pages.

Commercial funnel stays `https://opsdevco.de/products/mint` on Netlify.

## Interim DNS (until ingress+cert exist)

| Field | Value |
| --- | --- |
| URN | `urn:pulumi:domains::repave-aws-infra::repave:aws:CompanyDns$aws:route53/record:Record::rr-cname-mint-opsdevco-de` |
| Record | `mint.opsdevco.de` CNAME `opsdevcode.github.io` TTL 3600 |

Keep this CNAME until the Mint workload is applied. Then Pulumi-cutover mint
onto `PRODUCT_HOSTS` (A/AAAA alias to the NLB). Rollback is Pulumi reverse to
`opsdevcode.github.io`.

## What this org repo must not contain

- Pulumi Python/TypeScript/YAML
- Terraform HCL
- `pulumi up` / `pulumi preview` wrappers
- AWS credentials or invented TXT tokens
