# MinimalizerPublic R7: original-source human Golden review packet

2026-10-10 | **R7 engineering complete / review PENDING / release NO-GO**

## Why R7 was selected

R6 blocked eight release conditions. R4 whole-scene resvg DPR2 does not match Chrome due to the frozen PNG Facet resampling. Source-owned arm/tie/staff/faceless boundaries and human Golden review are also unsigned. Neither automatic similarity metrics nor a user's instruction to keep progressing authorizes us to sign a manual review or alter source material.

R7 removes a practical review blocker: no single canonical, source-grounded, verifiable per-person comparison packet existed linking actual original photo to the exact frozen v32 and v34 results. It **prepares review**, without claiming human approval or changing product geometry.

## Implementation

- New `scripts/build_public_r7_golden_review.py` consumes canonical v32, v34, R4 and R6 originals; Python Pillow is used only for non-generative PNG panel layout.
- Verifies **every input source photo, archived source segmentation, Facet, v32 Golden PNG, v34 Chrome PNG and v34 SVG** via existing SHA-256 manifests before creating an output folder. R4 independent 340 Chrome output must be pixel-identical to both frozen Golden and v34. R6 input must itself be `NO_GO` with `releaseAuthorized=false` and at least one blocked release gate.
- For each Kyoko / Noel / Ririka, creates an independently inspectable three-column by two-row review PNG. Five panels: **original source photo**, source segmentation **(diagnostic, NOT semantic truth)**, frozen Facet, v32 original Golden, v34 Chrome rendering; sixth region declares `REVIEW STATUS: PENDING`.
- Images are presented at native 340x340 panel size over a neutral **display-only** alpha checkerboard. The source files, semantic boundaries and 340x340 pixels in original files are unchanged. A separate unsigned Markdown checklist has eight manual review fields per case (original identity, silhouette, both arms, necktie/RGB, staff, garment interiors, face-hidden, overall human Golden), all unchecked with reviewer/date/device unset.
- Records immutable original SHA evidence and explicit `humanGoldenSigned:false`, `semanticPartOwnersSigned:false`, `releaseAuthorized:false`, `stage8OriginalRingBudgetApproved:false`. No automatic face/arm/tie/staff ROIs are invented; no masks are declared part authority.
- All generation occurs as **research artifacts** with a no-overwrite output guard. No Local worker, Local Minimalizer, Public route, CDN or model rendering is changed.

## Real frozen-source measurements

| Golden | Source RGB / output raw different pixels (diagnostic only) | v32 vs v34 Golden pixel diff | Independent R4 vs v34 pixel diff | Human review |
|---|---:|---:|---:|---|
| Kyoko | 54,934 of 115,600 | 0 | 0 | PENDING |
| Noel | 82,932 of 115,600 | 0 | 0 | PENDING |
| Ririka | 86,465 of 115,600 | 0 | 0 | PENDING |

The raw original-photo vs minimalized-output different-pixel metric is **not a quality score**: minimalization intentionally changes most source pixels. Nor does v32-v34 exact parity prove source silhouette correctness. The true comparison task is human confirmation of source identity, colors, tie, arms, staff and facial feature suppression from actual originals. This packet allows it but **does not fake the answer**.

Frozen R6 verdict fingerprint observed: `87a99ac2b4c48ba968413116916d978be9f123c1ffd2cb720c20e8c86e034f18`.

## Validation performed on real Windows archival mounts

- The original source PNG, segmentation diagnostic, Facet, v32 Golden and v34 Chrome are all genuine 340×340 RGBA for all three.
- The full R7-plus-prior regression suite: **70 pytest PASS**. Added five R7 safety tests for frozen source tampering, forged R6 GO refusal, wrong R4 Chrome Golden, no overwrite/production isolation, and honest unsigned packet production. Python compile PASS.
- Two independent source-to-review runs succeeded; **all 5 of 5 output files byte-identical** across replays: three labeled source/Golen contact-sheet PNGs, `GOLDEN_HUMAN_REVIEW_PENDING.md` and `public_r7_review_packet.json`.
- Source input untouched, production not promoted, Local Minimalizer untouched.
- Canonical preservation under `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R7_20261010/` after copying and read-after-write checks.

## R7 decision and next independent step

**R7 implementation/verification COMPLETE; all eight R6 release blockers remain NOT approved.** R7 simply makes the original source photo human review reproducible. Do not count new review packet as a release gate pass. Only an actual signed review can satisfy that part of R6.

Suggested R8: resolve *machine-actionable* remaining issues without changing pixels, e.g., license/notice redistribution evidence inventory and production-only rollback feasibility simulation, or further frozen Facet high-DPR renderer isolation. Keep real Safari/iPhone, Stage8 original contour budget, human source-owner review and full-scene cross-renderer DPR2 independently blocked. A Draft PR and evidence artifacts must not be merged or deployed as though they passed the release gate.
