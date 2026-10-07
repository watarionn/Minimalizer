# SA10.15 Fresh-Case Admission & Transaction Coverage Expansion — 2026-10-07

Status: COMPLETE / THIRD REAL TRANSACTION ADMITTED / GENERIC BLOCKERS REPAIRED / NO CASE-SPECIFIC PRODUCTION LOGIC

## Goal

Admit a fresh non-GC001 case that was not used to design SA10.11-14 repairs through the existing production and SA10.14 regression-transaction protocols.

No threshold calibration was allowed.

## Fresh case

Case:
`AZKi`

Source:
`AZKi_list_thumb.png`

Source SHA-256:
`571aacc7c08e7625c2390897f691d9d734c8317c0605c9a92b64d9469917230d`

Source Drive file ID:
`1OJ6HPgAqKYX_XqfwXgvp04rF0UAnuvp5`

The source came from the uploaded `HoloMenImages.zip` collection and had not been used to design SA10.11-14 repairs.

The source was preserved to the canonical Google Drive hierarchy before local execution. Local storage was not made authoritative.

## Fresh-admission blockers exposed

The first attempts intentionally used the existing pipeline without AZKi-specific production logic.

The fresh case exposed generic blockers:

1. Runtime bootstrap selected `C:\Python314`, which did not contain optional `rtmlib`.
   - Existing `C:\Work\Projects\Minimalizer\.venv` already contained `rtmlib`.
   - No package installation was needed.

2. Phase4 peripheral accessory detection assumed one OpenCV `HoughLinesP` singleton-axis shape.
   - The observed runtime returned equivalent coordinate data with a different singleton-axis layout.
   - `lines[:, 0]` yielded scalar `numpy.int32` values.
   - Fixed generically through deterministic `N x 4` normalization.
   - Malformed element counts fail closed.

3. Provenance bridge used `cv2.imread` on a Japanese Windows Drive path.
   - Replaced with Unicode-safe `numpy.fromfile + cv2.imdecode`.

4. Phase8-12 canonical source reads had additional direct `cv2.imread` paths.
   - Added shared `minimalizer_zerobase/image_io.py`.
   - Phase8, Phase9, Phase10, Phase11 source reads now use the shared reader.
   - Phase9 and Phase12 runners also use the shared reader.
   - Phase12 artifact writing already had equivalent Unicode-safe behavior.

5. Phase12 runner briefly imported the new project module before repo-root `sys.path` bootstrap.
   - Import order was corrected generically.

Admission history:
`benchmarks/regression/sa10/evidence/AZKi.sa10.15-admission-history.json`

No structural or face hard-evidence failure was observed after the generic blockers were repaired.

## No case-specific production logic

No AZKi-specific:
- coordinates;
- colors;
- masks;
- thresholds;
- production branches;
- semantic roles;
- exception paths

were added.

Regression tests explicitly verify that `AZKi` does not appear in the changed production modules.

## Baseline production run

The repaired generic pipeline completed Phase3-12 end-to-end.

Baseline candidate SHA-256:
`59248bc5da37acf77bba6fe47f88728bc245f4f7153cbc72a6e68a72d13c768c`

Selected profile:
`aggressive`

Selected primitive count:
`23`

Phase12 silhouette IoU:
`0.986138`

The baseline candidate was reviewed before adoption.

Phase13:
- PASS
- provenance gate PASS
- no first bad stage

Phase14:
- machine PASS
- human visual PASS
- determinism PASS
- identity feature retention: 0.953662
- silhouette preservation: 0.986138
- part-layout mean: 0.979727787606085
- part-layout minimum: 0.9284177367893154
- major-color-mass consistency: 0.7822552870959043

Baseline Drive file ID:
`10uCMHPD4O05YHrE_rGUSnR5t6SeEV_J0`

Baseline Phase14 Drive file ID:
`1gkr4zatMUCsdGJv3GqDaOsHQO7vpbujx`

## Legitimate baseline adoption

Canonical adoption record:
`benchmarks/regression/sa10/baselines/AZKi.sa10.15-adoption.json`

Adoption transaction:
`sa10.15-adopt-azki-20261007-v1`

The adoption record was committed before the evaluation production run.

Boundary:
- immutable record: true
- evaluation baseline allowed: true
- production inference allowed: false
- candidate self-reference forbidden: true

## Fresh evaluation run

After the adoption record existed, Phase3-12 was regenerated into a separate output root.

Fresh candidate SHA-256:
`59248bc5da37acf77bba6fe47f88728bc245f4f7153cbc72a6e68a72d13c768c`

The candidate is byte-identical to the adopted baseline, which is allowed because:
- the adoption transaction already existed;
- evaluation transaction is separate;
- same_transaction = false;
- production inference from the baseline is forbidden.

Evaluation transaction:
`sa10.15-regression-azki-20261007-v1`

