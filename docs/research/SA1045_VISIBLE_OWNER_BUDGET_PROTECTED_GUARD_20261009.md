# SA10.45: Composited-visible source owner compression with protected-pixel guard (2026-10-09)

**Research result:** for **one frozen Juufuutei-Raden source**, the actual deployed 340×340 SVG can be built with **1,409 counted expanded geometric vertices** under the unchanged **1,412** limit, while actual Chromium retains exactly **0 RGB mismatches inside the signed source face, left arm and right arm masks**. The whole-character RGB parity is **not** achieved: **882 mismatched pixels** remain. Historical original Stage8 ring budget is still **2,370 > 1,412** (FAIL). **No production promotion, no Golden PASS, no multi-character generalization.**

## Source authority

The seven original private artifacts are verified by fixed SHA-256 in `tools/research/sa1043_boundary_compaction.py`: Raden original source, Stage8 signed contour scene, canonical OpenCV preview, original full SA10.41 SVG, original Stage04 signed face/left/right arm masks. Source owner z-order is frozen and 11 original owners remain in immutable provenance. Chrom(e/ium) source is rendered by actual browser Playwright at 340×340 DPR1. No embedded bitmap, generative fill, forged face parts, material reassignment, PNG-to-SVG trace painting, or official 3D is used.

This signed Raden negative apparel case contains a **single Stage9 hair color plane** and **zero Stage37 apparel polygons**. The Stage9 hair owner source mask is disjoint from the union of signed face and arm masks, even though the unmasked Stage9 polygon itself would overlap a few protected pixels. Therefore the original inverse-protection wrapper was redundant **only inside this proven hair-owner mask**. A structurally supporting head owner is not painted. The source face owner is entirely overwritten by the final **opaque signed face guard**, with equal original source mask, and is likewise a no-op in this source scene. The respective unused SVG mask definitions are omitted from the *deployed* research SVG. All original source masks remain unchanged and lineage counts are reported separately. If the original negative apparel/guard/owner assumptions do not hold, the tool **fails closed**.

## Real Chromium results

Original source-defined Stage8 owner vertices: **2,370**, original Stage8 source budget **FAIL**. Deployed research SVG accounting includes all 10 actually referenced masks, 12 Stage9 extra vertices, and **4 vertices for every single black protected-trim rectangle**. Omitted source definitions are neither secretly present in `<defs>` nor counted as free reference uses. The original strict cap is never increased. This deployed-count experiment does not repair the historical original Stage8 budget failure.

| Source-signed Raden candidate | Real deployed expanded vertices | Full RGB mismatch pixels vs signed OpenCV | Signed face | Left arm | Right arm | Verdict |
|---|---:|---:|---:|---:|---:|---|
| SA10.41 original Chrome SVG | 2,976 | 2,681 | 122 | 237 | 255 | FAIL |
| SA10.44 source-exact reference | 4,086 | 148 | 0 | 0 | 0 | complexity FAIL |
| SA10.45 composited-visible exact | **2,994** | **148** | **0** | **0** | **0** | exact render PASS, complexity FAIL |
| SA10.45 uniform 1.0 epsilon | **1,310** | **832** | **0** | 14 | 19 | strict protected FAIL |
| SA10.45 guarded selective approximation | **1,409** | **882** | **0** | **0** | **0** | rendered complexity + protected PASS; global Golden HOLD |

The exact visible-geometry SVG produces **bit-for-bit identical Chromium rendered pixels** to the SA10.44 exact reference, with 1,092 fewer deployed expanded vertices. The guard candidate improves the prior SA10.44 shared-unique-budget variant's **1,938 vertices / 1,070 full RGB errors / 30 left arm / 21 right arm** to **1,409 / 882 / 0 / 0**. Its mask error outside signed protection remains nonzero and it **does not** equal the exact Chrome composite.

## Guarded approximation procedure

