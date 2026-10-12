# MinimalizerPublic P0 Stage52–56: Source-exact SVG stroke encoding, research-only

Date 2026-10-12. Scope ONLY Draft PR #390 branch `research/public-structural-recovery-p0-part-preservation-20261011`. Existing production preview `web/static/structural-p0-stage51-preview.html` and default site untouched, main untouched, Local Minimalizer untouched. Original source defines observed features; no hallucinated parts, generative fill, img2img or inpaint. All original photos, masks, colored visual diagnosis PRIVATE in canonical Drive under `chatGPT及びCodex用`.

## Stage52: geometry encoding alternative

Introduced `web/static/public-source-stroke-cover-p0.mjs`. Convert each SHA-pinned binary *source-observed part mask* to disjoint run rectangles via existing Stage49 code; consider both source axes and choose fewer rectangles. Encode each rectangle as a centered SVG `path` stroke with exact integer boundary and `stroke-linecap=butt`. Count **two line endpoints** per rectangle, instead of four contour/rectangle polygon vertices. Geometry exact algebraically by rectangle partition; center and width are derived only from source pixels. Source pigment NOT inferred, and this module emits black diagnostic strokes only, not colored render output.

## Stage53: fail-closed SVG emission

Recompute SVG commands from validated rectangle endpoints, verify all line fields and the precomputed SVG string match; reject injected markup, falsified width, stale mask SHA, unrecognized orientation, nonbinary masks, empty shape, source size errors and cut-short stroke budgets. Never permit external markup as code. Stroke endpoint count is **not formally interchangeable** with polygon vertex complexity: `endpointCostComparableToPolygonVertexBudget:false` always.

## Stage54: actual source-part Chrome 340/680 parity

Four source-only observed parts, GC001 eyewear (`goggles_highlight`) and Raden accessories (`bow_mid`, `bow_shadow`, `lacing_mid`); loaded exact 340×340 source observations from prior Stage5/Stage12/Stage47 PRIVATELY archived SHA lineage. Rendered actual SVG strokes in **headless Chromium 144** using a browser canvas at 340×340 and 680×680, compared every alpha pixel against 1x and nearest-duplicated 2x source mask. Eight comparisons: **zero mismatch, zero spill, zero missing, zero partial alpha**. This is a real Chromium browser test, NOT Safari, NOT full-color/full-body Golden and NOT an official deployed Public origin test.

| Case and observed part | Original contour polygon vertices | Stroke segments | Stroke endpoints | Endpoint reduction | Source-pixel mask proof at 340 / 680 |
| --- | ---: | ---: | ---: | ---: | --- |
| GC001 goggles | 398 | 123 | 246 | 152 (38.2%) | 0 / 0 mismatch |
| Raden bow_mid | 686 | 220 | 440 | 246 | 0 / 0 mismatch |
| Raden bow_shadow | 838 | 281 | 562 | 276 | 0 / 0 mismatch |
| Raden lacing_mid | 444 | 143 | 286 | 158 | 0 / 0 mismatch |
| **Raden subtotal** | **1968** | **644** | **1288** | **680 (34.6%)** | **0 / 0 mismatch** |

This encoding changes the representation, not the source pixel boundary. Grouped SVG path commands save shape endpoints; **stroke width itself is geometry**, so Stage8's earlier polygon-vertex budget cannot be marked PASS on these numbers alone. The full-scene reference remains **GC001 3604>1887 and Raden 2370>1412**, historically failing. These mask parts do not constitute a whole person. Stage52–54 do NOT fix eyes/face/arms, palette errors, missing limbs or existing Full SVG scene.

## Stage55: multiple observed-feature isolation, private comparison

Introduced `web/static/public-source-stroke-bundle-p0.mjs`. Rejects feature overlap, duplication, fake reviewer certification, untrusted feature names, signed face collisions, nonbinary and changed SHA-pinned data; holds independent review flags FALSE. GC001 `1173/1173` observed eyewear pixels, Raden `5049/5049` observed accessory pixels algebraically and by browser union-alpha confirmed. Produced private side-by-side source, orange original-observation overlay, blue SVG-stroke footprint and zero-difference maps. Overlay colors are **diagnostic labels, never actual Minimalizer output**. A source-provided hash proves byte consistency only; genuine reviewer identity and anatomical truth require outside evidence.

## Stage56: regression and release classification

New Node research tests `tests/js/test_public_source_stroke_stage52_55_p0.mjs`: 30 tests (geometry, limits, mutation, XML tampering, mixed signed parts, face, independent review and no release). Add to original Stage36 research CI adapter, check actual GitHub Actions job logs. Research SHA / Chrome evidence and pixel-exact private test artifacts must be stored in Drive. If CI not yet complete, mark CI PENDING; no inference from local tests.

**HOLD**: No new independent sleeve/skin/hair labels; no source-attested whole-character re-render; no source color semantic Golden; no Stage8 vertex budget approval; no real iPhone Safari, no product rollout of new renderer; production remains stable Stage51 comparison page only. Next Stage57+ should investigate source-observed *full* topology/shape budget and eye/arm/torso protection, not assume stroke masks resolve anatomy.
