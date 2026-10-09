# Real original Stage8 topology counterfactual revalidation (2026-10-09)

Following the research scripts and signed source manifests in the parent PR #333, the independent 340x340 Stage8 corpus was re-evaluated against all 11 original source-owner geometries for GC001 and Raden. Source authority: SHA-256 verified source PNGs and the saved role-mask SHA manifest. The structural head owner is not part of the ten painted-role mask manifest; it was checked for raw binary-topology preservation without pretending that it had an independently signed painted-visible mask.

- GC001: 13 safe candidate tiny rings jointly removable, 14 source-ring vertices. All eleven original raw raster owners are pixel-identical after the proposed removal, and the 8-connected component counts and OpenCV RETR_TREE contour hierarchies are unchanged.
- Raden: 6 safe candidate tiny rings jointly removable, 9 source-ring vertices. Same eleven-owner exact raw pixel, component and hole-hierarchy parity.
- Source original Stage8 JSONs were **not** edited. This is a reproducible research candidate, not production promotion. Private per-owner evidence: `stage8_micro_topology_real_result.json`, reproduction code `real_micro_topology_revalidation.py`.
- Counterfactual has not been independently checked for SVG/browser DPR4 rendering or complete Golden character quality; browser and human review remain HOLD.
- Remaining source vertex totals **if eventually authorized**: GC001 3,590 versus historical cap 1,887; Raden 2,361 versus cap 1,412. This does not solve the full Stage8 budget problem.

No face feature generation, no synthetic source RGB, no production change, no source deletion. Keep the previous Stage8 hard gate intact.
