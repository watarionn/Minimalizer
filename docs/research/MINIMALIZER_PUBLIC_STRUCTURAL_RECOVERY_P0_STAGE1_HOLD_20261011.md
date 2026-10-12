# MinimalizerPublic StructuralRecovery P0 Stage 1: source-signed part boundary prototype (HOLD)

2026-10-11. Research only. **Not an accepted image converter, default Public change, Local Worker change, or production release.**

## Authority and goal

Continue HND-20261011-MINIMALIZERPUBLIC-STRUCTURAL-RECOVERY-FIRST.md, Draft PR #389. Compare authentic GC001 and Raden sources against frozen real Public Facet40; do not optimize R67's remaining 19 source-fitted pixels. Restore missing sleeves/arms and clothing distinctions before pursuing one-pixel changes. Do not draw eyes, nose, or mouth; do not use generative fill, inpainting, img2img, or invented RGB.

Canonical private evidence and original photos: Google Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010` (existing P0 diagnostic). Source photos, masks, source-derived comparisons and raw pixel arrays remain outside public GitHub.

## Implemented isolated prototype

`web/static/public-structural-recovery-p0.mjs` exports `recoverSignedParts`. The caller supplies original source RGBA, frozen Public output RGBA, a nonempty 0/255 face mask, and disjoint nonempty 0/255 source-part masks. The **historical externally attested Stage04 masks** are provided by the private real-case harness, not embedded or inferred by the module. The module validates dimensions, binary masks, disjointness, source alpha, per-part budget, and fails closed on invalid input. **It does not cryptographically authenticate mask provenance:** that is still a required upstream gate before any product consideration.

For each authorized source part, it picks <=5 dominant source-only RGB samples independently (clustering, representative source pixel snap, 5x5 within-owner spatial vote). It never writes outside the provided owner; never changes alpha; and preserves source-transparent fringe. For the independently supplied face mask, it replaces source-eye-like high frequency microfeatures with one observed skin RGB value. This is **an aggressive privacy-policy proof, not a finished artistic face**. Eye-like patches *outside* the signed mask are not certified hidden. Baseline, source and masks remain read-only.

The file is **not imported by `web/static/public-route.js`, `browser-fallback.js`, or a production HTML page**. No new library dependency.

## Verified local evidence

- Node synthetic `tests/js/test_public_structural_recovery_p0.mjs`: **10 tests PASS** for disjoint boundaries, alpha parity, source-observed RGB, face flatten, deterministic replays, nonbinary/empty/malformed input refusal, overlapping owners, unsupported source alpha, missing owner negative control.
- **Actual frozen original 340x340 GC001 and Raden:** run the same JavaScript candidate on original sources + historical Stage04 face/left/right-arm masks + real Public Facet40 PNG baseline. Independently inspect RGB on all signed-owner pixels, no changes outside signed owners, no alpha changes, deterministic module. Original inputs are private Drive files, not public test fixtures.
- GC001: left owner 2,715 source-backed pixels, right owner 6,445, 41 unsupported alpha fringe, face 4,937, 5/5 part palette colors. Recorded 14,097 changed RGB pixels versus Facet40.
- Raden: left owner 10,307 source-backed pixels, right owner 9,870, 112 unsupported alpha fringe, face 4,052, 5/5 part palette colors. Recorded 24,229 changed RGB pixels.
- These large pixel counts are **not a quality metric** or proof that geometry, silhouettes, garments and eyes pass. The partial recovery of source sleeve/glove colors is visible, but signed-arm masks alone cannot fix distorted contours. Some source-owner pixel areas remain contaminated by background or incompatible overlaps, and the large flat face is not acceptable final quality.

## NO-GO and next P0 step

The bow, corset lacing, collars, goggles, garment layers, true silhouette, source-aware occlusion, accessories and held objects are still not protected as independent source-observed parts. The only protected anatomy regions here are independently existing left arm/right arm and face masks. The two-source visual Golden review is not signed, and real Chrome whole scene 340/DPR2 680 + physical Safari have not been rerun on this candidate. No additional source-part semantic masks may be invented from color guesses. Draw new candidate only after independently backed source-observation masks exist.

**Next:** introduce separately attested source part owners for collar/bow/corset/goggles/held objects, verify their overlap/z-order against source, allocate bounded contours and source-only palettes by part, and retest full-scene Chrome/DPR2 with independent human Golden review. Resolve background-contaminated mask ownership and prove all facial microfeatures stay hidden, including outside the face-mask boundary, before any potential release. Prior Stage8 source-ring budget, browser, license and rollback gates remain HOLD.

No production merge, source change, private-data upload to GitHub or deployment is claimed.
