# MinimalizerPublic StructuralRecovery P0 Stage106–115: human handoff integrity and source-bound color SVG preview

2026-10-13, research branch `research/public-structural-recovery-p0-part-preservation-20261011`, Draft PR #390. **Golden HOLD; NEVER merge/deploy, nor alter main, Local Minimalizer, ordinary Public engine or Stage51 production comparison.** The original-image no-inpainting/no-original-extra-content policy remains mandatory.

## Stage106–110: original full-frame human-review readiness, NOT human review itself

`web/static/public-human-review-evidence-106-p0.mjs`:
- **106:** Source-identity-locked cases GC001/Raden and two independent human-reviewer **empty enrollment slots**, never auto-enrolled. An ECDSA key or upload identity is insufficient to prove an actual distinct person.
- **107:** Source original opaque/nonopaque pixel and background/face/uncertain proposal audit for every original pixel; no syntactic proposal promoted to semantic truth.
- **108:** 32px original tile coverage and explicit count of source opaque pixels with no label proposals, including opaque background.
- **109:** Two source-bound untrusted drafts are independently validated, all tiles/abstentions/conflicts counted, duplicate drafts denied. User annotations remain *untrusted* until real external human verification.
- **110:** Entire release gate always HOLD, even if draft JSON contains self-proclaimed `approved`, `humanReviewed` or fake identity flags.

**No true independently authenticated human labels were supplied.** Real human semantic pixels independently verified: **0**.

## Stage111–113: untrusted original-color whole-frame *partial-proposal* prototype

`web/static/public-untrusted-fullscene-preview-p0.mjs`:
- **111:** Source RGB is taken literally from the *first original eligible RGB pixel within each proposed class*, never guessed or generated; only source alpha255 labeled pixels can appear, face/background **proposal labels** and totally unreviewed pixels remain transparent. Actual subject/background semantics are still unknown.
- **112:** Bitwise source membership via Stage49 exact rectangle cover for each proposal class. All quantized-color RGB mismatches to original per-pixel RGB are **explicitly counted**; source-first-pixel palette is NOT an exact RGB image reconstruction.
- **113:** Rebuild-and-verify the source SHA, proposal labels SHA, union membership SHA, complete SVG bytes, rectangle list/vertices and all release veto booleans. Forged positive review fields and transparent source-label additions fail closed.
- No SVG is emitted through any normal product path. This is a standalone **private inspection** tool.

## Stage114: real private SHA-pinned GC001/Raden Chrome rehearsal

Private script `stage114_real_source_untrusted_preview.mjs` seeded labels **exclusively from the preexisting historical left/right-arm signed owner masks**, then filtered face mask, historical background observation and original source alpha255. All retained pixels were marked `uncertain_subject`, explicitly **NOT manually human reviewed, not necessarily skin/sleeve anatomy and not a full character**. The precise original RGBA and private SVG output were never committed publicly.

| Original | Historical source-only candidates | Preview SVG UTF-8 bytes | Rectangles / explicit vertices | Original RGB different from single sampled source RGB | Numeric historic Stage8 cap |
|---|---:|---:|---:|---:|---:|
| GC001 | 9,160 / 115,600 | 3,814 | 220 / **880** | **9,159 / 9,160** | 1,887 |
| Raden | 20,177 / 115,600 | 4,082 | 231 / **924** | **20,176 / 20,177** | 1,412 |

True Chrome raster proof 340 and 680 on BOTH originals: **4/4 zero missing, extra or fractional alpha, 0 wrong RGB relative to the sampled class palette**. This is exact *synthetic candidate membership*, not original RGB fidelity. Source RGB mismatches are nearly 100%, a material color-quality failure. A vertex count under numeric caps for small historical fragments DOES NOT mean real full-body budget compliance or good image quality. Older real Stage8 full-character geometry STILL GC001 3604>1887 and Raden 2370>1412 (FAIL). No actual human anatomical signoff.

## Stage115: research-only CI and canonical Drive preservation

`tests/js/test_public_human_stage106_115_p0.mjs` adds **20** Node regression tests, including source tampering, human enrollment spoof, all-pixel agenda, alpha exclusion, exact observed source palette, RGB mismatch accounting, bitmap identity and veto. Starting point was 487 PASS at Stage105; actual GitHub Actions run 38283964179 / job 114927740900 on executable SHA 96410ec0aff15228b473dded99a66fe56c74d052 confirmed **507 PASS, 0 failed, 0 skipped** from decoded runner log.

Original private source/PNG/masks and SVG derived from source stay in **PRIVATE** Google Drive ZIP. GitHub retains only source-free JS/tests/research docs. Next Stage116+: actual separate enrolled humans must hand-review entire original body/background/arms/hands/sleeves/skin/hair/necktie/face suppression and independently adjudicate, then a *new full-subject* scene candidate should be checked for honest polygon budget, perceptual/color/edge fidelity, physical iPhone Safari HTTPS and rollback. Current PR stays Draft/Golden HOLD.
