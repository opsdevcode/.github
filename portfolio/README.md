# OpsDevCode family contract

This directory is the **canonical company and product-portfolio contract**.

It exists because company, product, brand, and ADR material have drifted
(ADR 009 vs ADR 020, websites, GitHub org copy, individual product repos).
Implementation stays in each repo. This contract is the shared semantic map.

**Principle:** One company system. Four independent products. One recognizable
product family.

Machine-readable source: [`products.json`](products.json).

JSON is used because this repository’s other contracts (`profiles/*.json`) are
JSON and validate with the Python standard library. This is not a CMS.

## Why this exists

`.github` already owns GitHub **repository governance** (`GOVERNANCE.md`,
`profiles/`). That is not the public portfolio.

This contract owns **identity and portfolio semantics**: what OpsDevCode is,
which four products exist, each product’s architectural role, maturity
vocabulary, endorsement, public URL pattern, and Convergence’s relationship.

Later PRs (company site, product identity pages, OG, ingress) should consume
this file rather than invent a fifth hierarchy.

## Company vs product

| | OpsDevCode | Products |
| --- | --- | --- |
| Kind | Company (umbrella) | Independent products |
| Public URL | https://opsdevco.de | `https://<product>.opsdevco.de` |
| Job | Portfolio, company story, approach, services | Own proposition, experience, CTA |

OpsDevCode is **not** a fifth product, not another Repave site, not a
runtime, and not Convergence.

## Four-product portfolio

Exactly four current products. Do not add Relay or Convergence here.

| Product | Semantic role | Role | Canonical URL | Maturity |
| --- | --- | --- | --- | --- |
| Repave | Govern delivery. | Governed software-delivery / repository lifecycle | https://repave.opsdevco.de | early-access |
| Overpass | Understand state. | Infrastructure/system state and relationships | https://overpass.opsdevco.de | in-development |
| Toll | Connect economics. | Engineering/infrastructure economics and attribution | https://toll.opsdevco.de | in-development |
| Dispatch | Governed interaction. | Governed engineering interaction / experience | https://dispatch.opsdevco.de | emerging |

Semantic roles are **architectural anchors**, not approved marketing taglines.
Do not silently polish them into slogans in this file.

`https://repave.dev` is a Repave **alias**. It does not change ownership.

## Product independence

1. Every product must be independently understandable.
2. A visitor should not need Repave in order to understand Overpass, Toll, or Dispatch.
3. Each product owns its proposition and product-specific experience.
4. Every product must remain recognizably part of OpsDevCode.
5. Shared family identity must not make products visually identical.
6. Products remain independently deployable.
7. **Repave is not the shell/container for sibling public identities.**

That last rule matters for Host routing: sibling identity hosts must not
depend on reaching the Repave origin. Repave `CanonicalHostMiddleware` correctly
owns **Repave** canonical-host behavior. Future ingress must route product Host
headers to the product identity workload **before** that middleware. This
contract records the invariant. It does not change DNS or ingress.

## Family endorsement

Canonical relationship form:

**`{Product} — by OpsDevCode`**

This is a **relationship rule**, not a requirement to print that exact string
on every surface. Product sites must make OpsDevCode ownership discoverable
while remaining independently branded.

## Public-domain pattern

Intended family:

```text
opsdevco.de
repave.opsdevco.de
overpass.opsdevco.de
toll.opsdevco.de
dispatch.opsdevco.de
```

`repave.dev` → Repave alias.

This file does **not** assert that sibling hosts are currently healthy.
Host health is operational evidence, not portfolio metadata.

## Convergence

Convergence is an **independent** body of knowledge / methodology
(https://github.com/opsdevcode/convergence).

OpsDevCode may follow, reference, support, or apply it.

Convergence is **not** an OpsDevCode product, not in the four-product
portfolio, not a runtime, and not a fifth product surface.

## Relay (not a portfolio product)

Relay is an **internal** conversational runtime (GitHub governance may still
classify `opsdevcode/relay` with the product *repository* profile). It is not
a public SKU and must not appear in `products:`.

## Authority (ADR 009 vs ADR 020)

**Authoritative for this contract:** [Repave ADR 020](https://github.com/opsdevcode/repave/blob/main/docs/adr/020-opsdevcode-product-architecture.md)
(company vs sibling products vs Convergence; Dispatch is not a fourth data domain).

**Not authoritative for portfolio hierarchy:** [Repave ADR 009](https://github.com/opsdevcode/repave/blob/main/docs/adr/009-v3-product-identity.md).
ADR 009 remains the historical record of Repave’s display name and mark. It
does not make Repave the company or parent platform. Phrases such as
“intelligent platform layer” in brand docs must not override this contract.

Historical ADRs are not rewritten here.

## Maturity vocabulary

Copied from existing company-site product definitions (`early-access`,
`in-development`, `emerging`). Values describe **product** maturity, not
whether a hostname returned 503 on a given day.

| Value | Meaning |
| --- | --- |
| `early-access` | Capabilities exist and are marketed; hosted access is waitlist/invite. |
| `in-development` | Identity and some implementation exist; not generally available. |
| `emerging` | Name and boundary defined; runtime/identity still early. |

Current assignments: Repave `early-access`; Overpass and Toll
`in-development`; Dispatch `emerging` (experience still hosted in Repave).

## What this contract governs

- Company vs product vs methodology vs internal runtime
- The four product IDs, names, semantic roles, canonical URLs, aliases
- Endorsement relationship
- Independence and runtime-boundary invariants
- Maturity vocabulary and current product maturity
- Which ADR is authoritative for portfolio structure

## What this contract does not govern

- CSS, color, type, logos, favicons, motion
- Page copy, heroes, screenshots, feature catalogs
- Product navigation chrome
- DNS, Route53, Netlify, EKS, ingress, deployments
- Repave `CanonicalHostMiddleware` implementation
- GitHub rulesets (see `GOVERNANCE.md`)

`.github` owns the **portfolio contract**. It does not centrally own each
product’s marketing implementation or visual design.
