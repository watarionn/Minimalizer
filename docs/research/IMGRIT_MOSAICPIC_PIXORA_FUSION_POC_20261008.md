# Minimalizer: imgrit + mosaicpic + Pixora, and three Art Mode combinations
**Date:** 2026-10-08 JST  
**Stage:** Real-library PoC PASS; nine new artistic outputs + full 19-style comparison. **Not production integration.**

## Intent and rules
After the owner's approval of all ten prior Art Modes, research three additional *non-generative* processing libraries and test style combinations, independently of Minimalizer Core, LocalWorker and Public. No image-generation model, img2img, Generative Fill, feature hallucination, or missing-part painting. These results are visual style studies, not permission to replace the production ZeroBase2 or its quality gates.

## Verified libraries (installed in isolated research target only)

| Library | Version actually executed | License | Tested API |
|---|---|---|---|
| [imgrit](https://github.com/tsjshg/imgrit) | 0.2.2 | BSD-3-Clause | `voronoi_mosaic`, `warhol_effect` |
| [mosaicpic](https://github.com/zl3311/mosaicpic) | 0.6.0 | MIT | `ConversionSession`, `Palette`, `Color`, `load_image`, `convert`, `pin`, `reconvert` |
| [Pixora](https://github.com/sepandhaghighi/pixora) | 0.4 | MIT | `pixelize`, `MeanBlock`, `ModeBlock` |

Packages are in `%LOCALAPPDATA%/Minimalizer/research/artmodes-imgrit-mosaicpic-pixora-20261008`, not the production Worker environment and not distributed to Browser. Existing Pillow/NumPy/SciPy/OpenCV are used in the research interpreter. **Another unrelated `Pixora` repository has more restrictive terms; it was not used.**

## Canonical input and outputs
Original Kyoko/GC001 `340×340` source SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, same source as the earlier ten styles. Reproducible code: `tools/research/art_modes_new_libraries_poc.py`.

Private Drive location (must stay inside `chatGPT及びCodex用`):
`Minimalizer/NewLibrariesAndFusion_PoC_20261008/`, folder ID `1IRP-8hOLGhyXm5TR3mjD_9Z8H5qtQzCz`.

- **imgrit Voronoi**, 160 source-colored Voronoi sites, *random-site mode with fixed Python seed*. This specific run did **not** use K-means site optimization. Raster edges/dense internal details are not preserved; this is an Art Mode candidate.
- **imgrit Warhol**, k-means palette to seven source-derived colors. Strong posterized palette, sacrifices facial detail.
- **mosaicpic Classic**, 34×34 grid with source-observed custom palette, nearest-pixel 340×340 preview, average color-distance score **ΔE 3.839** as defined by mosaicpic.
- **mosaicpic Dithered**, same source palette and grid, average **ΔE 4.961** (same package's internal metric). Scores compare color matching, **not** semantic preservation.
- **Pixora Mean Block**, 10-pixel blocks using source color averaging.
- **Pixora Mode Block**, 10-pixel blocks using source modal color.
- **Mosaic Sketch fusion**, mosaicpic Classic colors + strokes from earlier vsketch Contour result.
- **Voronoi Pop fusion**, imgrit Voronoi colors + observed dots from earlier pyfreeform Color Dots result.
- **Pixel Engraving fusion**, Pixora Mean Block + earlier vsketch Hatching, masked by contrast observed directly in original input.

The initial fusion composites incorrectly treated fully transparent PNG pixels as black, darkening entire images. Corrected by multiplying observed stroke darkness with the *actual vsketch alpha* when overlaying; visually inspected corrected output. Do not reuse the initial fusion images.

The program writes source comparison and results as actual 340×340 PNGs, `pin_probe.json`, `manifest.json` with all output hashes, and landscape/mobile composite preview atlases. There is no deployed endpoint or change to public site.

### Source-color pin experiment (potential Core technique)

Use the existing mosaicpic `pin(x,y,new_color)` API with a pixel sampled from the **original green necktie** region. Observed:
- Original pixel RGB **(134,232,13)** in source; corresponding output canvas cell **(16,29)**.
- Original mosaicpic Classic quantized cell before protection RGB **(148,210,27)**.
- After pinning this *actual source color* and running `reconvert("dithered",keep_pins=True)`, the target cell remained exactly RGB **(134,232,13)**. Tested through `get_pinned_cells()` and the output RGB array.

This proves **manual cell-level palette lock survives pipeline changes**. It does **not** prove auto-detection of the complete necktie, identification of arms, or preserved garment silhouette. Future Core proposal: apply per-part masks/anchors and semantic color budget to all relevant cells, then pass exact body/shape/color quality gates.

## 19-style full atlas

The original ten styles (pyfreeform 4, generativepy 3, vsketch 3) were checked against their prior 10-style manifest. New six independent and three hybrid outputs were checked against the newly generated manifest. The 20 images (one original + **19 styles**) were then composed **without editing the individual artworks**.

Reproducible code: `tools/research/build_art_modes_19_gallery.py`.

Private Drive location: `Minimalizer/ArtModes_19Style_Gallery_20261008/`, folder ID `1LcwKQGb81gJwkTFC41qElEbjX_rKjDt8`.

| Artifact | Layout | Verified SHA-256 |
|---|---|---|
| `gallery_19styles_landscape_5x4.png` | Desktop, 5 columns × 4 rows | `faa13b99783193ad045c97c53da39d47009dbc59d3c30a144a3310613fe74daa` |
| `gallery_19styles_mobile_2x10.png` | Mobile, 2 columns × 10 rows | `7ed53b29724be75fdd5129ceb9910375b595ef85e66ff6b57b0ebbdde7b372fe` |

Separate new-library PoC gallery hashes:
- Landscape 5×2: `72bc609a128ca5de0ee9c90d8c328f5c5c2c316a7618021627dee8d313e774d1`.
- Mobile 2×5: `c6cb7792a0cd7f4aaf40804b4151c2a3edc70baf53d197743bad34c43fbff28c`.

## Verified gates and unresolved checks
- Python 3.11 isolated packages import successfully, and all three library APIs actually run.
- Runs with `python -W error`; PNGs generated, source hash validated.
- Second execution: **all nine style output hashes unchanged** and both PoC gallery hashes unchanged; all 20-source atlas inputs verified, both 19-style gallery hashes unchanged.
- Original source is from established GC001 dataset, not generated or retouched.
- Real image previews examined; notable improvement after alpha fix.
- MinimalizerLocal `/health` remained `ready=true`. No change to Core, Public or RRM. No continuous research job is left running.
- **Google Drive cloud synchronization** is separately checked through the Drive connector; existence under the Drive-mounted filesystem is not sufficient evidence of server-side sync. Do not claim remote delivery until actual cloud files are visible.

## Next decisions for owner review
Retain all 19 as **research candidates**. Consider Local-only selectable Art Modes, not an automatic replacement for Core. Within Core, prioritize *mosaicpic style color anchors* with shape and region masks as independent hypotheses, tested via Golden Harness. Evaluate specific failure modes: facial-detail loss, strong imgrit posterization, edge-heavy overlays, tie color region growth, and arm/torso connectivity.

Exclude neural `styletransfer` and `neural-style-transfer` as Core rendering dependencies under the project's no-generative-img2img rule; a separate analysis of their metrics is allowable.
