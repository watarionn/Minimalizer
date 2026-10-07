# Handoff — SA10.12 Adopted Baseline Binding & Visual Hard-Gate Backfill — 2026-10-07

Status: SA10.11 COMPLETE / SA10.12 NEXT

Goal:
Create a legitimate, reviewable adopted-baseline binding protocol for non-GC001 cases, then backfill Feature Survival and forbidden-face-detail hard evidence without candidate self-reference.

## Current state

Hyakuto-Kyoko and Juufuutei-Raden_stylecal_source now have:
- Source Authority PASS
- Anatomy PASS
- Topology PASS
- Phase14 machine PASS
- Phase14 human visual PASS
- deterministic Phase12 output
- exact-output DINO diagnostics

Still UNAVAILABLE:
- Feature Survival
- forbidden-face-detail
- SA9 Teacher evidence

## SA10.12 requirements

1. Define a baseline registry contract with:
   - case_id
   - source SHA-256
   - baseline artifact SHA-256
   - baseline origin
   - explicit review status
   - reviewer / review evidence
   - adoption timestamp or immutable adoption record
   - production_authority boundary

2. Candidate self-reference is forbidden.
   The candidate under evaluation cannot become its own baseline in the same evaluation transaction.

3. Do not silently promote old Phase14 PASS output into a baseline.
   A separate adoption action/review record is required.

4. Once a baseline is legitimately bound:
   - run fresh Feature Survival;
   - run fresh forbidden-face-detail;
   - preserve both reports individually;
   - keep Anatomy, Topology and Source Authority independently visible.

5. If no legitimate baseline is available, remain UNAVAILABLE.

6. DINO remains diagnostic-only.

7. No aggregate score or production threshold calibration.

8. Preserve all artifacts in GitHub and under the canonical Google Drive `chatGPT及びCodex用` hierarchy.
