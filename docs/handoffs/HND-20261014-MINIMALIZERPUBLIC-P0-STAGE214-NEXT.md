# Handoff: MinimalizerPublic StructuralRecovery P0 after Stage214

Date: **2026-10-14 JST**
Repository: `watarionn/Minimalizer`
PR: **#393** https://github.com/watarionn/Minimalizer/pull/393
Branch: `research/minimalizerpublic-p0-stage136-155-20261013`
Status: **DRAFT / GOLDEN HOLD / UNMERGED**. Ordinary MinimalizerPublic production default, `main`, Local Minimalizer: **unchanged**.

## Starting point for the next ChatGPT conversation

**Do not trust recollected stage number alone.** Read the **live GitHub PR #393 and current branch HEAD**, then this file and the Stage205–214 research report:
`docs/research/MINIMALIZER_PUBLIC_P0_STAGE205_214_SOURCE_BOUND_FRONTIER_GOLDEN_HOLD_20261014.md`.
Machine-readable status and gates:
`docs/handoffs/MINIMALIZERPUBLIC_P0_STAGE214_CHECKPOINT_20261014.json`.
Reread Stage204 baseline if needed:
`docs/handoffs/HND-20261014-MINIMALIZERPUBLIC-P0-STAGE204-NEXT.md`.

The last verified **code+CI** head was `d0b5ce686d68845438679687e129d0489f8cc085` with actual GitHub Actions https://github.com/watarionn/Minimalizer/actions/runs/38536860562 **698/698 PASS**. This handoff and the report are **docs-only commits after CI** and do not themselves authorize release. Verify current HEAD and CI whenever code changes.

The user explicitly requested long-running development to include a robust handoff at every 10-stage boundary because conversation limit is not visible to ChatGPT. Continue this practice.

## Stage205–214 completed engineering checkpoints

205. Source-opaque A/B agreement and ordered role-confusion ledger; all 115,152 opaque pixels accounted in each original.
206. Private manual-triage tile priority, 121 tiles per 340×340 source image.
207. Per-pixel private original-RGB corroborated human adjudication *proposal* API, rejects unsupported requests; **no human semantic decision made by the assistant**.
208. Immutable A/B revision hash and transition audit for future human v2; **do not forge v2 or overwrite A/B v1**.
209. Exact per-role SVG contour research, with alpha and role-isolation source pixel replay.
210. Rectangle vs union vs per-part contour vertex frontier, each measured on identical *incomplete agreed-person proposal mask*.
211. Role-scoped source RGB-only palette with measured four-color/role L1 and mismatched pixels; **do not treat that palette as exact source colors**.
212. Explicit face-region-only, eyes/nose/mouth non-generation guards.
213. Fail-closed original integrity, Golden, fullbody, iPhone Safari, rollback, vertex and owner release gates.
214. Checkpoint manifest, documentation, tests, CI, privacy and next chat handoff.

New module: `web/static/public-stage205-214-evidence-frontier-p0.mjs`
New tests: `tests/js/test_public_stage205_214_p0.mjs` (+20, all PASS)
CI workflow: `.github/workflows/minimalizerpublic-p0-research.yml`
Total CI: **698 PASS, 0 fail**, head `d0b5ce686d68845438679687e129d0489f8cc085`.

## Private source SHA-pinned measurements (numbers only, no original arrays)

| Case | Agreed-person | Agreed-background | Background disputes | Part disputes | Abstained | Unknown | Exact union vertices | Exact part vertices | Historic cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GC001 | 47,448 | 60,632 | 1,589 | 3,466 | 2,017 | 7,072 | 4,588 | 4,832 | 1,887 |
| Raden | 47,888 | 44,574 | 1,297 | 21,074 | 319 | 22,690 | 2,436 | 2,546 | 1,412 |

- Original: each 340×340, 115,152 opaque / 448 excluded nonopaque.
- Top disputes: Raden A garment vs B sleeve **17,772 pixels**; GC001 A garment vs B accessory **2,390 pixels**.
- Source-only full mask replay of agreed proposal remains exact; unresolved pixels were NOT filled or adjudicated.
- Actual independent A/B review was **confirmed out of band by the operator** in chat. Individual pixel correctness was NOT confirmed. Do not confuse these claims.
- Simplified 4-color-per-role preview would change GC001 40,562 and Raden 45,759 agreeing subject RGB pixels. This is measured preview color distortion and remains a release blocker. The original source color loss is not waived by using observed palette entries.
- Different SVG encodings are compared only against their own per-mask actual costs; these **do not meet historical fullbody caps** or certify complete silhouettes.

## Private owner-only archives and privacy

Owner-only Drive, strictly inside `chatGPT及びCodex用 / MinimalizerPublic / StructuralRecovery_P0_20261010`:
https://drive.google.com/drive/folders/1ZLfnIQy6W4A0q0tu6q7uq45G5wuhx6lj

Private ZIP SHA256:
`fba3c929f85a0808fe5e655a5077d7bede3e4264ce711f8d2acdc42e650a51a4`.

Earlier private originals/A-B v1 remain separately in Stage191-193 archives. Do not upload originals, pixels, masks, reviewer JSON, derived PNG overlays or SVG to GitHub, public pages, CI, or artifact host. Public code/docs here contain source-free logic and aggregate metrics ONLY. Preserve A/B v1 exactly.

## Stage215+ execution order / next 10-stage roadmap

1. **215–216**: Privately review original Raden large sleeve/garment ROIs, GC001 accessory/garment ROIs. Obtain actual operator/human semantic decisions with reason and original reference, no blanket region auto-adoption. If not possible, record HOLD and continue independent safe engineering.
2. **217–218**: Check background/hair/skin boundary and residual unreviewed pixels. If human corrections arrive, preserve A/B v1, ingest signed or explicit v2 versions, check all pinned RGBA and label SHA, then rebuild tri-state source authority.
3. **219–220**: Investigate data-driven source-exact SVG topology/role complexity and geometry tradeoffs, no invented silhouette, no auto-Golden; measure verified original replay in Chromium and actual vertices.
4. **221–222**: Improve source-sampled internal color palette and apparel partition quality while quantifying L1 errors and following strict face part non-generation; candidate visual/Golden gate separately.
5. **223–224**: Validate source-only full research CI and real device/rehearsal requirements where physically available, archive owner-private artifacts, update user-facing status and the next chat handoff. Never claim real iPhone or rollback PASS without execution evidence.

## Explicit stop conditions

**Golden HOLD** until every original-opaque pixel is human adjudicated, fullbody silhouette/color/vertex constraints satisfy actual Golden, source fidelity holds, real iPhone Safari and rollback have been tested, independent reviewer human sign-off exists, and explicit operator release decision is recorded. PR #393 remains Draft/unmerged. Do not promote to `main`, deploy or touch Local Minimalizer.

If user asks “次の工程”, start Stage215 based on live branch, prioritize relevant non-blocked engineering if waiting on human corrections. Do not repeat unnecessary questions or mistake pending human review for completed work.
