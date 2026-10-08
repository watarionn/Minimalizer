# BrowserFallback Selective Region Merge v17: fidelity-first HOLD

Date: 2026-10-08
Scope: **BrowserFallback-only research**. No Local Worker, no generative image edits, no new model or dependencies.
Branch: `feat/browser-selective-merge-v17-20261008`
Status: **HOLD_NO_GEOMETRY_GAIN** (engine and safety guards implemented; actual geometry benefit not established; do NOT deploy or switch the public default).

## Reason for this phase

v16 attempted to reduce the canonical hierarchy from 40 color regions to 30. In real Chrome, the changes affected 37.07% of Kyoko pixels, 64.53% of Noel and 40.83% of Ririka. Kyoko's green necktie-associated palette area grew from 1,994 to 4,241 pixels and the left sleeve changed from gray to navy, while minimum contour IoU still passed. Consequently, arbitrary global hierarchy cuts are disallowed.

## Prototype architecture

A new `selectiveRegionMerge` flag is exposed only through the experimental `?browserFallback=force&browserFallbackQuality=selective` URL in the research branch. It is not in production main.

The implementation is inserted **after** the accepted 40-region hierarchy cut and canonical medoid palette assignment, but **before** shared-contour simplification. It reviews actual shared edges of neighboring region-label masks and merges only when all conditions hold:

- The two regions must have the **same already accepted palette ID**. The final palette mapping/representative color of the recipient is kept unchanged. Never recompute the palette after merging.
- Donor is very small: at most 0.15% of image pixels; donor bounding box has both sides at least 5 px and aspect ratio no more than 3:1, preserving narrow necktie-like structures.
- Source RGB mean separation is at most 16 (Euclidean RGB), shared boundary has at least 5 pixel edges and at least 18% of the donor bounding-box perimeter.
- At most 2 accepted merges per render, deterministically selected by smallest donor area, smallest source-color separation and largest contact.
- Recompute ownership labels and components; no uncovered pixels are permitted. Both sides use the same canonical shared contour and the pre-existing Facet v15 topological/IoU rasterization guards.
- Invalid requests pairing Selective with `spectral-exact`, non-Facet geometry, or unavailable contour modules fail closed.
- The canonical palette centers remain fixed. Existing `lite`, `sharp`, `shape`, `facet`, `exact` routing remains unchanged.

## Real Chrome 154 result: three original 340x340 character sources

| Input | Baseline Facet regions / vertices | Selective regions / vertices | Adjacent pairs inspected | Accepted merges | Selective PNG equals Facet? |
| --- | --- | --- | ---: | ---: | --- |
| Kyoko GC001 | 40 / 1,377 | 40 / 1,377 | 87 | **0** | YES, SHA256 |
| Shirogane Noel | 40 / 1,232 | 40 / 1,232 | 81 | **0** | YES, SHA256 |
| Ichijou Ririka | 40 / 880 | 40 / 880 | 92 | **0** | YES, SHA256 |

The strict same-palette constraints rejected every real input candidate. This is **a correct safe no-op**, NOT a quality improvement.

For all three inputs, real browser route `requestBrowserFallback()` and direct Selective engine produced **byte-for-byte matching PNG**. All five earlier profiles (`lite/sharp/shape/facet/exact`) were SHA256 identical to the previously accepted v15 baseline. Kyoko's dominant green stays RGB(149,211,27) across 1,994 pixels and left sleeve sample (95,275) remains RGB(65,66,74). The green count measures all pixels of that RGB, not the annotated tie alone.

## Test result

- `tests/test_browser_selective_v17.py`: new opt-in route and defaults, deterministic synthetic case with a valid same-palette compact region merging, rejection of different palette / high contrast / thin regions, exact no-op parity for unchanged inputs, and fail-closed structure/geometry paths.
- Extended v17+v15+v14+v13+v12 suite: **43 PASSED** in isolated checkout, plus JavaScript/Python syntax checks.
- CI: `.github/workflows/browser-selective-v17.yml`, containing JavaScript syntax, replay harness compile, new/inherited geometry tests and whitespace diff guard. Record actual CI result separately before concluding PASS.

## Quality decision and next approach

**Keep as a research-only branch. HOLD_NO_GEOMETRY_GAIN.** Do not merge, ship, or advertise a new quality mode until merges demonstrably simplify real examples and pass baseline-relative color/region fidelity. Preserving source-art constraints is more important than reducing shape counts.

The no-op result shows that same-palette adjacency is too strict on the real samples. Next research should estimate near-palette candidate distributions and establish a *paired* reference-aligned gate: small maximal recolor area, source-color difference, edge strength, thin-feature protection, automatic rollback on any tolerance violation, and a robust semantic-free reference-fidelity metric, before adding a near-palette merge. Do NOT blindly relax these thresholds.

## Evidence and repeatability

- [Google Drive v17 evidence](https://drive.google.com/drive/folders/1oXwr6I4ma0pZXGU4VpRC5dv4mPAIA5wG) under `chatGPT及びCodex用/Minimalizer`.
- Three-source montage, machine metrics, raw source+all six profile PNG/metrics archive, diagnostic report, Chrome harness and evidence generator.
- Reusable GitHub Chrome benchmark: `tools/run_browser_selective_v17_chrome_compare.py`.
- Parent baseline production remains [Facet v15 handoff](../handoffs/HND-20261008-BROWSER_FACET_V15_PRODUCTION.md). This work must not change it.
