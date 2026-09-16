# Minimalizer 2.0 Calibration 05 Phase H

Status: Legacy Entry-Point Integration Gate complete. V2 is reachable through explicit opt-in boundaries while all legacy defaults remain unchanged.

## Goal

Phase G closed the deterministic V2 PNG contract but did not cross the existing application boundary.
Phase H proves that the same contract survives real file, Web, and CLI entry points without silently replacing the legacy engine.

The integration rule is strict:
- existing `/api/minimalize` remains legacy-only,
- existing `/api/info` keeps its legacy supported-mode contract,
- the browser UI is not changed,
- existing CLI output remains legacy by default,
- V2 is available only through explicit opt-in/shadow paths.

## Shared file adapter

`minimalize_engine.v2.minimalize_file_png()` is the common file-boundary adapter.
It loads an image through the existing image loader, runs `minimalize_v2()`, and returns the unchanged Phase G `V2PngExport` contract.

This adapter is shared by Web and CLI so entry-point code does not implement a second V2 renderer or PNG encoder.

## Web opt-in boundary

Two V2-only endpoints are added:
- `GET /api/v2/info`
- `POST /api/v2/minimalize`

`/api/v2/minimalize` always returns the Phase G deterministic PNG contract. It accepts an explicit V2 preset and an `include_facets` switch.
The response exposes the contract version, preset, pixel SHA-256, PNG SHA-256, scene facet count, rendered facet count, shape count, and source/analysis dimensions as headers.

The legacy `POST /api/minimalize` Literal contract still accepts only:
- `standard`
- `rinka_reference`
- `color_strip`

Submitting `mode=v2` to the legacy endpoint remains invalid. V2 is therefore not an accidental fourth legacy mode.

The static browser UI is deliberately unchanged in Phase H.

## CLI shadow boundary

The legacy CLI gains three explicit shadow options:
- `--v2-shadow-png PATH`
- `--v2-preset PRESET`
- `--v2-no-facets`

Without `--v2-shadow-png`, CLI behavior is unchanged.
With the flag, the normal legacy SVG/PNG/WebP work runs first and an additional V2 PNG is written afterward through `minimalize_file_png()`.

The CLI prints the V2 contract version and PNG SHA-256 so shadow artifacts can be compared without replacing legacy artifacts.

## Canonical 18-case boundary verification

The Phase H Web service adapter was run against all canonical 18 source images and compared with the frozen Phase G export results.
Results:
- PNG SHA-256 equal: `18 / 18`
- pixel SHA-256 equal: `18 / 18`
- rendered facet count equal: `18 / 18`
- PNG byte length equal: `18 / 18`
- contract version: `minimalizer-v2-png-v1` for all cases

## Real entry-point guard case

Hakos-Baelz was used because it carries five accepted Phase F facets.
Through FastAPI `TestClient` and the real `/api/v2/minimalize` route:
- status: `200`
- response-body SHA-256: `b44d9ca98262b0b49baa5c13df95d38b32cd3241587565eea50c412f17674c2e`
- response header PNG SHA-256: same value
- Phase G expected PNG SHA-256: same value
- rendered facets: `5`

Through the real CLI shadow option, Hakos-Baelz produced the same V2 PNG SHA-256.
The legacy SVG was also generated once with V2 shadow enabled and once without it. Both legacy SVG files had SHA-256:
`5619C60331E7345951321414378B9D6C3F32A0C3EBF0894414A38A6655D21521`.

This proves the shadow path does not alter the legacy artifact for this canonical guard case.

## Regression status

- focused V2/Web/CLI integration tests: `35 passed, 1 warning`
- V2 regression: `125 passed`
- canonical 18-case regression: hard invariant failures `0 / 18`
- full repository: `461 passed, 2 failed, 1 warning`

The two failures are the existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Phase H.

## Decision

Adopt the V2 file adapter, explicit Web V2 endpoints, and CLI shadow path as the Phase H integration boundary.
Do not add V2 to the legacy mode selector.
Do not change the static browser UI yet.
Do not switch the legacy CLI default engine.
Do not deploy or merge as part of this phase.

Recommended next step: **Calibration 05 Phase I: Legacy-to-V2 Migration Readiness**.
Phase I should compare real legacy and V2 entry-point outputs, document capability/config gaps, and define the exact migration gate required before any default-engine switch. The default switch itself requires a separate explicit approval.
