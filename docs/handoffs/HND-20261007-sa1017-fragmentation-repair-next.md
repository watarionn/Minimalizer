# Handoff — SA10.17 Fragmentation Root-Cause & Generic Repair — 2026-10-07

Status: SA10.16 COMPLETE / SA10.17 NEXT

Goal:
Repair the repeated fragmentation failure cluster at the production/simplification level without relaxing the Phase14 fragmentation gate.

## Current canonical state

Five real PASS transactions:
- AZKi
- Hyakuto-Kyoko
- Juufuutei-Raden_stylecal_source
- Nekomata-Okayu
- Hoshimachi-Suisei

SA10.16 fresh failure taxonomy:
`benchmarks/regression/sa10/SA10_16_failure_taxonomy.json`

Repeated fragmentation failures:
- Fuwawa-Abyssgard: 0.26666666666666666
- La-Darknesss: 0.4339622641509434
- Kaela-Kovalskia: 0.29545454545454547

Current Phase14 maximum:
`0.2`

Do not change that threshold in SA10.17.

## Important separation

Fuwawa also has an earlier human visual break at Phase7 mass reconstruction.

Do not assume its fragmentation failure is the root cause.

Use:
- La-Darknesss and Kaela-Kovalskia as the clean fragmentation cluster;
- Fuwawa as a separate mass-reconstruction / visual-break case that may share downstream symptoms.

## SA10.17 requirements

1. Inspect exact tiny-component ownership for La+ and Kaela.
2. Determine whether fragments originate in:
   - Phase7 mass splitting;
   - Phase8 protection/keep policy;
   - Phase9 palette separation;
   - Phase10 primitive emission;
   - Phase11 composition;
   - Phase12 micro-component preservation.
3. Do not modify the Phase14 fragmentation threshold.
4. Do not add case-name branches, coordinates, colors, or masks.
5. Any repair must be generic and backed by synthetic regression tests.
6. Preserve Feature Survival, face, anatomy, topology, source authority, and provenance hard gates.
7. Re-run La+ and Kaela after the generic repair.
8. Re-run the five existing PASS transactions to prove no regression.
9. Keep Fuwawa's Phase7 visual failure separate unless the same generic repair demonstrably addresses it.
10. Use at least one untouched fresh holdout after the repair before considering promotion.
11. No aggregate score.
12. No calibration authority.
13. Preserve code/docs in GitHub and generated evidence under canonical Google Drive `chatGPT及びCodex用`.

Completion target:
- root cause localized;
- generic repair implemented or explicit HOLD if evidence rejects repair;
- La+/Kaela before/after evidence preserved;
- existing five PASS transactions remain PASS;
- untouched fresh holdout evaluated;
- Phase14 threshold unchanged.
