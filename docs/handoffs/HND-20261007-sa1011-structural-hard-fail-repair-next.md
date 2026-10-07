# Handoff — SA10.11 Structural Hard-Fail Repair — 2026-10-07

Status: SA10.10 COMPLETE / SA10.11 NEXT

Goal: repair the newly exposed non-GC001 Anatomy/Topology hard failures before any calibration.

Current failures:
- Kyoko: left_arm extreme bbox change; face-inside-head and left-arm attachment topology loss.
- Raden: head missing from final candidate; face-inside-head and head-above-torso topology loss.

Requirements:
1. trace each failure back to Phase10-12 primitive selection/simplification;
2. repair generically from source-supported semantic roles, never case coordinates/colors;
3. keep Phase14 PASS insufficient while Anatomy/Topology hard evidence fails;
4. rerun Phase12 -> Phase14 and exact-output DINO after repair;
5. rerun Source Authority and structural hard evidence;
6. preserve Raden actual-emission diagnostic separately from SA10.5;
7. Feature Survival/forbidden-face remain UNAVAILABLE unless a legitimate adopted baseline is formally bound;
8. no aggregate score or threshold calibration.
