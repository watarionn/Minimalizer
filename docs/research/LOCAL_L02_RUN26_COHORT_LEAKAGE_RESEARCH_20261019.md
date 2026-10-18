# Local L02 Lane A: Run26 cohort leakage and class32 deletion-only bounds (2026-10-19)

Research-only. L02 HOLD / Golden HOLD / L03 NO_GO / production NO_GO.

The existing per-character holdout manifest preflight verifies prediction freeze precedes its own annotation. This is insufficient for a *cohort*: annotations from one character can be inspected before another character's prediction is frozen. A new cohort-level fail-closed guard must require **latest prediction freeze < earliest annotation** and hypothesis freeze before all predictions, reject normalized ID reuse and source/prediction/annotation byte-digest reuse, and preserve unknown as unknown. Synthetic red/green regression demonstrates the cross-case leakage window.

A separate exact rational upper bound for **deletion-only class32 edits of the frozen candidate** treats every unlabelled candidate pixel optimistically as a true positive, assumes an oracle removes all class32 known false positives, and leaves nonclass32 known false positives fixed. H04 still has 3,704 unavoidable known false-positive pixels (of 3,875 original known FP), including underlayer 2,091, accessory 933, lower body 607, arm 65, hair 8. This upper bound is not achieved quality, is not an edit or new inference, and does not generalize to unseen characters. H06/H08 have zero *known* fixed nonclass32 FP but unknown pixels and absent independent holdout prevent any PASS.

Local source-free Run26 suite: 502/502 PASS (450 inherited + 52 new); no new original-image inference, no Golden or iPhone approval. Private images, NPZ, coordinates, masks and private digest mappings must remain Drive-only. Do not merge until source and tests are present on the branch and independently verified.
