# SA10.54: Original-pixel eye-chroma allocation by pixel-exact SVG contour splitting

**2026-10-09. Research-only technical gate PASS on two SHA-signed images. Facial anatomy/identity Golden HOLD; historical Stage8 source-ring gate FAIL; production unchanged.**

## Aim and source rules

SA10.53's prior-budgets (Raden **1,412/1,412**, GC001 **1,882/1,887** vertices) retained 4-color flat face regions but mostly removed original blue or green eyes. This stage tests whether source-observed eye-chroma paint can be restored **without any new path vertices, coordinates, masks or raster embedding** and without repainting outside the signed Stage04 face mask. Original source photos, Stage04/Stage9/Stage37 image and polygon authorities, and both SA10.53 candidate SVG hashes are immutable. No img2img, learned fill, external facial detector or synthetic pupil/iris anatomy is used.

## Implementation: source-pixel proof, conservative pixel-exact restructuring

`tools/research/sa1054_iris_component_palette.py` SHA verifies the signed Raden 7-file and GC001 8-file source authorities and pins both actual SA10.53 SVGs. It first checks every individual independent `M…Z` contour in the existing three face-color paths: separating a contour into a sibling SVG path is permissible **only if the full Chromium composite is pixel-for-pixel identical to the previous composite**. If a contour is a hole or interacts with even-odd painting and the split changes any pixel, that split is reverted. This resulted in **Raden: 13/13 safe splits** and **GC001: 20/25 safe splits, 5 rejected**. No original contour coordinate is edited, and independent SVG mask/body/apparel inventory and true expanded deployed vertex count are checked exactly unchanged.

Within the already visually annotated *approximate* original-2D screen-left and screen-right eye rectangles established in SA10.53, the code reads original HSV hue/saturation/value from the signed source RGB. Raden high-saturation source-blue observed hues are 85–135 (OpenCV scale 0–179); GC001 green observed hues are 35–90. Require source saturation >100, value >70 and at least 12 pixels. The candidate paint is an actual original RGB pixel selected by a deterministic L1-nearest median medoid. The colored-pixel mask is a **color proxy within an approximate eye ROI, not a verified iris/pupil detector**. An eye-colored contour fill replaces its old fill only if a real 340×340 DPR1 Chromium render improves target original-source chroma-pixel RGB MAE, does not worsen either chroma ROI, does not worsen original-source whole-face MAE, preserves the other eye and mouth ROI RGB error, and keeps all pixels outside the signed face **exactly unchanged**. Due to region overlap, eyebrow-only ROI RGB MAE can increase by **at most 0.25**; the actual change is always reported. No extra mask references are allowed.

## Reproduced Chromium 144.0.7559.96 results

| Original-source metric, lower is better | Raden SA10.53 | Raden SA10.54 | GC001 SA10.53 | GC001 SA10.54 |
|---|---:|---:|---:|---:|
| Expanded SVG vertices / cap | 1412 / 1412 | **1412 / 1412 PASS** | 1882 / 1887 | **1882 / 1887 PASS** |
| Whole signed face RGB MAE | 32.991774 | **32.957716** | 27.241105 | **27.163730** |
| Image-left eye color-proxy pixel RGB MAE | 60.641026 | **53.410256** | 55.985507 | **36.028986** |
| Image-right eye color-proxy pixel RGB MAE | 93.712644 | **93.712644 (tie)** | 59.902778 | **43.833333** |
| Image-left eye whole ROI RGB MAE | 33.233743 | **33.045475** | 36.273369 | **36.154762** |
| Image-right eye whole ROI RGB MAE | 34.049715 | **34.049715 (tie)** | 35.762505 | **35.427644** |
| Mouth ROI RGB MAE | 13.287001 | **13.287001 (tie)** | 4.392893 | **4.392893 (tie)** |
| Image-left brow ROI RGB MAE | 46.858333 | **47.000000 (regression +0.141667)** | 34.933204 | **34.898184** |
| All pixels outside signed face, including both arms | prior source | **identical** | prior source | **identical** |

Raden's screen-left source-observed blue medoid is **RGB(79,114,152)**; only one safe existing source contour was recolored. Its screen-right eye did **not** find a non-regressing feasible replacement and remains unchanged. GC001 used actual source green **RGB(148,224,80)** on one already-existing source contour; this changed visible color in *both* approximate eye ROIs while passing the source metrics. This does **not** mean correct iris boundaries or a semantically faithful color placement. The mouth, lids and hair are not claimed reconstructed or improved; the actual zoom board shows large omissions of original facial detail.

## Tests and artifact lineage

- `tests/zerobase/test_sa1054_iris_component_palette.py`: **7/7 PASS** with SHA-signed private originals and SA10.53 SVGs, including source tampering and old SVG hash rejection, source pixel medoid proof, ROI clipping, unsafe source-output separation, actual Chromium complete-scene pixel-equivalent split tests, component accounting, eye color fidelity and strict two-character expanded geometry budgets.
- **Two independent full Chromium executions produced 9/9 SHA-256 identical SVG/PNG/JSON results**. Color layer composition and signed mask/body geometry are preserved by explicit serialization inventory and direct screenshot proof; result hashes recorded in `sa1054_metrics.json` and archive manifest.
- Private original-inclusive full comparison, enlarged face image and actual SVGs are in user Google Drive under `chatGPT及びCodex用/Minimalizer/SA1054_SignedEyeChromaContourReuse_20261009`. **Do not add private SVG or source photo boards to GitHub**; only code, tests, coordinate-free metrics and this report may go to GitHub. No RDC, local worker or deployed web code modified.

## Release gate and next stage

`SOURCE_AUTHORITY_PASS`; `SAFE_COMPONENT_SPLIT_PIXEL_EXACT_PASS`; `TRUE_ORIGINAL_COLOR_SOURCE_PASS`; `FACE_AND_ARMS_STABLE_PASS`; `TWO_CASE_EXPANDED_VERTEX_BUDGET_PASS`; `FULL_CHARACTER_ORIGINAL_IDENTITY_NOT_CERTIFIED`; `HUMAN_REVIEW_PENDING`; `STAGE8_SOURCE_RING_BUDGET_FAIL`; `GOLDEN_HOLD`; `PRODUCTION_UNCHANGED`.

**SA10.55 next:** Test source-observed **separately bounded per-eye color patches** and strong shadow/lid/mouth topology (rather than broad existing contrast faces), and find exact no-op simplifications to fund further non-generative geometric eye detail within the strict budgets. Evaluate true structural eye, iris, lid and mouth proxies separately from whole-face MAE with no regressions hidden by RGB averaging. Keep historical Stage8 policy distinct from deployed geometry limits and require human visual review before production.

## Reproduce

```bash
python tools/research/sa1054_iris_component_palette.py --raden /private/raden --gc001 /private/gc001 --raden-svg /private/SA1053/raden_sa1053.svg --gc001-svg /private/SA1053/gc001_sa1053.svg --out /tmp/sa1054
SA1054_RADEN_ROOT=/private/raden SA1054_GC001_ROOT=/private/gc001 SA1054_RADEN_BASE=/private/SA1053/raden_sa1053.svg SA1054_GC001_BASE=/private/SA1053/gc001_sa1053.svg python -m pytest -q tests/zerobase/test_sa1054_iris_component_palette.py
```
