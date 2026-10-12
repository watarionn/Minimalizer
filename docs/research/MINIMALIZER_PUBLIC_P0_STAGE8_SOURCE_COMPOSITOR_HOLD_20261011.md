# MinimalizerPublic StructuralRecovery P0 Stage8 — bounded source-part compositor (2026-10-11)

**PROTOTYPE COMPOSITION TEST PASS / VISUAL AND RELEASE HOLD.** `web/static/public-source-compositor-p0.mjs` reuses Stage5 `replaySourceFeatureSurfaces` for SHA-pinned source RGB medoids, shape masks and original face guard, and Stage6 `blankSignedFace` for a featureless face. No reconstructed eyes, nose, mouth, inferred color, generative fill or bitmap embedding is used.

Generated rectangles are independently revalidated against their original source-observed feature mask, clip-box bounds, no overlapping ownership, signed face, pixel accounting and total vertex accounting before painting. Pixels not in an accepted part or the historically signed face are unchanged from the frozen Public Facet40 input; alpha is unchanged everywhere. Refused conditions are independently tested. The face is represented only by source-observed skin medoid; small eye-like fragments *outside* the signed face remain unresolved and cannot be claimed removed.

Real GC001: 504 feature pixels and 4,937 signed face pixels altered, 5,441 changed RGB pixels total. Real Raden: 1,764 feature pixels and 4,052 signed face pixels altered, 5,816 changed RGB pixels total. The exact output is repeated byte-identically. **This stage does not fix silhouette, collar, sleeves, arm attachment, held object or Raden bow topology.**

No production imports, main edits, Local Worker changes or data reconstruction. Prototype is research-only and must remain on Draft PR.
