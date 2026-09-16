# Minimalizer 2.0 Calibration 05 Phase G

Status: V2 rendering closure and deterministic PNG export contract implemented.

## Goal

Phase F made visually accepted facet overlays part of the default V2 raster rendering path.
Phase G closes that rendering path as an export-facing contract without changing the legacy CLI or Web service.

The V2 export boundary is now:

`MinimalizerV2Result + preset -> deterministic RGB render -> deterministic PNG bytes + metadata`

The legacy `minimalize()` engine remains a separate production entry point and is not modified here.

## Public V2 rendering/export API

`minimalize_engine.v2.render_scene(scene, include_facets=True)` is the canonical V2 raster renderer.
Accepted facet overlays are included by default; `include_facets=False` reproduces the Phase E baseline.
`minimalize_engine.v2.export_png(result, preset="minimal", include_facets=True)` returns a `V2PngExport` containing:
- PNG `content` bytes,
- media type and stable default filename,
- `V2PngMetadata`.

Metadata contract version is `minimalizer-v2-png-v1` and contains:
- preset,
- source width/height,
- rendered analysis width/height,
- visible shape count,
- palette count,
- scene facet count,
- rendered facet count,
- facet inclusion flag,
- SHA-256 of canonical rendered RGB pixels,
- SHA-256 of PNG bytes.

`V2PngMetadata.to_dict()` returns a JSON-serializable mapping without runtime timings or environment-dependent fields.
## Deterministic PNG encoding

The V2 exporter writes a fixed PNG structure:
- 8-bit RGB,
- PNG signature,
- one IHDR chunk,
- one IDAT chunk,
- one IEND chunk,
- filter type 0 for every scanline,
- zlib compression level 9,
- no timestamps or text metadata embedded in the PNG.

The pixel SHA-256 is the canonical content identity for rendered pixels. The PNG SHA-256 tracks the exact exported byte stream.

Phase G also updates the regression `algorithm_digest` to include accepted facet overlay data because facets are now part of the standard V2 rendered result.
## Canonical 18-case export verification

All canonical 18 source images were processed with the Phase G V2 pipeline and exported twice.
Results:
- PNG byte equality between repeated exports: `18 / 18`,
- metadata equality between repeated exports: `18 / 18`,
- decoded export pixels equal the Phase F canonical final image: `18 / 18`,
- rendered facet total: `11`, matching Phase F,
- mean PNG size: `4351.44` bytes at analysis resolution.

The canonical Phase G visual regression also reports hard invariant failures `0 / 18`.

## Regression status

Focused export/facet/regression tests: `22 passed`.
V2 regression: `124 passed`.
Full repository: `456 passed, 2 failed, 1 warning`.

The two failures remain the known missing `tests/assets/false_face_phase85.png` failures and are unrelated to Minimalizer 2.
## Decision

Adopt the V2 renderer and deterministic PNG export contract as the stable V2 output boundary.
Do not route legacy CLI/Web requests to V2 in this phase.
Do not add export-time image heuristics; all visual decisions remain inside the V2 pipeline and facet gate.
Keep `include_facets=False` only as an explicit baseline/debug escape hatch.

Recommended next step: **Calibration 05 Phase H: Legacy Entry-Point Integration Gate**.
Phase H should introduce an explicit V2 integration adapter or shadow/opt-in route for CLI/Web, verify legacy behavior remains unchanged by default, and compare V2 exported bytes/metadata through the real application boundary before any production switch is considered.
