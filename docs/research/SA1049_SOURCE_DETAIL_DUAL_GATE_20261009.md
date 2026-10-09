# SA10.49: Source-detail authority vs signed flat-reference gate

Date: 2026-10-09. **Research dual-gate audit PASS; artistic-detail reconstruction, full-character Golden, production remain HOLD.**

## Finding

The previous final protected RGB=0px measures equality to a frozen **Stage37 OpenCV flat-color image**, not parity with the full-color original input. Both signed frozen faces have one RGB color while the actual originals contain thousands. Thus a source-derived facial detail depiction (eyes, nose, mouth, shadows) cannot both differ from the frozen plain face and satisfy 0px final RGB mismatch to it. Preserve Stage04 geometric face silhouette and compare source RGB detail independently. Do not silently claim face identity preservation from flat-face agreement.

## Immutable sources, 340x340

| Face mask | Raden | GC001 |
|---|---:|---:|
| Signed mask pixels | 4052 | 4937 |
| Original source vs frozen flat RGB mismatch | 4047 | 4936 |
| Original distinct RGB colors | 2258 | 2467 |
| Frozen distinct RGB colors | 1 | 1 |

Arm areas also differ source vs frozen reference: Raden left 10,419 / 10,419, right 9,844 / 9,870; GC001 left 2,715 / 2,715 and right 6,486 / 6,486. A flat-color parity gate is a *composition stability* check, not a claim of original appearance fidelity. Other gradient measures and area statistics are saved in the SHA-locked JSON metrics. Color diversity by itself is not evidence every color can be semantically vectorized.

## Implementation

- `tools/research/sa1049_source_detail_dual_gate.py` independently rehashes seven signed Raden / eight GC001 private image authorities, compares original source RGB to frozen Stage37 composite only within Stage04 signed face and arms, records distinct RGB colors, edge-gradient evidence and source-vs-flat conflict; preserves the legacy per-character deployed vertex champion only as read-only metadata.
- Does not create an edited character, SVG, bitmap feature patch, facial anatomy, generative fill, synthetic material or segment inferred anatomy. One visual board is an unmodified side-by-side of user-owned originals and signed flat references, retained in approved private Drive only. **Do not commit source/comparison PNGs to public GitHub.**
- `tests/zerobase/test_sa1049_source_detail_dual_gate.py` checks frozen counts, source-authenticity rejection, no input overwrites, conflicting face gates, and audit output. 6/6 PASS with signed input folders.
- Two separate evaluations produced byte-identical JSON and comparison PNG: both SHA-256 hashes matched.

## Next research gate

1. Keep signed Stage04 silhouette, both arm region and z-order constraints as *shape protection*, not mandated single-color appearance.
2. Define an independent original-source fidelity suite, with source-measured interior color/feature consistency for hair, clothing and face. Check this suite on two characters without relying on Stage37 flat-color equality to assert identity.
3. Vectorize actual observed color boundaries from source (no generated pixels or hallucinated facial structure). Keep all polygon vertices/guard operations inside hard budgets, or explicitly report no feasible candidate.
4. Full-character human visual review and separate Stage8 historical source budget issue continue to block promotion.

## Reproduce

```
python tools/research/sa1049_source_detail_dual_gate.py --raden /signed/raden --gc001 /signed/gc001 --out /tmp/sa1049
SA1049_RADEN_ROOT=/signed/raden SA1049_GC001_ROOT=/signed/gc001 python -m pytest -q tests/zerobase/test_sa1049_source_detail_dual_gate.py
```

Production unchanged, Golden HOLD. No approval asserted for restored face details.
