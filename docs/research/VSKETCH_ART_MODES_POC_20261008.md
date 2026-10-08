# Vsketch / vpype independent line-art PoC, GC001 (2026-10-08)

Status: **actual execution PASS / 3 independent SVG+PNG / repeatable / no production integration**.

This is the third Minimalizer Art Mode library research stage, after pyfreeform (4 styles) and generativepy (3 styles). It does **not** modify `MinimalizerLocal`'s ZeroBase2/LocalV2 pipelines, `MinimalizerPublic`'s browser engine, RRM, or memory-management policy. The research code lives in `tools/research/vsketch_three_styles.py` and is intentionally optional. Existing policies against generative img2img/inpainting/hallucinated missing parts remain intact.

## Official library and compatibility

- **vsketch 1.2.0**, [abey79/vsketch](https://github.com/abey79/vsketch), **MIT**.
- **vpype 1.15.0**, headless line/plotter SVG backend, also MIT.
- Python **3.11**, isolated `%LOCALAPPDATA%/Minimalizer/research/vsketch-1.2.0` target, with existing separate `resvg_py 0.5.0` raster-preview renderer.
- Only core API is invoked: `vsketch.Vsketch()`, `size(340,340,center=False)`, `detail`, `stroke`, `polygon`, `line`, `save(..., color_mode="none")`. **No GUI/viewer, multiprocessing or GPU**.
- OpenCV, NumPy and Pillow inspect the original image. `cv2.Canny`, `cv2.findContours`, `cv2.approxPolyDP` extract observed edges, and original pixel luminance drives hatch density. This is deterministic observation + stroke placement, **not** image synthesis.

## Canonical input and private output

Source: canonical **GC001_source.png** (Kyoko), exactly **340×340** and SHA-256 **`75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`**, as in the Golden case metadata. The input is the **original**, not an earlier Minimalizer or other Art Mode output.

Output folder: **`chatGPT及びCodex用/Minimalizer/Vsketch_PoC_20261008/`**. Drive folder ID: **`1uctBYsHsg8ZNCxUKG4j0hZzcps7ARWok`**.

| Mode | Stroke entities | SVG size | Preview PNG size | Character |
| --- | ---: | ---: | ---: | --- |
| Contour Line | **145** observed polylines | 33,969 bytes | 106,734 bytes | Readable black-and-white hair, face and costume lines; some background borders present |
| Hatch Shade | **2,167** strokes | 165,484 bytes | 136,140 bytes | Etching/engraving hatch texture, plus 58 prominent contours; background hatching can be excessive |
| Sparse Outline | **60** selected polylines | 23,934 bytes | 92,714 bytes | Economy of lines and recognizable character silhouette; facial and costume details reduced |

Every mode has its own `GC001_{mode}.svg` and `GC001_{mode}.png`; plus original source copy, `manifest.json`, and `comparison_grid.png` (2×2 original + 3 modes), nine files total.

Comparison-grid SHA-256: **`8625585ac81dc65e76d2eaec6286f85a18716ebf94019a35390b431bcac4c95c`**. All 3 SVG and all 3 PNG artifact SHA-256 checks matched the manifest during remote verification. Source SHA matched. A second independent `-W error` rendering passed and reproduced the comparison grid's exact SHA. LocalWorker `GET /health`: `ready`, active `zerobase2` after PoC; zero active GPU image-generation jobs were started by this script.

### Rendering caveat: SVG size units

The default vsketch/vpype SVG writer emits page dimensions in **cm** (equivalent to 340 CSS pixels). The isolated `resvg_py 0.5.0` renderer rejected these legitimate physical-unit dimensions with `ValueError: SVG has an invalid size`. Research adapter changes **only** the top-level SVG `width` and `height` attributes to `340px`; **all vsketch-generated paths, coordinates and line ordering are preserved**. Native `vsk.save` remains the source of geometry. The first failing run and successful tested workaround should not be confused. SVG XML parsing, no embedded raster and PNG 680×680 size checks all passed.

## Visual assessment and limitations

The authentic output contact sheet was visually inspected:

- **Contour**: strong readability of hair/goggles/facial and clothing outline, although broad geometric background edges remain visible.
- **Hatch**: attractive dense printmaking pattern and strong tone but background competes with the subject; later test foreground-weighted hatching, using only observed masks, is optional.
- **Sparse**: many fewer lines and a cleaner sketch; some identifying details and facial features disappear.

These are **artistic mode candidates**, not a PASS against Minimalizer Core's silhouette, arm-connectivity, necktie-color and garment-region semantic Golden gates. The 60 sparse lines represent a plotter-centric aesthetic, not proof of meaning preservation. No style has been integrated into the live Local PWA or Public engine.

## Reproduction

Run headlessly with the isolated vsketch+vpype environment on Python 3.11:

`python -W error tools/research/vsketch_three_styles.py --source ORIGINAL_GC001_source.png --out PRIVATE_DRIVE_OUTPUT`

Check the `manifest.json` output SHA-256s, visually compare `comparison_grid.png`, and run a second time to confirm identical grid SHA.

## Next stage

Cross-library review: pyfreeform four modes + generativepy three modes + vsketch three modes, **10 Art Mode options** side by side from the *same* canonical source, with stable filenames and no synthetic additions. Do not choose a single winner until the owner sees and comments. Consider only a separately approved **Local-only opt-in Art Modes gallery**, while retaining Core and Public independently. The user has already said all 4 pyfreeform styles are favorites.

Cloud Drive synchronization is to be confirmed through the Drive connector; a file on the mounted Drive filesystem is not by itself proof of remote synchronization.
