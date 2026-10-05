# SA7.22 Macro Semantic Geometry Re-authoring v1 — 2026-10-06

Status: CONTRACT PASS / RENDERER NOT YET CONNECTED

Adds deterministic semantic geometry reconstruction for two macro roles:
- hair: at most 3 major masses
- major_clothing: at most 2 major masses

The algorithm removes tiny disconnected noise, closes small internal gaps, builds coarse hull polygons, and clips geometry back to a narrow dilation of source semantic support. It therefore re-authors a semantic mass rather than tracing every source contour, while remaining non-generative.

Focused tests: 4 PASS.
Full ZeroBase: 582 PASS.
Renderer remains disconnected until GC001 debug artifacts and hard guards are reviewed.
