# SA10.46 GC001 positive-character crosscase: source-owned browser geometry / hair and clothing errors

**Decision: independent positive-character measurement PASS; full-character Golden and production promotion HOLD.** Date: 2026-10-09.

## What was verified

GC001 is a separate real source case, **not** the Raden negative apparel-control. Its signed owner order is different: `hair, lower_body, right_arm, face, torso, major_clothing, unknown, left_arm, neck, head, accessory_or_held_object`. It has **five genuine Stage37 garment color panels (27 polygon vertices) and Stage9 interior color planes (28 vertices)**. Raden's SA10.45 rule that deletes an empty apparel group is not portable. The GC001 source, Stage8 scene, SA10.41 SVG, signed OpenCV full-body image and signed Stage04 face/arms masks are verified against immutable SHA-256 values in the tool and saved metrics. No private source image is committed to GitHub.

The signed Stage04 and Stage8 owner masks are **not identical** for GC001 left and right arms: left 5 pixel delta, right 24; face zero. They must never be silently aliased to the original owner path, even though the final SVG guard can cover the final composite. All 11 owners plus both protected masks are counted; the unpainted head support is not counted as zero in the unpruned baseline. Owner/z-order, original source RGB colors, five garment polygons, mask protection and immutable outputs were preserved.

## Actual Chromium 144.0.7559.96 results, 340×340 DPR1

| Candidate | Expanded vertices, including 55 color polygon vertices | Full RGB mismatch pixels vs signed original OpenCV | Face | Left arm | Right arm | 13 isolated masks exact | Budget (1,887) |
|---|---:|---:|---:|---:|---:|---|---|
| SA10.41 old SVG | 4,312 (original measurement) | 3,919 | 140 | 206 | 199 | No | FAIL |
| GC001 exact pixel-cell boundary, epsilon 0.5 | **6,083** | **683** | **0** | **0** | **0** | **PASS** | **FAIL** |
| GC001 nonprotected epsilon 1.0 | 3,273 | 1,453 | 0 | 0 | 7 | No (1,389 summed mask wrong pixels) | FAIL |
| GC001 nonprotected epsilon 1.5 | 3,073 | 1,679 | 0 | 0 | 7 | No (1,851 summed mask wrong pixels) | FAIL |

Note: the old 4,312 figure is from the signed SA10.41 original artifact and does not imply uncounted free geometry in the new candidates. Source Stage8 is **3,604 vertices against a source budget of 1,887**; source archival vertex excess remains a separate unresolved blocker. Exact geometry only improves SVG browser raster parity; it cannot certify overall design quality.

### Localization of the remaining 683 exact SVG RGB differences

Pixels are attributed to their *topmost source-defined owner*, not classified into semantically correct clothing panels. **No claim of real material-color accuracy is made from these labels.**

| Topmost source owner | RGB error pixels |
|---|---:|
| lower_body | **413** |
| hair | **106** |
| torso | **100** |
| major_clothing | **64** |
| face, left_arm, right_arm, unknown, neck, accessory, background | **0** |

This partitions all 683 mismatches without double counting. The exact SVG candidate is superior to the original SA10.41 SVG in all protected regions, but it **does not fix source RGB and interior color quality**, and its six-thousand-vertex geometry violates the lightweight constraint. Attempts at unguarded epsilon simplification corrupt signed right-arm pixels.

## Artifact/implementation controls

- Executable: `tools/research/sa1046_gc001_positive_holdout.py` reuses `sa1043_boundary_compaction.py` pixel-edge geometry, performs GC001-specific SHA and owner-order validation, retains five signed color panels, renders actual Chromium, checks all 13 source masks, measures all expanded vertices and partitions visible RGB errors.
- Regression tests: `tests/zerobase/test_sa1046_gc001_positive_holdout.py`, **8/8 PASS with private GC001 sources**; public tests skip source-dependent work when private original is unavailable. Signed tampering, cross-character index confusion, source protection, extra polygon accounting, and hard budgets are fail-closed.
- Independent repeat: **9/9 final PNG/SVG/JSON files byte-for-byte SHA-256 equal** across two fresh output folders.
- Evidence (private): `chatGPT及びCodex用/Minimalizer/SA1046_GC001_PositiveHoldout_20261009` includes comparisons, exact and approximate browser SVG/PNG, JSON report, source hash manifest and reproducible script/test (not source images).
- Original images, Stage04/08/09/37/41 authorities unchanged; no bitmap SVG embedding, generative fill, hallucinated face/arm details, RDC, worker deployment or product change.

**Gate:** `GC001_SIGNED_SOURCE_BROWSER_MASKS_13_13_EXACT_PASS`; `FACE_BOTH_ARMS_FINAL_RGB_ZERO_PASS`; `FULL_RGB_PARITY_FAIL` (683 px); `EXPANDED_VERTEX_BUDGET_FAIL` (6,083 > 1,887); `CROSSCASE_SA1045_OPTIMIZATION_NOT_TRANSFERABLE`; `HUMAN_VISUAL_REVIEW_PENDING`; `PRODUCTION_HOLD`.

## Next: SA10.47

Build a two-character **source-locked visible-owner optimizer** that never assumes original source order, material overlay emptiness, or signed arm-mask equivalence. Preserve original Stage37 color panels and Stage9 source color at every z-depth, budget all expanded mask references and added guards, then evaluate Raden and GC001 independently. Put special attention on remaining GC001 `lower_body` and `hair` regions, and maintain signed final face / both arms zero-delta requirement. Do not reduce 1,887 or 1,412 constraints by changing the gate definition.

## Reproduction

Place eight GC001 signed files named as listed in the tool's `EXPECTED_SHA` (downloaded from the approved private Drive authority) into `/path/to/gc001_signed`. Clone the repository; invoke:

```bash
python tools/research/sa1046_gc001_positive_holdout.py --root /path/to/gc001_signed --out /tmp/sa1046_primary --chromium /usr/bin/chromium
SA1046_GC001_ROOT=/path/to/gc001_signed python -m pytest -q tests/zerobase/test_sa1046_gc001_positive_holdout.py
```

Requires Python 3, NumPy, Pillow, OpenCV, Playwright and installed Chromium. No production entrypoint is changed.
