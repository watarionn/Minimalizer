# Reference Shape Editor v1.2 sync (2026-10-21)

## Canonical source and scope

The public website repository `watarionn/portfolio-site/tools/reference-shape-editor/{index.html,styles.css,app.js}` is the authority for deployable code. `web/static/reference-shape-editor.html` in Minimalizer is the convenience **standalone/offline** packaging of those exact CSS and JS sources (inlined). This update only touches the manual reference tracing editor; it does not change Local L02, Public/C08, Golden acceptance, worker infrastructure, research branches, or any machine-generated artifacts.

## v1.2 changes

- Multi-select layers by checkbox, then merge them into one lossless **composite layer**. A composite preserves each original polygon, fill, shared vertex, and render order. It is intentionally **not** a geometric polygon union.
- Drag the ≡ handle to change layer stacking order, including composite layer blocks. The existing front/back controls remain available.
- Unified de-duplicated palette derived from Characteristic, Featured, and Representative colors, independently editable (add/update/delete). Source category arrays remain unchanged.
- Underlay 01 and Vertex Snap 02 are closed by default using native `<details>`.
- Removed the redundant on-canvas vertical-position slider; camera pan, mouse wheel, fit-width, and zoom remain.
- JSON schema `reference-shape-editor/v1` unchanged, with optional `layerGroups` and `palette.unified`. Old v1 JSON remains loadable.
- Palette/layer operations participate in Undo/Redo. SVG/PNG continue to export source geometry without the original underlay.

## Verification

The deployed-source repo includes the dependency-free regression script `tools/test_reference_shape_editor_core.js`, covering layer merge/split/order, source geometry preservation, undo/redo, palette edit/import, and old/new JSON import compatibility. JavaScript parse, document element references, and standalone packaging should be verified against the source PR prior to merge. Real browser and iPhone/touch drag interaction remain separate manual acceptance checks.

## Safety and provenance

Never add user source photographs, traced project JSON/SVG, private source coordinates, or derivative training data to this public copy. This file is independent of the Minimalizer conversion pipeline. Do not treat site publication as a Golden pass.
