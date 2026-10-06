# SA7.40 Remaining Gap Re-attribution — 2026-10-06

Status: EVALUATION COMPLETE / NEXT TARGET CONFIRMED

SA7.40 re-runs the existing role-local Golden-gap attribution on the SA7.39 final candidate, after background geometry, source-supported Feature Survival, canonical semantic mass integration, and image-level face neutralization have all been restored in one canonical path.

Golden remains evaluation-only.

## SA7.39 role-local ranking

1. background_complement — 0.09093
2. hair — 0.04331
3. head — 0.03837
4. lower_body — 0.03069
5. right_arm — 0.01807
6. torso — 0.01394
7. major_clothing — 0.01114
8. left_arm — 0.00679
9. unknown — 0.00502
10. face — 0.00482
11. neck — 0.00367
12. accessory_or_held_object — 0.00057

## Change from SA7.31

The largest background/composition contribution moved from about 0.16390 to 0.09093, a reduction of about 44.5%.

Other major roles remain broadly similar:
- hair: 0.04362 -> 0.04331
- head: 0.03932 -> 0.03837
- lower_body: 0.03050 -> 0.03069

Face contribution improved after SA7.38:
- face: 0.00693 -> 0.00482

## Interpretation

The recent safety work did not merely move error from one subject role to another. The background reduction is real, Feature Survival is restored, and face error is reduced.

However background/composition remains the largest single remaining contribution, still about:
- 2.1x hair
- 2.4x head
- 3.0x lower_body

The next visual work should therefore continue on source-only background representation before returning to hair/head/lower-body geometry.

## Caveat

`background_complement` is still an evaluation proxy: the complement of the union of current Phase-4 semantic masks. It can include unclassified source content. It must not become a production semantic authority by itself.

## Next

SA7.41 Background Residual Field Attribution.

Decompose source-supported border-connected background evidence into palette/connected components and measure which source fields explain the remaining background gap. Do not tune production using Golden coordinates or colors.
