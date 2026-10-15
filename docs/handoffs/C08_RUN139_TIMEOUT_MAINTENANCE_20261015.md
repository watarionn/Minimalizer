# C08 Run139 test-timeout maintenance (2026-10-15)

## Scope and authority
Research-only QA maintenance; no original image, mask, conversion runtime, production deployment or release-gate changes. GitHub main at start: `e3cd876172d30c05c9e58735d9f99433a0dba8ed`. C08 campaign must remain `ACTIVE_RELEASE_HOLD`, C02 ABSTAIN, C03/C04 HOLD, C05 NO-GO. No Golden approval is represented.

## Confirmed problem and resolution
The monolithic 77-test invocation previously exceeded a short outer execution budget. Fresh private-isolated Chromium execution produced:
- Monolithic: `Ran 77 tests in 48.794s / OK`, no failed assertions. A short ~45s tool execution can still time out.
- Regression modules (Run134, Run135 + gates/model, Run136, Run137, Run138): `Ran 70 tests in 19.351s / OK`, process exit 0, launcher wall time 20.445s.
- Run139 only: `Ran 7 tests in 29.714s / OK`, process exit 0, launcher wall time 30.544s.

`tools/qa/run139_chunked_verify.py` is a source-free, fail-closed launcher. It accepts `--workspace` to point to the approved private test workspace, enforces a per-process timeout, requires correct test count, process exit code and terminal `OK`, and optionally writes a structured JSON receipt. The full 77-test workload now has **two short invocations**, each under the previous outer 45s bound in the measured environment. This does not claim all future hardware is equally fast.

## Reproduce (PRIVATE workspace only)

```bash
python tools/qa/run139_chunked_verify.py --workspace /path/to/private/overlay --group regression --timeout 90
python tools/qa/run139_chunked_verify.py --workspace /path/to/private/overlay --group run139 --timeout 90
```

Both commands must return process exit 0, output `PASS`, and verify 70 and 7 tests respectively. Do not publish signed photos, coordinates, masks, or local private fixtures to GitHub, PR comments, or public CI.

## Drive empty document follow-up
Prior recovery artifact `1QINOr1uAkZnJwU66smunoLJnIk0O0LvEXlK7sS9O7A8` now returns Drive API 404 in the connected account. A search of My Drive root and accessible Trash for recently created native Docs did not return that ID. **Connected-account visibility: absent;** whether the object was actually deleted or access was revoked cannot be distinguished from 404. Earlier protected move/delete refusal was not bypassed. An owner-side Trash check is required only for a globally definitive deletion claim.

## Human C04 Golden reviewer guidance
Open PRIVATE Run141 review six-panel boards for both GC001 and Raden, DPR1 and DPR2:
1. SIGNED ORIGINAL: source-only human visual reference.
2. OFFICIAL SA10.41: historical official baseline.
3. RUN140 RESEARCH: previous unapproved candidate.
4. RUN141 RESEARCH: new unapproved candidate.
5. CHROMIUM XOR: visible Chrome output mismatch.
6. SOURCE OWNER CV XOR: historical Stage8 owner-mask mismatch.

For Raden, inspect the two additional LEFT_ARM_ROI zoom images. Reviewer A and B must independently inspect **24 case-criteria each, 48 assignment decisions total**, recording case, DPR1/2, body-part/detail, PASS/FAIL/UNCERTAIN, rationale, reviewer identity and date. Examine silhouette (head/hair, shoulders, arms/hands, sleeves, garment outlines), source color ownership, accessories, and thin-part retention; default eyes/nose/mouth/eyebrows must remain hidden; source pixels and shapes must not be hallucinated. Any major anatomical disappearance or deformation is FAIL. Numerical vertex/DPR differences are supporting data, not approval. Keep reviewer signatures/authentic approvals absent until real human review.

The original Stage8 budget and new-invalid-ring lineage are still on HOLD; Golden assessment cannot clear them by itself.
