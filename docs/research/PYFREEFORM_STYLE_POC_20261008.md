# PyFreeform isolated art-style PoC (2026-10-08)

Status: **REAL LIBRARY EXECUTION PASS / ARTISTIC QUALITY NOT YET APPROVED / NO PRODUCTION INTEGRATION**.

## Scope and separation

This research follows the user-approved MinimalizerLocal/MinimalizerPublic split. Research only, using the **actual GPL-3.0-only** `pyfreeform==0.6.3` PyPI package and its published `Scene.from_image`, `add_dot`, `add_diagonal`, `add_fill`, `add_border`, `Polygon.square/hexagon/star`, and `scene.save` interfaces. The code was patterned on the official recipe:

https://github.com/MatheweB/pyfreeform/blob/main/wiki/_generator/recipes/gen_01_image_to_art.py

The package is installed only under the owner's external, isolated `%LOCALAPPDATA%/Minimalizer/research/pyfreeform-0.6.3` directory. It is **not** imported into or installed in LocalWorker's production runtime, and it is **not** shipped with MinimalizerPublic or committed/vendored in the public GitHub repository. The PoC Python code and outputs are kept only in the existing private Google Drive project folder.

## Canonical assets

Private Drive: `chatGPT及びCodex用/Minimalizer/PyFreeform_PoC_20261008/`

Folder ID: `1ZV7j2lREsxWuSIqVJ4azBKLVsNdRcWZ5`

Input: approved original `GC001_source.png` (Kyoko/GC001), verified source SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, matched to `benchmarks/golden/cases/GC001_IMG_1205.json`.

Saved reproducibility assets: `pyfreeform_poc.py`, `render_comparison.py`, `manifest.json`, `comparison.html`, original PNG, four independent SVG outputs, four PNG previews, `comparison_grid.png`.

### Actual produced outputs

| Mode | SVG cells drawn | SVG bytes | Approx. SVG drawing elements |
| --- | ---: | ---: | ---: |
| Color Dots | 1223 | 94689 | 1224 |
| Lines | 1222 | 157563 | 1223 |
| Mosaic | 1225 | 262164 | 2451 |
| Shapes | 1225 | 262874 | 1226 |

Each SVG was parsed, SHA-256 checked and verified to contain no embedded raster `<image>` element; all four generated successfully. PNG previews were produced via isolated Rust-backed `resvg_py==0.5.0`; a 5-image source+styles comparison grid was saved (PNG 942798 bytes, SHA-256 `64d1fda7b155a70b774d4391f5cfc86e99d8518ddb6b83a712fb73e9b753377b`). These are computational and artifact checks; no subjective visual-quality PASS has been claimed.

**Important finding:** these styles use ~1200 cells / ~1200–2450 SVG drawing elements, rather than Minimalizer's small semantic primitive budget. They produce distinctive art styles but do not replace Minimalizer's meaning-preserving silhouette/arms/clothing/color simplification or SA10/GOLDEN quality gates.

## Dependency and safety notes

- The user's input image was read from the already-established Google Drive source and copied with verified unchanged SHA.
- No generative AI, img2img, or missing-part fabrication was used; only deterministic image sampling and vector generation.
- pyfreeform is `GPL-3.0-only`. The personal-only PoC stays outside the Public runtime and public GitHub code. Any integration/redistribution still needs code-boundary and licensing review.
- CairoSVG 2.8.2 was initially tested in a separate research-only target but could not render on this Windows host due to a missing native Cairo DLL. No system libraries were installed; the failed research-only CairoSVG target was cleaned up. Preview generation was successfully replaced with isolated resvg_py, which bundles its renderer.
- The LocalWorker and Browser execution paths remain unchanged by this research.
- Keep research packages unloaded when not executing to avoid ongoing memory impact.

## Decision / next gate

1. Review the actual `comparison_grid.png` against the original and the project's meaningful silhouette/semantics target.
2. Choose which style(s), if any, warrant a **Local-only opt-in**. Do not assume all four belong in main Minimalizer.
3. Consider protected foreground/negative-space masks if experimental shape styling destroys body-part separations; test in a shadow PoC only.
4. Preserve genuine visual and Golden regression results before any production promotion.
