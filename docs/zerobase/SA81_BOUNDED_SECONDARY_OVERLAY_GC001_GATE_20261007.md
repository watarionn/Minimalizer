# SA8.1 Bounded Secondary Overlay GC001 Gate — 2026-10-07

Status: **SYNTHETIC PASS / GC001 HARD-GATE PASS / VISUAL HOLD / NOT MERGED**

## Hypothesis
Preserve the established dominant masses and add at most one source-supported SA8 palette component per selected role only when it contributes meaningful uncovered part-local coverage.

## Validation
GitHub Actions on PR #193:
- focused: 14/14 PASS
- full ZeroBase: 755/755 PASS
- compileall: PASS

Fresh GC001:
- Feature Survival: PASS, 16 required signatures, missing=0
- Forbidden Face Detail: 0.00%
- hard gate: PASS
- visual delta vs adopted baseline: 13.6315%
- visual delta vs SA7.44: 82.5398%
- evaluation-only Lab distance to Golden:
  - SA8.1: 95.3020
  - SA7.44: 51.4763
  - Browser fallback v12: 33.4426

Golden and v12 were evaluation-only and never production inputs.

## Decision
HOLD. Do not merge PR #193.

Coverage gain alone is not a sufficient promotion condition. The selected source-supported component can still interact badly with later renderer layers. The next selector must reason about downstream overwrite / occlusion compatibility in addition to part-local coverage gain.

## Next
SA8.2 should remain branch-only until real GC001 review:
1. established dominant masses remain authoritative;
2. candidate must provide positive source-supported coverage gain;
3. candidate must survive or intentionally compose with downstream garment/panel/accent layers;
4. no face authority;
5. global primitive budget remains bounded;
6. real GC001 gate precedes merge.
