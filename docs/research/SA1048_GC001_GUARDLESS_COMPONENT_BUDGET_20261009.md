# SA10.48: GC001 source-locked guardless apparel + component-sensitive visible geometry

**Date:** 2026-10-09. **Research implementation PASS, production/full-character Golden HOLD.** The signed GC001 source is a 340×340 image and previous source authority, not a new stylized or generated character. No original input bytes changed. Raden's SA10.45 1,409-vertex / 882-pixel research champion remains the unchanged two-character control; it has *not* been run through the new GC001 component pruning rules.

## Goal and decisive result

Reduce GC001's expanded SVG geometry from SA10.47 **2,925 / 1,887** without corrupting signed face, left-arm or right-arm RGB, without deleting any of the five real Stage37 clothing color planes or Stage9 material polygons, and without using img2img/generative fill/raster SVG embedding.

**Chromium 144.0.7559.96, DPR 1, 340×340:**

| State | All expanded mask/correction/color polygon vertices | Full RGB mismatched vs signed full OpenCV | Signed face / left / right RGB |
| --- | ---: | ---: | ---: |
| SA10.47 GC001 exact visible | 5,327 | 683 | 0 / 0 / 0 |
| SA10.47 GC001 guarded diagnostic | 2,925 | 1,980 | 0 / 0 / 0 |
| SA10.48 exact visible *without redundant Stage37 protector* | **4,675** | **683** | 0 / 0 / 0 |
| **SA10.48 component-optimized protected candidate** | **1,883** | **1,871** | **0 / 0 / 0** |

GC001 expanded budget **1,887**: new candidate **PASS by 4 vertices**. The former SA10.47 guarded diagnostic is improved by **1,042 fewer vertices** and **109 fewer RGB-different pixels**. This does not show pixel-perfect whole-image quality or improve the *original source's* historical Stage8 3,604 > 1,887 gate. It is not an assertion of semantic garment quality or restored eye/nose/mouth detail.

## Source-specific proof for removing a protector, without deleting clothes

Four original GC001 additional-color groups (Stage9 + five actual Stage37 apparel polygons) previously used `url(#sa1041-protected-clear)` to omit protected face/arms. In the exact source-controlled SVG, independently remove this mask from every subset of the four groups (**all 2^4 = 16 combinations**) and render complete SVG on real Chromium. **Each of the 16 composites is pixel-for-pixel identical to the original masked composite**. Therefore the source-specific protector (652 exact vertices) is redundant for this signed scene. Keep all 8 Stage9/37 actual color polygons (28 + 27 = 55 extra vertices). The optimizer removes only the outer mask attribute and unused definition; it does *not* delete or reorder any of the clothing polygons or invent any material color. It refuses removal if the number of protected groups or apparel panels differs.

A different character, new clothing or changed overlay geometry can invalidate this proof. The 16-case proof and SHA-256 authority gate must be rerun, never generalized as an unconditional removal rule.

## Component-sensitive geometry and signed arm protection

The remaining source-visible owner masks use approved polygon approximation with role-index lookup from the signed GC001 scene. Connected-component filtering is explicitly recorded, **not treated as lossless**: hair removes 14 micro-components / 23 source pixels, torso 8 / 10, `unknown` 63 / 137. This amounts to 170 source-owned pixels discarded before approximation, and is one reason full RGB remains nonzero. Stage9 clothing and Stage37 planes remain unchanged. Precise epsilons and thresholds are in the versioned `POLICY` dictionary and metrics JSON.

After each approximation, a *real Chromium isolated mask* is rendered, and new foreign paint in any signed protected pixel is removed with small source-derived black SVG rectangles. Every such rect counts **four expanded vertices**, including all 28 hair mask trims. The independent signed face/arm tests are checked **after complete final SVG compositing**, not merely mask-by-mask. No `<image>`, `feImage`, `foreignObject`, embedded PNG, generated fill or inferred facial features.

Full 1,871 RGB mismatch partition, by topmost **source** owner (not semantic garment segmentation): hair 534; lower_body 459; torso 222; major_clothing 175; unknown 274; neck 10; accessory 8; background 189; signed face and both arms 0. The partition sums exactly to 1,871. The visually blank face and remaining clothes/hair errors remain important quality failures even when the protected RGB parity is zero.

## Provenance, automation, tests, release decision

- `tools/research/sa1048_guardless_component_optimizer.py`: read SHA-verified private GC001 source through SA10.46/47; build signed source-visible exact SVG; run the 16-way protector non-effect proof in Chromium; build component candidate and count all expanded path/trim/color vertices; fail-closed gates; write SVG/PNG/JSON/comparison.
- `tests/zerobase/test_sa1048_guardless_component_optimizer.py`: **9 / 9 PASS with private signed source**, including source byte tampering, original color polygons, no unexpected guard deletion, disconnected pixel filtering, budget and final RGB protection; private-source tests skip if the source folder is not supplied.
- Two independent fresh output directories: **6 / 6 generated PNG/SVG/JSON files SHA-256 identical**, full artifact digest ledger in `sa1048_metrics.json`.
- Store private research outputs in approved Drive location `chatGPT及びCodex用/Minimalizer/SA1048_GC001_GuardlessComponentBudget_20261009`. GitHub contains source/test/report/metrics only, not private original character images. No RDC, local worker or production sites modified.

**Gate:** `GC001_EXPANDED_VERTEX_BUDGET_PASS` 1,883 / 1,887; `GC001_FINAL_SIGNED_FACE_BOTH_ARMS_RGB_ZERO_PASS`; `GUARD_NON_EFFECT_16_OF_16_PASS`; `SOURCE_OVERLAY_POLYGONS_8_OF_8_PRESERVED`; `FULL_RGB_GOLDEN_FAIL` 1,871 mismatches; `HISTORICAL_SOURCE_STAGE8_GATE_FAIL`; `HUMAN_REVIEW_PENDING`; `PRODUCTION_HOLD`. Raden original champion unchanged. No deploy or auto-promotion.

## Reproduction

Retrieve the eight GC001 signed source files with names and SHA-256 listed in `sa1046_gc001_positive_holdout.py` from the approved private Drive authority into a separate directory. From a repo checkout with `cv2`, NumPy, Pillow, Playwright, Chromium and pytest:

```bash
python tools/research/sa1048_guardless_component_optimizer.py --gc001 /path/to/private_gc001_signed --out /tmp/sa1048_first --chromium /usr/bin/chromium
SA1048_GC001_ROOT=/path/to/private_gc001_signed python -m pytest -q tests/zerobase/test_sa1048_guardless_component_optimizer.py
```

## SA10.49 recommendation

Concentrate on source-derived hair and clothing **color reconstruction** beyond geometry-only shortening, preserve the original source's visual identity including facial features without inventing new anatomy, and revisit the *separate* Stage8 historical ring budget and whole-scene Golden quality gates for both signed characters. Do not change production until genuinely approved by two-character source constraints and visual human review.
