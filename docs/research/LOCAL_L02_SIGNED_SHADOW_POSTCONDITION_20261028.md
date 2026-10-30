# L02 signed shadow postcondition and input-mutation gate (2026-10-28)

**Lane A research-only, HOLD.** This is a safety/integration contract change, **not a visible P0/P1 fix** and not a current-main composed-owner reconstruction. No original image, human mask, annotation coordinate, private NPZ, model weight or generated pixel is included here.

## Canonical state and independently checked inputs

- GitHub main read at start: `4a4348990084848c981811b414e6221411271f84`. PR #445 remains Draft and unmerged. Adopted completion plan and L02 research README were read directly from main.
- Private source material was read from the existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. ReviewedEvidence ZIP `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598` matched its external pin and 19/19 member SHA-256 values. Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c` matched its external pin and 7/7 member hashes. Independent sleeve archive `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7` matched its external pin.
- The 2026-10-23 source-free staged archive `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc` matched 98/98 internal source hashes. Its isolated historical tests returned 235 passed + 31 subtests passed. **This is not current-main full CI.**

## Implemented A-only change

- Added `tools/research/local_l02_signed_shadow_output_gate.py` and its source-free adversarial tests. The signed input adapter now checks the *returned* owner independently: no frozen-owner erasure/reassignment, class32/opaque-source-only additions, truthful added-pixel receipt, no new cross-owner contact, and preservation of each frozen 4/8-connected component identity.
- The adapter also takes an immutable snapshot of the frozen owner and rehashes the owner, independent class map and decoded source after shadow execution. A shadow that mutates authenticated inputs in place now fails closed before its result is accepted. These postconditions do not establish semantic clothing/arm correctness.
- Local files for the new module, tests, adapter, existing shadow and current-main frozen-owner audit and cross-owner contact gate were independently matched to their GitHub Git blob SHA values. A source-free subset of **20 tests passed**, including malformed outputs and in-place input mutation. This is not the complete PR test suite.

## Authenticated historical H06/H08 regression

The exact PR #445 shadow/adapter and the exact main safety-audit blobs were replayed in an isolated local environment against signed historical Run30 sources/classes/owners, using the public externally pinned H06/H08 manifest values. Human review labels were **not** supplied to inference. No owner arrays or private visual exports were committed.

| Known signed case | Frozen Run30 owner SHA-256 | Proposed owner SHA-256 | Added original-source pixels | Postcondition |
| --- | --- | --- | ---: | --- |
| H06 | `4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317` | same | 0 | PASS (unchanged) |
| H08 | `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52` | `b4e5201e22bef51b14e6aa814b745653cc91449b6d7427fc9eae7751ac351291` | 3,356 | PASS (historical candidate reproduced) |

H08 candidate SHA exactly matches the **already known** historical Run30 candidate. No new reviewed garment gain is claimed. The large H08 sleeve gap remains, H06 underlayer/coat ownership remains incorrect, and H04 is unresolved. The replay does **not** reconstruct current-main composed owners or constitute a fresh unseen-character blind evaluation. Unknown pixels are not counted as true or false.

## Review and shipping decision

**Accepted visible P0 fixes: 0; accepted P1 fixes: 0. Unresolved known P0 cases: H04/H06/H08 (3).** Source-free safety code and tests are staged only in PR #445. Do **not** merge the Draft PR or promote Phase4/5 on this result.

Remaining integration gates: reconcile 12 historical staged dependencies with current-main contracts; exact current-main H04/H06/H08 composed-owner replay and critical-part semantic/4-8 topology/visual checks; independently signed unseen-character blind evaluation; full PR test suite and independent review; then Golden and physical iPhone owner acceptance. No GitHub Actions, production LocalWorker, Lane B L04/L07, Public/C08 or Golden changes.

**L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
