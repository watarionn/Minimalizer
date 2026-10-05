# SA7.14 Geometry-First Eyewear Witness — 2026-10-05

Status: SAFETY PASS / NON-TARGET RECALL FAIL / NOT AUTHORIZED

## Contract
A geometry-first witness was implemented around paired closed contours, symmetry, scale, upper-face location, and source-supported bridge continuity.

Synthetic tests initially exposed a critical failure: two filled eye-like marks could be mistaken for a paired closed structure. Before any GC001 evaluation, the contract was tightened so a source-supported bridge is mandatory.

Focused synthetic result after fix: 5 PASS.

## Non-target evaluation
Using the SA7.13 references, before any GC001 evaluation:

Positive:
- Sorashina Sopia: paired=false
- Shiranui Flare: paired=false

Negative:
- AZKi: paired=false
- Gawr Gura: paired=false
- Ceres Fauna: paired=false
- Nanashi Mumei: paired=false

The observer rejected all negatives but also all positives. At thumbnail resolution, bridge continuity is too brittle.

## Decision
Safety is good; recall/generalization is unacceptable. Do not relax the bridge requirement after seeing target data. GC001 was not evaluated with SA7.14.

SA7.14 is not an independent semantic witness and does not enter SA7.6 promotion.

## Next: SA7.15 Region-Conditioned Structural Verifier
Use SA7.9 region proposals only as candidate locations, then verify local paired/frame topology inside each candidate at higher local scale. This verifier is explicitly dependent on the region observer and therefore must not count as a second independent observer role. Its purpose is false-positive suppression and better geometry localization, not promotion by itself.

Renderer remains disconnected.
