# HND-20260929 Phase 12 Quality Decision

## Scope
Minimalizer ZeroBase 2nd Cycle Phase 12 only.

## Goal
Phase 12 is the quality-decision phase, not a routine progression step.
Do not advance to Phase 13 merely because deterministic tests pass.

## Roles
- Rinka: architecture owner and visual quality gate.
- Codex: implementation support for Phase 12 simplification, guards, tests, and diagnostics.
- Nao: integration, regression, branch/worktree hygiene, and technical recovery.
- Claude: out of scope for this cycle.

## Current implementation direction
Phase 11 semantic composition remains the immutable upstream contract.
Phase 12 may simplify geometry only after grouping by semantic owner and palette evidence.
Generate at least conservative and aggressive candidates.
Keep identity/pose guards fail-closed.
Produce explicit before/candidate/final/removed-overlay artifacts.

## Visual decision
The primary question is whether outputs become visibly closer to Approved references.
Passing numeric gates alone is insufficient.

## Stop condition
If the Phase 12 candidate family does not materially improve:
- macro geometric simplification,
- face/head treatment,
- hair and clothing large-plane structure,
- fragment reduction,
- character identity and pose preservation,
then stop before Phase 13 and redesign the Phase 12 representation model.

## Integration rules
- Preserve existing uncommitted work.
- Do not edit another agent's worktree.
- Keep source/provenance contracts intact.
- Generation, inpainting, and hidden completion remain forbidden.
- Run focused Phase 12 tests before wider regression.
- Treat visual QA by Rinka as the final Phase 12 promotion gate.


## Round 6 - source-evidence lower-body plane recovery (2026-09-30)
- Added deterministic source-guided decomposition inside Phase 12 only; Phase 11 contract remains unchanged.
- Recovered a pale crossed-leg plane from source luminance evidence instead of carrying the fused dark lower_body slab through unchanged.
- Added a guarded large support plane for the brighter inner-skirt region using source pixels + morphology + convex hull clipped to the existing lower_body mask.
- Rejected two visual dead ends during QA:
  - direct bright-component skirt extraction produced a small floating patch,
  - separate dark-foot plane produced fragmented shoes.
- Preserved the successful leg-plane recovery and large inner-skirt support plane.
- major_clothing now bypasses merge-close and uses a tighter epsilon cap rather than weakening its quality thresholds.
- Current Raden calibration: aggressive PASS, 21 primitives, silhouette IoU 0.934349, provenance gate PASS (76 artifacts).
- Focused regression: 43 passed across Phase 10, semantic composer, stage-contract bridge, and Phase 12.
- Visual QA: materially improved lower-body readability versus Round 5, especially leg width/crossing and skirt plane hierarchy, but upper-body/hair/foot treatment remains below Approved reference quality.
- phase13_promotion_allowed=false. Continue Phase 12 redesign/visual refinement.


## Round 7-12 - source-guided identity-plane convergence (2026-10-02)
- Continued Phase 12 as a visual-quality gate. Numeric PASS alone remains insufficient.
- Phase 4 ownership refinements:
  - recovered a bright face-side hair strand across owner boundaries using the character's own bright-hair LAB prototype,
  - recovered two small secondary vivid shoulder accents from the primary accessory color family while rejecting face-adjacent warm skin,
  - recovered a large hair-like unknown component only when hair color clearly beat arm/clothing/torso color prototypes and the component contacted existing hair,
  - Raden hair ownership increased by 1157 px and Phase 4 unknown ratio fell from about 7.7% to 5.45%.
- Phase 12 hair refinements:
  - split the main highlight into face-relative side planes instead of one face-crossing convex hull,
  - added a relative-luminance gate so dark false highlights are not promoted,
  - added a local-contrast hair overlay for medium-size, elongated streaks with strong contrast against nearby dark hair,
  - local-contrast overlays do not subtract from the dark-hair silhouette, preventing thin-strand polygon error from degrading silhouette IoU,
  - highlight and local-contrast colors now use source-derived upper-quantile colors (0.90) rather than fixed or generated colors.
- Phase 12 lower-body and face refinements:
  - lower-body dark plane color now comes from the source pixels inside the dark plane,
  - central skirt panel color uses the upper 0.90 source luminance quantile,
  - face-plane color uses the original bright support rather than morphology-closed dark eye/mouth pixels,
  - small accessory components receive a dedicated minimum-area rule so meaningful shoulder accents survive while tiny noise is still removed.
