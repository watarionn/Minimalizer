# BrowserFallback Shape v14: corner-aware shared-boundary cleanup

Date: 2026-10-08
Project: **non-local BrowserFallback quality only**. This is separate from Local Worker ZeroBase2 production and semantic-anatomy research.
Base: [Sharp Lite v13 PR #225](https://github.com/watarionn/Minimalizer/pull/225)
Implementation: [stacked Shape v14 PR #226](https://github.com/watarionn/Minimalizer/pull/226)
Status: **PRODUCTION VERIFIED / opt-in Shape profile shipped; default Lite unchanged.**

## Goal and immutable product direction

The user wants simple, intentional **geometric color regions with crisp boundaries**, not better facial feature retention. Omitting eyes, nose and mouth is desirable. Kyoko revealed that old Exact/Geo preprocessing expanded the green tie and recolored the left sleeve. We must retain Lite's structural/palette behavior while improving shared-arc geometry.

## Modes and compatibility

| Mode | Query parameter | Structural preprocessing | Contour | Raster |
| --- | --- | --- | --- | --- |
| Lite (unchanged) | `browserFallbackQuality=lite` | l0-lite-jacobi | independent rings | Canvas |
| Exact (unchanged) | `browserFallbackQuality=exact` | spectral-exact | canonical shared chain | OpenCV 2x |
| Sharp Lite v13 (unchanged) | `browserFallbackQuality=sharp` | l0-lite-jacobi | canonical shared chain | OpenCV 2x |
| Shape v14 (new, opt-in) | `browserFallbackQuality=shape` | l0-lite-jacobi | canonical shared chain with corner-aware cleanup | OpenCV 2x |

Use `?browserFallback=force&browserFallbackQuality=shape` to invoke Shape from the actual UI after reviewed deployment. Nothing is enabled by default. No external package, downloaded model, GPU, image synthesis, or API is added.

## Implementation

The contour system already performs conservative OpenCV-like Douglas-Peucker simplification followed by `planarLineCandidate`; rewriting those would risk parity with previous v12 tests. Instead, add **optional post-pass** `cornerAwareLineCandidate` to `web/static/canonical-contour.js`:

1. Operate on each canonical **shared arc once**, not on separate region polygons. Keep both endpoints exactly fixed. Candidate only deletes interior vertices.
2. Map retained vertices back to the original raw contour. Every newly proposed long chord must keep **all intermediate raw contour points** within the prescribed tolerance (default 1.65 px, retried at 0.75x and 0.50x). No added/restored image content.
3. Protect major corners: a bend of at least 55° with both adjacent arms at least 3.5 px is not pruned. Short 1px stair notches can be removed.
4. Process candidates deterministically, lowest local deviation first, with a bounded work budget.
5. Accept an arc only after the original shared-edge intersection, connected-component/hole topology, min region IoU ≥0.90, area/centroid/directional safeguards all pass.
6. Further require each affected region's IoU not to decline by more than 0.004 versus the Sharp baseline at that arc. Otherwise revert the candidate. Shape metadata reports pruned chains/vertices and rejected candidates.
7. Invalid structural/contour combinations and missing critical raster/contour modules **fail closed**.

Keep per-region palette, shape owner IDs, color assignments and source preprocessing intact. No semantically guided features, eyes/nose/mouth reconstruction or new color segmentation.

## Real Chrome benchmark

Chrome 154, independent checkout, three existing 340×340 character reference inputs. Subject guidance active. Same shape budget 40, target palette 8, image and work resolution, SLIC settings. Existing output PNGs were checked against the previous v13 evidence at the SHA256 level.

| Source | Lite | Sharp Lite | Shape v14 | Reduction vs Sharp | Shape min region IoU | Sharp → Shape changed pixels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyoko | 1,409 | 1,727 | **1,513** | **12.4%** | 0.9021 | 0.1254% |
| Shirogane Noel | 1,555 | 1,576 | **1,366** | **13.3%** | 0.9021 | 0.1306% |
| Ichijou Ririka | 1,262 | 1,108 | **976** | **11.9%** | 0.9007 | 0.0753% |

Vertex counts refer to **rendered shape vertices**. The Kyoko shared-arc vertex count also went from 996 (Sharp) to 889 (Shape).

### Kyoko color acceptance

The representative green palette color is RGB(149,211,27) for Lite, Sharp, and Shape. It covers 1,873 / **1,994 / 1,994 pixels** respectively. The green count refers to all pixels with that color, not a manually annotated tie mask. Exact uses a different green RGB(181,215,92) across 4,111 pixels.

The left-sleeve reference sample at (95,275) is RGB(65,66,74) in Lite, Sharp and Shape. Exact had RGB(32,42,80).

The test confirms Shape **does not recreate the original Exact/Geo color regression**. It does not claim every pixel is unchanged: boundary placement is purposefully adjusted.

### Real UI route

Loaded query `?browserFallback=force&browserFallbackQuality=shape`, then invoked actual `app.js` `requestBrowserFallback()`. For all three sources it selected Lite preprocessing, canonical shared contour, corner-aware geometry and OpenCV-compatible 2x raster. Returned PNG bytes exactly matched the directly invoked Shape engine output.

### Visual review caveat

The boundary looks more intentionally simplified and the vertex count decreases by ~12–13%, but some coarse stair steps remain, especially on hair and clothing edges. This is **one geometry improvement**, not final pixel-independent vector design. Avoid overstating realism or facial fidelity: those are not product goals.

## Test and release gates

- `tests/test_browser_shape_v14.py`: tests new opt-in route/metadata, deterministic short-stair reduction, protection of meaningful 90° corners, strict same-owner/palette equivalence, shared contour + IoU guard, missing module/incompatible structural mode fail-closed.
- Prior `tests/test_browser_sharp_lite_v13.py` is updated only to permit a new explicit `shape` quality value without weakening the Sharp regression checks.
- New PR CI checks JavaScript syntax, benchmark script Python syntax, Shape + Sharp focused tests and stacked diff whitespace.
- Existing v12 BrowserFallback suite must remain green. A pre-existing stale test `test_browser_v5_exact_mode_reports_structural_profile` in main expects a v11 string while the app runtime is v12. Treat it as an unrelated known mismatch, not a new engine regression; report both counts honestly.

## Evidence, preservation and reproducibility

[Google Drive / chatGPT及びCodex用 / Minimalizer / BrowserFallback_GeometryV13_20261008 / ShapeV14_20261008](https://drive.google.com/drive/folders/1L0-Cla8SkmIJGbvSRMIW7DgbmNck3OxT)

- `shape_v14_three_source_5way.png`: source, Lite, Sharp Lite, Shape v14, Exact for each of three characters.
- `shape_v14_kyoko_upper_2x.png` and `shape_v14_kyoko_torso_2x.png`: magnified boundary checks.
- `shape_v14_metrics.json`: all numeric measurements, checksums and rendering metadata.
- `shape_v14_report.md`: compact review.
- `shape_v14_evidence_20261008.zip`: source and independent raw result PNGs, metrics and comparisons.
- `tools/run_browser_shape_v14_chrome_compare.py` in GitHub: browser replay harness.
- Source artwork belongs in Google Drive rather than in the GitHub repository. Google Drive folder is under the designated `chatGPT及びCodex用` hierarchy.

## Next work after gate

Do not merge into main without integrating/reviewing parent Sharp Lite PR #225 first. Geometry may progress to straight-segment angle consistency and long flat-side snap in an isolated experiment. Keep corners, palette ownership and original shapes protected. A 0.90 minimum IoU passing by itself is insufficient to approve visually degraded outputs.

## 2026-10-08 release closure (supersedes earlier HOLD/deployment-pending references)

Sharp Lite PR #225 was merged into `main` (merge `f3313926c909458f90dbd7f48b26bac5e166dd8c`) and Shape v14 PR #226 was merged after retargeting `main` (merge `14657714960e639e7d669612ad19c265e0aefaea`). These are **production-shipped opt-in quality profiles**, not the new default and not Local Worker changes.

The Shin static host was updated with only `canonical-contour.js`, `browser-fallback.js`, and `app.js`. Public HTTPS byte-for-byte verification succeeded, and live Chrome 154 executed original Kyoko input for **Lite, Sharp, Shape, Exact**, all producing PNGs byte-identical to previously accepted predeployment baseline outputs with browser-u2netp guidance. No rollback was required.

See the authoritative [production handoff](../handoffs/HND-20261008-BROWSER_SHAPE_V14_PRODUCTION.md) and [Drive release evidence](https://drive.google.com/drive/folders/1WS4dLGFYol5VByP1bNPGMX0FwS4P9MGA) for SHA256 manifests, backups, public test output, and rollback instructions. Previous mentions of not-yet-merged / not-yet-deployed describe the development stage and are superseded by this release closure.
