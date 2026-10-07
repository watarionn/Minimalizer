# Handoff — SA10.16 Multi-Fresh-Case Expansion & Failure Taxonomy — 2026-10-07

Status: SA10.15 COMPLETE / SA10.16 NEXT

Goal:
Expand the SA10.14/15 transaction protocol from three real cases to a broader fresh-case cohort and classify failures before any threshold calibration.

## Current real transaction coverage

Passing:
- AZKi
- Hyakuto-Kyoko
- Juufuutei-Raden_stylecal_source

AZKi was not used to design SA10.11-14 repairs.

## SA10.15 generic repairs now available

- HoughLinesP output-shape normalization;
- shared Unicode-safe OpenCV source reader;
- Unicode-safe provenance bridge;
- Phase8-12 canonical source read path cleanup;
- Phase9 / Phase12 runner bootstrap correction.

These are generic and contain no AZKi-specific production branch.

## SA10.16 requirements

1. Select at least two additional fresh cases from the preserved HoloMenImages source collection.
2. Prefer different visual structures, for example:
   - bright/light hair;
   - animal-ear or head-accessory silhouette;
   - stronger pose asymmetry;
   - different clothing complexity.
3. Do not add per-case coordinates, colors, masks, or thresholds.
4. Run each fresh case through the existing production pipeline before making any new repair.
5. Preserve every initial failure before repairing it.
6. Any repair must be generic and independently regression-tested.
7. Use legitimate reviewed-baseline adoption before evaluation transactions.
8. Produce SA10.14-style transactions for each admitted case.
9. Grow the real transaction set to at least five cases.
10. Build a failure taxonomy separating:
    - runtime/environment blockers;
    - Unicode/path I/O;
    - structural decomposition;
    - topology/anatomy;
    - Feature Survival;
    - forbidden face detail;
    - provenance/source authority;
    - Phase14 visual/machine;
    - diagnostic-only gaps.
11. Keep Teacher evidence UNAVAILABLE unless reviewed annotations exist.
12. Keep actual-emission evidence separate from SA10.5 unless its explicit contract is satisfied.
13. No aggregate quality score.
14. No threshold calibration yet.
15. Preserve code/docs in GitHub and generated artifacts under the canonical Google Drive `chatGPT及びCodex用` hierarchy.

Completion target:
- >= 5 real transaction cases;
- initial fresh-case outcomes preserved;
- generic fixes only;
- failure taxonomy artifact produced;
- no calibration authority introduced.
