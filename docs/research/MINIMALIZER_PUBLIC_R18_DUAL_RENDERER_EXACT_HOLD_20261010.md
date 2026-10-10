# MinimalizerPublic R18 | Actual Chrome 340/680 + OpenCV dual-renderer exact source owner gate

2026-10-10. **R18 engineering verification PASS; original Stage8 vertex budget and source-photo semantic quality HOLD; production NO-GO.**

## Canonical lineage and safety boundary

Stacked research branch `research/public-r18-dual-renderer-exact-vertex-gate-20261010` above Draft PR #374 (R17), Draft #373 (R12–R16), Draft #372 (R11). Original v34 remains separately held. **This PR is a self-contained research-only tool**, not a merge, user-facing deployment or update to any Local/Public conversion algorithm. No new pictures or facial details, no filled-in background, no source-owner changes, no new colors.

Original source authority is doubly pinned to SA10.34 signed photo hash and the complete immutable private owner geometry JSON SHA. The R17 candidate is also checked against its original PRIVATE R17 audit SHA and must be an original-point-only ordered subsequence with unchanged 11 owner rings and colors. All generated source geometry and owner diagrams remain private to `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R18_20261010`.

## What R18 actually implemented

- `scripts/verify_public_r18_dual_renderer_prune.py`: always start from the **immutable original** SA10.34 Stage8 scene, not from R17 reduced scene. Use R17 only as a list of *proposed* source-vertex deletions.
- Stage A: for each of 11 owner images, propose every R17 ring-wide change individually, calculate actual Chrome SVG owner-mask differences at native **340x340** and DPR2 **680x680**, reject any nonzero difference, and additionally verify the complete original OpenCV source-owner raster remains byte-identical.
- Stage B: for rejected or partly changed rings, test original R17-suggested vertex deletions **one by one** (bounded at 360 mask-exact candidates per owner) in actual Chrome at both DPRs. Only accept if a cumulative post-edit owner is *still* byte/pixel-identical to both its original OpenCV source-owner mask and the original SVG owner render in each resolution. All rejected proposals roll back.
- Final independent defensive cross-check: rerender original and selected owner masks again through two pre-existing separate Selenium Chrome reference paths (`render_rgba` and `render_2x`), compare RGBA; reject any disagreement with batched browser tester.
- No unapproved historical Stage8 cap waiver. All outputs retain `productionReleaseAuthorized=false`, `humanSemanticSourceOwnershipSigned=false`, `trueStage8OriginalRasterVsOfficialStage04Approved=false`.

## Actual source measurement

| Source case | Frozen original Stage8 vertices | R17 OpenCV-only compressed candidate (not adoptable) | R18 exact **OpenCV+Chrome 340+Chrome 680** candidate | Proven deletion | Historical Stage8 cap | R18 gap |
|---|---:|---:|---:|---:|---:|---:|
| GC001 | 3,604 | 2,359 | **3,601** | **3** | 1,887 | +1,714 |
| Raden | 2,370 | 1,455 | **2,370** | **0** | 1,412 | +958 |

GC001: 47 ring-level proposals and 541 individual **OpenCV byte-exact** candidate deletions tested. Of these, 1 torso single-vertex deletion passed Chrome both DPRs, and 1 left-arm ring containing 2 vertices was fully exact. All 11 owners independently rerendered at 340 and 680 were 0 pixels different from the original candidate after selecting these 3 source points. This is an **incremental candidate-vs-frozen-stage8 parity**, not human certification that the frozen stage8 was correct against the original official mask or source photograph.

Raden: 26 ring-level proposals and 346 isolated OpenCV byte-exact proposals tested. **None** satisfied the strict Chrome two-DPR requirement and no source vertices were adopted. All 11 original owner images remained unchanged.

The broad R17 savings of 34.5%/38.6% therefore **cannot be product-shipped**: they alter real SVG render. R18 is a safety improvement, not a large geometry cost breakthrough.

Chrome 154.0.8037.98 used as actual desktop browser. No fabricated iPhone/Safari/Golden/device/legal permissions. In particular, the original historical Stage8 signed counts remain **3,604/2,370**, not updated to 3,601/2,370 retroactively.

## Tests, reproducibility, privacy

- Added `tests/test_public_r18_dual_renderer_prune.py`: true browser DPR1/2 positive/negative geometry checks; candidate subsequence and SHA guards, no-overwrite, positive OpenCV-only proposal check, and no Local/Public route mutation.
- Full Public R1–R18 and Local/Public isolation regression suite **123 PASS**.
- Actual Chrome native/DPR2 11-owner independent render verifiers **pass for every selected R18 owner**. Candidate outputs and complete coordinate-free owner measurements saved privately in Google Drive. Two independent full runs compared at SHA-256 when archived.
- No live production files, source images, deployment switches or Local Worker changes. Research Draft remains unmerged.

## Next technical target (not authorized release)

R19: investigate a vector representation that has **provably equivalent browser rasterization** to the signed owner masks rather than relying on OpenCV's tolerance for vertex deletion. Explore exact line/edge representation or source-aligned vector tiles without embedded bitmap or artificially added semantic detail. Compare both exact per-owner Chrome DPRs and source official stage04 masks, including face hidden and separate arms/staff/tie. Do **not** claim a true source-quality or Stage8 budget PASS until the numeric owner-ring budgets and independent source-photo semantics are both satisfied.
