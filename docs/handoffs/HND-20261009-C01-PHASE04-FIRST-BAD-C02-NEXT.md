# Minimalizer campaign C01 → C02 handoff, 2026-10-09

Campaign: `CMP-20261009-SA1060-TO-PRODUCTION`. C01 **engineering diagnosis COMPLETE**, C02 **READY**, C03 **HOLD** (parallel Stage8 research), C04 human Golden **HOLD**, C05–C08 blocked until their respective release gates. **No production deployment.**

## Verified observation

- GC001 signed Phase04 right_arm has 533 source-border-connected exact RGB background-overlap pixels out of 6486. Of these 520 are fully opaque, 13 have alpha <255. Stage08 source right_arm rings **retain all 533**; Stage08 XOR signed Phase04 24 px. Left-arm 0 and face 0 source-border-connected overlaps. Thus **earliest checked bad output = Phase04**, not an inferred Phase03 algorithm root cause.
- Independent Raden same observer: signed right_arm 3, left_arm 7, face 0. A generic global recolor/prune is unsafe.
- Private candidate `gc001_right_arm_phase04_candidate_v1_PRIVATE.png` subtracts **only the 520 opaque** overlap pixels, 0 additions, preserves right-arm component count 1, freezes all signed masks. Not adopted or used in production.
- 10/10 test PASS with signed GC001/Raden inputs, 5/5 fresh output SHA matches. The original Phase04 masks, source image, Stage08 scene and SA10.57 SVG were not rewritten.

## Canonical sources

- GitHub: `tools/research/sa1060b_first_bad_stage_audit.py`, `tests/zerobase/test_sa1060b_first_bad_stage_audit.py`, `docs/research/SA1060B_C01_FIRST_BAD_STAGE_GC001_20261009.md`, `docs/research/evidence/sa1060b_c01_coordinate_free_20261009.json`; this handoff and campaign JSON/MD.
- Private Drive: `chatGPT及びCodex用/Minimalizer/Campaign_SA1060_to_Production_20261009/C01_Phase04_FirstBadStage_20261009`, linked in public C01 research note and tracker. Source comparison, candidate mask, private metrics and checksum manifest there. Do not publish original image or traced pixel positions.
- Prior PR #319 SA10.60A colour candidate stays rejected/HOLD. Earlier source Stage8 gate and human Golden are **separate** hard blockers.

## Next action (C02)

Before editing renderer or Stage04 logic: retrieve/replay the genuine Phase03/04/05/06 GC001 workspace if available, then compare owner masks with actual source arm/garment/hair contours, not only RGB flood. Distinguish subject-mask error vs Phase04 decomposition vs Phase06 binding. Build *versioned* source-proven candidates, do not overwrite signed prior stages. Test isolated Chromium + Raden and other independent holdouts with anatomical identity/arms/sleeves/hair and hard vertex counts. If old raw workspace is unavailable on GitHub/Drive, test accessible GitHub/Drive artifacts first and then justify the minimum needed RDC read-only access; don't claim earlier roots known from guesswork. Keep face microfeatures OFF and generated pixels prohibited. The release campaign continues but promotion is HOLD.
