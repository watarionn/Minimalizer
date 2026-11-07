# MinimalizerLocal Codex owner-gated next steps

Date: 2026-11-07

This handoff records the next actionable gates after the local-PC and private
Drive inventory. It is source-free and does not authorize a merge, deployment,
Golden update, or production change.

## Current protected state

- `main` baseline: `d7caae3bc9500a63c021e7cc51594a7f8084c7cc`.
- Lane A Draft PR #449 head: `acbc9ca4df7d0114c744b77eee6c511da3a22081`.
- Lane B Draft PR #451 head: `39b9281087ded96e54bab5f364f94cb737fe81e1`.
- Public/C08, LocalWorker production, Golden, signed originals, and main are
  unchanged.

## Evidence decisions

- The signed H06 source is available and SHA-256 verified as
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.
- No official Local Stage8 source JSON plus expanded SVG triple was found in
  the bounded Drive or local-PC inventory. Public Stage8 and manual trace
  artifacts are not substitutes.
- Lane A H06 remains candidate-only: four source-only removals were proposed,
  one independently observed garment pixel was restored, no accepted P0/P1
  improvement was established, and Phase4 remains `FAIL`.
- Lane B L04 remains `HOLD`; L07 static QA and L05 TestClient QA do not prove
  private HTTPS, browser, or physical iPhone behavior.

## Required owner-side inputs

1. Lane A: an independently provenance-pinned garment/arm/underlayer observer
   for H06/H08, bound to the exact signed source SHA and carrying its model,
   run, class-map, and output hashes. Unknown pixels must remain unknown.
   Human review masks remain post-inference evaluation only.
2. Lane B L04: the official signed original, Stage8 JSON, and expanded SVG,
   with exact SHA-256 values and cross-links. The triple must contain non-empty
   geometry, source-owner exactness, protected face/arm exactness, and exact
   silhouette measurements.
3. Lane B L05/L07: an owner-authorized private HTTPS PC run with PNG input,
   PNG output, rejection/429/worker-unavailable paths, and response/file
   readback. Physical iPhone acceptance is deferred until production
   reflection, as previously specified.

## Release rule

Keep #449 and #451 Draft. Do not promote Phase5, merge to `main`, change
Public/C08 or production, or treat static/TestClient results as device
acceptance until the owner-side gates above are read back and independently
verified.
