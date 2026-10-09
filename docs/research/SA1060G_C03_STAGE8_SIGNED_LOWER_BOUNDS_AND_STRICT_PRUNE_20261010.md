# C03 source Stage8 budget: verified arithmetic bounds and strict raster-exact pruning (2026-10-10)

**RESEARCH CHECKPOINT COMPLETE / C03 RELEASE GATE HOLD.** This report compares two original SHA-locked and independent source-ring scenes. It neither authorizes a release nor changes any signed source, shape, Stage8 policy, human Golden review or production runtime.

## Authority and exact reproducibility
- GC001 source SHA `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`; original Stage8 adaptive scene SHA `7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08`; signed metrics SHA `a3ca4f09a033603692e775f2587052c5e9e0112dd3b1868039c655ee1e4c085c`.
- Raden source SHA `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`; original Stage8 adaptive scene SHA `be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f`; signed metrics SHA `ea9415e172b17c6a52fb668c5183809af11d33afec809a308e90c1e58ecd501f`.
- Private source files archived under `chatGPT及びCodex用/Minimalizer/SA1034_Phase8_ExactReplay_20261008/{GC001,Raden}` and read-only snapshots available in the execution environment; individual metrics, signed scene SHA and original-source provenance all validated before calculations.

## Actual original Stage8 budget (never replace with compact deployed SVG cap)

| Original signed case | Original source ring vertices | Immutable source cap | Excess | Max hypothetical removal: all rings with <=16 vertices | Still over after that impossible deletion | Accepted existing-vertex strict pruning | Still over after strict pruning |
|---|---:|---:|---:|---:|---:|---:|---:|
| GC001 | 3,604 | 1,887 | 1,717 | 544 | 1,173 | **2 vertices** | **1,715** |
| Raden | 2,370 | 1,412 | 958 | 161 | 797 | **0 vertices** | **958** |

All <=16-vertex ring deletions and every hole-ring deletion are **counterfactual count-only bounds, not authorized or topology-safe edits**. Even those extreme deletions fail the source cap.

## Signed private-source tests freshly rerun for this PR
- `tools/research/c03_stage8_budget_bounds.py` + `tests/zerobase/test_c03_stage8_budget_bounds.py`: **15/15 PASS** including signed scenes/metrics, SHA tamper fail-closed, source/count checks, deterministic replay and synthetic bounds. Public checkout without private files skips signed cases.
- `tools/research/c03_exact_vertex_prune.py` + `tests/zerobase/test_c03_exact_vertex_prune.py`: **10/10 PASS** including signed scenes, two-scale OpenCV ring pixel-equality, orientation, source tamper, synthetics and repeated replay. The only observed ring-local 1×/2× raster-preserving deletion is 2 vertices in GC001; Raden 0.
- Combined, **25/25 PASS** against pinned real signed inputs on 2026-10-10. SHA of each GitHub script and test blob was verified equal to the actual byte content of the test-run scripts before review.
- The independent prior raster refit study accepted 0 replacements; these exact-prune results test a different, greedy existing-vertex-only restricted family. No blanket impossibility claim.

## Boundaries and next tasks
Strict *per-ring* OpenCV 1×/2× parity is a conservative sufficient check for these probes, not actual Chromium pixel parity, whole-scene perceptual identity, occlusion correctness, semantic owner topology or user human Golden. Current Stage8 history must remain `GC001 3604/1887 FAIL`, `Raden 2370/1412 FAIL` even if a future candidate reaches some other deployed SVG cap. A versioned alternative budget policy would require explicit owner approval and full compatibility, rollback and actual Chrome/iPhone evidence; this research offers no such approval.

Next: (1) independent source-equivalent topology/owner geometry with actual Chromium or decision-ready but **unapproved** Stage8 policy packet; (2) C02 source-aware confidence-bearing arm/garment/hair candidate with independent Raden and Approved holdout; (3) new candidate-specific human Golden sheets and Approved-18/78 before release.

**Status:** C02 `IN_PROGRESS`; C03 `HOLD`; C04 `HOLD`; C05–C08 `BLOCKED`; `release_authorized=false`, `deployment_verified=false`, `production_changed=false`.

Original research bundles and ancillary proof (private, no image pixels in this GitHub PR): https://drive.google.com/drive/folders/1N48_Ae5CWB8KSO0mEmgHJRJ-4w4AxDvS