- Geometry/simplification refinements retained:
  - arm epsilon cap 0.006,
  - lower-body epsilon cap 0.006 during the earlier fidelity sweep, later current policy values remain the canonical code values,
  - torso epsilon tightening,
  - major-clothing fidelity and tighter Phase 12 epsilon,
  - neutral unbound micro-fragment removal that preserves small chromatic skin fragments.
- Rejected or held experiments:
  - blanket hair-highlight dilation: over-whitened the crown,
  - torso light-plane convex hull: produced a large gray shield and was rejected,
  - neck warm-accent recovery: source evidence was too weak and face contamination risk was high,
  - global hair fidelity-budget escalation: remaining Phase 11 hair loss is mostly thin boundary/fringe detail, not a missing macro hair mass, so extra vertices are not currently justified,
  - enlarging the raised-hand skin plane: upstream source evidence is already approximately the same size as the retained hand mass.
- Latest Raden calibration:
  - Phase 11 primitive count: 51,
  - Phase 12 aggressive: PASS, 15 primitives, silhouette IoU 0.977642, 541 vertices,
  - Phase 12 conservative: PASS, 15 primitives, silhouette IoU 0.980853,
  - provenance gate: PASS, 76 artifacts,
  - wide regression around Phases 4/6/10/11/12: 77 passed,
  - current source-silhouette missing area: about 1086 px; remaining Approved-reference silhouette difference is predominantly reference-only stylistic expansion rather than source-supported missing geometry.
- Visual QA:
  - major source-supported identity cues are now present as a small set of meaningful planes: pale face, pale left hair strand, local silver hair streaks, dark hair mass, orange waist/shoulder accents, dark outer skirt, lighter center skirt panel, pale crossed legs, dark shoes,
  - current output is materially closer to the Approved large-plane reading than Round 6 while remaining deterministic and source/provenance constrained,
  - Phase 13 promotion remains held until final branch hygiene and one last clean-artifact review are completed.

## Final Phase 12 visual gate - PASS (2026-10-02)
- Clean artifact review completed against the latest `phase_12/stage.json`.
- Required Phase 12 artifacts are present with output SHA records:
  - before,
  - conservative/aggressive candidates,
  - final,
  - removed-shapes overlay,
  - simplification payload,
  - metrics,
  - preview.
- Provenance policy remains fail-closed:
  - generation forbidden,
  - inpainting forbidden,
  - hidden completion forbidden,
  - generated/inpainted pixel count = 0.
- Latest focused and broad regression suites pass.
- Latest Raden aggressive candidate remains the selected output and preserves the required semantic owners and pose/identity structure.
- Remaining large visual differences versus the Approved reference are predominantly reference-only stylistic expansion rather than source-supported missing geometry.
- Further expansion toward those unsupported reference shapes would violate the Phase 12 source/provenance constraint and is not a valid quality improvement for this phase.
- Rinka visual QA decision: **PASS** for the Phase 12 representation target.
- `phase13_promotion_allowed=true`.
- Phase 13 may proceed from this exact Phase 12 artifact contract. Do not reopen Phase 12 merely to chase reference-only silhouette or palette differences unless a new source-supported regression is discovered.

## Post-gate Diagnostic-2 regression and repair (2026-10-02)
- The first Phase 12 PASS decision was made after the Raden quality gate and clean-artifact review, before the second Diagnostic-2 case had a canonical Phase 12 artifact.
- Running the closed Phase 12 implementation on Hyakuto-Kyoko exposed a real cross-case identity regression: highly chromatic orange hair was reinterpreted as a huge achromatic/white highlight plane.
- First bad stage localization: Phase 11 preserved Kyoko's orange hair; Phase 12 was the first stage to invert the dominant hair color.
- Root cause: source-guided hair highlight splitting used luminance contrast alone. A highly saturated hair group plus bright white non-hair source pixels inside its broad geometry caused the top luminance quantile to select white as the light-plane representative.
- Fix: source-guided hair highlight reinterpretation is now restricted to low/moderate-saturation baseline hair groups. Highly chromatic hair keeps its Phase 11 palette instead of being split into achromatic light/dark planes.
- Regression guard: a synthetic orange-hair case with a large white crossing patch must not produce a hair-light plane.
- Kyoko after repair: Phase 12 PASS, aggressive 158 -> 31 primitives, silhouette IoU 0.978139; orange hair identity is visually preserved.
- Raden after the same repair: metrics and the intended low-saturation silver/black hair planes remain unchanged (aggressive 51 -> 15 primitives, silhouette IoU 0.977642).
- Diagnostic-2 Phase 12 human visual QA is now PASS for both Raden and Kyoko.
- Lesson / prevention: do not close a cross-case visual phase from a single calibration case. Diagnostic-2 must be generated and visually reviewed before a final promotion decision is recorded.
- `phase13_promotion_allowed=true` is reaffirmed only after this two-case repair and review.


