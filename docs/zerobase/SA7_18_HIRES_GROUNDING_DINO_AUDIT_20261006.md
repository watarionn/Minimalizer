# SA7.18 High-Resolution Grounding-DINO Eyewear Audit — 2026-10-06

Status: REGION PROPOSAL ONLY / SEMANTIC AUTHORITY NO-GO

Frozen SA7.9 prompt and 0.20 thresholds were reused on the corrected high-resolution corpus. No GC001 tuning.

Positive max detections:
- Friend-A 0.430651
- Kaela 0.440163
- Hyakuto Kyoko 0.553992

But negatives also produced strong eyewear labels:
- AZKi 0.496910
- Fauna 0.481110
- Flare 0.409555
- Gawr Gura 0.479808
- Nanashi Mumei 0.503618
- Sorashina Sopia head accessory 0.425047

Decision: Grounding-DINO is useful for region proposals but not for semantic authority. Preserve SA7.9 as proposal evidence only.
