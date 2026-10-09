# MinimalizerPublic: Delaunator 5.1.0 browser library integration (2026-10-09)

## Intent and project boundary

The purpose of this conversation is **library research and actual installation in MinimalizerPublic**, distinct from finishing MinimalizerPublic product quality/deployment in the other conversation. The Local/Python runtime is OUT OF SCOPE. The Public browser front end and route live under `web/static/` in the shared GitHub repository.

Previous installed Public libraries:
- `polygon-clipping@0.15.7` (MIT): self-hosted Public viewport polygon intersection, PR #344.
- `simplify-js@1.2.4` (BSD-2-Clause): opt-in mask-exact original-vertex reduction **research proposals only**, PR #345.

New library: `delaunator@5.1.0` (ISC) self-hosted browser UMD bundle. Delaunator triangulates 2D vertices; its UMD build also bundles `robust-predicates@3.0.2` (Unlicense), with both license texts preserved.

## Implementation

- `web/static/index.html`: loads the vendored UMD library and `public-mesh-research.js` before the existing browser processing engine. Also normalizes accidental literal `\\n` separators from earlier Public script insertion into ordinary HTML newlines. This is a markup-only correction.
- `web/static/public-route.js`: sets `publicMeshResearch: true` **only** for URL query `?publicMeshResearch=1`. Normal Public conversions keep this `false`.
- `web/static/browser-fallback.js`: in opt-in research mode, invokes `MinimalizerPublicMeshResearch.auditShapes`, exposing `X-Minimalizer-Public-Mesh-Audit`, `X-Minimalizer-Public-Mesh-Accepted`, `X-Minimalizer-Public-Mesh-Rejected` headers and in-memory analysis evidence. No source image bytes leave the browser.
- `web/static/public-mesh-research.js`: extracts existing per-owner contour vertices, deduplicates vertices by exact coordinates and Delaunator-triangulates **each owner separately**. It evaluates candidate triangles against the **complete existing owner raster**, as supplied by the existing `MinimalizerOpenCvRaster.rasterizeLoops`. A proposed triangle is accepted *for diagnostic counting* only if every binary pixel rasterized by the proposed triangle lies inside that same owner's original filled mask. This prevents a candidate spanning outside a concave contour or across an owner hole from passing.
- Compute bounds: up to **8 shapes**, **180 distinct points per shape**, **48 tested triangles**, **160,000 source pixels**. Invalid, missing and degenerate source data are fail-closed. If bound is reached, status is `truncated`; truncated audits do not certify full-scene mesh parity. Observer never mutates the original shape or applies candidate geometry. Full rendering, face-feature policy, 40-shape count, RGB, local environment and original source owners are left unchanged.

## Verified real integration

- Actual Delaunator 5.1.0 UMD invoked in Node VM: correct square triangulation into two triangles.
- `node tests/js/test_public_delaunator_mesh.cjs`: **7 scenarios PASS**. Simple square produced **2 accepted triangles**, source hole produced **2 rejected triangle candidates**, concave source produced **1 rejected triangle candidate**, and tests cover source immutability, bound enforcement, malformed input and unavailable dependency.
- `pytest tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **15 tests PASS**. This includes build output, vendor and license, Public route opt-in and Local isolation.
- JavaScript syntax checks for new adapter, existing browser fallback and Public route PASS.
- Real Chrome desktop, **built and served Public static release** (`dist/shin`), 64x64 sample PNG, actual `MinimalizerComputeRoute.minimalize(file)`:
  - Default Public: HTTP 200, 24 shapes, mesh audit `disabled`, polygon-clipping audit `ok`, Simplify research `disabled`.
  - `?publicMeshResearch=1`: HTTP 200, same 24 shapes, mesh audit `truncated`, **32 owner-contained triangles** and **8 triangle candidates rejected**, polygon-clipping still `ok`, Simplify still `disabled`.
  - Returned PNG exactly matched byte-for-byte: SHA-256 `29e33338f58d0e9c367b57c07f48b578d21ad5ae391e24a4529a88a0a891debb`, 482 bytes for both.
  - The unrelated subject guidance model was disabled in this isolated smoke test only. Public code and default app settings were NOT altered.

## Decision and limits

**Library installation and Public mesh research integration are complete upon merge to main**, not equivalent to MinimalizerPublic full production rollout. The mesh is diagnostic and never used for final paint. A Delaunay triangulation does not inherently respect a concave polygon or holes. The subset raster gate is why unsafe candidate triangles are rejected.

Any future true triangular rendering or interior-feature optimization belongs to the other product-completion conversation and must first independently pass the source RGB/owner and Stage8/Golden/iPhone Safari gate. This library should not be advertised as an image-quality increase until that validation occurs. No LocalWorker, Python runtime or source model changes are involved.
