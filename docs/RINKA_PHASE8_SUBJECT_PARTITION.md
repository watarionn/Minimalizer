# Rinka Reference Phase 8: Subject Macro Partition

Phase 8 addresses a failure mode that Phase 7 could not solve with cleanup alone: a character image can be interpreted as a general scene and collapse into one or two giant color polygons.

The Phase 8 rule is conservative. It does not replace the normal Rinka Reference path for every image.

## Rescue activation

A candidate opaque / nearly opaque square image is first processed by the normal Phase 7-compatible path. Rescue activates only when all of these failure signals are present:

- the normal result is not already in subject mode;
- the border has a stable dominant background color;
- the inferred foreground strongly occupies the center;
- the largest filled shape covers at least 25% of the canvas;
- the second-largest filled shape covers at least 22% of the canvas.

This makes rescue evidence-driven rather than image-name-specific.
## Macro reconstruction

When rescue is accepted, the inferred foreground is passed through Character Structure and the resulting real part masks are used directly.

The renderer rebuilds a small set of semantic masses for:

- face;
- hair;
- left / right arms;
- left / right lower body;
- outfit;
- protected hand / prop details.

Each part gets a base polygon plus only a few large accent-color polygons. Contours are simplified to a small vertex budget before they become final Shapes.

Outfit color ranking is not pure usage order. It also rewards perceptual distance from the face so a large accidental skin-colored overlap does not replace the intended dark or saturated garment mass.
## Fixed-corpus evidence

At level 4 / analysis max side 220 on the 16-image fixed corpus:

- rescue activates on exactly 1 image;
- macro partition activates on exactly the same 1 image;
- the other 15 images stay on the normal Rinka path;
- mean shape reduction remains about 38.32%;
- mean vertex reduction is about 32.22%;
- worst non-rescue identity delta is about -0.0449;
- worst non-rescue silhouette delta is about -0.0010.

For the rescue case, the normal path had giant filled shapes of about 25.4% and 24.7% of the canvas at the analysis checkpoint. The Phase 8 target result keeps its largest filled shape below 8%.

The older pre-target pixel identity/silhouette scores are not used as the rescue safety criterion because the rescue deliberately reconstructs the subject before target-style post-processing. CI therefore guards non-rescue images with the historical metrics and guards rescue images with activation, macro reconstruction, and giant-shape suppression metrics.
