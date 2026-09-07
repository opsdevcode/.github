# OpsDevCode visual system

Canonical **visual thesis and family grammar**. Product semantics live in
[`../portfolio/README.md`](../portfolio/README.md) (when present). This directory
does not own marketing copy or infrastructure.

## Visual thesis

**The governed section.**

OpsDevCode is drawn as an engineering *section cut* through a living system:
open joints, planes, and witness marks. The four products are different
**readings of the same cut** (delivery, state, economics, interaction)—not four
mascots and not a mandatory pipeline.

That idea must remain identifiable with the logos removed.

## Existing identity (what we keep / drop)

| Asset | Verdict |
| --- | --- |
| GitHub org banner as site lockup | Drop. Share art is not a logo. |
| PNG “O / terminal” marks | Drop. Weak family DNA, huge rasters, not a system. |
| Stripe-like Inter + `#635bff` + navy | Drop. Generic developer-tool kit. |
| Product accents amber / teal / blue / violet | Keep as *hue families*; retune for one paper/ink system. |
| Rail layout on the company site | Keep. It already reads as a drawing annotation. |

The company mark is **not** another product icon. Four open L-corners form an
empty aperture: the family. Products draw *inside* that same 32-unit stroke
grammar.

## Logo family

Shared DNA: 32-unit grid, 1.5 stroke, square caps, miter joins, no fill, open
joints. Color is the only product-specific pigment; geometry carries meaning.

| Mark | Concept |
| --- | --- |
| OpsDevCode | Four open corners. Empty center. The system. |
| Repave | Offset passes of a path (lifecycle / restore). |
| Overpass | Two planes and spanning members (topology). |
| Toll | Measured gap (attribution / exchange). |
| Dispatch | Intent through a gate into action. |

Files: `svg/mark-*.svg`, `*-mono.svg`, `lockup-*.svg`, `favicon-opsdevcode.svg`.

**Clearspace:** ≥ 6 units around the mark. **Minimum:** 16 CSS px for the mark.

**Misuse:** do not fill the marks; do not round the corners; do not recode all
four products the same hue; do not put the company mark in a gradient orb;
do not use highway / paving / booth / truck illustrations.

Endorsement form: **`{Product} — by OpsDevCode`**. Relationship rule, not
mandatory chrome on every pixel.

## Color

Paper `#F3EFE6`, ink `#1A1F1C`, rules `#C9C2B3`. Product accents (on paper):

- Repave `#C4841A`
- Overpass `#1A7A72`
- Toll `#2B5F9E`
- Dispatch `#5B4A8A`

Ink text on paper is the accessible default. Accents label planes and marks,
not body copy. Light is the drawing mode; dark is a later inverse, not a neon
theme.

See `tokens.json`.

## Typography

| Role | Face | Why |
| --- | --- | --- |
| Display | IBM Plex Serif | Instrument / drawing caption, not Inter hero |
| Body | IBM Plex Sans | Technical, licensed (OFL) |
| Data / code | IBM Plex Mono | Tabular evidence |

Do not use Inter as the brand face.

## Diagram grammar

An OpsDevCode diagram uses:

- hairline frames (section bounds)
- square-cap strokes
- product-colored planes
- mono captions
- no 3D isometric fluff, no glow, no node-blob graphs

Primitives: `svg/diagram-primitives.svg`. Signature system:
`svg/section-system.svg`.

## Motion

Explain a change (a plane resolving, a gap measuring, intent crossing a gate).
Honor `prefers-reduced-motion`. Never decorate.

## What this does not govern

Runtime UI chrome inside Repave (except future adoption of tokens), DNS,
photography, or Convergence’s independent identity.
