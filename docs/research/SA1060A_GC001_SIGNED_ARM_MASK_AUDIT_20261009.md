# SA10.60A: GC001 signed-arm/source-background ownership diagnostic and non-promoting color trial

Date: 2026-10-09 (JST). **Engineering audit/reproducibility PASS. Candidate promotion HOLD, Golden PENDING, historical Stage8 ring policy HOLD, Phase15 NOT RUN, production UNCHANGED.**

## Authority and baseline

Existing signed GC001 original and Stage04 face/left-arm/right-arm masks are SHA-pinned in `tools/research/sa1060_gc_arm_color_experiment.py`. SA10.57 signed base SVG is `bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939`, rendered in real Chromium 144.0.7559.96 at 340×340 DPR1 to the already signed PNG hash `c51c8bac13f68802b1a7d0022eccd1eff66ae2e4b2f601a7e9b881b936eb4445`.

Previous independent SA10.59 two-person Golden still only contains Raden and GC001. This experiment DOES NOT add a new independent source image to the Golden corpus; it does not claim a new human approval.

## First-bad-stage diagnostic

- Signed Stage04 GC001 left arm mask covers 2,715 pixels, right arm mask 6,486. Signed face guard remains independent.
- A conservative **exact RGB** analysis finds 35,514 background-connected pixels from the dominant scene-border RGB (255,134,46); of these, **533 pixels are inside the signed right-arm mask**, and **0 inside the signed left-arm mask**. This is a 533/6486 ≈ 8.2% exact-color conservative overlap, not the total extent of possible bad semantic binding.
- This is objective evidence that the arm mask has at least a background-connected visual contamination risk, not a full semantic segmentation proof. Diagnose Phase4/owner binding first before claiming that additional drawing corrects arms. Do not modify original signed masks to hide the leak.

## Non-generative SVG trial (NOT approved artwork)

Source RGB-only K-means observation provides a small number of candidate source-pixel-medoid polygon color planes. Proposed contours are derived from original RGB clusters within signed arm regions; no generated fill, external image API, raster-in-SVG, face features, or unverified pixels. Only parent owner groups 2 and 7 receive additional SVG polygons, already clipped by the immutable prior owner masks. No source or other baseline SVG bytes are mutated.

Trial reproduced in actual Chromium:

| Metric | SA10.57 frozen baseline | Unapproved trial |
|---|---:|---:|
| GC001 left signed-arm source RGB MAE | 76.071332 | 59.814733 |
| GC001 right signed-arm source RGB MAE | 55.439562 | 47.365762 |
| True compact research SVG vertices | 1873 | 1884 |
| Separate expanded SVG cap | 1887 | 1887 |
| New observed color polygons | 0 | 2 (5 + 6 vertices) |
| Signed face RGB changes | 0 | 0 |
| Pixels *outside* signed arms changed | 0 | 0 |
| Legacy signed original Stage8 source rings | 3604 / 1887 FAIL | untouched, still FAIL |

The new polygons alter 470 signed left-arm pixels and 499 signed right-arm pixels. The background-overlap audit must not be misrepresented as direct corruption by this particular candidate: the currently tested polygons themselves **do not recolor** the 533 exact-background-connected pixels. Nevertheless, flat arm owners and their source mask binding remain structurally questionable. RGB MAE gains are not artistic correctness, source arm geometry, or a valid Stage8 policy. **Trial rejected for production promotion**. Correct first-bad-stage part mask/ownership and human visual approval are necessary.

## Verification and preservation

- Focused unit and signed input integration: **8/8 PASS** (source pins, true baseline screenshot SHA, exact source color provenance, hard geometry cost, faceless guard, no outside-arm changes, output isolation, missing/corrupted source rejection, background contamination).
- Two independent fresh Chromium evaluations yielded **4/4 identical byte SHA** for generated SVG, PNG, baseline PNG and private comparison board.
- Source inputs are read-only; trial SVG and visual art stay only in private Drive. Public GitHub contains research harness/test, this text report, and **coordinate-free** numeric evidence JSON. No original PNG, mask PNG, traced vector path, or review contact sheet belongs on GitHub.
- Private Drive destination: `chatGPT及びCodex用/Minimalizer/SA1060A_GC001_ArmSourceAudit_20261009`, with manifest, ZIP, review board, trial SVG and derived PNG, original baseline screenshot, test harness/test and private result JSON.

## Next safe engineering step

SA10.60B should inspect signed Phase04 arm overlays and source/owner mask z-binding in the canonical pipeline, establish a new **versioned** candidate part mask in a separate staging area, and prove source-owned arm/garment topology and face preservation *before* introducing new arm repainting. Compare Raden and other independent signed sources. Keep all historical Stage04, Stage8 and SA10.57 SHA authorities frozen. Do not turn this single GC001 recolor into a general-purpose or production change. Golden formal human review and Stage8 policy remain separate HOLD gates.
