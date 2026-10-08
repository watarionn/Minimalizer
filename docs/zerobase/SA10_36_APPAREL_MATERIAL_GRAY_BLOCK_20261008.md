# SA10.36: GC001 gray clothing trapezoid → source-grounded apparel materials

Date: 2026-10-08 JST · Branch `research/sa1032-svg-contour-proposals` · Draft PR #223.

## Outcome

**Requested gray trapezoid visual defect: corrected in a research-only reproducible preview.**
**Production acceptance: HOLD / NO-GO**, because inherited exterior vector vertex budgets, true browser SVG clipping parity, and human review have not passed. No source input, Stage04, Phase8/9 baseline, production worker, deployed BrowserFallback or `main` tree was modified.

The user found that an enormous gray trapezoid swallowed GC001's clothes. Investigation of the **actual topmost pixel ownership** in the Phase8 11-primitive scene traced it to `lower_body`:
- Visible existing owner pixels: **12,640**.
- Existing flat parent palette: RGB **(104,91,86)**.
- The ORIGINAL RGB image inside this owner instead contains **3,140 clean light-shirt pixels**, **4,941 dark-uniform pixels**, **1,550 bright green tie pixels**. Hence the gray polygon is not itself a mis-segmented outer silhouette; it merges materially different pieces of the garment.

## Implemented semantic apparel material grammar

The source-provenanced rule automatically detects a strong **two dark panels + two white panels + one central green tie** pattern. Inside the existing exact lower-body owner silhouette it fits five **closed low-vertex polygons**:

| New material subpaths | Count | Source |
|---|---:|---|
| Dark uniform/navy | 2 | Original RGB dark clusters |
| White shirt/collar | 2 | Original bright near-neutral clusters |
| Central green necktie | 1 | Original source-green connected region |
| **Total** | **5 / 36 vertices** | Not generated or inferred from new content |

Materials are applied in order **dark → white → narrow tie**, ensuring the necktie is not smothered by the shirt. Each color is an RGB pixel genuinely observed in its own source material class; no source bitmap/textures are pasted. Source class precision thresholds are >=0.60 dark, >=0.74 white and >=0.82 green. The tie additionally cannot exceed **110%** of source-green class area or extend outside source-green x bounds by more than 2px. Source owner clipping, face/arm protection and hard error gates stop any unauthorized painting.

The material pattern must have substantial dark, light, and green source evidence; **nonmatching outfits are left unchanged.** This avoids adding a green necktie or a white shirt to arbitrary other characters.

## Measured real-image verification

| Criterion | GC001 | Juufuutei-Raden (control) |
|---|---:|---:|
| Source-image/Stage04/Phase8/Phase9 SHA lineage | PASS | PASS |
| Existing outer primitive geometry / topology | UNCHANGED / PASS | UNCHANGED / PASS |
| Existing face / left and right arm pixel colors | UNCHANGED | UNCHANGED |
| Existing gray-block largest connected region | **12,632 → 476 px** | 950 → 950 px |
| Largest gray connected region reduction | **96.23%** | 0%, no pattern |
| Lower-body source Lab color MSE reduction | **55.7641%** | 0%, no change |
| Green tie source area / drawn panel | **1,550 / 1,615 px (+4.2%)** | No tie; none drawn |
| Additional colored polygons | **5** | **0** |
| Extra geometry points | **36** | 0 |
| Full painted geometric elements, including prior Phase9 planes | **19** (11 outer +3 old +5 new) | 12 (11+1) |
| Off-owner/face/arms changed pixels | **0** | **0** |
| Distinct-source reproducible research gate | PASS | PASS |

The new GC001 preview shows **two white shirt sections, two dark navy garment panels, and a thin green center tie**, instead of a single gray trapezoid. The remaining preexisting silhouette and facial simplification are untouched. Existing hair/torso overlays from SA10.35 remain research-level, and further artistic review can still reject their placements.

**Determinism:** Both real cases were run independently twice. Their metric JSON, additional polygon JSON, preview PNG and 3-way comparison PNG SHA256 hashes all match byte-for-byte (4/4 artifacts per case). The Raden candidate image also hashes identically to its prior baseline.

## Code, testing and artifacts

- `minimalizer_zerobase/reviewed_sa10/semantic_apparel_material_planes.py`: deterministic source RGB material classification, exactly five anchored existing-owner geometric color panels, tie size gate and protected renderer.
- `tools/run_sa1036_color_owner_diagnosis.py`: observed semantic owner anatomy/large-block diagnosis.
- `tools/run_sa1036_material_grammar.py`: SHA contract verification, exact Phase9 RGB baseline reproduction, layer-aware material application, gray-block and color MSE metrics, screenshots.
- `tools/run_sa1036_apparel_crosscase.py`: requires one verified correction and one independently hashed nonmatching image left unchanged.
- `tests/zerobase/test_sa1036_semantic_apparel_material_planes.py` and `test_sa1036_apparel_crosscase.py`: **12 new tests**. Extended integrated regression **81 PASS**.
- The research GitHub Actions `.github/workflows/sa1032-svg-research.yml` must report SUCCESS before claiming CI passed.

Machine-readable:
- [GC001 material correction](evidence/sa1036_gc001_apparel_material_20261008.json)
- [Raden no-op control](evidence/sa1036_raden_apparel_material_20261008.json)
- [Two-source material research gate](evidence/sa1036_crosscase_apparel_gate_20261008.json)

Visual comparisons + research polygon JSON, user source and prior Stage9 candidate stored under
[Google Drive `chatGPT及びCodex用/Minimalizer/SA1036_Apparel_Material_20261008`](https://drive.google.com/drive/folders/1_57W-ftJqdPFAse8ZSVwBXVuEJaPfaw3).
The GC001 **`source_before_material_comparison.png`** shows the original / gray version / new geometric material version. Raden has its own side-by-side no-op.

## Release blockers kept intact

- **Inherited Phase8 outer ring budget still FAIL**: GC001 **3,604 >1,887**, Raden **2,370 >1,412**. These five *additional* polygons do not fix that, and their 36 points must be counted separately.
- **Browser SVG clip-path parity still UNVERIFIED**. A CV2 polygon clipped by a source-owned raster is not automatically a browser-valid SVG path. Need deterministic SVG polygon + actual browser render comparison; singleton islands remain unresolved.
- **Human quality approval pending**. User still must assess the bright white panels, green tie geometry, and whether the upper torso/face regions should be further simplified.
- The new material grammar is *pattern-specific*. Other garment combinations should be recognized only from actual source evidence, never forced onto all characters.

**Decision:** SA10.36 research implementation + two-image validation + preservation COMPLETED. Keep PR #223 **DRAFT/UNMERGED**, no production promotion. Continue research on source-meaningful clean internal planes and browser/vertex budget gates.
