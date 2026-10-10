# MinimalizerPublic: non-local v34 and installed library convergence

Date: 2026-10-10. Status: **revised roadmap adopted, research only, production HOLD**.

## Verified baseline and source boundaries

- Source GitHub repository: `watarionn/Minimalizer`, branch `main` contains all library PRs #344–#352.
- Draft PR #308 (`research/browser-svg-local-rollback-v34-20261009`) is stacked on Draft #306, **not** the current `main`. Do not merge it into main merely because diagnostic libraries are already merged.
- Archived sources: Google Drive `chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009` and `ConnectedSourcePlanesV32_20261009`; both include SHA-256 manifests. Preserve all originals.
- All nine libraries are in **MinimalizerPublic**; no changes to MinimalizerLocal, its worker, or Python package installation.

v34 reduced SVG bytes by 43.34% (Kyoko), 45.37% (Noel), and 52.66% (Ririka), with exact native Chrome pixel parity to v32. It achieved **zero vertex reduction**: 75 unsafe contour-proposal groups were rejected. It is a hybrid SVG with frozen raster Facet and source-color paths, **not** fully vectorized character art, and garment/arm semantics remain unverified.

## Replace / integrate / HOLD matrix

| v34 or prior custom processing | Real self-hosted JS/WASM | Decision |
|---|---|---|
| Manual H/V lossless path serializer | SVGO 4.1.0 + SVGPathCommander 2.3.3 | **R1 priority:** independently benchmark serialized bytes, parse/provenance, real Chrome exact RGBA; do not delete the proven serializer yet |
| OpenCV approximate polygon proposal | Simplify.js 1.2.4 | **R2:** shadow candidate only, whole owner+holes parity, source mask protected |
| Viewport/owner Boolean/intersection | polygon-clipping 0.15.7 / Clipper2-WASM 0.4.0 | **R2:** real topology, exact-grid and mask equality gates; choose one when equivalent, do not duplicate work |
| Component triangle rasterization | Earcut 3.2.4 | **R2:** preserve holes and full mask, not merely individual contained triangles |
| Delaunay-only point-cloud mesh | Delaunator 5.1.0 | **HOLD** as replacement: holes and disconnected owners not inherently safe |
| SVG native Chrome oracle | resvg-WASM 2.6.2 | **R4:** independent second renderer diagnostic; disagreement is a HOLD |
| Raster output-to-vector tracing | VTracer-WASM 0.1.0 | **HOLD:** actual Public conversion already produced 2 mismatched sampled pixels; not lossless |

All existing production shape paths remain unchanged until explicitly admitted by full Golden and source-material gates. No draw-in, img2img, facial features, inventing new colors or objects.

## Newly adopted R1–R6 execution roadmap

**R1: Frozen-v34 serializer candidate** (this PR). Read-only SHA-manifest verification, real pinned SVGO candidate under an isolated output folder, real Chrome RGBA comparison of candidate vs frozen v32 PNG and recorded v34 Chrome PNG for Kyoko/Noel/Ririka; inject unsourced painted pixels as a negative control. Verify determinism. No Public UI or Local changes.

**R2: Full-owner exact geometry observer.** Use SVGPathCommander, Simplify.js, clipping and Earcut/Clipper2 only for source-owned candidate geometry. Preserve RGB, holes, painter order, disconnected components and source-specified arms/staff. Test full owner binary masks and 2x replay, avoid 8-shape diagnostic truncation being mistaken for all-owner PASS.

**R3: Bounded geometric improvement.** Admit a vertex-saving candidate only if **whole-scene real Chrome RGBA exact**, source mask exact, no new RGB, stable silhouette and individual protected details; otherwise keep original exact lattice contours and record HOLD.

**R4: Cross-engine Golden matrix.** Chrome SVG native vs resvg, independent SVG-to-frozen v32, full triad comparisons, version-sequenced visual gallery, repeat SHA evidence, tie/sleeve/staff/alpha and faceless-output review. Discrepancy = HOLD.

**R5: Public-only shadow integration.** Behind an explicit opt-in flag with rollback/fail-closed research, real public route, normal/ON SHA unchanged unless release-authorized. Memory, browser DPR, missing-WASM and error fallbacks tested. Do not change Local.

**R6: Release admission.** Existing Stage8 original contour budget, signed source-owner semantic boundary and human Golden review, Chrome desktop, iPhone Safari, DPR, licensing/notice including resvg MPL-2.0, reproducibility, regression and rollback all PASS first. Then release PR review, merge, production deployment, actual production readback, preservation/handoff. **A technically successful research step is not a release gate.**

## R1 scripts and contract

- `scripts/public_v34_svgo_candidate.mjs`: genuine already-vendored SVGO, metadata-only plugin allowlist, deterministic double-run, disposable output `wx`, no production integration.
- `scripts/verify_public_v34_svgo_chrome.py`: verifies archived SHA manifests prior to output creation; uses Selenium real Chrome for all three 340×340 RGBA Golden comparisons, tests intentional unsourced rect injection (negative), writes metrics.
- `tests/test_public_v34_svgo_bridge.py`: static boundary tests + alpha-sensitive RGBA negative controls.

Run against the archived folders:

```powershell
python scripts/verify_public_v34_svgo_chrome.py --v34 "G:\マイドライブ\chatGPT及びCodex用\Minimalizer\SvgLocalRollbackV34_20261009" --v32 "G:\マイドライブ\chatGPT及びCodex用\Minimalizer\ConnectedSourcePlanesV32_20261009" --out "<fresh non-Golden disposable folder>"
```

Artifacts remain **research-only** even if Chrome Golden byte parity passes; no quality-gate waiver, source-owner certification or production promotion.
