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

## Checkpoint 4: Identity-bearing hands and major props

Hands return only as coarse masses: at most one polygon per side, three to six vertices, no fingers. Skin color comes from the compact blank face, while a widened face geometry is used only for hand-position gating so shoulder highlights are not mistaken for hands.

The auxiliary audit keeps hand recovery conservative: 10 of 15 accepted character images receive hands, 11 total hand planes, with only Omaru receiving both sides. Shirogane's earlier shoulder false positive is rejected.

Major props use a separate high-precision gate. Phase 18 promotes only external staff/sword-like objects and handheld microphone-like objects. Hat detection remains experimental and is intentionally not promoted because Otonose produced a false positive.

Long props must sit outside known head/torso/arm structure, differ from body color, avoid skin-like colors, and pass a low surrounding-subject occupancy gate. This preserves Nerissa's real staff while removing Koganei's clothing-edge false staff.

Microphones require a dark, highly saturated magenta head close to an arm. One logical microphone is rendered as at most two geometric planes: a characteristic-color head and a dark stem. Metadata distinguishes `identity_prop_count=1` from `identity_prop_shape_count=2`.

Final auxiliary closure: all 15 character images pass the Structure Candidate Gate, Night River remains rejected, Isaki alone carries the microphone symbol, Nerissa alone carries the staff symbol, and the remaining 13 images carry no major prop. Maximum shape count is 10 and maximum carrier exposure stays about 0.194.
