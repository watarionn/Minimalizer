# Nao Implementation Guide: Golden Comparison

Read this together with GOLDEN_COMPARISON_ARCHITECTURE_V1.md and GOLDEN_COMPARISON_ROADMAP.md before coding.

## First assignment
Work in parallel on:
A. Golden Harness/schema/tests
B. isolated VTracer fitting PoC
C. feature-level DINOv3 evidence PoC

Do not modify production behavior in the first PR.

## Deliverables
- generic manifest JSON schema
- Case 001 benchmark manifest with semantic labels/importance only, no golden geometry coordinates
- deterministic comparison CLI/report
- tests proving required-feature hard failure cannot be offset by perceptual score
- VTracer experiment report showing mask -> simplified polygon/curve fitting
- DINO experiment report comparing global evidence with feature-local evidence
- before/after images and metrics preserved to Drive
- feature branch + commit SHA + exact test commands/results

## Prohibited
No Stable Diffusion/SDS, generative image model, inpainting, redrawing, golden raster as reconstruction input, character-specific production heuristics, silent fallback, or weakening existing hard gates.

## Review protocol
Nao implements and reports. Rinka independently reviews code, artifacts, determinism and generalization risk. Only reviewed generic mechanisms may be merged.
