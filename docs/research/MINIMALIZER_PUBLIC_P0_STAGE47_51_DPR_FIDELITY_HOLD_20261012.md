# MinimalizerPublic P0 Stages 47–51 — Native origin, two-resolution SVG and original RGB ledger

Scope: `watarionn/Minimalizer` research-only branch, Draft PR #390. **Main, production Public and Local Minimalizer unchanged.** Source original is sole authority. No generative fill, content invention, new feature, inferred skin/hair label, or source-absent paint.

## Stage47: native browser origin capability

Module `web/static/public-review-secure-origin-guard-p0.mjs` probes runtime HTTPS, secure context and native WebCrypto without taking a caller-declared `approved` value. Its `realProductionOriginTested` and `iphoneSafariVerified` are **always false**. In isolated Chromium, injected `about:blank` has `isSecureContext:false`, `crypto.subtle:false`; intercepted `https://review.minimalizer.test/verify` navigation was blocked (`net::ERR_BLOCKED_BY_ADMINISTRATOR`). This is a **documented incomplete test, not secure-origin success**. iPhone Safari and real Public origin require external testing.

## Stage48: exact original RGB observation contour dual lattice

Module `public-source-dpr-budget-audit-p0.mjs`: independently SHA-pins each provided source-observed binary part mask, checks overlapping masks, computes polygon evenodd pixel membership on 340×340 and independently 680×680 (2×), inventories vertex cost. Geometry status and semantic/rendering approval remain separate. No SVG drawing or paint API. Source-observation labels are not independent human annotations. Raw RGB photographs/masks are PRIVATE and are never committed to public GitHub.

Real Stage12 observation subsets from the previous independently stored SHA-evidence archives:

| Case | Exact observed subset | Exact vertices | Stage8 budget for entire design | Pixel mismatches 340 / 680 |
|---|---|---:|---:|---:|
| GC001 | Goggle highlight (not body anatomy) | 398 | 1887 | 0 / 0 |
| Raden | Three bow/corset observations (not body anatomy) | 1968 | 1412 | 0 / 0 |

**These are not full-character SVG benchmarks**: GC001's eyewear subset fits, Raden's three accessories subset already exceeds the reference whole-character budget by 556 vertices. Historical Stage8 *full-scene* cost remains GC001 3604 / 1887 (over by 1717) and Raden 2370 / 1412 (over by 958), before further eyes/bow details. Stage8 release veto remains.

Existing epsilon=0.5 contour candidates reduce the two subset vertex totals to 296 and 1614, with 340 lattice unchanged, **but 680 lattice mismatches 148 and 428 source cells respectively** (GC001: 148; Raden: 142+208+78). Reject. This dual-lattice analysis uses deterministic mathematical scanlines, **not** a fresh secure-origin Chrome/Safari rendering proof.

## Stage49: exact source-run rectangle cover comparison

Module `public-source-exact-rect-cover-p0.mjs`: forms disjoint vertically merged rectangles from source-observed binary masks without adding pixels, returns actual 4-vertices-per-rect cost and a never-autopromoting cost comparison. On GC001, 123 rectangles / 492 vertices vs contour 398 (+94). On Raden, 224+291+143 rectangles / 896+1164+572=2632 vertices vs contour 1968 (+664). Rectangles are **worse** for both historical feature subsets, so neither gets adopted. The exact rectangle decomposition does not imply source semantics or accepted body geometry.

## Stage50: immutable original vs frozen Public RGB difference ledger

`public-source-fidelity-ledger-p0.mjs` checks independently supplied SHA-pinned original RGBA, frozen Public Facet40 RGBA, historic arm/face masks and **UNSIGNED** observed background, rejects owner overlap, preserves all buffers, emits aggregate RGB L1 / changed-pixel count and no original pixels. Source observations from previous PRIVATE Stage17–20 archive:

- GC001: 9,160 visible historic arm-owner pixels; 8,326 have RGB difference from frozen Facet40. Face 4,937 pixels, all differ. Original-observed background 39,577 pixels, 793 differ.
- Raden: 20,177 visible historic arm-owner pixels; 20,153 differ. Face 4,052 pixels, all differ. Original-observed background 29,942 pixels, 11,351 differ.

**This is a baseline discrepancy inventory**, not a target for copying original RGB directly, not an anatomical silhouette proof, and not an MSE-based promotion criterion. Facet40 is intentionally minimalist, so difference by itself does not imply a bug. The earlier distorted arms remain a qualitative blocker.

## Stage51 / release gate

Run new Node tests together with the inherited Stage1–46 research CI; record exact GitHub Actions run, SHA and counts in a separate final verification note. Never silently accept 340-only vectors, independent-review flags from user drafts, or estimated vertex counts. The independent sleeve/skin/hair boundary review is still 0 signed pixels in both cases. Full 340/680 body Golden, SVG vertex cap, actual native HTTPS/original Public, iPhone Safari, provenance, licensing and rollback remain HOLD. PR #390 **Draft, unmerged**.

PRIVATE provenance and exact runnable replay preserved only under Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage47_51_20261012`.
