# SA10.58: Stage8 signed source-ring budget versus compact deployed SVG, release-gate reconciliation

2026-10-09. **Two signed-source reconstruction and policy audit PASS; historical Stage8 source-ring equivalence/budget gate HOLD; face-and-arm protected conversion HOLD; full-character Golden HOLD; production UNCHANGED.**

## 1. Purpose, source authority, and definition of the problem

The original Stage8 `phase8_adaptive_source_contour_research.json` stores **11 source-owner ring groups** per character. It is a signed, immutable geometry **input**. Its vertex budget is not silently replaced by the independently passing **expanded deployed SVG** budget in SA10.57. `source_stage8_budget_pass` remains FALSE in the immutable history. The original character source images, source SVGs, masks and SA10.57 research SVGs are SHA-verified. The accepted target style continues to have **face microfeatures off**.

- **Raden:** signed original Stage8 rings **2,370**, historical cap **1,412** (over by **958**). Current SA10.57 research SVG uses **1,409 / 1,412 expanded vertices**. Original Stage9/37 colored overlay = **12 vertices**, reported separately (not smuggled into the Stage8 ring ledger).
- **GC001:** original Stage8 rings **3,604**, historical cap **1,887** (over by **1,717**). Current SA10.57 SVG **1,873 / 1,887**. Original Stage9/37 overlay = **55**, separately reported.

## 2. What was implemented

`tools/research/sa1058_stage8_budget_reconciliation.py` reconstructs actual original signed Stage8 source-owner masks from the 11 original ring sets. It tests finite original-coordinate-preserving `cv2.approxPolyDP` source contour simplifications at epsilons **0 / 0.4 / 0.5 / 0.75 / 1 / 1.25 / 1.5 / 2 / 2.5 / 3 / 4 / 6**. Ring depth and hole/fill flags are preserved; no new points are invented; no source file is mutated. Results record true source ring point occurrences, including hidden/support groups, and the separate unchanged painted Stage9/37 polygon ledger.

All candidate masks are rasterized from the derived rings. The frozen real source-owner topology and final visible ownership are compared pixel-for-pixel, including silhouette IoU and mismatches **inside signed face and arms**. A finite multiple-choice dynamic program seeks the **lowest measured original-visible-source error** under the *existing* Stage8 caps. A second independent search measures the **minimum achievable ring count among all tested per-owner choices that leave every original source face/arm pixel unchanged**. A third measure counts minimum **source-mask-exact** rings among all candidates in this finite search family. These minima are *within the enumerated epsilon family only*. They are **not proof that no other algorithm could succeed**.

The current SA10.57 faceless SVG is also rendered in **actual Chromium 144** with its visible paint replaced by black and neutral background by white, preserving masks and paint order. It is independently compared against the original Stage8 source-visible silhouette, rather than inferring accuracy from a low RGB MAE. The genuine SA10.57 colored screenshot SHA is verified before the matte measurement. All source-containing and derived geometries stay in private Drive.

## 3. Verified measurements

| Measurement | Raden | GC001 |
|---|---:|---:|
| Original signed Stage8 ring vertices | 2,370 | 3,604 |
| Unchanged Stage8 cap | 1,412 | 1,887 |
| Historical original overrun | 958 | 1,717 |
| **Smallest protected-pixel-safe ring total among tested choices** | **1,726** | **2,981** |
| Smallest exact-source-ring-mask total among tested choices | 2,306 | 3,424 |
| Exploratory compressed Stage8 ring total | 1,412 | 1,887 |
| Changed topmost source-owner pixels in compressed proposal | **186** | **467** |
| Changed source arm-ownership pixels in compressed proposal | **11 (FAIL)** | **5 (FAIL)** |
| Compressed source-visible silhouette IoU | 0.99863301 | 0.99512275 |
| **SA10.57 rendered SVG silhouette IoU vs signed source masks** | **0.99284544** | **0.98440694** |
| Current compact deployed SVG vertices | 1,409 / 1,412 | 1,873 / 1,887 |
| Full-character Golden / production | **HOLD / unchanged** | **HOLD / unchanged** |

