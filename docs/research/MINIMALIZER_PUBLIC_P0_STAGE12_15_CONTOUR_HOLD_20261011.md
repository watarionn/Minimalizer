# MinimalizerPublic StructuralRecovery P0: Stage12–15 source-exact contour research

Date: 2026-10-11 JST. Status: **STAGE12 EXACT SOURCE VECTOR PASS / STAGE13 SIMPLIFIED VECTOR REJECTED AT DPR2 / STAGE14 EXACT SVG 4/4 PASS / STAGE15 PRODUCTION DRAFT HOLD**.

## Source and authority

Replays the SHA-256-pinned private 340x340 GC001/Raden `source.bin`, `baseline.bin`, historical Stage04 signed `face.bin` and source-observed color-class feature masks from Stage5 (drive under `chatGPT及びCodex用/MinimalizerPublic`). Observed accessory semantics are **not independently human signed**. Inputs never modified. No generative model, image reconstruction, interpolation outside source, or face anatomy rendering. Public repo stores source-free code and reports only.

## Stage12: exact traced contour graph

`web/static/public-source-contour-p0.mjs` creates clockwise per-pixel edge loops, including holes and corner contacts; merges collinear grid-edge vertices without changing any covered pixels; checks the path reproduces the entire byte-verified original observation mask with zero missing or extra pixels. Returns SVG path data, fill-rule `evenodd`, explicit vertex count and machine-readable nonpromotion metadata.

Real two cases, independent original hashes and signed historical face:

| Case | Prior Stage7 rectangle coverage | Stage12 vector coverage | Stage12 feature vertices | Raw pixel boundary edges |
|--|--:|--:|--:|--:|
| GC001 eyewear highlight | 42.97% | **100%** (1,173/1,173) | 398 | 636 |
| Raden bow + corset observations | 34.94% | **100%** (5,049/5,049) | 1,968 | 3,288 |

The RGB color medoid of each observed part matches Stage5. Real Chromium SVG rendered foregrounds, composited on frozen Facet40, produce **identical RGBA bytes to the recorded Stage5 accepted research previews** for both cases. No embedded bitmap in vector, no user original images on public GitHub. This is not an independent qualitative improvement over Stage5, just a lossless vector representation of its large-part observation.

## Stage13: aggressive vertex reduction vetoed at DPR2

`public-safe-contour-simplify-p0.mjs` tries bounded RDP-like polygon simplification with pixel-centre source-only raster audit. The stable `eps=.5` research candidates remove vertices while preserving the 340px raster masks exactly:

- GC001: 398 → **296**; Raden: 1,968 → **1,614**; source mask coverage 100%, zero 340px spill.
- BUT Chromium 680px shows **GC001 74 outside-source pixels / 148 mismatching mask pixels**, **Raden 67 outside-source pixels / 217 mask mismatch** due diagonal-edge rasterization. **Reject simplified shapes** for promotion or default preview. Do not report 340px-only result as full parity.

## Stage14: real Chrome 340px / DPR2 680px hard gate

`public-svg-dpr-guard-p0.mjs` treats every nonzero pixel drawn outside the exact signed source observation as disallowed and demands exact binary coverage at both resolutions. Verified with Chromium 144.0.7559.96, via real Playwright browser screenshots of inline SVG (not fake screen estimators):

| Source | Source-exact SVG @340 | Source-exact SVG @680 | Simplified @680 |
|--|--|--|--|
| GC001 | 0 mismatch / 0 spill | 0 mismatch / 0 spill | **FAIL** 74 spill |
| Raden | 0 mismatch / 0 spill | 0 mismatch / 0 spill | **FAIL** 67 spill |

This confirms only source-part isolated SVG rendering, not full scene, secure-origin native WebCrypto, production Public route or mobile Safari.

## Stage15: protected research selection + budget

`public-contour-research-gate-p0.mjs` preserves the **exact** contour candidate for research and rejects the simplified candidate at DPR2. It counts Stage8 existing owner vertices and additional feature ring vertices explicitly, including conservative combined estimates GC001 3,604+398=4,002 vs cap 1,887 and Raden 2,370+1,968=4,338 vs cap 1,412. These sums are conservative, not a substitute for complete composited SVG audit. Original Stage8 alone already fails budgets; drawing more paths cannot be represented as a production budget PASS. Human Golden, independently attested costume ownership, whole-image silhouette/arms, external face features, real secure origin, iPhone Safari, license and rollback still HOLD. No main/production/Local Worker edits.

## Tests and evidence

18 new Node synthetic tests PASS: mask SHA, holes, tangent rings, face and owner crossing, changed pixel budget, negative simplified SVG DPR2, source-only raster coverage and release guards. Real source independent JS replay + Chromium PNG captures + source-mask/alpha byte comparisons and SHA-256 private manifests reproducible. Browser DPR screenshots are private. All source images/masks and real-image previews stored only in Drive. **Stage12–15 is a research milestone, not product-quality sign-off.**

Next focus: semantic owner attestation for goggles/bow/sleeve, true silhouette/arm/ruffle structural recovery and source-derived vertex-budget reduction; avoid claiming tiny 1px contour compaction is a solved large-structure defect. Any curve-only raster anti-alias must pass strict source mask at both DPRs, or be vetoed.
