# HND-20261008 SA10.38 → SA10.39 (Chrome vector raster remaining edge pixels)

**Primary canonical:** `watarionn/Minimalizer`, branch `research/sa1032-svg-contour-proposals`, **PR #223 draft / NEVER MERGE OR DEPLOY on this evidence alone**.
**Completed report:** `docs/zerobase/SA10_38_CHROME_VECTOR_MASK_CALIBRATION_NO_GO_20261008.md`.
**Binary evidence:** Google Drive `chatGPT及びCodex用/Minimalizer/SA1038_VectorMaskChrome_20261008`, https://drive.google.com/drive/folders/1rpCp_Ypg26XEdxL1L55ktQulySXFHkJs.

## Quality direction from user

User likes outer silhouette. Giant gray clothing trapezoid unacceptable; previously corrected by navy/white/green geometric color planes. Next changes must preserve original silhouette, no new face eyes/nose/mouth, no left/right arm recoloring, thin tie and source-observed material colors. Do not conflate low RGB difference with clean geometric minimalization quality.

## Latest code and reproduction

`tools/run_sa1038_vector_mask_browser.py`
1. `--outer-scene [SA10.34 GC001_adaptive phase8_adaptive_source_contour_research.json]`, `--apparel-scene [SA10.37 GC001 apparel_simplified_subpaths.json]`, `--apparel-metrics [SA10.37 apparel_simplified_metrics.json]`, `--output-dir [new isolated temp dir]`.
2. `--render-chrome --chrome-bin "C:\Program Files\Google\Chrome\Application\chrome.exe" --output-dir [same dir]`.
3. Read `svg_material_parity_metrics.json` and `real_chrome_execution.json`; compare official 340×340 OpenCV material render to actual headless Chrome screenshot. Source/scene/browser executable/screenshot SHA256 verified. No user normal Chrome profile used.
4. Negative control Raden remains unchanged from SA10.37; `tools/run_sa1038_two_source_browser_gate.py` validates both real SHA-distinct cases.

SA10.37 baseline best: **528 mismatched RGB pixels** in isolated material SVG, 388 severe (>48 max-channel delta). New real Chrome **69 mismatched RGB pixels**, 51 severe, MAE 0.080363; **86.9318% reduction**. 63 are colored/uncolored occupancy disagreements and 6 are actual overlapping-color disagreements; 54 are near reference edges, 15 farther. It is NOT SVG exact parity PASS.

### SVG vector-only method

- 5 original signed clothing filled polygons / **27 original material vertices**, each outlined by **1px same observed source color**, with pixel-center shift +0.5px. This is not a sixth clothing polygon.
- Source lower_body owner uses **luminance SVG `mask`**, 7 nondegenerate even-odd rings/152 source geometry vertices, **5 explicitly counted hole-boundary SVG white stroke paths** that reuse 31 original owner ring point occurrences (not extra hidden source parts), parent transform **(-0.25px,+0.5px)** as a GC001 research-only Chrome calibration.
- One 1-point hole contour is omitted from SVG ONLY after comparing canonical `rasterize_primitive_candidate` with/without ring: source owner pixel delta **0**. Fail closed if a degenerate filled island or hole affects any source pixel. The canonical source, existing scene and Stage04 records are never mutated.
- SVG/HTML includes NO `<image>`, PNG, base64 bitmap, generative painting, unknown-owner reclassification, or source image pixel overlays.

### Tests and safety

- `tests/zerobase/test_sa1038_vector_mask_browser.py`, `test_sa1038_two_source_browser_gate.py`: 6+5 tests, including failure on singleton filled island, tampered SHA, fake identical PNG pretending to be Chrome, unrelated Raden edits, missing counted hole strokes, browser pixel mismatches.
- Full relevant suite **108 tests PASS + 11 parameterized subtests** locally; CI `.github/workflows/sa1032-svg-research.yml` includes these. Real Chrome run **twice** with 6 matching output SHA256 each.
- Evidence JSON `docs/zerobase/evidence/sa1038_*.json`. Drive path above holds actual SVG, Chrome PNG, expected OpenCV PNG, visible before/after PNG, heatmap, stroke/clip/mask tuning sweeps and SHA manifest.
- Parent input version and Chrome binary hashes attested. The optional `chrome.exe --version` command can hang on this Windows installation, therefore version string is not used as execution proof.

## Full release blockers: UNCHANGED

1. Chrome mismatch **69 pixels != 0**: exact browser SVG gate still **FAIL**.
2. Inherited original total vector budget still FAIL: GC001 3,604 >1,887, Raden 2,370 >1,412 before any interior subpaths. New SVG mask's additional hole-border strokes are tracked in complexity, not free.
3. Current Chrome PNG compares only **isolated material layer**. Need full-character Chrome render to verify arm ordering, face protection, source-topology across all owners.
4. GC001-specific SVG offset calibration is not general source truth. Need other matching outfits and broader corpus before applying universally.
5. Human visual approval PENDING. Research PR #223 stays **DRAFT**, no production deployment.

## SA10.39 recommended next

- Diagnose remaining **63 binary occupancy and 6 color boundary** mismatches by tracing each to source owner-hole nesting, stroke junction, or clipped edge. Use actual Chrome screenshot and canonical per-owner/per-panel OpenCV masks; avoid hand-wave about antialias.
- Seek source-faithful low-complexity SVG geometry without raster embedding, perhaps distinct even-odd mask fill and hole perimeter handling with a proof-gated owner clip. Keep all new SVG strokes counted.
- Add second matching garment case; Raden currently only ensures no wrong outfit generated.
- Independently pursue source-topology-constrained whole-character vector vertex reduction before production.
- Preserve code on GitHub and images/evidence on Drive. Use local RDC only for original images and actual Chrome browser benchmarking; never modify local main repo.

**Quality disposition:** SA10.38 proof of bounded **research** progress COMPLETE, production NO-GO.