The Stage8 candidates reach the numeric cap by accepting source-shape differences. Even though their individual original *face and arm ring groups* are unchanged, approximated **other owner rings can overwrite arm ownership** after the source z-order is applied. That subtle distinction is directly tested: 11 / 5 arm-label changes. **Neither compressed Stage8 proposal may be promoted or substituted** for original signed masks or SA10.57 champions. This is more important than reporting a favorable IoU by itself.

SA10.57's SVG silhouette IoU is a diagnostic comparison to the **signed Stage8 source-derived masks**, **not proof of human silhouette quality** against the actual colorful source picture or correct garment semantics. The human review board still shows major geometric and costume simplifications. A source-RGB improvement or compact SVG limit PASS does not clear the artistic quality gate.

## 4. Validation and archive provenance

- **9/9 signed-input regression tests PASS.** Includes source/SVG tamper rejection, owner source-coordinate provenance, finite dynamic-program budget failure behavior, protected face-and-arm pixel candidate rejection, frozen source owner labels and true Chromium two-case replay.
- Two clean full evaluations yielded **8/8 SHA-identical** PNGs, original-scene board, derived private ring JSONs and metric report. ZIP stores the source, tests, documentation, manifest, private derived ring JSON and artwork; verify every ZIP member SHA. Chrome v144.0.7559.96 at 340×340 DPR1, no GPU/local worker/remote desktop.
- **Private source and prototype artifacts** must be saved in the approved Drive subfolder `chatGPT及びCodex用/Minimalizer/SA1058_Stage8SourceRingGate_20261009`. Only the coordinate-free numeric report, reproducible algorithm and tests belong on public GitHub. Do not upload private candidate ring coordinates or original-containing PNGs to public GitHub.

## 5. Policy decision / what remains

`SIGNED_SOURCE_AUTHORITY_PASS` / `STAGE8_RING_BUDGET_ORIGINAL_FAIL` / `COMPACT_DEPLOYED_SVG_BUDGET_PASS` / `SAFE_STAGE8_RECONSTRUCTION_NOT_DEMONSTRATED` / `CANDIDATES_REJECTED_ON_SIGNED_ARM_OWNERSHIP` / `TWO_CHARACTER_SOURCE_SHAPE_MISMATCH_MEASURED` / `FACELESS_DEFAULT_PASS` / `HUMAN_VISUAL_GOLDEN_HOLD` / `PRODUCTION_UNCHANGED`.

**This completes SA10.58 as a fail-closed engineering reconciliation and quantified blocker, *not* as a claim that the historical source-ring budget was solved.** The Stage8 source geometry cannot be rewritten retroactively. A future compatible solution must either (A) produce a new source-authorized owner geometry encoding that truly passes the old cap while maintaining face/arms/source ownership and acceptable silhouette, with independent browser/golden verification; or (B) submit a **separate, explicit versioned policy change** that distinguishes immutable Stage8 input-complexity evidence from the final deployed-SVG complexity limit, with the user's approval and a truthful migration/release audit. No blanket cap increase or automatic waiver is approved here.

**Next SA10.59**: prepare multi-image Golden review and visual source-identity criteria, **without claiming production readiness** while the Stage8 release decision and artistic quality remain HOLD. Production integration and deployment are not authorized until gates are explicitly cleared.

## 6. Reproduce with private signed materials

```bash
python tools/research/sa1058_stage8_budget_reconciliation.py \
 --raden /private/Raden --gc001 /private/GC001 \
 --raden-svg /private/SA1057/raden_structure_guarded.svg \
 --gc001-svg /private/SA1057/gc001_structure_guarded.svg \
 --out /private/SA1058
SA1058_RADEN_ROOT=/private/Raden SA1058_GC001_ROOT=/private/GC001 \
 SA1058_RADEN_BASE=/private/SA1057/raden_structure_guarded.svg \
 SA1058_GC001_BASE=/private/SA1057/gc001_structure_guarded.svg \
 pytest -q tests/zerobase/test_sa1058_stage8_budget_reconciliation.py
```
