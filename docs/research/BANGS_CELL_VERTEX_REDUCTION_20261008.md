# Bangs Pixel-Cell Vertex Reduction (2026-10-08)

**Outcome: source-only local fringe quality+complexity PASS; full character/Golden HOLD.**

The canonical 340×340 Kyoko GC001 source contains a source-observed 694-pixel contiguous inter-eye orange hair strand. Prior Pixel-Cell Boundary v1 restored 687/694 pixels (98.99%), with zero excess, but 485 SVG vertices. This experiment keeps the same source masks, source RGB medoid tonal layers, same 340px native resvg renderer, and varies only the source pixel-cell boundary simplification epsilon. Code: `tools/research/bangs_cell_vertex_reduction.py`.

| Epsilon | Source-covered /694 | Missing | Outside source | Vertices | Contours |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 687 | 7 | 0 | 485 | 15 |
| 0.1 | 687 | 7 | 0 | 485 | 15 |
| 0.2 | 687 | 7 | 0 | 485 | 15 |
| **0.35** | **692** | **2** | **0** | **288** | **15** |
| 0.5 | 684 | 10 | 0 | 204 | 15 |
| 0.75 | 666 | 28 | 1 | 118 | 14 |
| 1.0 | 673 | 21 | 16 | 80 | 11 |

Selection gate: rendered original-source footprint must cover **at least 687 pixels with zero excess**; among candidates meeting it choose the fewest vertices. The selected epsilon **0.35** retained 692/694=**99.71%**, missing 2, exceeding prior by 5 pixels while cutting vertices by 197 (**40.62%**), all colors still original-derived. This is an **actual rendered output** measurement and does not equate to a generalized vector Golden PASS. More aggressive 0.5, 0.75, 1.0 settings are rejected by footprint gates despite fewer vertices.

The 2 remaining missed pixels require a separate source/component inspection, not invented hair. The result remains **GC001 manually observed fringe only**. The rest of the character is still unresolved (blank face, costume/outer hair gaps). Do not deploy to Local PWA or Public.

Research tests at `tests/test_bangs_cell_vertex_reduction.py` and previous related guards: **27 PASS**.

Artifacts saved to `chatGPT及びCodex用/Minimalizer/BangsCellVertexReduction_20261008/`, private Drive folder `1bW3Y0DJxCTBbUk_2qtbPwHYxZpQLJjdj`. Eightteen files (7 SVGs, 7 PNGs, comparison image, manifest plus possible sync metadata), source provenance and SHA-256 recorded per result. Check cloud-side synchronization separately from mount.

Next: inspect the last 2 missed pixels and distinguish actual source topology from raster thresholding; then evaluate local vector stitching against the actual character SVG with source mask and face-plate gates.
