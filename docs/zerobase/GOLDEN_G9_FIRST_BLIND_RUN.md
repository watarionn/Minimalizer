# G9 First Untuned Blind Run

Status: COMPLETE / REVIEW PENDING

The fresh G9 suite was executed only after the generic semantic template and source corpus were sealed on main. No thresholds, prompts, semantic roles, case membership, or required-feature policy were changed after seeing the five cases.

Results:
- Frozen Grounded-SAM observer: 5/5 completed on CUDA.
- All four frozen observer roles had non-zero area in all five cases.
- Binder: unresolved=0 for every case.
- Feature Survival / Production Bridge: READY for 5/5.
- Authorized Geometry + SvgRenderer: rendered 5/5.
- Golden raster: not used.
- Manual semantic labels: not used.
- DiffMin: off.
- Kiara produced one oversize hair hypothesis; the pre-existing fixed guard rejected it.

Runtime mean was 0.583 s/image after model load; peak allocated CUDA memory was about 1378.6 MiB.

A run-only palette adapter sampled median RGB inside each already-authorized semantic bbox. It did not decide semantic ownership, but it is not a reviewed canonical production palette API and is therefore not adopted production behavior.

Full NPZ evidence, masks, source inputs, contact sheet, SVG candidates, report, and handoff are preserved in Google Drive under `chatGPT及びCodex用/Minimalizer/GBLIND_G9_FRESH_20261005_first_run.zip`.
Bundle SHA-256: `e446a04bcb913b354876048b40957f10d8a76126b5fb9aa4c76c111d15e72aab`.

Next: visually and quantitatively review the five sealed candidate SVGs without changing this run, then decide the next generic production improvement.
