# SA7.31 Role-localized Golden Gap Attribution — 2026-10-06

Status: EVALUATOR PASS / GC001 ATTRIBUTION COMPLETE

SA7.31 adds an evaluation-only role-local gap attribution tool. Golden is read only inside evaluation. No Golden coordinates, colors, masks, or geometry are promoted into production inference.

The evaluator measures per semantic role:
- area ratio
- Lab mean absolute error
- edge disagreement
- whole-image weighted contribution

GC001 evaluation uses the SA7.30 HOLD candidate and existing Phase-04 semantic masks. Background is an evaluation-only complement of the semantic foreground union.

## Ranked GC001 contributors

1. background_complement — weighted 0.16390, 60,557 px, Lab 69.40, edge disagreement 0.041
2. hair — 0.04362, 17,541 px, Lab 34.09, edge 0.154
3. head — 0.03932, 17,229 px, Lab 32.26, edge 0.137
4. lower_body — 0.03050, 12,606 px, Lab 43.60, edge 0.109
5. right_arm — 0.01659
6. torso — 0.01390
7. major_clothing — 0.01133
8. face — 0.00693
9. left_arm — 0.00598
10. unknown — 0.00512
11. neck — 0.00372
12. accessory_or_held_object — 0.00060

The background/composition contribution is about 3.8x the hair contribution and about 14.5x the major-clothing contribution. This explains why SA7.30 palette recovery improved local structure but barely moved the global Golden distance.

Caveat: background_complement is an evaluation proxy, not a production semantic part. It can contain unclassified foreground and overlap effects.

## Decision

SA7.31 is evaluation infrastructure only and is safe to merge.
Do not tune production from Golden coordinates.

Next: SA7.32 Source-only Background / Composition Abstraction. Build a source-derived background semantic model (dominant field, subject occupancy, negative-space relationship) and validate it without Golden authority. Golden remains evaluation only.
