# Face Parts Only v1 (2026-10-08)

**Scope:** independent original-image Face Parts research, NOT authorized production Minimalizer Core. User specifically rejected v2–v4 face-wide skin/color overlays because they cover bangs and the face boundary. The new code does not call `face_plan` or paint any face-sized shape.

Reproducer: `tools/research/face_parts_only_v1.py`. Regression: `tests/test_face_parts_only_v1.py`.

The source is GC001 original, SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, with Phase03/04 source-observed subject, face and hair masks. Part candidates are individual original-observed connected pixel sets: two eye-color islands, restricted nose-color pixels, restricted mouth-stroke pixels. Hair is excluded from all candidates; eyebrows are **unverified**, not inferred. Candidate masks and SHA hashes are saved for audit. These Kyoko-specific optical heuristics are not a general-purpose face parser.

A / Preserve: Build canvas from exact original image. Optionally apply SHA-verified previous D-style art ONLY to pixels that are inside subject but outside both face and hair; original face and bangs are left intact. Source face pixel differences: 0. This is a visibility/identity research baseline, and remains NOT allowable as a Core result because Core facial-detail rendering is forbidden.

B / Individual parts only: Keep the same canvas and only change pixels inside previously observed eye/nose/mouth micro-component masks, each to a pixel RGB medoid that exists in that original source component. On real GC001, **170 pixels changed**, **0** pixels outside approved feature masks changed when comparing A to B; **0** face-nonfeature or hair pixels changed from original. No new eye geometry or skin-plane overlays; still not a production/Core-allowed image because it deliberately retains observed facial details for experimentation.

C / Feature Suppression: **BLOCKED_FAIL_CLOSED**. A missing face feature requires a verifiable observed skin surface *beneath* the source eye/nose/mouth pixels. No such pixels exist in the single flat source, so painting estimated skin would amount to inventing missing imagery. No C preview is generated; the refusal is explicit in manifest. User policy forbids generative img2img, new facial-feature invention and whole-face recoloring.

A/B real PNGs, four individual diagnostic masks, `gallery_A_B_C_decision.png` (shows Original, A, B with blocked C in caption), and `manifest.json` are saved in `chatGPT及びCodex用/Minimalizer/FacePartsOnly_v1_20261008/`, Google Drive folder `17dRMLh7QJXpyV7m5tSybJx7cnqg5xTrg`. Gallery SHA-256 `5e624a1df73add8195d8d0763b04f91c7468166d427d662672e9ef2dc49a4590`.

Unit regression: **31 PASS** combining Face Parts Only v1 and previous Semantic Mixer v1-v3 research tests. Full production suite is separate and should not be implied.

**Important quality caveat:** The above A and B images still have eyes and other existing facial details from original. That is intentional for *diagnostic identity preservation*, not approval to deploy as a Minimalizer rendered result. The current Golden gate explicitly forbids internal facial drawing. The candidate C could not safely satisfy that rule without missing-pixel invention, so no image was fabricated.

Next research is original-space observer mapping for brows and independently verified removal without inpainting, or a true no-feature vector rendering that does not need to fill back hidden pixels. Do not regress to painting a skin-colored oval. No change to Local PWA or Public runtime.
