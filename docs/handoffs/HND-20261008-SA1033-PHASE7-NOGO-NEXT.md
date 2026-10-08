# HND-20261008 SA10.33 Phase7 → Phase8 (NO-GO)

## Exact starting point

- Repo `watarionn/Minimalizer`.
- Draft PR #223, head branch `research/sa1032-svg-contour-proposals`. **Do not merge/deploy.**
- Phase7 report: `docs/zerobase/SA10_33_PHASE7_REAL_HARD_GATES_20261008.md`.
- Source of truth: GitHub; image evidence on Drive only under `chatGPT及びCodex用/Minimalizer` if saved there. This handoff requires no live local worker/GUI operation.
- Existing Phase6 owner metrics are **superseded** because the custom renderer was noncanonical. See corrected report before drawing conclusions.

## What is finished

- Exactly reproduce historical GC001 Phase12 serialized 11 primitives AND preview pixels, source/policy hashes, full silhouette metrics and previously recorded global failure.
- Independent second real case Juufuutei-Raden sourced from repository corpus and archived Phase04/11; Stage12 run in isolated temp folder.
- Cross-case distinct source evidence PASS, both structural quality FAIL.
- GC001 source → render lost 23 tiny hair pixels, 18 tiny left-arm pixels. Raden lost 3 tiny hair pixels.
- GC001 source union (1,9) → render (2,21); Raden source union (1,3) → render (1,8). Both FAIL original hard gate.
- Both images: serialized vector rings do not rasterize identically to preview masks for face/hair/left/right arm. Part XOR GC001 [12,204,26,18]; Raden [15,134,29,18].
- Hair/arm visibility is not lost due to z-order in these specific cases; every owned arm pixel survives pre-face-guard paint order.
- Broader local tests 48 passed. GitHub focused CI success (latest branch head to be verified).
- Three Phase7 machine-readable evidence files under `docs/zerobase/evidence/sa1033_*.json`.

## Root technical fact

`minimalizer_zerobase/simplification/style.py`, inside `_candidate_for_profile`, sets `mask=group["mask"].astype(bool).copy()` for `source_mask_replay`, **after** independently serializing `parameters.rings`. Thus the actual rendered image uses a protected source-derived pixel mask while re-rasterizing exported polygon rings may differ. **Do not assume the polygon matches preview.**

`_candidate_for_profile` also discards components smaller than `group_min_area`, set to 2 for structural source repair. This removes source tiny fragments (the observed 23, 18, 3 px), causing raw topology mismatches. A separate canonical `material_topology` tiny-component threshold of 8 removes those fragments for diagnostics but MUST NOT replace the original raw hard gate without policy change explicitly approved by user.

## Phase8 execution order

1. Create a fresh research branch/PR from Phase7 state or continue PR #223 as a draft, with isolated changes and new tests. Do not affect deployed BrowserFallback or local worker until gated.
2. Preserve source-owned micro-islands and hole topology *within existing owner primitives* without inventing geometry or altering owner/material count. Prove exact raw source topology; measure geometry budget and avoid jagged outlines. Separate visually meaningful islands from noise in **evidence**, without silently discarding either.
3. Make the serialized vector geometry and selected render mask authoritative together: re-rasterize `parameters.rings` using the **same** production `cv2.drawContours` routine, compare pixel and topology, fail-closed if drift. Do NOT paint source pixels into an SVG or use a raster overlay to hide vector problems.
4. Repeat exact historical GC001 and independent Raden outputs; require zero source topology hard failures, strict geometry/export agreement, arm/face safeguards and budget invariants; then expand to at least one other new real case.
5. Run full regression and obtain independent human visual approval before any PR merge, deployment or quality claim. Existing failure evidence cannot be overridden by a high IoU, canonical normalization or synthetic test.

## Reproduction CLI

```powershell
python -m tools.run_sa1033_gc001_full_gate --case-dir <case_dir> --source <original_input> --phase12-dir <phase12_output_dir> --benchmark <historical_metrics.json> --output <safe_evidence.json>
python -m tools.run_sa1033_crosscase_gate --case GC001=<first_report.json> --case Raden=<second_report.json> --output <summary.json>
```

No source pixels were generated, face details were not added, and no production changes were made.

## Mistake prevention

Do not use ad-hoc ring rasterization in evaluation. Always import and call the actual `rasterize_primitive_candidate` for polygon geometry. When a production path uses separate source-mask replay, report **both** paths and protect the discrepancy as an independent hard failure. Include an explicit `structural_support_only` filter when computing the painted subject silhouette; invisible support geometry must never contaminate the rendered silhouette gate.
