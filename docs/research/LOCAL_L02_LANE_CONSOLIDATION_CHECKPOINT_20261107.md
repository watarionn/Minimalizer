# MinimalizerLocal Lane A consolidation checkpoint (2026-11-07)

Status: **RESEARCH CHECKPOINT ONLY / NOT A QUALITY PASS / NOT A RELEASE APPROVAL**.

## Verified GitHub snapshot
- Repository: watarionn/Minimalizer.
- Main SHA: `131416b5f6edb99d86e1fe035e6877fe440db76e` (compare API, checked 2026-11-07).
- Lane A candidate: `research/local-l02-class32-topology-palette-shadow-20261102`; compare API reports **79 ahead / 0 behind** main, **15 changed files**, restricted to `tools/research/`, `tests/`, `docs/research/`.
- Canonical plans consulted: `docs/roadmaps/MINIMALIZER_LOCAL_COMPLETION_PLAN_20261015.md` and `docs/research/README_L02_RESEARCH_20261016.md`. They explicitly prohibit interpreting synthetic checks or known-character replay as L02 quality approval.
- PR #449 state, private Drive Run29+ contents and Lane B current HEAD were **not independently verified for this checkpoint**. Re-check before consolidation.

## Outstanding quality gates
- H06: distinguish true costume pixels from arm/underlayer misownership. Prior candidate removed 208 true-costume pixels; do not assume class32 retention/colour similarity is semantic proof.
- H08: recover sleeve while preventing arm-to-costume owner promotion. Topology/anchor/contact guards alone cannot establish semantic correctness.
- H04: known false positives.
- Signed-source RGB/alpha, SHA, independent observation, Phase4 owner exclusivity/critical-part/connectivity and Phase5 exact replay/visual review are **not certified** for this candidate. Unknown pixels are unknown, not negatives.
- **L02 HOLD; L03/Golden/Local production NO_GO.** No Golden or iPhone approval is implied.

## Safe consolidation boundary
1. Preserve Lane A as a separate research-only candidate; do not merge its 79 commits merely to simplify task management.
2. Snapshot and independently verify Lane B L04/L07 status and its own PRs/QA before combining automation ownership.
3. A unified campaign may coordinate both lanes while retaining separate quality gates and branches; merge only verified source-free changes that satisfy their own gates.
4. Keep private signed images, masks, NPZ, coordinates and replay boards on approved private Drive with read-after-write; GitHub only source-free artifacts.
5. Do not touch Public/C08, production LocalWorker, Golden or signed originals in the consolidation.
6. Next A work: execute latest-head synthetic negative/regression tests, evaluate H06 true-costume preservation **and** arm/underlayer false-owner removal separately on signed source, then address owner-exclusivity semantics. Record exact failing test/replay evidence and a concrete code delta, not another generic status cycle.

This is a handoff/checkpoint, not a claim of improved P0/P1 image counts. Counts remain **unverified**.
