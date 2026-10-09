# MinimalizerPublic exact geometry serialization experiment (2026-10-09)

**Research-stage serialization PASS; Stage8 original source vertex Gate HOLD; production NO-GO.** Follow-up to Draft PR #327.

Two signed GC001/Raden original Stage8 10-painted-owner masks and frozen L1 40-shape full-character SVG candidates were used unchanged. All face microfeatures remain disabled; no generated pixels, raster images, modified owner geometry or new RGB colors.

The input clip paths consisted exclusively of verified orthogonal integer `M x y L x y ... Z` instructions. Each original corner endpoint was retained, and axis-aligned absolute `L` commands were converted to `H` / `V`. This is lossless **SVG command-level compression**, not reducing original vertices.

| Case | Original clip path characters | Encoded characters | Saved | Unchanged vertices | Counted shapes |
| --- | ---: | ---: | ---: | ---: | ---: |
| GC001 | 45,928 | 27,278 | 18,650 | 5,353 | 40 |
| Raden | 30,838 | 17,561 | 13,277 | 3,586 | 40 |

Rendering regression: CairoSVG original vs recoded RGBA at 340×340 (1x) and 1360×1360 (4x). **Both characters at both resolutions: exact 0 differing RGBA pixels**. These are CairoSVG comparisons, not Safari or Chromium multi-browser certification. The original stage8 input ring counts of GC001 3,604 > 1,887 and Raden 2,370 > 1,412 remain frozen FAIL/HOLD. New lossless encoding does not change them or evade the separate browser-rendered 5,353 / 3,586 vertex counts.

Research script: `tools/research/public_geometry_js/lossless_path_encoding.py`. Test conditions for retained islands and holes, malformed paths, and exact 40 shape contract are in `test_lossless_path_encoding.py`. Strict parser rejects unverified paths. Do not use this as an authorization to merge or deploy. GC001 40-shape color MAE was still 42.012781 versus existing champion 40.318419, and human Golden remains PENDING.

**Decision:** code-size optimization PASS. Vertex reduction Gate HOLD, RGB Golden HOLD, iPhone Safari HOLD, production unchanged. Next must separately address source-ring budget in a source-authorized versioned decision or find a legitimately topology-parallel but semantically exact representation counted under unchanged budget policy; no unapproved budget waiver.
