# SA10.50: Two-character source-observed SVG color boundaries, source/flat dual quality gate

2026-10-09 · **Research prototype PASS; strict expanded-vertex budgets FAIL; full Golden/production HOLD.**

## Goal

Go beyond SA10.49's diagnostic: actually render original-input-observed color boundaries for facial features, hair, and major apparel via geometric SVG, with a real Chromium run and an *original-source* RGB metric distinct from the frozen Stage37 flat OpenCV metric. No img2img, generative fill, inpainted or inferred anatomy, source image SVG embedding, or official 3D. Every emitted paint color must appear verbatim in the authenticated original RGB source.

## Implementation

`tools/research/sa1050_source_color_vectorization.py` verifies the private signed 7-file Raden/8-file GC001 authorities via the Stage10.49 loader and also verifies the two immutable, SHA-256-pinned SA10.45/SA10.48 best deployed-budget research SVGs. Chromium reproduces the original signed flat-reference mismatch counts *882* (Raden) and *1,871* (GC001) before making changes.

For each 340×340 signed Stage04 face mask, extract 4 source-observed color clusters from a lightly smoothed LAB observation, deterministically with fixed OpenCV seed. Convert source cluster regions into explicitly sourced polygons, preserving source pixel medoid RGB as SVG fill. Recolor the existing signed face guard's flat face using the source-observed dominant paint; paint other colors in a group using the existing source-signed face guard mask. Count **every face path vertex plus the second expanded face-mask reference** (138 Raden/140 GC001). Chromium confirms **exactly zero changed RGB pixels outside the signed face** in this face-only stage. This is observed color quantization, **not** an explicit eye/nose/mouth semantic detector or identity reconstruction.

Test four extra original-source topmost owner materials (`hair`, `major_clothing`, `lower_body`, `torso`) independently: add source LAB color clusters with real medoid colors as interior SVG paths into the *existing masked owner group*, behind Stage9/Stage37 supplied color polygons. Retain only proposals that actually decrease the Chromium-rendered foreground/source-owner RGB MAE and do not modify either signed arm relative to the original best SVG. No source-owned z-order or protection mask shape is altered. Colors are not generated. Every new path vertex and reused face-mask vertex reference is included in the expanded budget; no aliasing trick reduces the count. Because a previous SA10.45 SVG uses a differently named trim marker, its 50×4 trim vertices are explicitly counted instead of silently dropped.

## Chromium 144.0.7559.96, DPR1, 340×340: source-image comparison

| Metric, **lower is better** | Raden prior champion | Raden observed detail | GC001 prior champion | GC001 observed detail |
|---|---:|---:|---:|---:|
| Original source face-region RGB MAE | 50.752632 | **31.191346** | 54.766660 | **30.804942** |
| Original source character-region RGB MAE | 29.278547 | **22.415575** | 47.924278 | **37.506238** |
| Original signed arm image RGB vs prior champion | reference | **unchanged** | reference | **unchanged** |
| Full expanded SVG vertex occurrences | **1,409** | **2,308** | **1,883** | **2,746** |
| Existing hard vertex limit | 1,412 | **FAIL +896** | 1,887 | **FAIL +859** |

These foreground masks derive from source owner-visible masks and the source-signed face mask; they are **not** the same metric as source-photo vs whole white-background SVG RGB error. The photograph background is colored while the signed SVG background is white, so whole-scene original RGB MAE would be dominated by background and is not used to claim character quality. Pixels are not segmented into semantically correct materials solely by owner labels. All 4 per-case owner color proposals improved original-source MAE and retained the inherited Stage9/37 polygons. Raden face paint uses 223 new path vertices + 138 additionally expanded mask vertices = **361**; GC001 face uses 210 + 140 = **350**. Further source-observed hair, apparel and torso interior path vertices are counted individually in the JSON report.

**Do not conflate source fidelity with preservation of the frozen flat face.** The prototype intentionally adds legitimate facial color within the immutable signed Stage04 face geometry, so the *old flat-RGB-face 0px gate is no longer a release criterion for original-source fidelity*. The new criterion is actual original-source face MAE plus shape/arm-protection checks. No verified facial landmark classifier or human review has approved restored individual eye or mouth anatomy. Real image comparison still reveals missing fine details and hard color facets in hair and apparel. Strict SVG budget is not met, historical Stage8 original-source vertex budgets remain failed; Golden, human visual approval, and production remain HOLD. The prior best deployed-budget candidates stay untouched.

## Reproducibility / artifacts

- `tools/research/sa1050_source_color_vectorization.py`: source-authenticated deterministic k-means, actual original-color medoids, source contour conversion, SVG masking, strict expanded geometry ledger, Chromium MAE/gates, research PNG/SVG/report.
- `tests/zerobase/test_sa1050_source_color_vectorization.py`: **10/10 PASS with private authenticated inputs**, covering champion SHA tamper and source SHA tamper, palette provenance, deterministic replay, mask reference accounting, no RGB spill outside face, no arm RGB edits, strict budget rejection, source-output separation and real Chromium measurement.
- Two fresh independent full evaluations: **12/12 produced SVG/PNG/JSON files SHA-256 identical**. The report includes SHA-256 of every sidecar except its own.
- Google Drive approved private path `chatGPT及びCodex用/Minimalizer/SA1050_SourceObservedColorBoundaries_20261009` stores the comparison containing original photo, source-observed SVG and full diagnostics. **No original source photo, board containing private photos, or vectorized character SVG is committed into GitHub**. Public GitHub contains only code, tests, documentation and path-redacted summarized measurements (source RGB colors are approved source medoids; no raw pixel positions in metrics JSON).
- Original source images/masks and prior candidate SVG files unchanged; production site and worker unchanged; no RDC.

## Next SA10.51

Solve *expanded vertex allocation* for original-source detail. Current best shape-protected candidates have only three/four spare vertices. A genuine rendered facial-feature upgrade cannot be enabled in those candidates without reshaping or reducing the other source geometry, or changing the budget, which is forbidden. Explore multi-owner shared vector boundaries, mask-reference costs, and source-observed color regions with lower cost, while accepting only source-image visual improvements at the two-character hard budget and retaining arm geometry. Only approve deployment after separate Stage8 issue and human visual/Golden gates are actually resolved.

## Reproduce

```bash
python tools/research/sa1050_source_color_vectorization.py \
  --raden /path/to/sha-locked-raden --gc001 /path/to/sha-locked-gc001 \
  --raden-svg /path/to/SA1045/visible_guarded_budget.svg \
  --gc001-svg /path/to/SA1048/gc001_guardless_component_budget.svg \
  --out /path/to/sa1050_outputs
SA1050_RADEN_ROOT=/path/to/sha-locked-raden \
SA1050_GC001_ROOT=/path/to/sha-locked-gc001 \
SA1050_RADEN_CHAMPION=/path/to/SA1045/visible_guarded_budget.svg \
SA1050_GC001_CHAMPION=/path/to/SA1048/gc001_guardless_component_budget.svg \
python -m pytest -q tests/zerobase/test_sa1050_source_color_vectorization.py
```
