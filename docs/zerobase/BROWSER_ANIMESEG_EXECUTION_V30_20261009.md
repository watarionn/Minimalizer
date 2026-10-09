# BrowserFallback v30: Noel/Ririka AnimeSeg v3 CPU inference
Date: 2026-10-09

Status: **REAL CPU INFERENCE PASS; SEMANTIC RENDER QUALITY HOLD**.
Parent: research/browser-anime-corpus-gate-v29-20261009, Draft PR #299.
Branch: research/browser-animeseg-execution-v30-20261009.
Production Public Facet v15 and Local Worker unchanged.

## Updated user constraint
The previously enforced minimum 5 GiB available physical RAM threshold was **removed by explicit user instruction**. This does not authorize killing unrelated workloads or replacing OS/system settings. v30 reuses the existing isolated Python 3.11 anime_seg 0.3.8, transformers 4.57.6, CPU torch environment, without installing packages. Two cases are run *sequentially*, with a nine-minute per-worker timeout and original source SHA verification. The old v29 safety script is a historical artifact, not the v30 execution gate.

## Verified original source and actual results
The frozen v27 stage archive has SHA-256 91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39.
Noel original source SHA-256 f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26.
Ririka original source SHA-256 6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914.
Both isolated workers returned exit code 0, status ok, authority false, exactly 12 known classes and unknown_pixel_count=0.

| Source | Hair pixels | Clothes pixels | Accessory pixels | Model mask SHA256 |
| --- | ---: | ---: | ---: | --- |
| Noel | 15194 | 21777 | 18191 | 859da4900b7d509ad9a87fb9c12573e454b7c42a2dfebbc6da94d053d6e4e7a2 |
| Ririka | 13569 | 45200 | 7935 | 13f64e315ced17dad41e8a1187c4cf5503a884d70af9e7c9de4f0ee6fc070190 |

Frozen v29 original-source sparse probes use 5 hair and 5 garments per case, not exhaustive image truth. AnimeSeg comparison at these fixed probes:
- Noel: 7 correct, 3 wrong, 0 background/abstention.
- Ririka: 8 correct, 1 wrong, 1 background/abstention.
The photographic six-class model's same sparse probes had Noel hair incorrectly clothes 3/5, clothing correct 0/5; Ririka hair incorrectly clothes 3/5, clothing correct 3/5. Comparing these is a tiny falsification test, not global accuracy.

## Qualitative review
The 2x4 source/Facet/AnimeSeg/sparse probe gallery shows far better large hair-clothing decomposition than the previous photographic accepted-class map. Accessory and arm areas remain imperfect; Noel's large shoulder/armor/accessory masses and Ririka's white fluffy sleeve are not separately labeled reliably. The AnimeSeg 12-class taxonomy does not distinguish left versus right arms; the existing pose result is insufficient. No generated facial internals, recoloring, or altered silhouette. All semantic ownership remains UNBOUND.

## Preservation
Source, unchanged frozen Facet, actual predicted 12-class PNG, per-case worker JSON/stderr, computed sparse review, montage, source audit code, ZIP and SHA-256 manifest preserved under chatGPT及びCodex用/Minimalizer/AnimeSegExecutionV30_20261009:
https://drive.google.com/drive/folders/1Estz4ykeVJJLznhVjHshIeZhiC2v0GGR

## Gate and next
V30 real-inference acquisition is **complete**. Do not use masks as final output or merge this research branch to main. Next: independent holdout/full-region semantic assessment and pose/arm corroboration, then seek actual browser ONNX/WASM compatibility, memory and latency. Removed 5GiB preflight remains removed unless the user asks to reinstate it; runtime failure may still be recorded but should not be converted into a silent threshold.
