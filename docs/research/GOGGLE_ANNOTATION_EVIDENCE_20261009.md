# Goggles Source Annotation Review Sheet (2026-10-09)

**Source-review evidence completed; visible lens/frame boundary annotation remains HOLD / NO-GO. Production untouched.**

Generated a reproducible original-source 340×340 contact sheet for manual inspection of left lens, right lens and frame, each with full original image, review window, and nearest-neighbor enlarged crop. Canonical GC001 source SHA-256: `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.

The review windows (not semantic masks) are left lens [106,45,150,90], right lens [143,31,197,77], frame [102,32,201,98]. The actual original crop visibly contains goggles and adjacent orange bangs/hat. **Do not turn these rectangle boundaries into a polygon, SVG, mask, or inferred hidden material.** A source-verified visible-lens/frame pixel segmentation has **not** been established. The prior AnimeSeg accessory output remains broad, and frozen SA7.9 tiny eyewear candidates were below the head goggles near eyes. No reason to relax multi-observer authority.

Source code: `tools/research/goggle_annotation_review.py`; regression: `tests/test_goggle_annotation_review.py`. Research suite: **53 PASS**. Result images and SHA manifest under `chatGPT及びCodex用/Minimalizer/GoggleAnnotationEvidence_20261009`, Drive folder ID `1opHQxLxaMxcqbCAt8yjm0cv2HHmw8jBy`. Verify cloud-synced files separately.

**Next substantive step:** use a genuine human-reviewed source-following contour trace or verified per-material observer rather than another rectangular proposal. Establish left lens, right lens and frame source masks from visible boundaries with hair/hat exclusions, annotate provenance, quantify false overlap and test on a second subject. Only then authorize Pixel-Cell SVG integration; face-hole and whole-character Golden remain NO-GO.
