# L04 Lane B: dual-budget admission contract (2026-10-16)

The new research-only evaluator at `tools/research/local_l04_budget_gate.py` separates original signed Stage8 source-ring vertices from expanded SVG vertices. It also requires source owner, protected face/arm ownership, and silhouette exactness, plus SHA-256 authority fields. It never changes source geometry or grants human Golden or production release.

A local synthetic test harness passed **62/62** cases, including compact SVG with source-ring overrun, the converse, single-pixel ownership changes, missing authority hashes, malformed counts, zero caps and invalid schema. The test source is not yet committed because its GitHub write was blocked; the number must not be treated as repository CI coverage.

The historical SA10.58 evidence for Raden and GC001 is a methodology reference, **not Local H04/H06/H08 proof**. In that older evidence, original Stage8 source rings exceed their caps even though expanded SVG counts fit. Do not import those numeric outcomes as Local Golden.

**L04 HOLD; L02 HOLD; L07 HOLD; production NO_GO.** No signed Local Stage8 source-ring evidence was evaluated in this run. Next: commit the synthetic tests through a permitted normal review path, acquire SHA-pinned Local Stage8 evidence, replay both independent budgets and visual owner/silhouette comparisons, then human Golden review.
