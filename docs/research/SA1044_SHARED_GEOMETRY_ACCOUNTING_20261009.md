# SA10.44: Shared Source Geometry and Honest Expanded SVG Budget (2026-10-09)

**Result: exact shape reuse VALIDATED in real Chromium; strict deployed-vertex and whole-character Golden gates NO-GO. Research only.**

This follows merged PR #291 SA10.43. Original frozen Raden source, Stage8 source-owner scene, original full-scene SA10.41 SVG, signed OpenCV raster baseline and face/left/right arm masks are verified by the seven existing SHA-256 records in `tools/research/sa1043_boundary_compaction.py`. No source materials, visibility, source bitmaps, generated imagery, anatomical details or Local/Public/Worker endpoints were modified. One source is a negative character control and **does not prove universal generalization**.

## What can really be reused?

Across the signed 340×340 source masks, face owner = signed face mask exactly; left-arm owner = signed left-arm mask exactly. Importantly, the right-arm owner and signed right-arm mask **differ by 2 pixels**. We deliberately keep two distinct right-arm geometries rather than erasing this discrepancy. Source face/arms are disjoint; the inverse protection mask can be expressed using three independently signed source masks. New `<defs><path .../></defs>` plus `<use href="#..." .../>` references enable that reuse, without bitmap SVG embedding or hidden bitmap paint. Source owner z-order is unchanged.

## Actual browser measurements

Chromium 144.0.7559.96, Playwright DPR=1, source 340×340, signed OpenCV reference. Exact source mask parity checked in **all 13 isolated masks** (11 owner masks including structural head, one face guard, one inverse combined face/arm protector). Independent full SVG render is then compared to frozen original OpenCV RGB.

| Candidate | Stored unique path vertices + Stage9 | Expanded painted mask vertices + Stage9 | Full RGB mismatch px | Signed face | Signed left arm | Signed right arm |
|---|---:|---:|---:|---:|---:|---:|
| SA10.41 original (reference) | Not applicable | 2,976 | 2,681 | 122 | 237 | 255 |
| SA10.44 shared exact (epsilon 0.5) | 3,510 | **4,086** | **148** | **0** | **0** | **0** |
| SA10.44 shared unique-budget (other masks epsilon 1.5) | **1,362** | **1,938** | 1,070 | **0** | 30 | 21 |

The strict signed budget is **1,412** expanded vertex occurrences, including Stage9 plane 12. Therefore, although 1,362 unique stored vertices fit, **1,938 expanded vertices do not**. The 576 repeated vertices saved from stored path duplication are not a free pass for rendered geometry. No candidate passes both exact protection and expanded complexity.

**Semantic caution:** compressed variant can retain exact isolated protected masks while other painted owner mask approximations still alter final arm RGB via z-order interactions. Do not confuse exact protected mask itself with the final composited arm color parity. The previous full image candidate has 148 remaining global RGB errors despite 13/13 exact masks. That remains an independent blocker.

## Verified provenance and reproducibility

- New isolated tool: `tools/research/sa1044_shared_geometry.py`. Reuses the prior SA10.43 evaluator's SHA-locked OpenCV source-mask raster and pixel-edge walker; adds frozen exact/protected source geometry sharing, explicit non-aliased signed right arm, `href` reference graph validator, strict unique *and expanded* vertex accounting, real Chromium mask/full-image comparison.
- Regression: `tests/zerobase/test_sa1044_shared_geometry.py`, 8 tests locally passed with frozen source inputs. Private-source integration tests can skip on other environments without inputs. Actual real-image Chromium research run was independently executed.
- **Two independent runs: 7 of 7 generated SVG/PNG/JSON artifacts SHA-256 identical**. Full hashes are included in `sa1044_metrics.json`; no differences hidden in browser effects.
- Visual four-way comparisons and full research outputs are preserved privately at `chatGPT及びCodex用/Minimalizer/SA1044_SharedSourceGeometry_20261009`.
- Fully synthesized facial skin plate, eyes/mouth reconstruction, generative fill, source PNG embedding, and official 3D are forbidden and absent.
- Source owners, palette and all signed images unchanged. Site production not touched.

**Decision:** SHARED-SVG-SEMANTIC-RGB-PARITY PASS for exact verified Raden source; expanded vertex budget **FAIL**, candidate compressed final-arm parity **FAIL**, overall Golden **HOLD**. Never use stored unique vertex count in place of expanded complexity. This is not a universal impossibility proof for different representations.

## Next stage

Investigate **composited-visible source geometry compression** or an alternate low-complexity semantic owner representation with independent post-z-order zero-arm/face RGB gate, accurate silhouette, exact source ownership and a second character holdout. Strictly retain original expanded 1,412 budget; do not simply move masks into `<defs>` and count them once.

## Reproduce

Bring the seven frozen source files referenced in SA10.43 from approved Drive into a separate local input folder, then:

```bash
python tools/research/sa1044_shared_geometry.py --root /path/to/frozen_raden_inputs --out /path/to/sa1044_output --chromium /usr/bin/chromium
SA1044_SIGNED_ROOT=/path/to/frozen_raden_inputs python -m pytest -q tests/zerobase/test_sa1044_shared_geometry.py
```

Dependency set: Python, cv2/NumPy/Pillow/Playwright and Chromium, pytest for tests. The research tool is not installed as a production pipeline entrypoint.