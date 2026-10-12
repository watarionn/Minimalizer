# MinimalizerPublic StructuralRecovery P0 Stage17–20

Date: 2026-10-11. **Research only; DRAFT/HOLD. Do not merge, deploy, or claim human Golden.** Public route, Local Minimalizer and default production files were not edited.

## Real-source finding: historical signed arm mask != independent garment semantics

Frozen actual 340×340 source original and production Facet40 baseline for GC001 and Raden, with **historical Stage04** face/left_arm/right_arm masks, confirmed SHA-256. A valid Stage04 arm owner includes more than a clean sleeve/forearm material: GC001 left/right source regions contain hair/background-adjacent image areas; Raden's arm regions overlap visually nearby long hair and outfit layers. A source-pinned owner or high RGB fidelity **does not attest sleeve vs skin vs hair**, and an external background observation is not signed semantic authority.

Owner/face/alpha/background pinned audit:

| Real source | historical left arm pixels | historical right arm pixels | surviving pixels after explicit background/alpha/face exclusion | separate coarse source color masses |
|---|---:|---:|---:|---:|
| GC001 | 2,715 | 6,486 | 9,160 | 7 |
| Raden | 10,419 | 9,870 | 20,177 | 7 |

The background exclusion was a **private, case-specific flat-color connected-region observation**, seeded from the original image. It is conservative and **neither signed nor sufficient to eliminate all hair/background contamination**. SHA-256 proves bytes, not semantics.

## Stage17: visible owner boundary guard

`web/static/public-owner-evidence-guard-p0.mjs` verifies raw decoded original RGBA, signed historical owner masks, signed face, externally observed background bytes and SHA-256; excludes protected face, explicitly observed backdrop and source alpha !=255, rejects conflicting owner IDs/overlaps. Returns an auditable mask and `productPromotionAuthorized:false`. Research authority only.

## Stage18: medoid-only source color masses

`web/static/public-owner-color-mass-p0.mjs` accepts source-observed disjoint color partition masks nested in Stage17 visible owner masks. Each color is a **literal original source RGB pixel medoid**, no average color synthesized, no generative reconstruction. Rejects SHA drift, paint outside observable owner, alpha change, overlap, changed-pixel budget. Abstains where candidate color MSE fails to improve >=1%. External private source observer uses seeded k-means RGB clustering plus connected component thresholds to **propose** masks (not a semantic classifier).

Real replay on actual frozen Facet40:

| Case | accepted color masses | changed pixels | non-face original-source RGB squared-error gain | background / face / alpha / outside signed-visible owner mutation |
|---|---:|---:|---:|---:|
| GC001 | 7 | 6,891 | +3.93286897% | 0 / 0 / 0 / 0 |
| Raden | 7 | 16,197 | +6.41023316% | 0 / 0 / 0 / 0 |

Source+baseline inputs and masks are SHA-pinned. Re-run twice: RGBA SHA identical:
- GC001 `9092d6bdae150f39ce489104dfdbd4b3bfceb8c07e2186e1101b849065f35738`
- Raden `004575b07a01e7c79e69e54eda26c99b790e253addd38b867d48d36223db8881`

**Visual review rejects adopting this candidate.** GC001 navy arm pattern is partially restored but surrounding hair-like streaks/body structure remain problematic. Raden dark sleeves and ruffles reveal more source contrast, but long hair/sleeve boundary and body silhouettes remain wrong. This is a source-color fitness demonstration, **not** successful anatomical restoration, human Golden, or improved product candidate.

## Stage19: negative-result lock

`web/static/public-owner-review-gate-p0.mjs` refuses to infer anatomy from improved MSE. Two independently named cases required. Vetoes background, alpha, face, unsigned background evidence, unverified sleeve/skin/hair boundary, unapproved silhouette, external Golden and full SVG budget/E2E. Actual two-case result: `DRAFT_HOLD`, **13 blockers**, `productPromotionAuthorized:false`.

## Stage20: CI / preservation

`tests/js/test_public_owner_evidence_p0.mjs`: **21 new tests PASS** locally on Node 22 with real repository path layout; reject tampered source/owner/partition pins, unsigned origins, background/face overlap, source-alpha, duplicate roles, changed budgets, semantic overclaims. CI workflow in existing research PR to run all seven previous suites plus new Stage17–19 suite; CI conclusion must be checked separately and never inferred from local test.

Preserve all private original photos, signatures, source-exact RGB input, unsanctioned masks, source comparison previews and color fit audits **only** under Google Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage17_20_20261011`. Source-free code and this report in Draft PR #390. No img2img / generative fill / new parts. No Live Public or Local Minimalizer touches.

## Next

Do not try more paint-first k-means to solve anatomy. First obtain separately reviewed **source-correct anatomy owner masks** for forearm/sleeve/hair and collar, including RGB and topology of source parts; then verify visually meaningful corrected silhouette and full-character crosscase, with 340/680 SVG and vertex limits and iPhone Safari. Keep Stage5 as research fallback until independent owner proof and human Golden. 