## Post-pass source-supported refinement and latest revalidation (2026-10-02)

Phase 12 remained closed to reference-only imitation, but additional source-supported defects were found and repaired before final handoff. All changes remain deterministic and preserve the no-generation/no-inpainting/no-hidden-completion contract.

### Source-supported refinements retained
- Added a source-guided wrist-skin overlay:
  - arm-local bright components must be small relative to the arm owner,
  - strongly brighter than their local sleeve neighborhood,
  - and close to the source-guided face color in LAB space.
  - Existing small skin-colored unbound fragments are merged into the same overlay when compatible.
  - Raden now keeps both wrist skin cues as one primitive with two components.
- Hair refinement:
  - local-contrast silver streaks are rendered as overlays on top of the dark-hair underpaint instead of cutting holes out of the dark-hair mass,
  - nearby source-guided light-hair groups are palette-merged when their colors are within the dedicated hair-light threshold,
  - final hair epsilon cap tightened to 0.00125,
  - local-contrast streak epsilon uses 0.006 so internal streaks stay simple without weakening the outer silhouette.
- Lower-body refinement:
  - light leg and white shoe/tights openings are combined into one multi-component light primitive,
  - the center-skirt panel now follows a simplified closed source-support contour instead of a broad convex hull,
  - the dark lower-body plane remains as an underpaint beneath the panel to avoid internal-hole complexity.
- Large-plane color refinement:
  - dark torso materials may use the brighter half of their own source pixels as the representative color when a real luminance span exists,
  - no fixed or reference-derived color is introduced.
- Geometry caps currently retained:
  - hair 0.00125,
  - arms 0.002,
  - face 0.008,
  - torso 0.004,
  - accessory 0.004,
  - lower body 0.0025,
  - major clothing 0.0011.
- Candidate selection rule changed to:
  1. fewest passing primitives,
  2. highest silhouette IoU,
  3. fewest vertices.
  Equal-primitive candidates therefore prefer visible quality before small vertex-count savings.

### Latest Raden revalidation
- Phase 12: PASS.
- Selected profile: conservative.
- Phase 11 -> Phase 12: 26 -> 14 primitives.
- Selected silhouette IoU: 0.984893.
- Selected vertex count: 696.
- Key selected part IoUs:
  - hair 0.963584,
  - face 0.967280,
  - left arm 0.968012,
  - right arm 0.988724,
  - torso 0.978647,
  - lower body 0.988454,
  - major clothing 0.966539,
  - accessory 0.984158.
- Phase 12 provenance gate: PASS, 76 artifacts.
- Latest visual QA confirms the source-supported large-plane reading remains intact while preserving 14 primitives.

### Latest Diagnostic-2 / Kyoko revalidation
- Canonical source SHA was rechecked before regeneration and matched the Phase 3 contract.
- Phase 12: PASS.
- Selected profile: aggressive.
- Phase 11 -> Phase 12: 158 -> 31 primitives.
- Selected silhouette IoU: 0.981039.
- Selected vertex count: 752.
- Hair IoU: 0.984324.
- Orange-hair identity remains visually preserved; the prior achromatic-hair regression did not recur.
- Phase 12 provenance gate: PASS, 76 artifacts.

### Latest Phase 13 visualizer revalidation
- Raden Phase 13: PASS.
  - human review: pass,
  - machine first-bad-stage: none,
  - human first-bad-stage: none,
  - provenance gate: PASS, 81 artifacts.
- Kyoko Phase 13: PASS with the same checks.
- Both debug boards were visually reviewed against the regenerated Phase 12 output and showed no new cross-stage identity break.

### Regression and promotion decision
- Latest broad regression around Phases 4/6/10/11/12: 84 passed.
- Latest focused Phase 12 regression: 18 passed.
- Remaining source-supported misses are predominantly tiny distributed boundary fragments; further pursuit would add geometry without a material visual gain.
- Rinka visual QA: PASS remains reaffirmed for the latest implementation.
- `phase13_promotion_allowed=true` remains reaffirmed.
- Do not reopen Phase 12 for reference-only expansion. Reopen only for a newly discovered source-supported or cross-case regression.
