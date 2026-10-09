# MinimalizerPublic Stage8 geometry research closing audit, 2026-10-09

## Scope and decision

**Research loop documented and frozen; NOT production-release complete.** Study the non-generative contour minimization of the immutable SA10.34 signed GC001 and Raden originals with full official OpenCV even-odd owner mask identity, and retain the existing face-features-hidden design. A successful research raster replay does not imply a Golden approval.

## Frozen source and best candidates

| Case | Immutable original signed Stage8 vertices | Latest research candidate | Saved | Historic original cap | Budget result |
| --- | ---: | ---: | ---: | ---: | --- |
| GC001 | 3,604 | **1,937** | **1,667** | 1,887 | **FAIL, 50 over** |
| Raden | 2,370 | **1,176** | **1,194** | 1,412 | **Candidate PASS, 236 under** |

Latest independent verification directly against original signed 11-owner Stage8 scenes **PASS for both cases**: full raw 340x340 pixel equality of every owner, identical 8-connected component counts, contour-hole RETR_TREE hierarchy and stable primitive identity/owner/color. This is a **research candidate gate**; the immutable signed originals were never overwritten.

Latest technique: rotate cyclic starting indices of each closed contour through six shift variants and apply source-exact nearby-grid greedy fusion. GC001 1,941 -> 1,937 (four additional points); Raden 1,177 -> 1,176 (one point). Prior OpenCV approxPolyDP strict pixel parity tried multiple epsilon values and saved zero vertices; this negative result was preserved too. Significant diminishing returns were observed after radius 7/8 and six cyclic shifts.

GC001 current bottlenecks from before cyclic update: hair 578, unknown/unbound 411, major clothing 234, torso 161. The 50 unresolved vertices cannot be declared removable without verified new algorithmic evidence. No implicit raising or redefining the historic cap.

## Release readiness matrix

- **PASS (research):** immutable original source identity; 11-owner canonical 340x340 OpenCV raw raster exact replay; original-owned masks, component counts, RETR_TREE hole hierarchy; original primitive ownership/palette/z preservation in candidate.
- **PASS (research candidate only):** Raden ring count under original cap 1,412.
- **FAIL:** GC001 strict original ring vertex cap (1,937 > 1,887 by 50).
- **NOT VERIFIED/HOLD:** candidate SVG serialization and high-DPI Chromium DPR1/DPR4 edge/alpha/source-owned RGB replay. An OpenCV pixel-center match does not establish SVG path/winding/sampling equivalence.
- **NOT VERIFIED/HOLD:** whole-character 40-shape nonface color MAE, clothing/arms/tie visual fidelity, Golden side-by-side/human review, mobile iPhone Safari, final production integration/rollback.
- **PRESERVED:** non-generative-only policy, original source owner masks, no newly drawn eyes/nose/mouth, no production source switch.

## Reproducibility and future research queue

Public code `stage8_completion_owner_pareto.py` and `stage8_cyclic_start_probe.py`, baseline official polygon replay `stage8_official_polygon_replay.py` and source independent validator `stage8_multi_point_original_gate.py`; prior PRs #330–#342 document the iterative geometry search. Private candidate source geometry, evidence, source PNG SHA and per-owner masks reside **only** under `chatGPT及びCodex用/Minimalizer`. The latest signed candidate and gate data: `PublicGeometryJS_CompletionGate_20261009`.

To complete the remaining engineering study, prioritize **GC001 contour-graph/owner sharing exact-geometry optimization** to close 50-vertex gap, and create browser-renderable SVG that respects singleton/2-vertex source rings without inventing paint. Compare Chrome and Safari at DPR1/4, source RGB and full-character 40-shape Golden. Obtain user human visual acceptance before merging/deploying. Preserve private authority rather than publishing raw source PNG/coordinates.

**Final conclusion:** Source-raster geometry exploration produced substantial, reproducible improvements; **overall production research-to-integration readiness is HOLD**. Not eligible to mark full user-requested research and release as 100% complete, and not appropriate to issue a merge.
