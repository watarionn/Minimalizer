# Lane A L02: signed H08 morphology-before-class30 integration (2026-10-25)

**Research-only, known-case-exposed; no semantic quality approval. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

The earlier Draft PR #439 used an older H08 composed owner. This run independently reconstructed the **latest** source-only sequence from authenticated private Drive inputs: composed `3e467694...`, strict `32bb5266...`, single-anchor `6472cfc4...`, class32 palette `f847f995...`, and class30 opt-in `94122b85...`. Four ZIP SHA pins and reviewed/Run30/AnimeSeg internal member manifests (19/7/5) were verified. Human labels were opened only **after** source-only owner candidates were frozen and hashed.

## Root cause and source-only correction

Applying morphology **after** the latest `94122b...` owner changes 0 pixels, because the 17 reviewed arm mistakes are already immutable. Morphology must run on the `6472...` **pre-palette** owner, before the class30/32 opt-in. Another hazard was exposed: the opt-in tries to resurrect **27** class32 pixels rejected by morphology. The new composition preserves that veto and prunes disconnected additions. Source-alpha confinement, immutable original owners, 4/8 component identity and cross-owner contacts are checked.

| Signed H08 known-only metric | Latest `94122b...` | New veto-preserving `c3a7e642...` |
| --- | ---: | ---: |
| Reviewed garment TP | 144,221 | 144,056 |
| Known false owner | 17 | **0** |
| Known arm false owner | 17 | **0** |
| Reviewed garment FN | 12,349 | 12,514 |

This **partial P0 tradeoff** removes 17 reviewed arm misassignments but sacrifices 165 reviewed garment pixels. The visual difference is small; the much larger missing sleeve/garment regions remain. **0 P0 cases fully resolved, 0 P1 cases accepted, 3 P0 cases unresolved.** The original signed RGB/alpha is unmodified. No generated pixels, annotation-based inference, unknown-as-negative scoring, or face drawing.

H06's pinned composed owner `ceaae119...` was unchanged (TP 294,020 / known FP 1,077 / FN 20,803). H04's signed Run30 owner was unchanged (known FP 4,423). Source-free targeted regressions: **38 PASS + 4 subtests**, not full repository CI. The candidate SHA `c3a7e642fe161207710bf59d7483bf77c9dd4e39549f0aff2483528696a3e0d2` was reproduced by the integrated source-only composition. Private source and comparison board remain outside GitHub.

## Integration gate

This PR remains **Draft**. Required: exact GitHub-head source-only replay and full CI; H08 sleeve/arm visual comparison and semantic owner review; genuinely unseen signed blind evaluation; Phase4 exclusivity/connection/critical-part preservation. Do not merge as production-quality or treat the tiny known-arm correction as completion. A-only source-free code/tests/docs; B L04/L07, Public/C08, production LocalWorker, Golden and release untouched.
