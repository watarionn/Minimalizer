# SA10.43 Source-owned pixel-edge compaction versus original vertex budget (2026-10-09)

**Status: original-mask browser parity PASS; product vertex gate FAIL for exact source topology; budgeted variants reject protected-arm parity. Full-character Golden HOLD, Local/Public/Worker unchanged.**

## Starting point and authority

Continuation of merged PR #289 SA10.42. The signed Raden source (`d9982c...03a00`), the original Stage8 contour scene (`be6001...49b5f`), the SA10.41 vector (`ecc48f...97db`), signed OpenCV full-scene baseline (`749fc3...74a92`), and original face/arm masks are verified against their frozen SHA-256 before processing. Raden is an **independent negative/holdout source**, not proof of goggles material transfer. No generated/embedded source pixels, inferred facial features, material replacement or production source modifications.

SA10.42 proved pixel-run rectangles can repair face and both arms but uses excessive vertices. This stage compares true pixel-square boundary SVG paths, with topological corner and hole preservation, to source-derived OpenCV binary masks **in real Chromium**. A closed boundary walk on literal pixel edges handles islands and holes; collinear points are removed, and contour variants are considered at `approxPolyDP` epsilons 0.5, 0.75, 1.0, 1.25, 1.5. Nothing is accepted based on OpenCV approximation alone: actual Chromium isolated mask renders are checked for each owner and protection mask.

The original Stage8 project budget **1,412** is unchanged. Counts include all eleven owner-mask geometry occurrences (including non-painted structural head), face mask, combined protected inverse mask, plus the signed 12 Stage9 material plane vertices. Reused vertices in separate masks are **not** silently deduplicated. The original SA10.41 full SVG counted **2,976** geometric occurrences including masks and color planes.

## Actual Chromium 144.0.7559.96 results (340 × 340, DPR 1)

| Candidate | Geometric occurrences | Actual whole-scene RGB pixel mismatches vs signed OpenCV | Face mismatch | Left arm | Right arm | Release gate |
|---|---:|---:|---:|---:|---:|---|
| Original SA10.41 | 2,976 | 2,681 | 122 | 237 | 255 | FAIL |
| All masks exact (`epsilon=0.5`) | **4,086** | **148** | **0** | **0** | **0** | BUDGET FAIL |
| Budgeted weighted mask search | **1,411** | **1,010** | **0** | **60** | **21** | PROTECTED FAIL |
| Uniform approximation (`epsilon=1.0`) | **984** | **951** | **21** | **42** | **41** | PROTECTED FAIL |

All thirteen isolated masks (eleven owners + face guard + combined face/arm inverse protection) are **binary-pixel exact in Chromium at epsilon 0.5**, including hair and unassigned mask. The remaining 148 whole-scene RGB discrepancies in that variant must not be called complete parity; they may involve other SVG composition/polygon raster semantics and require separate localization. No claim is made that the Raden source image itself is fully reproduced.

Finite budget selection is a reproducible *exploratory* knapsack using measured mask errors and hard total vertex cap, with deliberately protected-heavy weights. It is **not** a Golden or perception score. A candidate satisfying the vertex budget but altering 81 source-signed arm pixels is rejected regardless of better overall RGB error. Similarly, `epsilon=1.0` alters 104 protected pixels; rejected. Neither can be deployed.

**Observed representation-bound lower bound:** exact paths for face guard (138), inverse protected (636), right-arm owner (198), left-arm owner (300) and face owner (138) already consume **1,410** vertices; adding the actual twelve Stage9 plane vertices makes **1,422**, beyond 1,412 *before* any other owner. This is a lower-bound demonstration for this literal per-mask path scheme, **not a proof that every possible SVG/compression technique is impossible**.

## Verification, storage and controls

- Independent research script: `tools/research/sa1043_boundary_compaction.py`.
- Non-production synthetic regression tests: `tests/zerobase/test_sa1043_boundary_compaction.py`. **6 tests PASS** in local pytest, plus actual independent Raden research Chrome execution.
- Two independent runs yielded byte-for-byte equal SHA-256 for **all 9 generated outputs** (SVG/PNG/JSON). PNG snapshots and complete per-mask epsilon sweep preserved in the evidence manifest.
- Original source hashes, existing Stage8 contours, z-order, color palette and signed masks remain unchanged.
- Private authoritative assets: Google Drive `chatGPT及びCodex用/Minimalizer/SA1043_SourceBoundaryCompaction_20261009` (folder URL in PR description).
- Product promotion: **NO-GO**. Full-character Golden HOLD. Do not publish the accurate 4,086-vertex candidate or the near-budget but anatomy-inaccurate candidates.

## Next investigation

Research shared topological owner/protection geometry and compact SVG reuse **while accounting for expanded geometry occurrences honestly**. Alternatively test controlled source-authored lower-vertex representations with strict zero-error protected face/arm gates, plus original-silhouette and real-browser checks across distinct sources. Local repair cannot be promoted to full-character quality. Avoid changes to production renderer until all hard gates pass.

## Reproduce

Retrieve the seven signed files referenced by SHA in the research script from the existing SA10.34 and SA10.41 private Drive artifacts. Place all in one input directory, then:

```bash
python tools/research/sa1043_boundary_compaction.py --root /path/to/frozen_input --out /path/to/isolated_outputs --chromium /usr/bin/chromium
python -m pytest -q tests/zerobase/test_sa1043_boundary_compaction.py
```

Dependencies: Python, NumPy, OpenCV, Pillow, Playwright and Chromium. Output directory must not contain or be an ancestor/descendant of the signed input directory.
