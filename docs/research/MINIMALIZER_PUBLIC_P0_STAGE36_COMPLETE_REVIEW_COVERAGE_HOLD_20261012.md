# MinimalizerPublic StructuralRecovery P0 Stage36: complete original-source review coverage

Date: 2026-10-12 (JST). Research-only, Draft PR #390, NEVER merge/deploy until full Golden.

## Problem and change

Stage32 returned a risk-ranked *subset* of visual review tiles (`maxTiles`), not a durable accounting of every eligible arm pixel. Stage36 implements `web/static/public-annotation-complete-review-queue-p0.mjs`, an independently source-rehashed, complete no-paint queue. It enumerates **every** eligible original source pixel in exactly one grid tile, including areas with zero risk score, and hard-fails instead of silently truncating a queue when `maxTasks` is exceeded. Coordinates, counts and SHA lineage only; no source RGBA, masks, original photographs or labels in the public output.

The stage accepts zero or two untrusted manual review JSON drafts. If two, each draft is independently validated against separately supplied original image and signed historical arm mask inputs; the existing Stage33 logic recomputes the pair accounting. A proposed agreement is still *unverified*, a disagreement is flagged for manual attention, an unlabeled pixel remains unknown, and all are queued. An `approved` flag or duplicated review bytes are refused. SHA equality authenticates bytes, not sleeve/skin/hair meaning or reviewer identity.

## Reproducible real-source results

Source-private replay: `private/replay_original_stage36.mjs`, using the separately pinned GC001/Raden 340×340 RGBA, Stage04 arms/face and source-observed background. The two 49-pixel annotations are **artificial parser exercises** with a deliberately different 1-pixel label; no genuine human reviewer classification was imported.

| Metric | GC001 | Raden |
|---|---:|---:|
| Source-eligible arm pixels | 9,160 | 20,177 |
| Complete 20px review tiles | 47 | 78 |
| Review-tile-assigned original source pixels | 9,160 | 20,177 |
| Unclassified under artificial draft pair | 9,111 | 20,128 |
| Unverified draft agreements | 48 | 48 |
| Artificial draft disagreements | 1 | 1 |
| Independently verified human anatomy labels | 0 | 0 |

The prior risk-only queue counted 47/76 on GC001/Raden; Stage36 includes all 78 Raden tiles with eligible pixels. These tile counts do **not** indicate a recovered sleeve or a better image. The output is source-only, deterministic across two runs per case; each full queue's SHA-256 is recorded privately.

Tests: `tests/js/test_public_annotation_stage36_p0.mjs` has 18 checks: complete coverage, disjoint owner accounting, forced no-paint, deterministic tile rank, protected pixels, forged claims, SHA tampering, duplicate review bytes, invalid task budgets, unknown abstention. Stage31–34 plus Stage36 local suite 48/48 PASS. CI adds the new file to the existing research-only full regression workflow; run ID and PASS count must be recorded **after** actual GitHub Actions verification.

## Remaining release blockers

Independent reliable sleeve / forearm skin / hair / other garment pixel classification; reviewer provenance; visual Golden for full GC001/Raden and collar/arm silhouette; signed background; original Stage8 whole-character SVG over-budget (GC001 3604 > 1887 vertices, Raden 2370 > 1412); DPR 340/680 full SVG; real Public-origin WebCrypto; iPhone Safari; licenses and rollback. Stage36 never issues reviewer signatures, paint tokens or production approval. Keep `main`, normal Public production, Local Minimalizer untouched.

Private RGBA/masks/draft examples/real replay and manifests belong under `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage36_20261012` on Google Drive. No private data on public GitHub.
