# Minimalizer v0.3.0

Status: **stable release**

Minimalizer converts an input image into a minimal graphic built from a small palette and geometric Shapes. The core goal remains image -> minimalize, with minimalization quality prioritized over optional features.

Stable v0.3.0 includes conservative thin/noisy rectangle cleanup, near-background fragment cleanup, safe same-role fragment union, primitive promotion, adaptive polygon simplification with strict local IoU, character identity and semantic protection, simplified basic GUI with advanced controls hidden by default, and high-resolution durability improvements.

Face primitive drawing is OFF by default. Experimental role-fragment merge remains OFF by default.

Validation: 156 tests passed in completed batches, 16/16 corpus images processed, compileall passed, and an 8192x6373 (52.21 MP) input completed successfully. A single-process full pytest run exceeded the interactive execution window and is not counted as a completed pass.

Important restoration rule: `v0.3.0-alpha8 Character-specific Quality / Retry` is an old development checkpoint, not the current state.
