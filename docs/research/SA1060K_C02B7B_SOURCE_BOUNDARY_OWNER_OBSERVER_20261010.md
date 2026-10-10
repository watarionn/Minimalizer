# C02b7b: SHA-bound two-case source-boundary and owner evidence observer

Status: **RESEARCH COMPLETE / C02 QUALITY STILL IN PROGRESS / NOT A RENDERING CANDIDATE** (2026-10-10).

Original 340×340 source PNG and Stage8 scenes are verified against immutable SHA pins for **GC001 and Raden independently**. Read-only code observes the source's Canny edges (50/120, 3×3 dilation), declared owner-mask borders, raster core, inter-owner overlap and source alpha, plus the SHA-pinned historical/current Phase04 arm-mask discrepancies for GC001. These are *independent image measurements*, not independent manually labeled semantic ground truth. No source, masks, Stage8 rings, or production files have been rewritten.

| Original signed case and part | Declared pixels | 3×3-border px | Border near original Canny | Border lacking Canny match | Alpha-zero / partial | Inter-owner overlap |
|---|---:|---:|---:|---:|---:|---:|
| GC001 right arm | 6510 | 494 | 405 | **89** | 3 / 38 | 0 |
| GC001 left arm | 2718 | 486 | 456 | 30 | 0 / 0 | 4 |
| GC001 hair | 14605 | 2530 | 2380 | 150 | 0 / 0 | 4 |
| GC001 major clothing | 3741 | 1375 | 1146 | 229 | 0 / 0 | 0 |
| Raden right arm | 9872 | 467 | 380 | 87 | 0 / 0 | 2 |
| Raden left arm | 10419 | 572 | 430 | **142** | **74 / 38** | 0 |
| Raden hair | 19503 | 1955 | 1706 | 249 | 0 / 0 | 8 |
| Raden major clothing | 3773 | 1261 | 901 | **360** | 0 / 0 | 6 |

The GC001 signed historical left-arm mask differs from current recovered Phase04 by 385 pixels, Stage8 by only 5, and current Phase04 differs from Stage8 by 390. Right-arm Stage8 vs historical/current both differ by 24. These observations are provenance comparisons, **not correctness certificates**; Stage8 lacks the historical mask input SHA so the actual producer lineage remains unproven.

**Research validation:** `test_c02b7b_source_boundary_owner_observer.py` **9/9 PASS with pinned original inputs**, including byte-identical replays, signed GC001/Raden comparisons, SHA fail-closed tamper tests, negative control for Raden historical-substitution and synthetic owner overlap. Public checkout without private assets runs synthetic tests and SKIPs real-asset fixtures. Earlier C02b7a prospective SHA sidecar independently rerun **9/9 PASS**; combined C02b7a+b **18/18** on the signed source. SHA original remains unchanged.

**No automatic mutation**: edge mismatch is not proof of false arm; source alpha is not anatomical ground truth; overlap may arise from valid layering; a raster-core point is not a semantic true positive; and historical-revision agreement is not artistic verification. These observational feature values must not automatically modify owner masks or introduce new pixels. Outcome `candidate=NONE`, `independent_semantic_ground_truth=NOT_AVAILABLE`, `release_authorized=false`.

**Next:** C02b7c should introduce externally independently supported owner/pose/semantic anchors (with uncertainty/abstention) on both signed cases and additional Approved-18/78 holdouts. Only after a candidate preserves source support and passes canonical Chromium DPR1/DPR2 plus a **new** human Golden could it be promoted. C03 original Stage8 source ring cap remains GC001 3604/1887 FAIL and Raden 2370/1412 FAIL; C04 human Golden is PENDING; C05–C08 BLOCKED. No production deploy or human signoff was performed.
