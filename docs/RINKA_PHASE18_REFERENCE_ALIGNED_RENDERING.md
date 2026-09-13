# Rinka Reference Phase 18: Reference-aligned Rendering

Phase 18 begins after Phase 17 proved that structure extraction can be gated safely but was still visually too blob-like for the Approved 18 references.

## Checkpoint 1: Faceted Blank Face

The Phase 17 final blank face was still generated from an ellipse. Checkpoint 1 replaces the final rendered face mask with an eight-point faceted plane derived from the detected face center and real head bounds.

The face is intentionally smaller than Phase 17: the accepted face/head area ratio is 0.08 to 0.22 instead of 0.12 to 0.30. The result stays inside both the head silhouette and a dilated face hint.

Front hair now renders above the blank face while side/back hair remains behind it. This matches the Approved 18 visual grammar where bangs may overlap a featureless skin plane.
