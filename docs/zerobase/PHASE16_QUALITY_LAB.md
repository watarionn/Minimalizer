# Phase 16 Quality Lab

Status: PoC

## Goal
Raise visual quality without weakening ZeroBase quality Gates or introducing generated/inpainted pixels.

## Non-negotiable constraints
- Source-observed evidence only.
- Mitsuba is evaluation-only. It must not generate, redraw, inpaint, or supply pixels to the product output.
- A Mitsuba opinion never overrides deterministic provenance or regression Gates.
- Improvements must be localized to the responsible Phase 3-12 stage and re-run regression tests.

## Loop
Source -> ZeroBase2 -> deterministic metrics -> Mitsuba semantic comparison -> lost-feature/stage hypothesis -> algorithm change -> exact-image replay -> Approved regression.

The first baseline is the mobile image that exposed the large-hair Phase 10 fidelity-budget failure. That incident is useful because the quality loop already demonstrated the desired rule: keep the Gate strict and improve representation until the image passes.

## PoC acceptance
1. Quality Lab emits a machine-readable report for source/output.
2. Mitsuba receives both images and returns evaluation JSON only.
3. The report identifies concrete lost critical features and maps each hypothesis to Phase 3-12.
4. Findings are treated as hypotheses until deterministic artifacts confirm them.
5. No generated image enters the pipeline.

Tool: `tools/run_phase16_quality_lab.py`.
