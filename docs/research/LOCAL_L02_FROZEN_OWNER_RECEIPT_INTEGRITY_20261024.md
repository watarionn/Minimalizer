# Local L02: frozen-owner deletion receipt integrity (2026-10-24)

**Source-only research integration. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Verified defect

The unmerged Lane A source-free integration candidate from 2026-10-24 10:00 contained `prune_new_cross_owner_additions`. When an exact preapproved abstention erased a frozen owner pixel, the receipt counted the abstention but still reported `frozen_owner_pixels_modified: 0`. That value was incorrect and could hide real deletion of a critical original region from later audits.

The integration candidate has a corrected receipt expression `int(np.count_nonzero(erased))` and a regression asserting that one approved deletion is reported as one modified frozen pixel. A separate, self-contained `audit_frozen_owner_transition` has been added on this research branch to establish a reusable fail-closed contract: uint8 owner domains 0/1/2, no reassignment of existing nonzero owner, exact preapproval required for deletion, and actual deletion counts. This audit is post-inference only; it never receives human-label coordinates.

## Verification and scope

The local corrected 10:00 integration candidate passed **249 tests plus 31 subtests**. The new standalone audit passed **4 targeted tests**. These are source-free tests, not signed real-image replay. The full integration bundle is preserved in the existing private Drive Lane A folder; this PR does not import the entire unmerged bundle and does not alter inference or production behavior.

The known signed H04/H06/H08 quality frontier remains unchanged: H04 known false owner 4,423px; H06 known underlayer false owner 1,077px and missing outerwear 20,803px; H08 missing outerwear 18,781px (previous safe research candidate). **New P0 fixes 0; new P1 fixes 0; three cases unresolved.** Unknown pixels remain unknown; no blind unseen-character generalization is claimed.

No source image, RGB/alpha array, mask, NPZ, hand annotation, private preview, or model weight is committed. No B L04/L07, Public/C08, LocalWorker production, Golden, or release flag change. Follow-on work must wire the audit into the staged cross-owner repair only after review, revalidate signed H04/H06/H08 and Phase4 semantics, then consider L03.
