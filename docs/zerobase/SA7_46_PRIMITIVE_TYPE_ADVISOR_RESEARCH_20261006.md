# SA7.46 Primitive-Type Advisor Research — 2026-10-06

Status: CONTRACT PASS / SOURCE-GEOMETRY AUDIT PASS / PRODUCTION NO-OP

SA7.46 absorbs the StarVector idea of semantic primitive-family selection while keeping all advisor output outside production authority.

## Purpose

Allow future VLM/LLM/vector-model systems to suggest primitive families without executing arbitrary SVG/code or allowing model output to choose production geometry directly.

Studied advisor vocabulary:
- polygon
- rectangle
- ellipse
- line
- ribbon

## Architecture

External/deterministic advisor suggestion
-> vocabulary/provenance validation
-> source-derived geometry evidence
-> agreement/disagreement audit
-> renderer-support audit
-> research report only
-> explicit later promotion decision required

No SA7.46 advisor result changes production rendering.

## New module

`minimalizer_zerobase/semantic_abstraction/primitive_type_advisor.py`

Contract version:
`sa7.46-v1`

### PrimitiveGeometryEvidence

Source-only metrics:
- source area
- bbox aspect ratio
- extent
- solidity
- contour vertex count
- fitted ellipse IoU
- deterministic evidence family

### PrimitiveTypeSuggestion

Required:
- semantic role
- primitive family
- confidence
- source/provenance
- optional rationale

Safety:
- unsupported family fails closed
- confidence outside [0,1] fails closed
- `authoritative=true` fails closed
- unknown role fails closed
- duplicate role suggestions fail closed

### PrimitiveAdvisorAudit

Records:
- advisor suggestion
- source geometry evidence
- family agreement
- current renderer support
- production eligibility
- reasons

SA7.46 deliberately sets:
- production_eligible = false for all advisor suggestions
- authoritative = false
- production_output_changed = false

A later explicit deterministic rule promotion is required before any advisor idea may affect rendering.

## Deterministic geometry evidence baseline

This stage adds a source-derived baseline so external advice can be challenged rather than trusted.

Classification order:
1. extreme elongation -> line
2. strong elongation -> ribbon
3. strong ellipse fit + solidity -> ellipse
4. high extent + solidity + low contour complexity -> rectangle
5. otherwise -> polygon

The first focused test exposed a baseline bug:
a fully filled thin strip has `extent=1.0`, so the initial logic incorrectly classified it as rectangle.

Fix:
- prioritize extreme bbox elongation before extent/rectangle checks.

After correction:
- line/ribbon synthetic evidence behaves correctly;
- full focused suite passes.

## Renderer boundary

Current advisor vocabulary intentionally includes research families that the current canonical renderer does not yet support.

Renderer-supported for promotion study:
- polygon
- rectangle
- ellipse

Research-only / not currently renderer-supported:
- line
- ribbon

An advisor may suggest line/ribbon, but the report explicitly records renderer_supported=false and production_eligible=false.

## StarVector runtime inventory

Local environment checked before attempting model use.

Results:
- Python `starvector` module: absent
- `C:\AI\Models` StarVector directory: absent
- Hugging Face local cache StarVector model: absent

Decision:
- do not download/install a new heavy StarVector runtime merely to force SA7.46;
- preserve StarVector as a future optional advisor;
- close this stage on the model-agnostic safety contract and source-geometry audit.

## GC001 source geometry audit

External advisor called:
- false

StarVector runtime present:
- false

Production output changed:
- false

Promotion count:
- 0

Status:
- UNAVAILABLE external advisor
- source geometry evidence AVAILABLE

Analyzed roles:
- accessory_or_held_object -> polygon
- hair -> polygon
- head -> polygon
- left_arm -> polygon
- lower_body -> polygon
- major_clothing -> polygon
- right_arm -> polygon
- torso -> polygon

Representative evidence:

### hair
- source area: 17,541
- bbox aspect: 1.269912
- extent: 0.270436
- solidity: 0.413053
- contour vertices: 20
- ellipse IoU: 0.426243
- deterministic family: polygon

### major_clothing
- source area: 3,217
- bbox aspect: 2.370000
- extent: 0.135738
- solidity: 0.373629
- contour vertices: 9
- ellipse IoU: 0.166667
- deterministic family: polygon

### head
- source area: 17,229
- bbox aspect: 1.389262
- extent: 0.558603
- solidity: 0.721062
- contour vertices: 19
- ellipse IoU: 0.655190
- deterministic family: polygon

Interpretation:
GC001 source masks do not currently provide strong deterministic evidence to replace the canonical polygon-heavy representation with ellipse/rectangle/line/ribbon families.

This supports a production no-op decision for SA7.46.

## Verification

Focused SA7.46:
- 10/10 PASS

Full ZeroBase:
- 669/669 PASS

Other:
- compileall PASS
- git diff --check PASS

## Drive preservation

Folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_46_20261006_ADVISOR`

Folder ID:
`1zD5tuaoOXdf-wMagZxIAVzK5jW8MbHfM`

Verified cloud artifacts:

- `GC001_sa746_primitive_advisor.json`
  - `1l8gCJy5i6Id1vUKICvKgxdF3nVTu-vyr`
- `GC001_sa746_advisor_context_4way.png`
  - `1YxEjLQz3UNtrwcKHe-ZLfsI4oWzcpINs`

## Decision

Merge SA7.46 as advisor-only research infrastructure.

Do not change the visual baseline.
Do not modify canonical production primitive selection in this stage.

## Next

SA7.47 Layer / Occlusion Evidence Research.

Primary precedents:
- LayerPeeler
- SuperSVG

Goal:
add source-derived layer/occlusion evidence that can describe front/behind/overlap relationships without taking anatomy/topology or rendering authority away from the existing canonical path.
