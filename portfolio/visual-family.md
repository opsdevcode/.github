# Visual family

Benchmark: the approved **Repave product sheet** (company `/products/repave`
and the hosted Repave marketing surface at the same density), not a logo PR
and not the company homepage as of 2026-09.

## Shared DNA (all public surfaces)

- Paper/ink drawing, not a SaaS gradient card
- Display serif for the named object; sans for chrome and body; mono for meta
- High information density, low chrome
- Hairline rules, square construction, no drop shadows
- One captioned technical figure per major section — not four identical cards
- Scarce product accent (hue family), not a rainbow on every band
- Product nav prioritizes the current product; OpsDevCode is discoverable
- Footer: endorsement, siblings, company, Convergence-as-independent

## Product visual concepts (must differ)

| Product | Concept | Do not |
| --- | --- | --- |
| Repave | Lifecycle / progression / evidence / restore | Company umbrella art |
| Overpass | Topology / relationships / stored state | Generic cloud icons; APM dashboards |
| Toll | Attribution / flow of spend to owners | Accounting charts; fake savings |
| Dispatch | Intent → evidence → proposal → confirm | Giant chat window; “AI” chrome |

Company homepage: same DNA, **company-level** composition. Not another Repave.

## Marks

The company symbol is **open** (not locked to the four-corner aperture).
Until a company mark is approved, product sites use a **clean wordmark** plus
accent and concept diagrams. Do not ship four independent logos. Do not
hard-wire a temporary company mark into every template.

## Shared implementation

**Documented tokens and primitives, copied locally** — not an npm/Python UI
package. Family contract + `brand/tokens.json` are the SoT. Drift is caught
by review and contract tests, not by coupling four deployables.

## Routing vs visual

Sibling hosts must hit **that product’s identity workload**. Do not CNAME
Overpass/Toll/Dispatch to the Repave origin so `CanonicalHostMiddleware`
rewrites them. That is an architecture invariant, not a visual shortcut.
