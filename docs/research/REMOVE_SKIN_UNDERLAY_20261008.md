# Removing the implicit subject-wide skin plate (2026-10-08)

**Stage executed. Real SVG rendered and visually inspected. Structural plate-removal PASS; artistic/whole-character quality NO-GO. Production untouched.**

The user correctly objected to the skin-colored face shape overlapping the fringe. PR #255 established the root cause: `put(owner,skin,"subject","underlay")` filled the entire character silhouette in sampled facial skin RGB, then selectively attempted to cover it with hair/clothes. Wherever masks/colored polygons dropped source details, the false-colored plate showed through. Calling this layer "subject" rather than "face" did not make it safe.

## Actual modification

Research-only `tools/research/remove_subject_skin_underlay.py` forks the previously color-corrected, owner-partitioned vector pipeline **without** the full-subject skin plate. It directly emits source-derived, per-part masks/colors, tie and residual source regions. It still reserves the original visible face from unrelated part ownership, to avoid face-overdrawing. The face itself is therefore **unresolved/blank**: no restoration of invisible skin underneath eye/nose/mouth imagery, no fake skin ellipse/polygon, no generated image, no embedded raster. The background is a neutral canvas for comparison and **is not a substitute for face reconstruction**.

Output folder `chatGPT及びCodex用/Minimalizer/RemoveSkinUnderlay_20261008/`, Google Drive folder ID `1D-QUDpMpxba2CPKgNZDtunHbpyaRQtrh`.

Real images:
- `character_part_vector.svg` (colored source-part vector graphics, background)
- `character_foreground_alpha.svg` (transparent part graphics, no background)
- `character_part_vector.png`, `character_foreground_alpha.png`
- `comparison_source_vs_vector.png` (visual source versus result)
- `manifest.json` (SHA-256 and structural metrics)

## Source-based metrics

| Measure | Previous Part Occlusion v1 | Current no-subject-plate experiment |
| --- | ---: | ---: |
| SVG elements | 31 | 30 |
| Contours | 244 | 238 |
| SVG vertices | 4,616 | 4,240 |
| Rasterized subject silhouette IoU | 0.97593 | **0.84221** |
| False-positive foreground pixels | 188 | 97 |
| Missing source foreground pixels | 1,127 | **8,510** |
| Underlying full-subject skin plate | 1 | **0** |

Existing Phase04 face mask reserves **4,808 source pixels**. These are intentionally NOT recreated in this SVG because doing so with a flat skin fill would repeat the user's rejected aesthetic/structural error. Some missing-foreground pixels also come from source-mask/contour losses outside the face. The result has a visible blank hole for the face. **This is honest evidence that plate removal alone cannot complete a human figure**, not an accepted fallback, and not a successful aesthetic output.

## Gates

- Structural regression added: `tests/test_remove_subject_skin_underlay.py`.
- `pytest tests/test_remove_subject_skin_underlay.py tests/test_audit_no_face_plate.py -q`: **6 passed**, covering absence of subject-wide face underlay, whole-foreground completeness false claims and the prior audit.
- Real GC001 program with `python -W error` executed successfully; comparison SHA-256 `57bae1596a1cf4758c5628c89bd476ceb753c4ae75cba73691e7d468a3f4b221`.
- **No claim of silhouette Golden PASS, completed Minimalizer SVG, or suppression of visible original facial details when the source photo is layered underneath.**
- Do not deploy this diagnostic incomplete vector scene to MinimalizerLocal/Public.

## Next engineering experiment

Need a genuine source-grounded **non-face layer composition** strategy that simultaneously preserves natural bangs, ear/neck boundary, and identity without inventing unobserved skin under existing eye and nose lines. Possible solution: an explicit vector *scene representation where facial feature contours are not ever authored*, yet the observed skin areas are constructed from local source color/geometry as ordinary adjacent source regions rather than a face-sized cover or subject-wide plate. This requires input-derived mask provenance, a no-large-skin-polygon gate, anti-overlap validation and independent image review. A transparent facial hole is not a solution.

Keep PR #255's implicit-face-plate gate and add an SVG-drawing order/source-ownership assertion before any future production promotion.
