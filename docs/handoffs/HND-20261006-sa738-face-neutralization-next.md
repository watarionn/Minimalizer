> **SUPERSEDED CURRENT-STATE NOTICE (2026-10-06):** SA7.38 was subsequently completed, followed by SA7.39, SA7.40, and SA7.41. The canonical continuation point is now **SA7.42 Multi-Component Background Field Geometry**. For restart instructions, read `docs/handoffs/HND-20261006-sa742-background-multicomponent-next.md`. The remainder of this file is retained as historical SA7.38 context only.

# HND-20261006 Minimalizer SA7.38 Face Neutralization Handoff

Date: 2026-10-06
Status: HISTORICAL SA7.38 SNAPSHOT / SUPERSEDED BY SA7.42 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main
Historical implementation SHA at original handoff: `7b01deca662fa99765f1b163bf60d5e1a00dcef6`\nCurrent restart instructions: `docs/handoffs/HND-20261006-sa742-background-multicomponent-next.md`.
Latest adopted visual baseline: `a60aaa12ff22c2f6384a598442964710ce939d87` (Silhouette Proportion Recomposition)
Visual baseline has NOT changed since that commit.

## Historical restart rule

This section describes the original SA7.38 restart state and is no longer current. Do not restart from SA7.38. Continue from current `main` using `docs/handoffs/HND-20261006-sa742-background-multicomponent-next.md`.

Do not continue from older SA7.29/33/34/37 experiment branches.

## Non-negotiable rules

- No generative img2img / fill / inpainting / missing-content redraw.
- Golden and Browser fallback v12 are evaluation-only, never production inference inputs.
- Do not hard-code GC001 colors, coordinates, masks, or missing signatures into production.
- Every visual candidate must run the canonical SA7.35 hard gate fresh from the candidate image.
- Never copy a previous hard-gate JSON forward.
- Feature Survival is source-supported.
- Forbidden Face Detail must be measured from the current rendered candidate.
- Current accepted visual hard requirements remain:
  - Visual Delta >= 1.5% vs adopted baseline
  - Feature Survival missing=0
  - Forbidden Face Detail ratio=0.00%
  - actual four-way: Source | Browser fallback v12 | current | Rinka Golden
  - Browser fallback v12 is the visual regression floor
  - no accepted Version History entry for HOLD/REJECT stages

## SA7.35 Hard-Gate Path Reconciliation — COMPLETE

PR #168
Merge SHA: `85ee2cf7870d24e1ffd58375f2b8e5f95fb8df59`

What was fixed:
- restored `source_supported_feature_survival_report`
- added `minimalizer_zerobase/evaluation/canonical_hard_gate.py`
- added `tools/run_canonical_hard_gate.py`
- canonical hard gate now requires actual current candidate bytes/path
- exact missing signatures are emitted
- stale reused SA7.2 hard-gate claims in SA7.29/33/34 docs were corrected

Fresh replay:
- SA7.2: required=16, missing=0, face=0.000000 — PASS
- SA7.29: missing=3, face=0.144622 — FAIL
- SA7.33: missing=3, face=0.144622 — FAIL
- SA7.34: missing=3, face=0.144622 — FAIL

Root cause:
later scripts reused SA7.2 hard-gate evidence instead of recomputing the current candidate.

Drive:
`Semantic_Abstraction/SA7_35_20261006`
Folder ID: `1yga2XTh2HKuMXDt8sdy-Qaslbe6VLbYS`

Memory-vault mistake record:
`20-projects/minimalizer/mistakes/MIS-20261006-stale-hard-gate-reuse.md`

## SA7.36 Missing Signature Semantic Attribution — COMPLETE

PR #169
Merge SHA: `4d5fef009debf43b35718268bc175020bc7bcbda`
ZeroBase at closure: 615/615 PASS

Implementation:
- `minimalizer_zerobase/evaluation/missing_signature_attribution.py`
- `tools/attribute_missing_signatures.py`

Fresh GC001 semantic attribution:
1. missing RGB signature [16,16,16]
   - connected source component: 399 px
   - torso overlap: 94.99%
   - major_clothing: 4.51%
   - hair: 0.50%
   - primary role: torso
2. missing RGB signature [16,48,48]
   - connected source component: 34 px
   - right_arm overlap: 100%
3. missing RGB signature [144,176,16]
   - connected source component: 72 px
   - torso overlap: 83.33%
   - major_clothing: 16.67%

Interpretation:
the regression is semantic survival loss in two torso-associated masses and one right-arm mass, not a request to hard-code those colors.

Drive:
`Semantic_Abstraction/SA7_36_20261006`
Folder ID: `1KsRzVW98w1tBxjmqQ329P_mECsOL972U`
Report ID: `1RJemhxLLa2FQeRivTVq7TJsA41112BVo`