## Fresh hard evidence

Feature Survival:
- AVAILABLE
- PASS
- required signatures: 10
- missing signatures: 0

Forbidden Face Detail:
- AVAILABLE
- PASS
- ratio: 0.0

Anatomy:
- AVAILABLE / PASS

Topology:
- AVAILABLE / PASS

Source Authority:
- AVAILABLE / PASS

Phase14 machine:
- AVAILABLE / PASS

Phase14 human visual:
- AVAILABLE / PASS

Determinism:
- AVAILABLE / PASS

Fresh Phase14 determinism SHA-256:
`b587e84b73ff95ca095412906d9897e616959e7a917d836cbb854af2e7e35141`

## FaceRasterGuard

AZKi Phase12:
- face pixels: 5,568
- changed face pixels: 5,568
- changed outside face pixels: 0
- fill RGB: [251, 219, 215]
- generated/inpainted pixels: 0

The guard remains source-only and Phase4-face-mask bounded.

## DINO diagnostic

Exact-output DINO semantic retention:
`0.8350633040526145`

Spatial research score:
`0.6313874096893057`

DINO remains:
- non-authoritative;
- unable to override hard failures;
- unable to change production output.

## Actual-emission diagnostic

AZKi actual-emission evidence:
- component representation: 0.75
- primitive support: 1.0
- emission realization: 0.75

This remains diagnostic-only.

It is not silently mapped to:
- SA10.5 Component Survival;
- SA10.5 Primitive Economy.

Those diagnostics remain UNAVAILABLE for AZKi because no explicit SA10.5 evidence contract was produced for this fresh admission.

SA9 Teacher evidence also remains UNAVAILABLE because no reviewed AZKi teacher annotation exists.

## SA10.14-style transaction

Canonical transaction:
`benchmarks/regression/sa10/transactions/AZKi.sa10.15-transaction.json`

Transaction result:
`PASS`

All evidence links:
`PASS`

All eight hard gates:
`PASS`

Canonical payload SHA-256:
`6de7831f3ddc8e33e0031ca91c271b6656124c677fe5ee3800d708021537a34c`

A second transaction generation from the same real source/candidate/evidence reproduced the same canonical payload SHA exactly.

## Three-case transaction set

Canonical:
`benchmarks/regression/sa10/SA10_15_transaction_set.json`

Real transaction cases:
- AZKi
- Hyakuto-Kyoko
- Juufuutei-Raden_stylecal_source

Transaction count:
`3`

All three transactions:
`PASS`

Boundary:
- aggregate quality score: false
- hard failures individually visible: true
- diagnostics cannot override hard failures
- calibrated thresholds: false
- case-specific production logic: false

## Verification

Focused regression chain:
- 73/73 PASS

Covered:
- Unicode-safe image I/O;
- Phase4 semantic decomposition;
- Hough-line shape normalization;
- provenance bridge;
- Phase12 simplification;
- SA10.14 synthetic negative transaction contract;
- SA10.14 real transactions;
- SA10.15 AZKi admission;
- immutable adoption boundary;
- three-case canonical payload hashes;
- absence of AZKi-specific production branches.

Transaction reproduction:
- canonical: `6de7831f3ddc8e33e0031ca91c271b6656124c677fe5ee3800d708021537a34c`
- reproduced: `6de7831f3ddc8e33e0031ca91c271b6656124c677fe5ee3800d708021537a34c`
- match: true

## Boundaries preserved

- no generative img2img;
- no Generative Fill;
- no inpainting;
- no hidden completion;
- no Golden production inference;
- no browser-v12 production inference;
- no adopted-baseline production inference;
- no aggregate quality score;
- no threshold calibration;
- no hard-fail rescue through diagnostics;
- no case-specific AZKi production logic.

## Decision

SA10.15 is complete.

A third real, previously unused non-GC001 case passed the same hard-gate transaction protocol after only generic runtime / I/O robustness repairs.

Three passing cases are still too few to justify threshold calibration. SA10.16 should expand fresh-case coverage and build a failure taxonomy before any calibration proposal.


## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_15_20261007_FRESH_CASE_AZKI`

Drive folder ID:
`1gScyuEbvg6ewB2SF8JaxaiIExLlabx-x`

The source was uploaded through the Drive API before local execution.

Drive API read-back verified all 18 preserved artifacts:
- source image;
- reviewed baseline PNG;
- baseline Phase14 JSON;
- baseline summary;
- fresh evaluation PNG;
- fresh Phase12 metrics;
- fresh Phase14 JSON;
- fresh evaluation summary;
- adopted-baseline record;
- visual hard-gate report;
- structural/source-authority hard-evidence report;
- exact-output DINO report;
- FaceRasterGuard evidence;
- admission-history report;
- SA10.15 case fixture;
- AZKi regression transaction;
- three-case transaction set;
- SA10.15 closeout document.
