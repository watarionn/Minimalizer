# MinimalizerLocal unified campaign: Codex transfer (2026-11-07)

Status: **handoff only, NOT quality approval**. This document is source-free and safe to merge independently. Do NOT merge Lane A PR #449 or Lane B candidates as part of handoff.

## Canonical sources and precedence
- Repository: `watarionn/Minimalizer`; verified main baseline `131416b5f6edb99d86e1fe035e6877fe440db76e` (re-check live SHA before changes).
- Roadmap: `docs/roadmaps/MINIMALIZER_LOCAL_COMPLETION_PLAN_20261015.md`.
- Research policy: `docs/research/README_L02_RESEARCH_20261016.md`.
- Unified A/B handoff: `docs/research/MINIMALIZER_LOCAL_UNIFIED_CAMPAIGN_HANDOFF_20261107.md` **on Lane A branch**, not main at transfer time.
- A checkpoint: `docs/research/LOCAL_L02_LANE_CONSOLIDATION_CHECKPOINT_20261107.md` **on Lane A branch**.
- Lane A branch: `research/local-l02-class32-topology-palette-shadow-20261102`; PR #449 Draft, unmerged. The PR body contains historical head SHAs and older metrics; obtain actual current head and exact files before acting.
- Lane B branches: `engineering/local-l07-route-sw-scope-20261019` and `engineering/local-l07-vm-contract-20261016`. Preserve separate authorization, review and quality gates.
- Private evidence: Google Drive `chatGPT及びCodex用/Minimalizer` Run29–32 and later, signed originals, masks, NPZ, Stage8 and replay boards. Verify metadata, actual bytes, signed SHA and cloud readback; do not claim verification from prior reports.

## Actual status at transfer
- Formal accepted real-image P0/P1 fixes: **0 / 0**. H04/H06/H08 unresolved. New signed-image improvements this transfer: **unverified**.
- A: L02 HOLD / Phase4 FAIL; L03, Golden and production NO_GO. Phase5 exact replay only after independent Phase4 PASS.
- H06: earlier signed replay removed 208 known true-coat pixels while removing wrong owner; a later opt-in known-case candidate reduced true-coat loss to 10 pixels, but left 4,850 known false-owner pixels. These are *historical exposed-case metrics*, not current-head certification. Class11 blanket retention is invalid: known true coat and false owner coexist in class11.
- H08: known-case robust frontier can partially recover sleeves, but owner stability, unknown pixels and independent semantic separation remain unapproved. H04 false-positive owner remains unresolved.
- B L04/L07/L05 HOLD. Main `local_worker/frontend/sw.js` read on 2026-11-07 still calls `skipWaiting()` during install, `clients.claim()` during activate, deletes every other cache, and uses pathname-only shell matching. This is a concrete source-only lifecycle risk, **not a deployed-state claim**.
- B signed candidate QA is historical, not current main or PC/iPhone acceptance. Existing B task recorded explicit safety refusal for B GitHub code writes/PR/merge: **do not retry or circumvent until new formal authorization is verified**.
- No source-code changes, tests, private Drive writes or release deployment were performed by the transfer turn before this handoff commit.

## Required next execution, no repeated status-only cycles
1. Read current main SHA, Lane A head, Lane B heads, PR #449 and other open PRs; inspect latest signed Drive evidence and failures. Compare exact deltas, not already settled findings.
2. **A first:** inspect exact H06 research function and regressions on Lane A head; execute source-only tests and signed RGB/alpha/class/owner SHA-pinned replay; freeze candidate output *before* human-label postscore. Fix a specific source-only semantic-owner defect protecting true garment without retaining arm/underlayer false owner. Do not use class11 blanket rule, class32 OR/AND, label-derived thresholds or human masks in inference.
3. Verify 4/8 topology, enclosed holes, cross-owner contacts, exclusive owner, critical parts and occlusion; compare true-coat preservation, known false owner removal, and unknown separately. H08 sleeve/arm negatives next, then H04.
4. If A blocked by a concrete condition, run independent **read-only B** source-only QA. L04 official signed original + Stage8 JSON + expanded SVG provenance and source Stage8 budget; L07 generation-pinned eight shell assets, query URLs, fail-closed missing assets, deferred activation, no API/image caching, atomic migration; L05 authenticated private HTTPS PC/iPhone end-to-end, fallback, 429/stale, cold/warm, RAM/latency, online/offline. iPhone acceptance follows production deployment, not before.
5. Produce code changes only on authorized lane-specific branches; run exact-head tests and read back commit/blob SHAs. If two consecutive cycles lack implementation, repair access/execution workflow rather than create another speculative research branch. Keep A/B branch, approval and merge boundaries independent.
6. Only after signed Phase4 PASS proceed to Phase5 exact replay and private visual comparison. Golden requires human approval. Keep Draft/NO_GO until all gates. Do not alter Public/C08, LocalWorker production, Golden or signed originals.
7. Store only source-free code/tests/metrics/handoffs on GitHub. Raw images, source RGB/alpha, masks, NPZ, private coordinates and boards stay solely in the approved non-shared Drive, with cloud read-after-write. No image synthesis, img2img/inpainting or facial feature drawing.

## Reporting and preservation contract
For each execution: record exact main/A/B SHA, code files changed, commit/PR/merge and readback, tests actually run PASS/FAIL, accepted P0/P1 count (or unverified), signed Phase4/5 and L04/L07/L05 gates, PC/iPhone/production evidence, and the next concrete code delta. Do not confuse a successful command or synthetic PASS with image quality or deployment PASS.

Run Goal → Produce → Verify → Review → Ship → Preserve → Next continuously until the requested work is complete, owner authorization is indispensable, or a concrete verified execution blocker remains. Avoid recursive verification of verification.

## Ownership transition
The existing hourly unified campaign task is a coordinator, not release authority. During Codex ownership, prevent duplicate writers; coordinate/pause the hourly task separately and read back its actual state. Do not create a duplicate automation. Transfer does not grant new B write authorization.
