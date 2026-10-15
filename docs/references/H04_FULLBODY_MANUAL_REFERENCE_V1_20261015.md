# H04 Full-Body Manual Reference v1

**Reference ID:** `H04_FULLBODY_MANUAL_REFERENCE_V1`  
**Recorded:** 2026-10-15  
**Status:** `REGISTERED_HUMAN_AUTHORED_REFERENCE` (technical inspection PASS; semantic-part attestation and Golden approval are **NOT** implied).

## Authority and version isolation

This is the **user-drawn full-body** polygon reference exported by **Reference Shape Editor v1.1.0**, on the **actual signed H04 source** (canvas **453 × 1400 px**, signed source SHA-256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`). Embedded source PNG is **byte-identical** to the signed original. The uploaded JSON and SVG correspond in shape count, order, vertex coordinates, palette and names.

- Polygon count: **17**, unique vertices: **156**, vertex references: **211**.
- Shared vertices: **43** (55 additional references); at most four shapes share a vertex.
- Fill colors: **13**. All 17 polygons have valid geometry; SVG matches JSON **17/17**.
- Signed-source alpha silhouette IoU: **0.969847** (236,121 intersection pixels / 243,462 union). Diagnostic only, **not** an official Golden or semantic PASS; anti-aliased edge pixels count as non-zero alpha.
- Earlier **3-polygon jacket-only** H04 trace is a separate predecessor, **not a byte-identical subset** of this 17-polygon revision. Keep both; no automatic transfer of polygon labels.
- **Kyoko Manual Reference v1** is a different case and must never be silently treated as H04.

## Storage, confidentiality and reuse

Original signed PNG, user JSON (contains embedded original PNG), original SVG (coordinates), all previews and read-only diagnostic programs are preserved together in the **PRIVATE** archive:

`Google Drive/chatGPT及びCodex用/Minimalizer/H04_FullBody_Manual_Reference_v1_PRIVATE_20261015.zip`

The public GitHub registry is **source-free and coordinate-free**; do not commit source images, SVG/JSON shape coordinates, exact layer masks, source-containing previews or review signatures to GitHub. Import the **unchanged JSON** in Reference Shape Editor to edit; use SVG for its fixed order and color geometry. Any human change is v2, not in-place modification of v1.

## How this supports MinimalizerLocal L02

The manual shapes are useful as a **human-authored reference for silhouette, layering, limb visibility, jacket coverage, hair outline, shoes, and relative colors**. The current source shape names are generic (`図形 1` to `図形 17`); they are **not per-part semantic labels**. Do not automatically assert hair, skin, arm, jacket or cloth masks from shape names or position alone. For supervised semantic evaluation, independently review and assign each polygon's source pixel region and z-order, especially the hair/jacket sleeve/right-left arm interactions. An image-right area is not automatically subject-right; preserve subject-oriented annotation.

The alpha-mask discrepancy panel marks **red = source not covered by manual polygons** (5,061 pixels), **blue = manual outside source alpha** (2,280 pixels), not classifier errors. Deliberate simplification and anti-aliasing can contribute; use the panel to guide human review only. User polygons are not signed Phase4 segmentation masks.

**Release gates remain unchanged:** L02 source-colored classifier candidate HOLD; semantic labels UNASSIGNED; Phase5 Graph, C03 Stage8 source-vertex, C04 Golden A/B and Local deployment/iPhone acceptance **not approved**. No private worker or Public code has been changed by this reference registration.

## Review artifacts (inside PRIVATE ZIP)

- `00_fullbody_comparison.png`: original / manual output / overlay.
- `05_layer_numbers.png`: numbered polygons for identifying which source shape should receive a future part label.
- `06_alpha_silhouette_delta.png`: red uncovered / blue outside-source regions.
- `07_roi_hair_face.png`, `07_roi_jacket_arms.png`, `07_roi_pants_shoes.png`: source, trace, indexed shapes, alpha discrepancy.
- `audit_metrics.json`, `08_private_shape_index.json` (intentionally all `UNASSIGNED`), `verify_h04_fullbody.py` and `test_h04_fullbody.py`: reproducible inspection. 1 real fixture + 9 deliberately malformed negative cases = **10/10 PASS**.

## Next gate

Review **numbered regions** and confirm part labels, occlusion direction and any deliberate underlay/overlap. Then compare those reviewed regions with L02's `H04_COLOR_WITNESS_SHADOW_NOT_APPROVED` against the **same signed H04 PNG and masks**, without overwriting originals, before deciding if any classifier rule is promotable.
