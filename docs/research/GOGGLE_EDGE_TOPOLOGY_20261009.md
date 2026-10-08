# Goggle Edge Topology Observer (2026-10-09)

**Executed on canonical GC001, source-edge evidence completed, semantic frame/lens segmentation remains HOLD. No production changes.**

Previously source color candidates were mixed with hair and hat, and Phase04 accessory mask was only chest decoration. This stage implements `tools/research/goggle_edge_topology.py` to extract genuine **source Canny edge traces** within the preexisting manually designated *diagnostic* goggle window x=104..240, y=38..103. It records candidate bounding boxes, contour length, closure heuristic, original RGB pixel sample, and original Phase04 hair occupancy for each candidate bounding box. It does NOT infer goggles by filling rectangles, synthesize unseen lens, use img2img, alter hair ownership, produce a semantic goggles mask, or output a goggles SVG.

Actual source output: **40** edge contour candidates after minimum size and length filtering. Largest bounding boxes include [175,38,44,55] length 533.84 and [104,38,83,62] length 466.56. Some contours are closed and some open; all overlap very large areas of existing Phase04 hair mask. Visual source overlay shows these traces intermix lens/frame contours with bangs, hat and accessory edges. **Do not interpret every detected contour as goggles or infer semantic segmentation precision.** The current source remains insufficient to cleanly split goggles from hair using only color + generic Canny geometry. Research quality: evidence PASS; independently labeled goggles mask: NO-GO.

Tests `tests/test_goggle_edge_topology.py` and prior regression suites: **46 PASS**.

Artifacts under canonical private Drive `chatGPT及びCodex用/Minimalizer/GoggleEdgeTopology_20261009` folder ID `1bOIXXGPn9MEFFekqbh9EflZKzN3PLiOn`: `goggle_edge_candidates.png` and `source_goggle_window_edges.png` plus `manifest.json` with coordinates and file hashes.

**Next gate:** obtain independent semantic segmentation evidence from an existing observer / validated human polygon annotation for the actual visible frame and separate left/right lens, with manual source-image boundary review. Then pixel-cell vectorize **only** the verified visible regions, compare against original and preserve three certified inter-eye fringe paths. Do not fill unobserved hidden geometry. Full character's face remains incomplete; no Local/Public deployment.