1. Preserve original signed z-order, 11 owner records and shape provenance; compute each *finally visible* mask from original opaque front-to-back source owners and final signed face guard. Reject unexpected Stage9 parent, nonempty Stage37 garment content, signed protected source overlap, or source SHA change.
2. Remove only SVG paint/masks proven unreachable under those frozen assumptions. The historical Stage8 source geometry is **not claimed to have vanished**.
3. Enumerate `cv2.approxPolyDP` pixel-boundary approximations at epsilon 0.5, 0.75, 1.0, 1.25 and 1.5 for each nonprotected owner. Render each candidate mask in actual Chromium. Compare every source-protected pixel with signed face and arm masks.
4. For color-paint intrusion **only where the signed original source owner has no protected pixels**, place source-derived exact black rectangle holes **inside that SVG mask**. The black pixels suppress overpaint, not fabricate missing anatomy. Merge row spans deterministically; count **4 vertices per rectangle**. Do not use a post-hoc bitmap or overwrite an original arm/face layer.
5. Solve a finite multi-choice budget DP choosing the minimum total *unprotected mask mismatch* among combinations that fit **at most 1,412 expanded vertices** including all holes and 12 signed Stage9 vertices. This is a research heuristic, **not** a release visual-quality gate.
6. Independently rerender the full candidate and check: expanded count, signed face/left/right RGB error **zero**, and globally compare against original signed OpenCV reference. Any protected mismatch or uncounted geometry must hard fail.

Guarded DP selected: `owner-0=1.5, owner-1=1.25, owner-4=1.25, owner-6=1.0, owner-7=1.25, owner-9=1.0, owner-10=1.0`; original source right and left arms and final face guard retain exact source boundary epsilon 0.5. The 1,409 figure includes all black mask-erase rectangles as geometric occurrences. It is not the count of merely stored unique paths.

## Testing, reproducibility, evidence and release

- `tools/research/sa1045_visible_geometry.py` implements actual browser experiments and generates SVG, PNG, comparison board and full JSON ledger in a *separate output folder*.
- `tests/zerobase/test_sa1045_visible_geometry.py`: **10 tests passed** with the signed source root and real Chromium; includes source tampering fail-closed, no-apparel hard gate, protected-mask collision negative gate, every rectangle vertex count, source owner order and actual signed browser integration.
- Two independent complete runs produced **16/16 byte-identical SHA-256 artifacts** in the same environment, including the complete ledger and candidate SVGs.
- Real-source private visual evidence saved in approved `chatGPT及びCodex用/Minimalizer/SA1045_VisibleSourceGeometry_20261009`, with separate full research ZIP, SVG, PNG, signed metric JSON and comparison image. Do not commit input PNG or private rendered PNG into GitHub.
- The JSON evidence in GitHub records the rendered results; source hashes are frozen and independently checked by the tool. Do not claim CI passed without a confirmed GitHub Actions run.

**Release: HOLD** because one negative-case study is insufficient, full RGB is still 882px off the signed OpenCV target, source historical Stage8 vertex budget remains FAIL, silhouette/owner-material/visual gates have not passed in a positive holdout, and the original strict budget semantics require review of source-lineage accounting before calling this a production-level budget pass. NO LOCAL/PUBLIC/WORKER site changes.

**Next SA10.46:** improve globally visible hair/major-clothing/unknown material shapes and edge accuracy while retaining zero source face/arms, and validate GC001 as independent positive holdout. Do not waive source-lineage, expanded geometry, or signed protected-region gates.

Reproduce (private source must already be available on approved Drive and SHA-verified; do not store in the repository):

```bash
python tools/research/sa1045_visible_geometry.py --root /path/to/signed_raden_inputs --out /path/to/sa1045_result --chromium /usr/bin/chromium
SA1045_SIGNED_ROOT=/path/to/signed_raden_inputs python -m pytest -q tests/zerobase/test_sa1045_visible_geometry.py
```
