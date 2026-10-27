# MinimalizerPublic P0: Stages194–203 research implementation and gate results

Date: 2026-10-14 JST
Scope: **research-only**, existing draft PR #393. No main merge, no production deploy, no Local Minimalizer changes. The public GitHub repository contains **NO** original art, RGBA bytes, A/B reviewer masks, source-derived SVG previews, or private adjudication screenshots.

## Source authority

The operator explicitly confirmed Reviewer A and Reviewer B worked independently and without seeing each other's results. This is accepted **out-of-band operator attestation**, not software identity authentication, and not pixel semantic truth.
Both original-review submissions remain immutable; class disagreement and abstention require separate human adjudication. Do not promote two matching classification proposals into Golden. Preserve official no-eyes/nose/mouth-generation rule. Do not create missing arms, silhouette surfaces or interior color from generative AI.

## Ten engineering stages

| Stage | Implemented technical result | Gate |
| --- | --- | --- |
| 194 | Working taxonomy distinguishes sleeves, garment, neckwear, accessory, hair, skin and background. No color-only relabel. | Rules only, original inspection required |
| 195 | Exact opaque-pixel state accounting: background agreement, person agreement, role disagreement, background ownership, abstain, uncertain. | Proposals only |
| 196 | All-original source 32px tile prioritizer; 340px frames map to 121 tiles with zero-loss unresolved accounting. | Unresolved preserved |
| 197 | Immutable A/B label revision SHA and class-transition audit; rejects labels on nonopaque source. | Await human correction v2 |
| 198 | Individually witnessed source-pixel correction proposals; rejecting batch rubber-stamping, missing reasons, duplicate indices. | Does NOT certify |
| 199 | Conservative tri-state subject/background/unknown mask; explicitly excludes undecided pixels from candidate subject. | Whole-body silhouette unverified |
| 200 | Exact replay-verified axis-aligned rectangle cover of agreeing subject evidence, no outward spills or invented pixels. | Complexity high |
| 201 | Per-role top original RGB colors sampled only from source-visible agreeing pixels; 0 invented colors. | Untrusted roles |
| 202 | Real private original-data measurement against historical full-body numeric vertex targets, distinguishing exact source replay from geometry/semantic approval. | **Numeric budget FAIL both cases** |
| 203 | Fail-closed readiness summary checks original identity, semantic adjudication, iPhone physical acceptance, rollback, full-scene RGB, independent Golden and budget. | **Golden HOLD** |

Source-free module: `web/static/public-stage194-203-recovery-p0.mjs`
Synthetic tests: `tests/js/test_public_stage194_203_p0.mjs`
Research CI: `.github/workflows/minimalizerpublic-p0-research.yml`.

## Private real-source evidence

Under owner-only `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/Stage194_203_Private_20261014` is a private report and full replay masks/experimental vectors. Original RGBA bytes were independently decoded and SHA256 recomputed from the PRIVATE iPhone source pack, and every review RLE identity and nonopaque policy was rechecked. All full-source artifacts remain private.

Aggregated observations (neither proves full-body acceptance):
- GC001: agreeing proposed subject area **47,448** opaque pixels; **7,072** unresolved opaque pixels; exact source-only rectangle cover **1,573 rectangles / 6,292 vertices**; historical numeric vertex cap **1,887**.
- Raden: agreeing proposed subject area **47,888** opaque pixels; **22,690** unresolved opaque pixels; exact source-only rectangle cover **883 rectangles / 3,532 vertices**; historical numeric vertex cap **1,412**.
- Original 340×340 frames: 115,152 opaque and 448 nonopaque each. Pixel-exact private SVG prototypes draw agreeing subject only, omitting disputed pixels. **The prototypes are neither finished character drawings nor release candidates.**
- A rectangle vertex-cost measurement is a different encoding from historical Stage8 curves. It is evidence that the current **rectangle** representation misses the numeric target, not a proof that all possible SVG contours cannot meet it. Historical Stage8 separate contour baseline also exceeds caps (GC001 3,604>1,887; Raden 2,370>1,412).

## Testing and verification

- Synthetic Stage194–203 tests: 26/26 PASS on authorized workstation, covering fullframe accounting, alpha guards, source-only rectangle raster replay and randomized masks, SHA-version audit, data-integrity guards, original palette-only extraction and permanently nonautomatic Golden.
- PR full research CI: run at head of updated workflow. Record the actual result before treating CI as complete.
- The private real-original replay is a distinct offline Python audit and must not run in public CI because images and reviewer masks must not leave owner-only storage.
- Real physical iPhone Safari test and real rollback rehearsal remain unverified. Report these as unresolved even though the iPhone reviewer app is in service.

## Next stages and explicit STOP conditions

1. Original-art human adjudication of the private 7,072 / 22,690 unresolved pixels, preserving A/B originals; complete fine edge and class-definition checks.
2. If genuine correction is required, solicit revised human output in separate immutable v2 and verify original source pins and classification bounds.
3. Investigate **source-exact boundary-aware SVG representations** and measured vertex/frontier improvement; never smooth across original non-subject or unknown pixels.
4. Fullbody silhouette, arm, sleeve and neckwear Golden quality checks only after a complete reviewed source case exists.
5. Real iPhone acceptance, end-to-end rollback, regression gates, explicit operator release decision.

**Keep PR #393 Draft, Golden HOLD, main untouched. No production authorization.**
