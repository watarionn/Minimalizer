# BrowserFallback v29: Frozen Anime Corpus Spot-check and Heavy-Model Safety Gate

Date: 2026-10-09
Status: **SPARSE ORIGINAL-SOURCE REVIEW PASS / ANIMESEG + ARM SEMANTIC HOLD**
Draft PR: [#299](https://github.com/watarionn/Minimalizer/pull/299), based on v28 PR #297. Public Facet v15 and Local Worker remain unchanged.

## Goal and constraints

V28 found a real cached AnimeSeg v3 Mask2Former mask for Kyoko (same exact source as v27) but no source-aligned AnimeSeg masks for Noel or Ririka. AnimeSeg v3 has 12 classes, including hair_main, clothes and accessory, but NOT left_arm or right_arm. The Python checkpoint is 431,643,704 bytes. In the v29 real Windows preflight, free physical RAM was approximately 2.0GiB; the conservative safety gate requires 5GiB to attempt later isolated inference. This threshold is a research protection policy, NOT a measured actual peak memory requirement. Therefore no new AnimeSeg inference, model conversion, downloads, package installations, process termination or OS tuning were performed. Both cached weight and source ZIP passed exact SHA verification.

## Frozen sources and provenance

The genuine frozen v27 source/stage archive SHA-256: 91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39.
- Noel source SHA: f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26
- Ririka source SHA: 6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914
- Noel Facet SHA: d369aea0c89fc50918efaa0221a3445a642091e748ad7f86ab873edc6854e6a5
- Ririka Facet SHA: badb7de356d1672d98399df3ea3800c6d42c10a34d6eca5ab76375773413ea45
- Actual cached AnimeSeg v3 model SHA: f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394 (no model copied).

## Noel/Ririka evidence: small manually selected original-visible pixels only

The source and v27 accepted-class images were inspected side by side. Five hair and five garment points per character were chosen as inspectable, opaque, fully source-visible coordinates. This is a *falsification spot-check*, NOT representative ground truth, full segmentation accuracy, or reliable independent semantic masks.

| Input | Hair points misclassified as clothes | Hair abstained | Garment correct | Garment abstained |
|---|---:|---:|---:|---:|
| Noel | 3 / 5 | 2 / 5 | 0 / 5 | 5 / 5 |
| Ririka | 3 / 5 | 2 / 5 | 3 / 5 | 2 / 5 |

The black accepted-class preview means **unclassified OR background**, never authoritative background. These pixels count as abstentions, not correct negative examples. The clear photographic-model false positives include Noel's silver hair and Ririka's red/pink hair. An initially chosen Ririka point on sunglasses was caught during review, moved onto a genuinely visible hair strand and re-evaluated. The final evidence includes every fixed anchor coordinate, original source, colored labels and two image review panels.

v27 Pose Lite returned no validated pose for any of Kyoko/Noel/Ririka. The separate ZeroBase Phase4 RTMLib WholeBody success used different source-image hashes, so those arm points CANNOT be silently transferred to current browser images. The current default Windows Python does not have RTMLib installed or source-verified Noel/Ririka pose outputs. The source [RTMLib WholeBody project](https://github.com/Tau-J/rtmlib) documents lightweight CPU ONNXRuntime models and is only an unvalidated future candidate.

## Code, tests and source of truth

- tools/audit_browser_anime_corpus_v29.py: exact frozen ZIP/source/Facet SHA, point-by-point labels, separate abstention and misclassification, manually reviewable original/class annotated gallery, CSV/JSON/report. It cannot paint Minimalizer output or add anatomy.
- tools/gate_browser_anime_inference_v29.py: independently read real Windows physical RAM, streaming SHA/size of existing 431MB checkpoint, archive SHA, conservative free-RAM requirement. Never imports torch or launches inference. When resources are insufficient, records explicit HOLD.
- tools/verify_browser_anime_corpus_v29.py: repeat exact original-source sparse audit in a separate directory and compare **14 output files byte-for-byte**, with a SHA record. RAM snapshot intentionally excluded from replay equality because free RAM changes over time.
- tests/test_browser_anime_corpus_v29.py: 5 synthetic contract tests for immutable sources, source anchor/schema, refusal on bad models and lower RAM thresholds, unchanged frontend.
- Existing browser research workflow runs the new tests and inherited v13-v28 regressions. No extra workflow, runtime dependency, default changes or heavy model copy.

## Decision

**V29 sparse benchmark and safety/replay verification are complete. Global semantic quality and arm reconstruction remain HOLD.** Noel/Ririka AnimeSeg v3 source masks, unseen holdout, independently reviewed full-image semantic truth, left/right arm pose corroboration, browser ONNX conversion and Chrome WASM memory/latency are not done. Do not claim they passed.

The highest-quality available production stays Facet v15. No public merge/deploy, no Local Worker changes, no facial-feature synthesis, no img2img, no fabricated parts. Future work must get accurate AnimeSeg/pose observations under a verified memory-safe compute budget and then re-test these frozen errors. The project cannot substitute speed of phase closure for visible improvement.

## Preserve

Canonical Google Drive location: chatGPT及びCodex用/Minimalizer/AnimeCorpusSafetyV29_20261009. Link is recorded in PR once created and cloud-visible.
Outputs: original/no-change Facet/class images, 20-point source QA panels, 2x4 source/class gallery, metrics JSON, CSV, resource guard JSON, reproducibility SHA report, code, tests, detailed handoff, artifact digest manifest.
