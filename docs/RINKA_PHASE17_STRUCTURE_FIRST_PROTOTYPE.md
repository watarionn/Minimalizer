# Rinka Reference Phase 17: Structure-First Prototype

Phase 17 starts from merged Phase 16 main `50a37755f782254410678fef7bae33ef6790c025`.

The Approved 18 review showed that Phase 16 still optimizes the wrong abstraction layer. Color-plane cleanup can improve accents, but it cannot reliably preserve pose when the person is represented as generic clustered regions.

## Direction change

Phase 17 changes the pipeline concept from:

`image -> color clusters -> connected regions -> polygons`

to:

`image -> subject silhouette -> semantic macro parts -> coarse polygons -> representative colors`

The first implementation is intentionally experimental and is not connected to the production renderer yet.

## New module

`minimalize_engine/structure_first.py`

It accepts an RGB image plus an already-established subject mask, then derives:
- hair;
- blank face carrier;
- torso;
- left arm;
- right arm.

The neck is estimated from a local silhouette-width valley rather than a fixed Y coordinate.
The torso is a central corridor that adapts to each silhouette row.
Arms are taken from silhouette protrusions outside that corridor and retain simplified contour geometry instead of being replaced by rectangles.
The blank face is synthesized inside the head silhouette, with the remaining head region treated as coarse hair.

## Approved 18 prototype findings

The local 18-image prototype confirmed that this direction fixes an important conceptual problem: parts are now derived from the person's outer shape before color simplification.
Vestia Zeta and Houshou Marine already show substantially more recognizable macro body layout than the old color-first collapse cases.

The remaining major failures are now more specific and structural:
- raised arms crossing above the head are truncated because the first arm search starts near the neck;
- long side hair is reduced to the immediate head region;
- some side hair can still compete with an arm because silhouette alone does not identify the endpoint hand;
- representative part colors are still primitive medians.

These are the next Phase 17 targets. Do not return to Phase 16-style per-color threshold tuning as the primary strategy.
