# Independent source-material holdout on Raden (2026-10-09)

**Decision: source RGB / edge measurement PASS; GC001 material transfer HOLD; full-character Golden HOLD.** This stage neither installs the GC001 palette gate on another character nor deploys changes.

## Why this follows PR #287

PR #287 corrected a locally overpainted GC001 visor, but the positive result was on a single source and a manually annotated one-piece visor. Its source-pale threshold is not a semantic frame detector. This holdout freezes a *different* existing real Golden source, Juufuutei Raden, before evaluating the independent measurement method.

Raden is a **negative/non-eyewear control, not a second verified visor positive**. Her face and signed left/right arm masks are from the preexisting SA10.41 full-character study; they do not certify goggles, hair material, or a new part taxonomy.

## Signed assets and rendering

Inputs are listed, with exact SHA-256 and Drive file IDs, in [Raden input manifest](evidence/raden_source_material_holdout_inputs_20261009.json). The source PNG, full experimental SVG and OpenCV full-character baseline were all verified against their previously saved SA10.41 hashes. Face/arm masks were separately verified by their saved artifact hashes. Source RGB was measured inside each signed mask **only where source alpha > 0**; this excludes 74 alpha-transparent pixels in the left-arm mask and avoids treating unknown transparent background as character material.

The unchanged SVG was rendered by **Chromium 144.0.7559.96**, Playwright, 340 × 340 CSS pixels, DPR 1. No original raster source is embedded in the SVG. The role-based source comparison and source-edge distance use native original RGB, not the SVG's own mask. The full trace is in [actual metrics](evidence/raden_source_material_holdout_metrics_20261009.json).

| Raden signed visible source part | OpenCV original-source RGB MAE | Real Chromium SVG original-source RGB MAE | SVG minus OpenCV |
|---|---:|---:|---:|
| Face (4,052 px) | 50.75263 | 50.92078 | +0.16815 |
| Left arm (10,345 px) | 23.45065 | 27.27646 | +3.82581 |
| Right arm (9,870 px) | 25.66001 | 29.34468 | +3.68467 |

This is **source-image fidelity** testing, not the separate browser-to-OpenCV exact raster parity from SA10.41. A lower source MAE would not by itself prove correct anatomy.

## Source geometry edge checks and invalid generalization

| Role | Signed perimeter near original Canny edge (within 2.5 px) | Vertically shifted signed-mask negative control | Frozen GC001 pale RGB class in Raden part |
|---|---:|---:|---:|
| Face | 89.933% | 67.953% | 65.523% |
| Left arm | 67.839% | 63.672% | 1.102% |
| Right arm | 76.801% | 29.025% | 4.823% |

Proximity to *some* Canny edge is not evidence that this is the correct semantic outline. Left-arm boundary evidence is weak relative to the shifted negative control, so geometry promotion is explicitly forbidden. More importantly, the frozen GC001 white/silver RGB gate labels much of Raden's **face** while discarding nearly all of her signed **arms**. Therefore, a color threshold is only a source-pixel observation, never generalized semantic part ownership. No GC001 candidate is accepted on Raden.

## Verified outputs and scope

- Research evaluator: `tools/research/source_material_holdout.py`; checksum-locked inputs, Chromium raster, Canny shift control, masked native RGB MAE, color-transfer negative probe, PNG comparisons, machine-readable gate record.
- Regression: `tests/test_source_material_holdout.py`. **5 local synthetic tests passed**. One real Raden run completed using the exact frozen inputs. This is not an assertion that the whole repository CI suite ran.
- Original Raden visual source, saved baseline and masks remain untouched. No face/eyes/nose/mouth construction, image generation, generative fill or production pipeline edits.
- Real comparison, Chromium raster and RGB error heatmap preserved in approved private [Drive holdout artifacts](https://drive.google.com/drive/folders/13zjlc2uayrd-iKv-ih6ezmeAksSzp0ZQ) beneath `chatGPT及びCodex用/Minimalizer`. All three PNG SHA-256 values appear in the metrics manifest.
- **Release gate: NO-GO.** Neither another real positive visor holdout nor whole-character Golden quality is proven.

## Reproduce

Place the seven original **unchanged** input files from the Drive IDs in the input manifest into one directory, then run:

```bash
python tools/research/source_material_holdout.py \
  --root /path/to/frozen_raden_inputs \
  --manifest docs/research/evidence/raden_source_material_holdout_inputs_20261009.json \
  --out /path/to/raden_holdout_outputs
python -m pytest -q tests/test_source_material_holdout.py
```

Dependencies: OpenCV, NumPy, Pillow, Playwright plus a working Chromium binary (and pytest for tests). Fail closed on source/SVG/baseline/mask hash differences, changed size, empty signed owner, external raster `<image>` or `<foreignObject>` in SVG.

## Next

Stop copying GC001-specific pale color rules. Investigate source-owned **face/arm SVG raster semantics**, including zero-alpha ownership, small components, contour holes, and actual browser parity per owner (SA10.42), then restore whole-character face visibility, clothing and arms **using only observed source geometry/color**. A new independent positive visor reference would be a separate optional study, not a substitute for the full-character deficit.