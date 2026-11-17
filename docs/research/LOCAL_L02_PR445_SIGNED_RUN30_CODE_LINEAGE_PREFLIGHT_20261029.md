# L02 PR #445 signed Run30 replay code-lineage preflight (2026-10-29)

**A-only source-free integration safety fix. Not a P0/P1 image improvement, not Phase4 PASS, not an exact-main replay, and not an unseen signed holdout.**

## Problem and fix

The historical `local_l02_dual_owner_signed_replay.py` validated external source/owner SHA pins but did not independently verify the exact code modules that would process the private signed inputs. The existing 20-module PR lineage gate covered the composed/strict path, but omitted the separate signed dual-owner LAB-reach adapter, its candidate implementation, and its output postcondition module. A stale/mixed local checkout could therefore run a mismatched research algorithm on authentic private data.

- Extended `PR_445_REPLAY_BLOBS` from 20 to **23** exact Git blob pins: `local_l02_dual_owner_lab_reach_shadow`, `local_l02_dual_owner_signed_input_adapter`, and `local_l02_signed_shadow_output_gate`.
- The signed Run30 runner now calls `verify_pr_replay_lineage()` **before opening any private manifest, image or NPZ**.
- The signed adapter import is deferred until after the lineage gate, so its module-level code is not imported before verification.
- A mismatch fails closed with `PR_DEPENDENCY_LINEAGE_HOLD`; the source-free receipt exposes `pr_dependency_lineage` while keeping `Phase4=FAIL`, `L02=HOLD`, `L03=NO_GO`, `Golden=HOLD`, and `production=NO_GO`.
- A negative test verifies that a lineage mismatch rejects execution before any private-file read; the positive source-free test expects 23 verified dependencies.

## Verified / not verified

The three newly pinned module Git blobs matched the exact remote PR head after the changes. The other 20 pinned module Git blobs were individually read back from the same branch and matched their pinned values; their direct static local imports were inspected. The updated gate, runner and test blobs were also read back from the remote branch. **These are static remote provenance checks, not Python execution or a full CI pass.**

The exact-head GitHub Actions workflow-run list, check-runs and commit status returned no runs/checks at inspection. No new private H04/H06/H08 replay or independent visual score was produced in this step; the private evidence ZIPs were not newly downloaded or written. The previously reported exposed H08 improvement is **not** promoted to accepted P0/P1. H04/H06/H08 remain unresolved.

## Actual repository verification route

The repository's canonical `.github/workflows/README.md` explicitly says **GitHub Actions are not the execution platform** and identifies `scripts/Test-MergeReadiness.ps1` on the owner PC / authorized remote execution as the pre-merge verification path. The present `Test-MergeReadiness.ps1` checks general compile, stable tests, Phase16 corpus and local server smoke, but its explicit pytest list does **not** include the new L02 tests. Therefore **zero Actions runs on this PR head is expected and cannot be reported as a passing CI result**. A real acceptance run needs BOTH the repository's adopted merge-readiness command and the exact-head L02 source-only tests, with signed receipts and read-after-write. Do not silently switch on or edit unrelated GitHub workflows to manufacture a CI signal. No owner-PC execution was performed in this checkpoint.

## Next acceptance gates

1. Execute the **exact PR-head** L02 source-only regression suite, including the new negative pre-private-read gate, and the adopted `scripts/Test-MergeReadiness.ps1` route on an authorized owner PC. Record both receipts; GitHub Actions is not the adopted CI platform.
2. Resolve source-only Phase4 semantic owner/critical-part/connectivity FAIL and H06 frozen underlayer FP, H08 sleeve loss, H04 regression. Do not use reviewed labels as inference inputs.
3. Only after Phase4 source-only PASS, run independently pinned private replay, score known labels post-inference and compare visually; obtain a genuinely unseen signed blind cohort for generalization.
4. Keep original private RGB/alpha, owner NPZ, masks and comparison images exclusively in the established non-shared Drive hierarchy with cloud read-after-write. No source pixels or human coordinates in GitHub.
5. Keep PR #445 Draft and do not merge, alter B L04/L07, Public/C08, LocalWorker, Golden or production until all required gates pass.

**Accepted P0 fixes 0 / P1 fixes 0; major unresolved H04/H06/H08 = 3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
