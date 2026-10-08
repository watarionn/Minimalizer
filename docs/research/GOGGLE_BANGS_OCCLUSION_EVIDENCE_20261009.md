# GC001 Goggle Rim Gaps and Bangs Occlusion Evidence (2026-10-09)

**Real original-source gap inspection completed; semantic occlusion not independently certified and bridge SVG remains NO-GO.**

Source SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. Starting from the 785 candidate pale source pixels in PR281, identified three connected regions of sizes 306, 300 and 179. For each pair, computed nearest observed pixel endpoints and sampled the original source colors on the direct shortest-gap segment. These red diagnostic segments are **not a proposed frame**.

- Left to middle: nearest 3.606px, 0 orange among 4 sampled source pixels, 4 pale.
- Left to right-upper: nearest 34.366px, 24 orange among 35 sampled, 7 pale.
- Middle to right-upper: nearest 10px, 8 orange among 11 sampled, 2 pale.

Thus orange source material **blocks naive straight white-frame connections** in two pairs, while a short pale-only gap does not itself prove an uninterrupted semantic frame. The visual comparison was inspected against the original character; none of these samples is sufficient to establish which foreground object owns all gap pixels or the hidden frame. No speculative bridges, face/skin plate, goggles fill, bangs repaint or production changes.

Code `tools/research/goggle_bangs_occlusion_evidence.py`, regression `tests/test_goggle_bangs_occlusion_evidence.py`. Initial synthetic test used two 9px islands below the program's 10px minimum component cutoff, so 1 test failed; corrected fixtures to 16px, reran with explicit detached commit `3743155904b40afc906566cbc6bd0d1e7d0ced14`: **71 tests PASS**.

Artifacts saved under `chatGPT及びCodex用/Minimalizer/GoggleBangsOcclusionEvidence_20261009`, Drive folder `1l-QxD6gR1TKE0T-LmL_Nnt324V0mxE8z`: source comparison `rim_gaps_source_review.png` and machine-readable `manifest.json`.

Next: independent source-verified semantic owner mapping (goggles rim, colored lens, front bangs) at the two orange-bearing gaps; do not repeatedly grow white masks or join endpoints by shortest path. Whole-character Golden HOLD, Local/Public unchanged.