## SA7.37 Required Semantic Mass Reservation — COMPLETE

PR #171
Merge SHA: `7b01deca662fa99765f1b163bf60d5e1a00dcef6`
ZeroBase: 618/618 PASS
`git diff --check`: PASS

Implementation:
- `minimalizer_zerobase/semantic_abstraction/required_semantic_mass.py`
- `tools/inspect_required_semantic_mass.py`
- `tests/zerobase/test_sa737_required_semantic_mass.py`
- `docs/zerobase/SA7_37_REQUIRED_SEMANTIC_MASS_20261006.md`

Production contract:
- source RGB + semantic masks only
- default reservation roles:
  - torso: up to 4 Lab palette clusters
  - left_arm: up to 2
  - right_arm: up to 2
- face/head reservation explicitly forbidden
- connected component per palette cluster
- weak contrast rejected
- polygon guards:
  - source coverage >= 0.65
  - expansion <= 1.12
  - outside-role spill = 0

GC001 source-only extraction produced 6 reservations, including:
- dark torso mass
- yellow/green torso mass
- dark right-arm mass

Research overlay on SA7.34:
- canonical Feature Survival: missing=3 -> missing=0 PASS
- Forbidden Face Detail: 14.4622% unchanged FAIL
- Visual Delta vs adopted: 69.8901%
- SA7.34 -> Golden LAB diagnostic: 33.1502
- SA7.37 -> Golden LAB diagnostic: 32.6883
- v12 -> Golden LAB diagnostic: 16.2422

LAB remains diagnostic only, not the canonical visual floor decision.

Decision:
- semantic survival repair mechanism accepted into architecture
- research overlay NOT connected to production renderer
- visual adoption remains HOLD
- accepted visual baseline unchanged

Drive:
`Semantic_Abstraction/SA7_37_20261006_HOLD`
Folder ID: `1WLel4JhWl2DZYL_2aee-5fQ6phoM1Mi-`
Contents verified through Drive connector:
- `GC001_sa737_required_semantic_mass.json`
- `GC001_sa737_reservation_overlay.png`
- `GC001_sa737_gate_report.json`
- `GC001_sa737_eval.json`
- `GC001_comparison_4way_sa737_hold_20261006.png`

Four-way ID: `1YgBpJOKaY6m4Qhd_tmtX3WgAsxLoYhWu`

## SA7.38 Face Neutralization Path Reconciliation — COMPLETE (historical diagnosis below)

The following diagnosis was captured before implementation. SA7.38 was later completed; the canonical completion record is `docs/zerobase/SA7_38_FACE_NEUTRALIZATION_RECONCILIATION_20261006.md`.

### Confirmed diagnosis

Phase4 face mask area:
- 4,937 px

SA7.2 candidate:
- face-mask median RGB: [234,130,50]
- all 4,937 face-mask pixels are exactly [234,130,50]
- Forbidden Face Detail ratio: 0.000000
- no internal detail components

SA7.29 / SA7.34 / SA7.37 candidate family:
- face-mask median RGB: [255,255,255]
- 4,197 px are exactly white [255,255,255]
- 580 px are exactly [234,130,50]
- additional tiny color fragments exist
- Forbidden Face Detail ratio: 0.1446222402268584
- three major internal detail components:
  - 362 px, centroid approx (207.3,134.5)
  - 268 px, centroid approx (166.3,111.6)
  - 84 px, centroid approx (130.0,130.9)

This proves the remaining face failure is not primarily “eyes reappeared”.
The faceless surface itself was split by later head / protected identity layers.

### Why the semantic face gate did not catch this

`face_neutralization_gate(plan)` is policy-level only:
- face semantic part must exist
- facial_feature parts must be SUPPRESS

It does NOT validate the final rendered raster inside the face mask.

Therefore semantic Face Neutralization could report PASS while the final rendered image failed the image-level Forbidden Face Detail gate.

### Source face evidence

Source Phase4 face mask:
- area: 4,937 px
- source face median RGB: [251,225,218]
- largest exact source color [252,238,233]: 956 px
- source face contour:
  - raw contour vertices: 110
  - contour area: 4,818
  - bbox: x=128, y=109, w=87, h=73

Important:
SA7.2's flat [234,130,50] face is hard-gate-safe but is not the representative source face color.
SA7.38 should prefer source face semantic authority rather than reproducing the historical orange fill.

### Face polygon safety probe

Using the Phase4 face mask outer contour:

