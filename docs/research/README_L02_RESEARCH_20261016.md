# Minimalizer Local L02 research handoff, 2026-10-16

**Formal L02 HOLD; production NO_GO.**  The provided sources are private, and the public code here contains no images, hand polygon coordinates or masks. The H04 alpha overshoot exception is narrowly pinned to the exact user-reviewed H04 original and full-trace digest, not a global acceptance-threshold relaxation.

All commands assume this research code is placed in `watarionn/Minimalizer` at the specified `tools/research`, `tests` and `docs/research` paths. `benchmark_leave_character_out.py` imports the pre-existing `tools/research/local_l02_manual_supervised_shadow.py` introduced in PR #402.

Run fail-closed synthetic regression tests: `python tests/test_local_l02_manual_intake.py`, `python tests/test_reviewed_annotation_intake.py`, `python tests/test_local_l02_reviewed_transfer_benchmark.py`. Total **52/52 PASS** in the 2026-10-16 development sandbox.

With authenticated private inputs in a directory, run:
`python tools/research/verify_reviewed_annotations.py <private-input-dir> <private-output-dir>`
`python tools/research/benchmark_leave_character_out.py <private-input-dir> <private-output-dir>`

Original private names used: `H04_original_signed_trace (1).json`, `H06_trace.json`, `H06_trace.svg`, `H08_trace.json`, `H08_trace.svg`. The tool validates signed source bytes and SVG/JSON polygon parity. Never commit these files or their generated NPZs to GitHub.

`tools/research/color_cluster_shadow.py` is retained as a reproducible **REJECTED** H04-adjusted experiment. Do not wire it into production. H06/H08's partial annotations are not a fully signed segmentation and unlabelled pixels must remain `unknown` for trustworthy metrics.
