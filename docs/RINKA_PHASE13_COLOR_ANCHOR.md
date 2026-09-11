# Rinka Reference Phase 13: Face / Hair Color Anchor

## Goal

Phase 13 improves the color fidelity of the Phase 12 face and hair anchors, especially for pale skin + white/silver hair portraits on bright colored backgrounds.

The structural rule from Phase 12 is unchanged: no facial features are reintroduced. The face remains one plain geometric slab and hair remains a small number of large masses.

## Color selection

Face color is no longer always the median of every accepted skin pixel. Candidate pixels are quantized into source-derived color clusters, filtered by skin plausibility and background separation, then ranked by frequency and warm-skin evidence.

Hair color is likewise selected from source-derived clusters. Candidates must remain bright enough, low enough in chroma, and sufficiently separated from the detected background. If the dominant hair candidate is too face-like, a real source cluster with better face separation is preferred.

A secondary hair color may be recorded when a meaningful second source cluster exists, but Phase 13 does not create fine hair detail. The primary large hair plane remains the visual anchor.

## Safety

All selected colors come from source pixels. No arbitrary recoloring is introduced. Existing Phase 12 geometry, collapse detection, quality fallback, Standard mode, Color Strip, and Rinka presets remain unchanged.

Dedicated tests cover warm-skin cluster selection, silver-hair selection against skin contamination, and the face/hair separation fallback. Fixed-corpus evaluation must remain unchanged before merge.
