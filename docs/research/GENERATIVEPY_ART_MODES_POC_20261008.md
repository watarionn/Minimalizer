# Generativepy three-style GC001 research PoC (2026-10-08)

Status: **3 real SVG + PNG modes PASS, visual review preliminary, NOT production-integrated**.

## Reason / project scope

This is the second art-style research candidate after the owner's pyfreeform (four-mode) PoC. Preserve all four pyfreeform modes; add three **independent** generativepy concepts, without altering production MinimalizerLocal (ZeroBase2/LocalV2) or MinimalizerPublic (browser). Production quality gates and the no-generative-img2img policy remain unchanged.

Library: Martin McBride's [generativepy](https://github.com/martinmcbride/generativepy), tested using **PyPI v50.0**, **MIT license**, with **pycairo 1.29.2**, Pillow and NumPy. Generativepy is a procedural drawing framework, NOT an automatic photograph-to-stylized-art converter: our `tools/research/generativepy_three_styles.py` defines deterministic pixel-sampling and vector-geometry rules using generativepy's real `make_image`, `make_svg`, `Circle`, `Polygon`, `Bezier`, `Color`, and `setup` interfaces. No text-to-image or generative inpainting.

## Input and output provenance

- Source: original `GC001_source.png` (Kyoko), **340×340**, SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. This matches the tracked `benchmarks/golden/cases/GC001_IMG_1205.json`, not an intermediate Minimalizer output.
- Private Drive canonical output folder under **`chatGPT及びCodex用/Minimalizer/Generativepy_PoC_20261008/`**, folder ID `1Ms2lNqZpo2MrOKEgYWHApBh0_KQGbxcM`.
- Each style: independent PNG (680×680) and vector SVG (340×340), with standalone `manifest.json`. A 2×2 PNG `comparison_grid.png` compares the *original* and all three.
- PNG/SVG each rendered via the actual generativepy drawing functions. SVG XML parsed to check that no `<image>` raster is embedded. Source and all generated file hashes verified on the working host.
- Final comparison-grid SHA-256: `93a84f727481b9f2132f48a298af1104cab660bd0b7cc79630734c8554e7bb48`.

| Mode | Drawing primitives | SVG bytes | PNG bytes | Look and mechanism |
| --- | ---: | ---: | ---: | --- |
| Circle Field | 784 circles | 178946 | 132979 | Circles preserve local source colors, opacity and brightness |
| Geometric Blocks | 624 quads | 132755 | 149030 | Color samples become lightly rotated tile geometry based on local gradients |
| Flow / Ribbons | 1156 Bézier curves | 267720 | 126307 | Segmented colored scanline ribbons guided by a bounded luminance gradient |

## Verification

- Real execution on the user's authorized PC, using the **Drive-mounted original** and isolated packages in `%LOCALAPPDATA%/Minimalizer/research/`; no GUI click automation, no GPU model loading, no production engine imports.
- An initial edge sampling issue triggered NumPy warnings on out-of-bounds probes. It was repaired by clamping x/y *before* slicing. The final run used `python -W error` and **passed with no warnings**.
- Every output and `comparison_grid.png` passed readback SHA-256 verification against `manifest.json`.
- Visual inspection of the 2×2 comparison: circle grid maintains rough color-coded subject recognition; blocks have strong mosaic character; flowing horizontal strokes are more abstract and sacrifice small facial / clothing details. This is **style exploration**, not Core semantic-retention certification.
- Private Google Drive sync verification is separate from the local Drive-mounted write; do not claim complete remote sync until the cloud connector sees the expected outputs.
- Note: Google Drive folder display and PNG comparison artifacts may take time to sync through Drive for desktop.

## Reproduction

1. Prepare a Python 3.11 research environment (do **not** modify the running LocalWorker's service packages). Install generativepy 50.0 and pycairo/Pillow/NumPy in the isolated research location.
2. Supply the exact approved original `GC001_source.png` in a private path. Script rejects different hashes.
3. Run `python -W error tools/research/generativepy_three_styles.py --source SOURCE --out DRIVE_OUTPUT_FOLDER`.
4. Verify `manifest.json` SHA-256s and inspect `comparison_grid.png`.
5. Do **not** treat the 3 styles as the production Minimalizer result. Optional Local-only Art Modes require separate UI design, performance testing, licensing compliance and owner review.

## Next stage / handoff

Research **vsketch** in an equally isolated PoC, first evaluating its license, current maintenance, vector/export API and whether vpype is needed. Proposed modes: `Contour Line`, `Hatch Shade`, `Sparse Outline` on the *same verified GC001 source*. Compare three generativepy modes and four pyfreeform modes alongside vsketch after the three-stage research passes. Preserve generation-free constraints and Local/Public separation.
