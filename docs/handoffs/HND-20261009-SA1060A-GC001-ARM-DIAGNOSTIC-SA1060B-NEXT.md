# Minimalizer SA10.60A → SA10.60B handoff (2026-10-09)

**SA10.60A research diagnostic COMPLETE; prototype release HOLD; source Stage8 ring policy HOLD; human Golden PENDING; Phase15 NOT RUN; production UNCHANGED.** This is not SA10.60 production-integration completion.

## Canonical entry points

- GitHub: `tools/research/sa1060_gc_arm_color_experiment.py`, `tests/zerobase/test_sa1060_gc_arm_color_experiment.py`, `docs/research/SA1060A_GC001_SIGNED_ARM_MASK_AUDIT_20261009.md`, `docs/research/evidence/sa1060a_gc001_arm_numeric_20261009.json`.
- Private Drive: `chatGPT及びCodex用/Minimalizer/SA1060A_GC001_ArmSourceAudit_20261009`, https://drive.google.com/drive/folders/126DtYlC_OxJJLKbszaXL9VqKkQ-5K3WR . Contains 13 canonical files (private actual SVG, Chromium candidate, source comparison board, mask overlay, full test evidence, ZIP/manifest, this stage's code) plus 3 clearly renamed SUPERSEDED import snapshots. Do not publish actual character geometry or source images.
- Previous stable baseline: PR #317 merged `a7caef3050726078f47fb2015dc685aef1de69a9`. SA10.57 SVG pin `bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939`.

## Evidence

- Source-original signed left/right arm masks 2,715 / 6,486 pixels. Exact foreground-color flood from border identifies 533 source-border-background-connected pixels inside signed `right_arm`, zero inside `left_arm`. This is a conservative source-owner contamination diagnostic, **not proof of complete semantic classification**.
- Actual Chromium 144 baselines and 2 source-observed plane trial: left-arm RGB MAE 76.071332 → 59.814733; right 55.439562 → 47.365762. Vertex count 1873 → 1884/1887. Signed face changed 0 pixels, outside signed arms 0 pixels. 470/499 left/right signed-arm pixels changed within candidate. The candidate's changes do **not** recolor the 533 exact background-connected pixels. Do not misstate the relationship between preexisting mask contamination and trial output.
- Strict signed source and original SVG SHA checked. 8/8 tests PASS, including actual two-arm Chromium run. A second fresh Chromium run yields four identical SHA artifacts. These are **research engineering** tests only, not Artistic Golden.
- The two source arms still include incorrect-looking semantic ownership regions and reduced costume structure; the source observation technique cannot independently authorize artistic release. **Trial remains unapproved in private Drive and is NOT integrated.**

## Next SA10.60B

Inspect Phase04 actual part masks and Stage05/Stage06 attachments, then source-owner binding, starting with GC001. Find the first bad stage of the background-connected arm-mask contamination; validate original-coordinate masks/alpha/edge evidence (not analyzer-as-truth). Prepare versioned **new candidate** Phase04 arm/garment ownership masks separately, retaining all signed masks immutable. Require source/face/arm topology verification, actual Chromium and before/after boards, hard true SVG geometry caps, source-original RGB diagnostics, Diagnostic-2 and independent signed holdout coverage before any candidate is accepted. Keep faceless default (no eyes/nose/mouth/brows), no generated visible pixels or raster-in-SVG. Human Golden and original source Stage8 policy continue as **independent unresolved release gates**. Do not run Phase15 or deploy without clearance.

Use GitHub and Google Drive as sources of truth; no RDC needed for this research. Production routing has not been changed or reverified here.
