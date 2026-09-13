# Rinka Reference Phase 18: Reference-aligned Rendering

Phase 18 begins after Phase 17 proved that structure extraction can be gated safely but was still visually too blob-like for the Approved 18 references.

## Checkpoint 1: Faceted Blank Face

The Phase 17 final blank face was still generated from an ellipse. Checkpoint 1 replaces the final rendered face mask with an eight-point faceted plane derived from the detected face center and real head bounds.

The face is intentionally smaller than Phase 17: the accepted face/head area ratio is 0.08 to 0.22 instead of 0.12 to 0.30. The result stays inside both the head silhouette and a dilated face hint.

Front hair now renders above the blank face while side/back hair remains behind it. This matches the Approved 18 visual grammar where bangs may overlap a featureless skin plane.

## Checkpoint 2: Directional hair planes

Hair rendering no longer polygonizes the detailed connected-component contour directly. Each front / left / right / back hair region is converted into a 4-6 point directional plane sampled from real mask row spans.

This keeps the approved-reference intent of large straight-edged hair masses while avoiding the rejected bounding-box prototype that produced oversized trapezoids.

Front hair stays above the blank face; side/back hair stay behind it. Regression tests cap every hair plane at six vertices and lock this z-order relationship.

Auxiliary corpus closure remains 15/15 character images passing the Structure Candidate Gate, with Night River rejected as non-character. Hair count is two planes on all 15 accepted corpus characters and maximum carrier exposure is about 0.231.

## Checkpoint 3: Characteristic outfit accents

The new AI-free `characteristic` feature-palette selector is reused only inside the torso mask. It is not applied to the whole image, so hair, skin, and background colors do not compete directly with outfit colors.

The established dominant torso color remains the base plane. `characteristic` is used only to rescue up to two secondary identity-bearing colors, selected from up to four palette candidates and filtered by area, Lab distance, connected-component size, and the existing coarse-plane budget.

Sleeves remain one plane each and never receive characteristic accents. If feature-palette extraction cannot produce a safe torso accent, the previous two-cluster accent detector remains as fallback.

A/B review against Checkpoint 2 showed that keeping the dominant base avoids large recoloring on Koganei while still restoring meaningful salmon/purple secondary planes on Otonose and Todoroki. The 16-image auxiliary audit remains 15/15 character PASS with Night River rejected; maximum carrier exposure is about 0.203.
