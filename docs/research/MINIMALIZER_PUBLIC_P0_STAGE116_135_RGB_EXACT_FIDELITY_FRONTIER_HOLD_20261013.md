# MinimalizerPublic StructuralRecovery P0, Stage116–135: source RGB losslessness vs polygon budget

2026-10-13 JST, repo `watarionn/Minimalizer`, Draft PR #390, branch `research/public-structural-recovery-p0-part-preservation-20261011`. Scope only isolated **nonproduction public-browser RESEARCH**. Golden HOLD. Never change main, normal Public, Stage51 or Local Minimalizer. NEVER invent missing anatomy or fill source-unobserved pixels.

## Stages116–124: realistic independent-human-review intake (human approval still absent)

- **116** full-original source RLE manual draft intake (source SHA and packet SHA bound).
- **117** actual original RGB/alpha source tamper reject.
- **118** original-frame opaque/nonopaque/label-proposed/unreviewed pixel conservation.
- **119** full-image 32px review grid including border and 121 tiles at real 340x340 size.
- **120** untrusted JSON's self-declared human/Golden/production claims fail closed.
- **121** independent human identity slots remain empty: no actual person enrolled.
- **122** side-by-side exact source-bound review draft conflict ledger.
- **123** unreviewed/abstained pixels remain unresolved, not consensus.
- **124** duplicate untrusted draft not accepted as two independent reviewers, and production gate never inferred from `approved`.
- Source-free module: `web/static/public-manual-intake-audit-p0.mjs`, using Stage77 and Stage93 validators. No anatomy inferred from RGB source gradients, historic owner masks, duplicate labels, or cryptographic key ownership.

## Stages125–134: EXACT original RGB SVG diagnostic, intentionally partial and untrusted

- **125:** `web/static/public-source-rgb-lossless-preview-p0.mjs` source-original SHA validated, roles background and face excluded, only originally alpha255 untrusted candidate pixels.
- **126:** label and literal-original-RGB-keyed contiguous horizontal runs, conservative vertical rectangle extension. No color produced unless present in original RGBA.
- **127:** exhaustive original RGB/alpha membership raster replay from rectangle geometry; no overlap, no new pixels, no wrong RGB.
- **128:** alpha0 or partial alpha cannot be painted by this candidate.
- **129:** byte deterministic complete SVG, original labels SHA binding and negative tamper tests.
- **130:** compare original RGB exact output to previous Stage111 first-original-RGB-per-class quantization.
- **131:** explicit rectangle 4-vertex cost and byte size, not equating partial mask to whole-body budget.
- **132:** original RGBA SHA mutation rejected.
- **133:** **true private desktop Google Chrome, source-original RGB pixel-by-pixel proof at 340 and 680**, both GC001 and Raden: 4/4 checks, missing/extra/partial-alpha 0, **0 RGB differences against original RGBA at EVERY SELECTED pixel**. This replaces earlier comparison only to the sampled palette.
- **134:** `web/static/public-source-rgb-frontier-p0.mjs` checks that the two partial previews share exact original SHA, labels SHA and membership and reports the actual fidelity/vertex/byte tradeoff. This is NOT global optimality proof.

### The decisive real-original tradeoff

Input proposal: **only historic untrusted arm-owner candidate masks**, marked `uncertain_subject`. This does **not** authenticate arms, sleeves, full person/body or source background. Of all 115,600 pixels per source, selected: GC001 **9,160**, Raden **20,177**.

| Original | Method (same SHA+labels) | RGB differing from ORIGINAL | SVG bytes | Explicit rect vertices |
|---|---|---:|---:|---:|
| GC001 | Stage114 one original sampled color for proposal class | 9,159 / 9,160 | 3,814 | 880 |
| GC001 | Stage133 original RGB exact per selected pixel | **0 / 9,160** | **257,837** | **27,496** |
| Raden | Stage114 one original sampled color | 20,176 / 20,177 | 4,082 | 924 |
| Raden | Stage133 original RGB exact per selected pixel | **0 / 20,177** | **398,021** | **67,572** |

All four original-source SVG real Chrome checks 1x/2x: selected RGB mismatch **0**, missing alpha **0**, unexpected alpha **0**, fractional output alpha **0**. **This establishes exact source RGB fidelity ONLY for selected historic owner candidate pixels.** Underlying Stage114 colors for non-first source pixels were far from original. The fully color-exact rectangle method has extraordinarily high explicit geometry costs. Two tested partial candidates do not meet both numeric stage8 limit and 0 original RGB differences; this does not prove no better algorithm is possible.

Historic **whole-character** Stage8 polygon budget remains GC001 **3,604 > 1,887**, Raden **2,370 > 1,412**: HOLD. Comparing subset-only 880/924 vertices to whole-character caps is prohibited. Comparing 27,496/67,572 partial-only vertices to the caps is a diagnostic, not a complete-scene proof. Pixel fidelity and shape-semantic human Golden both remain mandatory.

## Stage135: CI, isolation, handoff

`tests/js/test_public_stage116_135_p0.mjs` adds **26** new Node regressions to the prior Stage115 **507** tests (expected actual total **533**, confirm **real GitHub CI** before reporting). Archives:
- Source-free code/tests/research/handoff in GitHub Draft PR #390 and public ZIP.
- Actual original-derived exact RGB SVG, original RGBA SHA/label SHA, source Chrome pixel proof, cost-frontier JSON and replay scripts in **PRIVATE Google Drive ZIP only** under `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage116_135_20261013`.
- No main, Local, Stage51 or production change, no merge/deploy.

**Remaining**: real two distinct independently enrolled humans must manually classify both full originals (subject/background, arms/hands, skin/sleeves, hair, collar/necktie, face-parts suppression, clothing internal colors), independently adjudicate and approve. Only then is whole-character source-constrained SVG, true total polygon cap, full-body Golden, physical iPhone Safari HTTPS and rollback meaningful. Next Stage136+ must work on optimizing a **source-exact or measured bounded-color-error** adaptive geometry on only legitimately reviewed subject pixels; report RGB error and vertices side-by-side. Keep Golden HOLD throughout.
