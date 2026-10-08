# Minimalizer BrowserFallback v19: rejected adjacency diagnostics and rendered rollback

Date: 2026-10-08
Status: **HOLD_NO_GEOMETRY_GAIN**. Research-only; **NOT merged, NOT deployed**.
Branch: `research/browser-merge-diagnostic-v19-20261008`
Draft PR: [#230](https://github.com/watarionn/Minimalizer/pull/230), based on draft v18 PR #229 (stacked on draft v17 PR #228).
Production canonical: Facet v15; Lite, Sharp, Shape, Exact unchanged.

## Goal / adopted constraints

The goal is geometric color design, deliberately omitting eyes/nose/mouth. Source consistency and stable geometric clothing/hair boundaries outrank shape count. Kyoko's green tie and gray left sleeve are required non-regression anchors. v16 global 40->30 region cut failed severely (Kyoko 37.07%, Noel 64.53%, Ririka 40.83% pixels changed). v17 strict same-palette and v18 near-palette controls safely accepted zero real merges.

This phase instruments the **exact first-failing rejection reason** for each adjacency pair and adds an independent render-space gate before one tentative region merge is committed. It does not loosen color thresholds just to produce more merges.

## v19 implementation

Files:
- `web/static/browser-fallback.js`: first-reason counters, `compareRegionRenderFidelity`, final acceptance gate.
- `web/static/app.js`: `near`/research `selective` modes now explicitly request `maxMerges:1` so one transaction can contain at most a single tentative merge.
- `tests/test_browser_merge_diagnostic_v19.py`: 3 automated tests for no-default-change, deterministic reason accounting, and render gate pass/fail behavior including missing-raster fail-closed.
- `.github/workflows/browser-merge-v19.yml`: CI.

The diagnostic reason counters are:
`incompatiblePalette`, `donorAreaOrAspect`, `protectedArea`, `paletteDistance`, `recolorBudget`, `regionColorError`, `sourceColorDistance`, `boundaryWeakOrShort`.

They use the **first failing reason** per reviewed neighboring pair. Reasons after an earlier failing gate are not evaluated, so these are gate-path frequencies, not independent causal probabilities. Counts are exposed in response metadata as `selectiveMergeRejectReasons`.

If exactly one merge candidate passes the structural/label-space gates, the implementation computes an unchanged baseline `analyzeRgba()`, rasterizes **both** baseline and merged shape sets with the existing OpenCV-compatible 2x renderer at the same work dimensions, and compares:
- Changed pixels <=0.15% of work raster.
- Mean absolute RGB channel error <=0.30.
- Largest mass change of any individual RGB <=0.15% of work pixels.

If any bound fails, or the renderer is unavailable, the tentative entire transaction is rolled back to the unmodified baseline. Acceptance uses `selectiveMergeRenderGate=pass`, rejection uses `rejected:<reason>`. The one-merge cap makes rollback candidate-specific. No image-generating AI, external dependency, or Local Worker requirement.

**Limitation:** those checks are not a semantic human ROI classifier. A candidate that passes global budget is not automatically production-safe. Important thin colored details, silhouette and visual style still require separate checks.

## Real Chrome 154 benchmark, three sources

Each test used the same original 340x340 Kyoko GC001, Shirogane Noel, Ichijou Ririka references and browser-subject guidance as v15-v18, through actual `app.js requestBrowserFallback()`.

| Input | Adjacency pairs reviewed | Area/compactness rejection | Palette-distance rejection | Source RGB rejection | Accepted | v19 PNG vs Facet |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Kyoko | 87 | **76** | 11 | 0 | **0** | byte-identical |
| Noel | 81 | **74** | 6 | 1 | **0** | byte-identical |
| Ririka | 92 | **67** | 22 | 3 | **0** | byte-identical |
| Total | 260 | **217** | 39 | 4 | **0** | unchanged |

There were no other first-failing categories on these three inputs. The major bottleneck is **donor area/shape**, not near-palette color tolerance alone. The combined area/compactness category must be split into width/aspect/area subreasons before considering legitimate relaxation.

All six older Lite/Sharp/Shape/Facet/Selective/Exact PNGs were SHA256 byte-identical to their accepted v18 counterparts for each character. The v19 near-profile PNG matched the direct engine output and was identical to the Facet v15 output in all three cases. Kyoko's dominant green RGB(149,211,27) remains 1,994 pixels, and left sleeve x95,y275 RGB(65,66,74). The green count is across the whole image, not a manually segmented tie-only mask.

**Important verification nuance:** the post-render rollback function has positive/negative/missing-raster synthetic unit tests, but **NO real-image merge was admitted** in the 3-case trial, so its rollback path was not exercised by an actual Kyoko/Noel/Ririka merge. Do not claim an observed real-image improvement or a full live candidate rollback.

## Tests and release decision

- Isolated v19 + v18 + v17 + v15 + v14 + v13 + v12 extended regression: **49 passed**.
- JavaScript syntax and branch build parsing: PASS.
- CI workflow result: see Actions run on PR #230 (record verified result after completion).
- Research quality: **HOLD_NO_GEOMETRY_GAIN**. PR #230 stays Draft; no production deployment, no main merge.
- No bypass of v16 rejection. No lowering of default region count; no changes to production Facet v15.

## Evidence

[Drive v19 evidence](https://drive.google.com/drive/folders/1m0RHI0MEIJ6miRkG7hAhziZsDqGoOwZy) under `chatGPT及びCodex用/Minimalizer/BrowserFallback_GeometryV13_20261008/ShapeV14_20261008/FacetV15_20261008/SelectiveV17_HOLD_20261008/NearColorV18_HOLD_20261008/MergeDiagnosticsV19_HOLD_20261008`.

Files: 3-source original / Facet / v19 comparison PNG, detailed JSON rejection metrics, report, archive with all original sources & seven-mode PNGs, runnable diagnostic harness and report builder. Repro uses existing `tools/run_browser_near_v18_chrome_compare.py` on this v19 branch.

## Next research task: v20

Split `donorAreaOrAspect` into donor area, minimum bounding-box side, and aspect ratio. Quantify each neighboring donor's area and aspect distributions, then identify promising region pairs without changing thresholds. A later experimental merge must pass **per-candidate render-level** fidelity *and* targeted distinctive-color/silhouette checks. Do not change global hierarchy cut or publish a quality improvement until visually verified against the three golden sources.
