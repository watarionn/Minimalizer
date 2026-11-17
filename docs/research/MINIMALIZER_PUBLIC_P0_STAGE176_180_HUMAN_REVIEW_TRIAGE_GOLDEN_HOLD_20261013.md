# MinimalizerPublic StructuralRecovery P0 Stage176–180: Original Full-frame Review Triage (GOLDEN HOLD)

Date: 2026-10-13 JST. Canonical repository: `watarionn/Minimalizer`, Draft PR #393. Research-only changes; **do not merge or release**. Main, Local, normal Public, Stage51 and deployed Stage135 must remain unchanged.

## What was actually implemented

- **176** `web/static/public-human-review-triage-p0.mjs` binds diagnostics to the SHA-validated original-source RGBA, source PNG and source eligibility hash. Both untrusted full-frame drafts are revalidated using the existing Stage77 validator. Identical draft hashes are rejected. The source bytes and labels are not changed.
- **177** Exhaustive full-source accounting: every original pixel is exactly one of both-proposed-agreement, both-proposed-disagreement, or unreviewed/abstained. Per-tile sums and global sums are checked. Transparent pixels are not secretly assigned semantic roles.
- **178** Exact untrusted class-confusion pair counts (hair/face/skin/sleeve/garment/neckwear etc.), class agreement counts, and source-only edge evidence. These figures are diagnostics, not independently human-adjudicated semantics.
- **179** Priority-sorted tiles computed from conflict/abstention/source-color boundary density, stable deterministic tie-breaking; completely labelled synthetic duplicates cannot impersonate two people. Per-tile and source hash pins remain intact.
- **180** An unconditional hold release gate resists forged approval flags, duplicate cases and partial case lists. No automatic paint, no public activation, no identity or human-Golden claims.

## Verification

- New `tests/js/test_public_stage176_180_p0.mjs`: **12/12** Node tests PASS locally in an isolated clean clone.
- All **23** registered research suites on Node v26.3.0: **608 tests, 608 PASS / 0 fail / 0 skipped** locally. Previous Stage175 GitHub-hosted 596 PASS on executable SHA a86d9125f3922f7586df2c4b04f75c6c31fcf2d9. This is not a claim that a new GitHub-hosted CI run has passed, unless verified separately.
- Research workflow `.github/workflows/minimalizerpublic-p0-research.yml` registers the new suite and Stage180 label.
- Source-bearing private HTML, original RGBA, derived original-colored SVGs and any future real review drafts must **never enter GitHub or the public site**. Generic code, synthetic tests and source-free docs only.
- **0 independently authenticated human reviewers, 0 authenticated human source semantic pixels**. Stage8 genuine complete-character budget **GC001 3604>1887, Raden 2370>1412 FAIL**. No physical iPhone Safari HTTPS or exercised rollback.

## Next

Stage181+: actual separate human reviewer enrollment and offline original GC001/Raden whole-frame annotation are the priority. From independently sourced annotations, compare subject/background, hand/arm, sleeve/skin, hair, collar/necktie and face blank; adjudicate disagreements. Existing Stage91 private offline editor and Stage92 signed receipt transport are ready but do not establish human identity. Until that evidence exists, only nonpromoting tooling improvements are permitted.

Research PR remains **DRAFT / GOLDEN HOLD / UNMERGED**. Any test derived from synthetic input does not count as reviewer evidence.
