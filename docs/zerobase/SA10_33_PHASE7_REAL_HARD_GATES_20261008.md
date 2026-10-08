# SA10.33 Phase 7: Real full-scene authority and multi-case hard gates

Date: 2026-10-08 (JST)
Branch: `research/sa1032-svg-contour-proposals` · PR #223 (draft, unmerged)

## Final Phase 7 assessment

**Phase 7 evaluation IMPLEMENTED AND COMPLETED; quality NO-GO, promotion forbidden.**

The independent-source evidence coverage gate **PASS** (two distinct real-source SHA256s, both fully reproducible). The full-scene structural quality gate **FAIL for both images**. Human visual approval remains pending, and there is no deployment, raster patch, scene mutation, geometry promotion, or PR merge.

The quality gate's failure is a measured result, not a failure to execute the tests.

## Critical correction to Phase 6

SA10.32 Phase 6 had a custom `fillPoly`-by-depth contour replay. It did **not** match the canonical production `rasterize_primitive_candidate` implementation, which draws all rings with an even-odd `cv2.drawContours(..., FILLED)` pass. It also did not distinguish **selected preview mask** from **serialized polygon export** when `source_mask_replay=True`. Phase 6's previous per-part metrics therefore do **not** represent either authoritative output.

Phase 7 now measures **three separate evidence layers**:
1. Phase04 source-owned binary part mask.
2. Actual selected Phase12 `primitive_masks`, recomputed from saved Phase11 with the unchanged `StyleSimplificationPolicy` (`source_mask_replay` may use the original mask, rather than polygon raster).
3. The selected primitive's **serialized contour rings** rasterized via the actual production polygon renderer.

The full silhouette is the visible union of the selected masks **excluding `structural_support_only`**; including invisible support creates false metrics.

## Reproduction and provenance checks

Both cases passed:
- Source SHA256 matches Phase04, Phase11 and Phase12 manifests.
- Same Phase12 configuration SHA256, selected `aggressive` profile and **11 primitive records**.
- Selected in-memory records exactly match serialized primitive records.
- Preview stored SHA256 and scene stored SHA256 are valid.
- Reconstructed production render, including the deterministic face color guard, is **pixel-for-pixel identical to the saved preview** (0 changed pixels).
- Face guard changed no pixels outside authorized face mask.
- All required owners are explicit and traceable; unbound regions remain unbound.

GC001 is independently checked against **historical SA10.30 full-scene baseline**: source/candidate mask areas, component/hole topology and silhouette IoU match that stored baseline exactly.

Raden uses separate **archived Phase04/11 diagnostics and a separately SHA-verified corpus source image**. Its Phase12 output was generated in a temporary isolated test directory for this evaluation; it is not claimed to be an earlier production deployment.

**Archive limitation:** The standalone Phase12 CLI wrote complete Stage12 artifacts but then returned a nonzero exit at the all-phases contract bridge because the lightweight archived fixture did not contain a Phase03 stage manifest. The independent Phase7 observer verified the Stage04/11/12 SHA contracts, serialized primitives and preview bytes/pixels, not an end-to-end Phase03-to-12 archive replay. This remains a NO-GO research case, not a production PASS.

## Source vs actual render, per-owner

| Source case | Face IoU | Hair IoU | Left arm IoU | Right arm IoU | Missing tiny source regions |
|---|---:|---:|---:|---:|---|
| GC001 | 1.000000 | 0.998418 | 0.993370 | 1.000000 | Hair 23 px, left arm 18 px |
| Juufuutei-Raden | 1.000000 | 0.999846 | 1.000000 | 1.000000 | Hair 3 px |

At the canonical 8-pixel material component cutoff, **normalized part masks match exactly** between source and actual preview for these four owners. **This is observer evidence only.** It cannot erase or override loss of any raw source island or a raw topology hard failure.

In GC001, the source hair mask has 18 components and the actual render has 4; the left arm source has 10 and the render has 3. The missing islands total 23 and 18 pixels respectively. Raden hair has 8 vs 5 components, with 3 source pixels missing.

### Serialized vector vs actual preview raster

Rasterizing the selected polygon rings with the official renderer differs from the actual selected mask on **all four watched parts in both images**.

| Case | Face differing px | Hair differing px | Left-arm differing px | Right-arm differing px |
|---|---:|---:|---:|---:|
| GC001 | 12 | 204 | 26 | 18 |
| Juufuutei-Raden | 15 | 134 | 29 | 18 |

Thus even a visually intact preview is **not proof** that exporting the stored polygon will retain identical region geometry and holes. No prospective SVG should be promoted until an exact geometry-to-render authority check has passed.

## Full-scene anatomy and z-order results

| Case | Source silhouette topology (components, holes) | Render topology | IoU | Missing/extra source-union pixels | Gate |
|---|---|---|---:|---|---|
| GC001 | (1,9) | (2,21) | 0.99656700694 | Missing 178 / extra 11 | **FAIL: source_topology_changed** |
| Juufuutei-Raden | (1,3) | (1,8) | 0.99956805944 | Missing 30 / extra 0 | **FAIL: source_topology_changed** |

Both arm masks are **fully visible in the selected mask z-order, prior to the face color guard**. In these two test cases, overlap-based arm disappearance is not the culprit. This does not establish quality for other test images or a separate local worker pipeline.

The face color guard is a deterministic source-color substitution applied after compositing, never a license to draw standalone eyes or mouth.

## Code, tests, and decisions

- `minimalizer_zerobase/reviewed_sa10/phase7_geometry_authority.py`: raw/canonical (diagnostic-only) mask evidence, lost-component ledger, render/export drift, pre-face-guard visibility.
- `tools/run_sa1033_gc001_full_gate.py`: recompute exact Phase12 result, verify all source/config/serialization/preview provenance, run the real global SA10.18 gate. Despite the historical filename, accepts other real cases via CLI.
- `tools/run_sa1033_crosscase_gate.py`: require >=2 **distinct source hashes**, not two names for the same file; aggregate real-image quality failures without authorizing promotion.
- `tests/zerobase/test_sa1033_phase7_geometry_authority.py`, `test_sa1033_crosscase_gate.py`: synthetic regression guards.
- Existing Phase12, SA10.18 topology, material topology, SA10.11 structural-repair and SA10.33 tests: **48 passed** on authorized isolated checkout.
- GitHub Actions focused research regression: success; run status in PR #223.

Machine-readable evidence:
- [GC001 real full-scene authority](evidence/sa1033_gc001_phase7_full_gate_20261008.json)
- [Raden real full-scene authority](evidence/sa1033_raden_phase7_full_gate_20261008.json)
- [Two-case gate](evidence/sa1033_crosscase_gate_20261008.json)

## Final decision / Phase 8 gate

- **Phase 7 data collection, diagnosis and reproducibility: DONE.**
- **Structural full-scene gate: FAIL** in both real images.
- **SVG export/render agreement gate: FAIL** in both real images.
- **Human visual gate: PENDING.**
- **Production promotion/merge: NO-GO.** Keep draft PR #223 unmerged.

Next Phase 8 should focus on a **geometry-to-preview authority fix** and **source-derived tiny-island preservation**, without changing owner/color/primitive budgets, inventing geometry, adding eyes/mouth, using generative AI, suppressing failure metrics or weakening raw topology gates. Require new real images and explicit human visual approval **after all hard checks pass**. See [handoff](../handoffs/HND-20261008-SA1033-PHASE7-NOGO-NEXT.md).
