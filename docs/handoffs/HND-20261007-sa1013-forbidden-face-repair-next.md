# Handoff — SA10.13 Forbidden-Face Hard-Fail Repair — 2026-10-07

Status: SA10.12 COMPLETE / SA10.13 NEXT

Goal:
Repair the forbidden-face-detail hard failures exposed by legitimate SA10.12 adopted-baseline evaluation, without weakening the face hard gate.

## Current evidence

Hyakuto-Kyoko:
- Feature Survival: PASS, 17 required, 0 missing
- Forbidden Face Detail: FAIL
- forbidden-face ratio: 0.058444259567387684
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS
- Phase14: PASS

Juufuutei-Raden_stylecal_source:
- Feature Survival: PASS, 9 required, 0 missing
- Forbidden Face Detail: FAIL
- forbidden-face ratio: 0.012738853503184714
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS
- Phase14: PASS

## SA10.13 requirements

1. Trace forbidden face pixels to Phase10-12 primitive/source-guided face construction.
2. Do not change `max_forbidden_face_ratio=0.0` to make the cases pass.
3. Do not remove required source-supported identity features outside the forbidden face-detail contract.
4. Repair generically from existing face-neutralization semantics.
5. Keep eye/mouth/detail drawing forbidden unless explicitly permitted by the existing production contract.
6. Rerun Phase12 -> Phase14 in an isolated worktree.
7. Rerun:
   - adopted-baseline binding;
   - Feature Survival;
   - forbidden-face-detail;
   - Anatomy;
   - Topology;
   - Source Authority;
   - exact-output DINO diagnostic.
8. Feature Survival must remain independently visible and must not be sacrificed to obtain face PASS.
9. Baseline adoption records from SA10.12 remain immutable.
10. If output changes, it is a new candidate only; do not mutate the adopted baseline record.
11. No aggregate score or threshold calibration.
12. Preserve artifacts in GitHub and under the canonical Google Drive `chatGPT及びCodex用` hierarchy.
