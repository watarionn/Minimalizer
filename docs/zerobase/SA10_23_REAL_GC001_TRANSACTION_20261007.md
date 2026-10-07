# SA10.23 real GC001 / Kyoko transaction — 2026-10-07

Status: REAL SOURCE TRANSACTION COMPLETE / HOLD at immutable hard gates

## Source binding

- Canonical Drive folder: `GC001_IMG_1205`
- Drive source: `GC001_source.png`, ID `1LxHHizN1nC9JVpbHegqMtO38O6xWwjpj`
- Local source used: `C:\Work\Temp\macro-gc001\GC001_source.png`
- SHA256: `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`
- Local pre-existing `GC001.png` was byte-identical (153746 bytes).
- Existing Phase 4 artifacts were reused only as explicit RTMLib-unavailable fallback; no Golden raster was used as inference input.

## Reproduction

The real transaction tool is `tools/run_sa1023_real_gc001_transaction.py`. The Phase 3–12 replay was emitted outside the repository under `C:\Work\Temp\sa1023-gc001\GC001_source` and the report was written to `sa10.23_transaction.json` there. The Phase 12 result selected `aggressive`, with final SHA256 `5514542cce099d2bfb5c265b811699348d628f5f803ca25813d1ebbeb79ce1dc`.

The replay completed Phase 5–12 with provenance gates passing. Phase 6 reported 469 bound / 55 unbound regions, Phase 7 244 masses, Phase 10 198 selected primitives, and Phase 11 retained 16 unresolved depth pairs.

## SA10 evidence

- SA10.18 source silhouette/anatomy: **FAIL**, silhouette IoU `0.849834`, topology changed. The hard gate is not overridable.
- SA10.20 structural evidence: anatomy available; topology **FAIL**.
- SA10.19 source-shape observer: OpenCV contour evidence available, `match_shapes_i1=0.033428`; observer-only.
- SA10.21 saliency/per-region evidence: emitted in the external transaction report; observer-only.
- SA10.22 `pydiffvg`: unavailable. The transaction recorded `fallback_noop`; no generative pixels or optimizer adoption occurred.
- No malformed candidate was promoted as BEST. Production promotion remains false.

This is an honest real-source HOLD, not a threshold relaxation. The next repair must be fail-local at the candidate silhouette/topology boundary; SA10.19/21 scores cannot clear the SA10.18/20 failure.
