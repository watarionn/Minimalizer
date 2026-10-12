# MinimalizerPublic StructuralRecovery P0 Stage3 — source-fit selective apparel planes (2026-10-11)

**Research implementation + two-source validation PASS; overall structural/Golden/production HOLD.** Continues Draft PR #390 and separate 2026-10-11 Stage1–2, while following the original-source-only rule. No changes to the normal Public BrowserFallback entry, Local Worker, production, or `main`.

## Source-of-truth reuse and the regression we caught

- Reused the already-reviewed source-derived **SA10.36** GC001 five app​arel polygons, not a fresh shape or an invented color. External original source image SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`; inherited plan file SHA-256 `1b6394f4852036a1f058628be088609a9d6908c4242183ac4ee557da0a4787b7`.
- Independently retrieved frozen signed `signed_final_visible_lower_body_mask.png` for GC001 and Raden from the canonical SA10.41 Drive records. SHA-256 `7427189b7c246050282f10d842946e489b744b678a4875cb7a492d77daf719ee` and `5ba299e855331e17de361b0fd13760e4acc6b25f2ab6652b39f26e1c18935adb` respectively. Rechecked the original signed historical face and two arm masks and source alpha. The signed Stage8 material owner is **not** the current browser-generated authoring stage, and mere clipping does not authenticate its semantics in the new Public output.
- Original five SA10.36 panels drawn over real frozen Public Facet40 GC001 **regress** its parent-owner source-RGB squared error by **4.07%**. Previous SA10.36 success applied to a *different baseline*; we must not blindly layer its two navy panels over today's Public rendering.

## New isolated gate

`web/static/public-apparel-selective-p0.mjs` verifies the **decoded** source, frozen baseline, parent owner and protected masks by SHA-256; also verifies each externally authored polygon mask's SHA. It checks:

- Every source pixel has full alpha; all changes are bounded by the frozen signed lower-body owner and excluded from face/arm guards. RGBA alpha, external scene, masks and source input are read-only.
- All material colors are exact RGB triplets present in the original source within the corresponding positive color class; class precision >=0.60 dark, >=0.74 white, >=0.82 green.
- Green tie source bounding/area cannot expand beyond independently observed green-source support; rendered polygon geometry is supplied externally and vertex budget counted, never guessed or synthesized.
- Sequential per-panel source RGB squared error must improve by >=0.8% before a panel is adopted. Bad panels are automatically excluded; full parent-owner loss must not increase. This is a *numerical guard*, not artistic acceptance.
- Source PNG hashes and polygon segmentation provenance remain the responsibility of the separate real-case runner. The API's `evidenceRef` string alone is not a signer or proof of manual independent approval.
- No face eyes, mouth, nose or source eye patches are *newly* rendered by Stage3. Already wrong Public eye-like patches outside signed face are **unfixed**.

## Verification

- `tests/js/test_public_apparel_selective_p0.mjs`: **15 synthetic Node tests PASS** (SHA tampering, off-parent and face collision, source alpha, invented colors, unsupported Raden lacing classification, quality-regressed source, vertex cap, determinism, true no-op control, rejection of claimed production authority).
- GC001 real 340x340 original + historical signed Stage8 owner + signed face/arms + frozen real Public Facet40: navy panels **both rejected**; white shirt 2 and green tie 1 **accepted**. 4,260 actual RGB pixels changed, source owner squared error **140,777,117 → 139,138,280**, a **1.16%** decrease. All values are conditional on that frozen reference and are *not* visual quality/Golden passes.
- Raden: independent real source and signed lower-body owner, no matching uniform material panels; **0 changes**, squared error **4,434,396 unchanged**. This is a cross-character negative control, not Raden costume reconstruction.
- The original five all-at-once panels failed and were **not** adopted. Present masks/preview/source pixels stored only in private Drive, never GitHub.

## Status and residual work

**P0 artistically still HOLD.** Facet40 remains visibly low quality. Whole-body silhouette, sleeves/ruffles, collar, goggles, actual Raden bow/corset/held object, and eye-like patch suppression need genuine source-part authority and geometry, not brighter color metrics. Original Stage8 vertex budgets remain GC001 3604 > 1887 and Raden 2370 > 1412. Chrome module execution, SVG/resvg geometry, iPhone Safari, human Golden, license and rollback gates remain unpassed. Not imported into `public-route.js`/`browser-fallback.js`.

All original and new mask PNGs, original source comparisons, private case runner/scripts and checksum manifest: `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage3_20261011`.
