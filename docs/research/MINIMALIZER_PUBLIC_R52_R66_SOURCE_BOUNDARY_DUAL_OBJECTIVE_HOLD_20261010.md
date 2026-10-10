# MinimalizerPublic R52–R66 | Pinned source-boundary corrections and double-objective negative controls

2026-10-10 | **Fifteen continuous research stages executed, source-to-Chrome evidence verified; source photo semantic and production approval HOLD.**

## Authentic signed sources and hard boundaries

This Draft research stack builds upon R50–R51 Draft PR #384. Inputs are genuine signed original source photographs **GC001** and **Raden**, frozen 11-owner SA10.34 Stage8 geometry, unchanged source RGB palette, original Stage04 protected arms/face where applicable, R37 exact Chrome owner renderer, and immutable R6 8-gate NO-GO evidence.

The research **never overwrites** original source photos, original masks, original owner/palette/Stage8 geometry, Local Worker, public production assets, GitHub main or deployed host. It uses no img2img, Generative Fill, image completion or generated face parts. All source-derived candidate PNGs, SVGs and photo comparison sheets are **private Google Drive only**; the public repository has reusable algorithms, tests and a coordinate-free numeric report.

### R52: source-original photographic RGB/luminance and Stage8 owner provenance

Reauthenticated photo and original Stage8 SHA-256, independently reconstructed 11 source owner masks. Used original RGB/alpha, conservative original mask centers, source photo luminance and LAB/HSV color-edge observers. Source photo transparency at 340px is not a semantic arm segmenter. No untrusted proposed source mask can replace the authentic Stage8 original.

### R53–R55: source-photo seeded graph-cut, restricted to the existing 1-pixel outline

`scripts/verify_public_r52_r57_source_boundary_candidates.py`: OpenCV GrabCut observes image colors but modifies only pixels on the **signed original owner's 1px inner/outer border band**; original 2px-eroded interior fixed; other protected face/arm masks frozen. Metrics must independently preserve components and hole contours, remain within 5% affected pixels, and avoid worsening LAB chroma boundary evidence.

The first full six source-derived shape candidates are all **REJECTED** for preview/release:

| Photo / owner | Original 1px-region changed source pixels | Source photo mean luminance-edge gain | Why first candidate fails |
|---|---:|---:|---|
| GC001 right_arm | 386 | +18.607 | excessive affected area; topology change |
| GC001 left_arm | 367 | +16.108 | excessive affected area; topology change |
| GC001 major_clothing | 1,349 | +12.296 | excessive area; topology; chroma degradation |
| Raden right_arm | 290 | +14.210 | topology; chroma degradation |
| Raden left_arm | 382 | +12.589 | chroma degradation |
| Raden major_clothing | 1,253 | **−12.112** | excessive area; topology; edge/chroma degradation |

An apparently improved single edge score **is not evidence that an arm got better**.

### R56–R57: Chrome-authority raster and original release blockers

For all six diagnostic source contour candidates, independent actual Windows Chrome at **340px and 680px** renders the original and candidate bit-exact to their respective 340px signed binary raster (using R30 exact pixel rectangles, both original row-run and vertical-merging variants), and changes zero pixels outside the proposed mask delta. This validates browser behavior, **not anatomy**. R6 eight original release blockers, face microfeature hiding and historic Stage8 budget remain HOLD.

### R58–R61: select only tiny topology-preserving edge improvements

`scripts/verify_public_r58_r61_conservative_source_boundary.py`: greedily select a *subset* of the prior R53 source-band proposal (≤1% owner pixels, same components and holes, ≤2% original boundary length increase), with positive source-photo SOBEL luminance and chroma edge scores. Separately evaluate image-derived **SCHARR** LAB+HSV and Canny boundary coincidence, retaining only research previews with non-regressing alternate scores. Every source-derived mask stays private.

| Photo / owner | Tiny research boundary changes | Alternate SCHARR gradient gain | Alternate Canny gain |
|---|---:|---:|---:|
| GC001 right arm | 49 | +104.795 | +0.009414 |
| GC001 left arm | 27 | +51.183 | +0.005934 |
| GC001 major clothing | 37 | +45.652 | +0.000909 |
| Raden right arm | 24 | +38.654 | +0.009172 |
| Raden left arm | 15 | +26.299 | +0.007823 |
| Raden major clothing | 32 | +26.351 | +0.005505 |

