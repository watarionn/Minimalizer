# MinimalizerPublic StructuralRecovery P0 Stage37–41: Complete review-bundle and navigation evidence

Date: 2026-10-12. Canonical research branch of `watarionn/Minimalizer`, Draft PR #390. **No main, production Public, Local Minimalizer, release or generated content changes.** All modules are opt-in, research-only, fail closed, and cannot promote to production.

## Intent and execution

Stage36 enumerates ALL historically signed visible arm-owner pixels without inventing sleeve/skin/hair semantics. Stages37–40 turn that into a reproducible reviewer workflow rather than using more RGB-loss improvements to guess anatomy.

- **Stage37: `public-review-tile-manifest-p0.mjs`.** Independently validates original RGBA, face/background/arm SHA pins through Stage36. The deterministic manifest includes source identity, per-tile coordinates/counts, private original data omitted, and SHA-256 digest of canonical core. No semantic labels or paint masks.
- **Stage38: `public-review-progress-ledger-p0.mjs`.** Readback recomputes the manifest digest from the core, rejects forged bytes or extra `approved` flags, and tracks `unvisited`, `visited` and `needs_revisit` as *untrusted navigation bookmarks* only. No reviewer signature or semantic authorization implied.
- **Stage39: `public-review-progress-diff-p0.mjs`.** Compares same-source snapshots, refuses changed geometry/identity, describes tile-level bookmark changes without upgrading trust.
- **Stage40: `public-review-stage40-gate-p0.mjs` and PRIVATE offline HTML.** Both real case worklists feed a fail-closed anatomical review gate. Private HTML embeds original images and all historical masks, highlights the current 20px tile, confines marking to the active tile, navigates previous/next, saves/imports untrusted bookmarks, refuses mismatched case and manifest, and retains prior Stage29 annotation import/export. **Do not put private HTML, photographs or masks in GitHub.**
- **Stage41: CI integration, byte-for-byte Drive/GitHub source readback, final evidence and handoff.** CI pass status is separately recorded only after decoded GitHub Actions logs confirm it.

## Real-original replay (340 × 340 pixels)

| Case | Visible historical arm authority | Complete worklist tiles | Actual queued pixels | Independent semantic signoff |
|---|---:|---:|---:|---:|
| GC001 | 9,160 | 47 | 9,160 | 0 |
| Raden | 20,177 | 78 | 20,177 | 0 |

Real-original manifests deterministically reproduced, and a synthetic navigation bookmark produces exactly one tile change. Any synthetic 49-pixel drafts from prior work remain parser exercises only, not an accepted anatomy review. Two-case Stage40 gate returns **DRAFT_HOLD**, 11 blockers, and explicit `paintAuthorized:false`.

Isolated Chromium (`page.set_content`, opaque `about:blank` origin) tested both private pictures: tile count, previous/next navigation, marking, JSON download/reimport and forged-manifest refusal; semantic labels changed **0** in these navigation tests. This does **not** verify an HTTPS secure-origin WebCrypto execution, iPhone Safari or mobile gesture behavior. Private screenshot and browser audit saved in Drive only.

New unit coverage: **28** tests spanning digest tamper, preserved source, all pixel coverage, untrusted claims, duplicate bookmarks, cross-case, history diffs, forged release flags and complete HOLD. No independently signed sleeve, forearm, skin, hair boundaries exist yet. The historical Stage8 full-character SVG complexity budget and full image Golden remain unresolved (GC001 3,604 > 1,887; Raden 2,370 > 1,412), as do real Public route, iPhone Safari and rollback gates.

## Next work

Stage42: enable useful zoom/canvas navigation on mobile review without silently accepting a semantic label; use actual independent reviewer annotations when and only when they exist, keep unknown pixels unknown. Prioritize end-to-end real Public non-local SVG and source-authoritative silhouette improvements only after real source ownership proof and Golden.

Canonical Drive subfolder: `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage37_41_20261012`.
