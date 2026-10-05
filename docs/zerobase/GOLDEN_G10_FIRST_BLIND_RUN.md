# G10 First Untuned Blind Run

G10 was mechanically selected and committed before its first observer execution. The production baseline already included effective primitive-budget geometry, the deterministic 4x4 mask descriptor, and deterministic authorized palette extraction.

Results: Frozen Grounded-SAM completed 5/5; every frozen role had non-zero area in every case; Binder unresolved 0/5; Production Bridge READY 5/5; Authorized Geometry rendered 12 primitives for each case using the production palette API. No Golden raster, manual semantic labels, DiffMin, or post-result tuning was used.

Observer mean: 0.5674 s/image. Peak CUDA allocation: 1378.6 MiB. Fixed oversize guard rejected 7 hypotheses.

Artifact: Google Drive `chatGPT及びCodex用/Minimalizer/GBLIND_G10_FRESH_20261005_first_run.zip`
SHA-256: `f859a44091e59d6eda306c770f3a79c230e174cad39967aa7b106833101a1d4e`

This closes the fresh wiring/generalization execution. Visual quality still requires independent review; passing hard gates is not equivalent to Golden-level abstraction quality.
