# Minimalizer 2.0 Calibration 05 Phase J

## Purpose

Phase J profiles V2 performance and prepares the performance-budget contract needed before any legacy-default migration.
It is observational only: it must not change canonical pixels, algorithm digest, facet decisions, legacy defaults, browser UI, or deployment behavior.

Canonical profiler schema: `minimalizer-v2-performance-v1`.
Canonical profile artifact: `MINIMALIZER_2_CALIBRATION_05_PHASE_J_PERFORMANCE.json`.

Representative corpus:
- Kikirara-Vivi
- Otonose-Kanade
- Todoroki-Hajime
- Raora-Panthera
- Hakos-Baelz

Each case is measured twice with the canonical Minimal preset. Profiling repeats must produce the same `algorithm_digest`.

## Migration baseline

Phase I measured legacy Standard level 4 at `0.740 s` mean and V2 Minimal at `5.954 s` mean over the same five representative cases.
That was approximately `8.28x` slower for V2.
Phase J does not treat one workstation measurement as a production SLA; it uses it to locate dominant costs and prepare a reproducible budget method.

## Canonical Phase J profile

Five-case / two-repeat mean wall time: `5.885 s`.

Dominant mean phase costs:
- `oversegmentation`: `1.734 s` / `29.46%`
- `region_merge`: `1.034 s` / `17.57%`
- `minimal.contour`: `0.761 s` / `12.93%`
- `preprocessing`: `0.688 s` / `11.69%`
- `minimal.palette`: `0.567 s` / `9.64%`
- `minimal.facet_gate`: `0.528 s` / `8.97%`

These six phases account for roughly `90%` of V2 wall time on the representative corpus.
The remaining major measured phases are primitive fitting (`3.96%`) and initial RAG construction (`3.25%`).

The profiler is implemented in `minimalize_engine/v2/performance.py` and exposed through `tools/profile_v2_performance.py`.
It records wall time, per-phase timings, and algorithm digest for every repeat.
A digest mismatch across repeats is treated as an error rather than a performance result.

## Function-level hotspot confirmation

A cProfile run on Raora-Panthera confirmed the phase-level result.
The dominant cumulative costs were:
- NumPy SLICO (`_run_numpy_slico`)
- hierarchical Region Merge and repeated `evaluate_merge`
- shared-boundary contour simplification and validation
- L0 gradient smoothing
- palette CIEDE2000 evaluation
- facet-gate macro-facet measurements

The Raora run executed about `7.46 million` Python-level function calls under cProfile.
Facet gate called macro-facet measurement repeatedly for viable trial overlays; this is a meaningful optimization target, but its acceptance semantics must not change.

## Optimization safety order

Phase J does not implement performance shortcuts.
The first candidates for later work should be exact-result optimizations only:
1. cache immutable shape-dependent numeric scaffolding, such as L0 spectral denominators;
2. remove repeated observational computation where the exact same input/configuration is measured more than once;
3. reduce Python overhead in Region Merge without changing candidate ordering or floating-point formulas;
4. optimize contour validation while preserving every existing topology/IoU/directional/intersection guard;
5. optimize palette distance evaluation only if CIEDE2000 results and merge decisions remain bit-for-bit equivalent.

Changing SLIC targets, retry thresholds, Region Merge costs, contour tolerances, palette thresholds, or facet acceptance criteria is not a performance optimization for this phase because those changes can alter the image.

## Performance-budget preparation

No hard production latency threshold is invented in Phase J because the target hosting hardware and acceptable interactive SLA have not been fixed.
The future budget must be evaluated with both a latency target and non-negotiable output-equivalence gates.

Required acceptance gates for any performance patch:
- canonical 18-case hard invariant failures remain `0 / 18`;
- canonical rendered pixels / PNG contract remain unchanged unless a separately approved visual calibration changes them;
- `algorithm_digest` remains unchanged for the canonical corpus;
- facet decisions remain unchanged;
- representative five-case phase profile is rerun with the same preset and repeat count;
- full V2 and repository regressions pass apart from the known missing-asset failures.

The migration-readiness `performance_budget` item therefore remains blocked after Phase J.
Phase J has converted it from an unknown problem into a measured problem with reproducible instrumentation and ranked hotspots.

## Regression closure

Phase J final local validation:
- focused performance tests: `10 passed`;
- V2 suite: `130 passed`;
- full repository: `466 passed, 2 failed, 1 warning`;
- the two failures remain only the known missing `tests/assets/false_face_phase85.png` asset.

No image-producing pipeline stage or visual threshold changed in Phase J. The profiler-vs-normal-run test proves identical `algorithm_digest`, so the Phase H canonical `0 / 18` hard-invariant visual baseline remains the active image baseline without regenerating the corpus solely for timing instrumentation.

## Next engineering step

Proceed to Phase K: Exact-Result Performance Optimization.
Start with the smallest output-invariant optimization that addresses a measured hotspot, then prove digest/pixel equivalence before attempting the next hotspot.
Do not switch the legacy default, change visual thresholds, deploy, or run paid GitHub Actions as part of that step.