| epsilon fraction | vertices | coverage | expansion | spill px | missing px |
| ---: | ---: | ---: | ---: | ---: | ---: |
| .0200 | 7 | 0.89731 | 0.89751 | 1 | 507 |
| .0100 | 11 | 0.96536 | 0.96678 | 7 | 171 |
| .0075 | 13 | 0.98805 | 0.98906 | 5 | 59 |
| .0050 | 15 | 0.99473 | 0.99635 | 8 | 26 |
| .0030 | 18 | 0.99615 | 0.99797 | 9 | 19 |
| .0020 | 39 | 0.99878 | 1.00041 | 8 | 6 |
| .0010 | 110 | 1.00000 | 1.00000 | 0 | 0 |
| .0005 | 110 | 1.00000 | 1.00000 | 0 | 0 |
| raw | 110 | 1.00000 | 1.00000 | 0 | 0 |

Finding:
a coarse ordinary filled polygon cannot currently satisfy both aggressive simplification and exact zero spill. Exact 110-vertex contour is the current correctness baseline.

Do NOT relax a spill guard merely to reduce vertex count.

### SA7.38 Drive artifacts

Local/generated:
- `GC001_sa738_face_diagnosis.json`
- `GC001_sa738_face_polygon_probe.json`

Target Drive path:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_38_20261006_IN_PROGRESS`

Cloud-side preservation verified through the Drive connector.\n\n- folder ID: `1Uju-tex7SEnGXtbYtYx77ahUbOmsaCKo`\n- `GC001_sa738_face_diagnosis.json`: `19MH8REp2tlsNygklVwSTabw9rhpW_ix5`\n- `GC001_sa738_face_polygon_probe.json`: `1QnVYqnRUOAvShAkq2aGU0SXMEmfuQUHH`

## Historical SA7.38 implementation direction (completed)

Goal:
restore final image-level Forbidden Face Detail to 0.00% without reintroducing eye-like geometry.

Do NOT simply replay SA7.2 orange face.

Preferred investigation order:

1. Add a late canonical `face_surface` stage after head/identity recomposition so later layers cannot split the face.
2. Face geometry authority must come from the source-derived face semantic mask.
3. Face palette must come from the source face region only.
4. Start with exact source face contour as correctness baseline.
5. Then test generic simplification strategies that preserve zero outside-face spill:
   - inward-safe contour fitting
   - mask-clipped polygon support
   - renderer clipPath support if added generically
6. Final image-level gate must be measured fresh with SA7.35 canonical runner.
7. Also rerun eye-like / paired-dark-region semantic regressions. A flat face that passes color-uniformity but creates eye-like islands elsewhere is not acceptable.
8. After face=0, combine with SA7.37 semantic mass reservation in a canonical scene candidate.
9. Generate actual four-way and compare against v12 floor.
10. Only then consider visual adoption.

### Suggested first SA7.38 acceptance checks

Synthetic:
- face region partially covered by later head/accent polygons -> late face stage restores one flat surface
- face stage cannot write outside face authority
- face/head reservation from SA7.37 remains forbidden
- deterministic rerun

GC001:
- Feature Survival remains missing=0
- Forbidden Face Detail becomes 0.00%
- no eye-like paired islands
- subject topology/anatomy unchanged
- actual 4-way generated
- v12 floor checked

## Local execution paths

Do not modify dirty canonical checkout for experiments:
`C:\Work\Projects\Minimalizer`

Use fresh worktree under:
`C:\Work\Temp\minimalizer-sa738`

Python:
`C:\Work\SharedAI\minimalizer-observers\Scripts\python.exe`

GC001 workspace:
`C:\Work\Temp\macro-gc001`

Phase3 subject mask:
`C:\Work\Temp\macro-gc001\artifacts\GC001\phase_03\03_subject_mask.png`

Phase4 semantic masks:
`C:\Work\Temp\macro-gc001\artifacts\GC001\phase_04\part_masks`

Current research candidate:
`C:\Work\Temp\macro-gc001\semantic_abstraction\GC001_sa737_reservation_overlay.png`

SA7.38 diagnostics:
`C:\Work\Temp\macro-gc001\semantic_abstraction\GC001_sa738_face_diagnosis.json`
`C:\Work\Temp\macro-gc001\semantic_abstraction\GC001_sa738_face_polygon_probe.json`

## Historical SA7.38 immediate next action (completed)

1. Verify SA7.38 Drive folder/file IDs.
2. Create fresh branch `feature/semantic-abstraction-sa738-face-surface` from current main.
3. Implement generic source-authorized late face surface stage.
4. Focused synthetic tests.
5. GC001 candidate from canonical scene + SA7.37 reservation + SA7.38 face surface.
6. Fresh canonical SA7.35 hard gate.
7. If Feature Survival remains 0 missing and face becomes 0.00%, run full ZeroBase and actual four-way.
8. Preserve all artifacts and update this handoff.
