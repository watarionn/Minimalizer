# Reference Shape Editor v1 (2026-10-15)

Source-only independent polygon authoring utility for a human-built Minimalizer reference image. **Not** part of the production conversion path, Local Worker or C04 Golden approval workflow.

## Entry

`web/static/reference-shape-editor.html` is a **standalone** HTML file: inline CSS and JavaScript, no NPM, remote dependencies, network requests, ML inference or generated pixels. Download it and open locally. If the site serves `web/static/` unchanged, it may also be accessible as a static page, but production HTTP availability has **not** been verified or deployed by this change.

## Functions

- Load PNG/JPEG/WebP/GIF as adjustable-opacity background without modifying the source.
- Add polygon vertices in Draw mode and finalize with button / Enter.
- Reuse **the same vertex ID** from existing polygons via adjustable 4–24 CSS px snapping; dragging a shared vertex moves all owning polygons together.
- Select, edit, add/remove vertex, move shape, change layer order/visibility, fill using feature/accent/representative sampled palettes or exact imported ColorStrip JSON, or sample source pixel.
- Undo/redo (last 100 edits), pan/zoom, inspect layers.
- JSON project for ongoing editing (includes private original image bytes as base64), SVG/PNG for polygon-only transparent output (no source raster embedded).
- Reject self-intersecting/repeated-point polygons on creation and reject non-image/external-URL payloads in JSON restore.

**Palette provenance:** offline feature/characteristic/representative computation is an independent local **approximation**. It is **not** cryptographically or mathematically equivalent to Minimalizer's canonical ColorStrip. Import its official `metadata.colors` / `colors` JSON for exact selected values.

## Verification

Original source ZIP and test suite are separately archived in the approved private Drive folder `chatGPT及びCodex用/Minimalizer` (do not upload signed original or user projects to public GitHub).

2026-10-15: Node `--check` PASS; six isolated Chromium UI tests PASS: source load, local palette, shape creation, polygon rejection, shared-vertex movement and Undo/Redo, JSON restore, ColorStrip metadata JSON import, SVG/PNG output and no source image embedding, narrow mobile-panel behavior, malformed project rejection. Native iPhone Safari has **not** been tested or signed off.

Human Golden review and Stage8 source vertex gates remain independent and held. No release authorization or C08 closure is claimed.