The alternate source-edge metric is **not** independent source-photo part annotation or human Golden. Exact Chrome 340/680 mask delta was again verified.

### R62: critical negative control, source RGB color-match actually worsens

`scripts/verify_public_r62_r66_dual_photo_color_edge.py`: render full 11-owner source Stage8 RGB/z-order in exact native Chrome, and compare original vs R58's edge-only experimental composite against the **real original photo RGB** (source photo unmodified).

| Photo | R58 changed whole-canvas pixels | Changed pixels closer to source photo | Changed pixels farther from source photo | Global original photo RGB MAE effect |
|---|---:|---:|---:|---|
| GC001 | 113 | **18** | **95** | **+0.070222** worse |
| Raden | 63 | **10** | **53** | **+0.054296** worse |

Thus R58 gradient gains cannot justify a source-quality signoff. Source RGB fit across the original photograph is a separate necessary (but not sufficient) condition.

### R63–R66: tiny dual-objective previews, still NOT approved anatomy

R63 retains only original-alpha-opaque pixels where the **actual 11-owner z-ordered candidate canvas RGB** is strictly *closer* to original source photograph than the untouched baseline. R64 repeats original-source topology/cap and alternate SCHARR/Canny. Raden's left-arm option failed the alternate gradient test and was restored to the original signed owner shape.

| Photo | Changed full composite pixels kept | Original-photo RGB improved | Original-photo RGB worsened | Global source RGB MAE difference |
|---|---:|---:|---:|---:|
| GC001 | **18** | 18 | **0** | **−0.009983** |
| Raden | **8** | 8 | **0** | **−0.009065** |

These are tiny, **source-photo-fit-selected** improvements with strong selection bias; they do not independently certify original facial/arm anatomy, coherent garment/tie/staff ownership, visual quality, silhouette aesthetics, human Golden or source crop boundary ground truth. They remain PRIVATE candidate previews. Original signed owner geometry/palette remain unchanged.

R65 independently constructs original and previewed **full 11-owner colored vector SVG** using R30 rectangles, authentic original RGB and exact source back-to-front order; actual Windows Chrome **340px and 680px** renders bit-exact versus separately computed NumPy composition in both baseline and candidate. No rendering spill, no generated photo pixels.

R66 release gate explicitly maintains original R6 **8 blocked** (human semantic owner and Golden, Stage8 cap, full-scene Chrome/resvg Facet DPR2, iPhone Safari physical checks, legal redistribution and live-host rollback). Original Stage8 GC001 **3,604 > 1,887**, Raden **2,370 > 1,412**. `productionReleaseAuthorized=false`, source files unchanged, PR Draft and unmerged.

## Validation, isolation, privacy, next

- Targeted R52–R66 tests: **16 PASS**, including signed trust band restriction, source topology/hole reject, source photo RGB non-worsening, forged source/palette/face status, real Chrome owner and whole composited DPR2 parity.
- Selected Public R1–R66 + Local/Public isolation full regression: **250/250 pytest PASS** in genuine Windows environment.
- Preserve authenticated original source JSON + raw photos outside public GitHub. Private artifacts under `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R52_R66_20261010`, All **27/27 private source-derived PNG/SVG/JSON files** re-generated in a second independent actual Chrome execution and found **bit-for-bit SHA-256 identical** (R52–R57: 7; R58–R61: 7; R62–R66: 13). Preserve canonical Drive readback SHA after upload.
- Next meaningful task R67: human source-photo semantic Golden comparison using independent actual source owner annotations. Potential R67 preview should compare *source photo part ROI* and historic silhouettes with a real reviewer, not automatically treat +0.01 RGB-MAE as repaired arms.

**Research finding:** Browser and source-photo color nonregression can be made technically exact under frozen original source owners, but automated owner anatomy remains genuinely UNSIGNED. **PRODUCT NO-GO**.
