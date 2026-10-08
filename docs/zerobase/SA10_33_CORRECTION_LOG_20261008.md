# SA10.33 Correction and prevention record (2026-10-08)

**Incident:** Earlier SA10.32 Phase6 reported GC001 owner geometry metrics from a custom mask replay, mistakenly presenting them as close to the authoritative vector/preview result.

**Cause:** The research-only diagnostic used sequential `cv2.fillPoly` fill/erase by contour depth instead of the actual `minimalizer_zerobase.composition.semantic.rasterize_primitive_candidate` routine, whose polygon rings are composed in a single `cv2.drawContours` even-odd filled pass. It also conflated the Phase12 `source_mask_replay` mask (actual rendered pixels) and the serialized `parameters.rings` (export geometry), which can differ.

**Impact:** Historical Phase6 per-owner areas, hole count and IoU are noncanonical. That analysis correctly held promotion but could have sent subsequent investigation toward the wrong cause. Code updates in later phases could mistakenly use its metrics as a gold baseline.

**Correction executed:** Read unchanged Stage12 source, reproduce selected scene and saved RGB preview exactly; compare source mask, live `selected.primitive_masks`, and official polygon rasterizer independently. Corrected GC001 evidence and second Raden benchmark, independent two-case gate and tests are saved in Phase7 report. Phase6 report is prominently marked SUPERSEDED for numeric replay claims.

**Prevent recurrence:**
1. Only use the same production rasterizer for export geometry benchmarks. Require golden synthetic odd/even ring tests and parity/owner coverage checks.
2. Distinguish source mask vs selected rendered mask vs re-rasterized serialized vector in every report.
3. Confirm selected 11 primitives (not Phase11 initial 150) and compare actual preview pixel-for-pixel.
4. Exclude support-only primitives from painted silhouette but keep them in graph/support analysis.
5. Use two distinct real source hashes, raw topology hard gates, owner/material invariants, strict export/render equality and a human visual gate.
6. Leave this research PR draft and unmerged when quality is FAIL, even if code CI is green.

**Disposition:** Identified, corrected and reproducibly evidenced; **full-scene quality not solved**, production promotion blocked. Source-of-truth report `docs/zerobase/SA10_33_PHASE7_REAL_HARD_GATES_20261008.md`.
