# SA7.20 Frozen-Threshold Variant Holdout — 2026-10-06

Status: FAIL / CROP NORMALIZATION REQUIRED

SA7.19 froze small anyglasses probability >= 0.80 before this holdout.

Untouched visually labeled variants:
Positive:
- Friend-A pr-img-02: 0.992849 PASS
- Kaela pr-img-02: 0.437923 FAIL

Negative:
- AZKi pr-img-02: 0.410527 PASS
- Fauna pr-img-02: 0.105875 PASS
- Gawr Gura pr-img-02: 0.294330 PASS
- Nanashi Mumei pr-img-02: 0.376289 PASS

The semantic classifier suppresses all four negatives and recognizes Friend-A, but is not invariant to Kaela's full-body crop geometry despite visible forehead goggles.

Decision: do not lower the 0.80 semantic threshold. Move SA7.20 images into development evidence for crop normalization only. SA7.21 must freeze a head-size-normalized crop rule and use new untouched variants for holdout.
