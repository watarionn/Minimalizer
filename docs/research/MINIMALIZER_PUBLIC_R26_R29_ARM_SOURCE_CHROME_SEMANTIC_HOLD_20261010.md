# MinimalizerPublic R26–R29: signed right-arm source-background candidate and genuine Chrome HOLD

2026-10-10. **R26–R29 engineering and two-case diagnostics COMPLETE. No source-semantic owner correction approved, release NO-GO.**

## Baseline, provenance, safe boundaries

This is an isolated research branch stacked on R25 Draft PR #378. Signed input authority:
- Original GC001/Raden RGBA photos, original Phase04 signed face/left/right-arm masks and complete original SA10.34 Stage8 11-owner source geometry (SHA-256 pinned by previously tested R25/R17 validators).
- Independently frozen R25 real Chrome 340px/source/reference error attribution (JSON SHA-256 `5f7bb72c101c3254a8e2f9beb0c60063d2bb484518dcced12f96726fcd8bd9aa`).
- Actual R6 conservative 15-gate release report: eight critical gates remain BLOCKED.

The only new source pixel observation is an exact RGB match to the *dominant opaque border RGB* **4-connected** to the source boundary. This is **NOT** an arm/background anatomy oracle. Pixel alpha must be exactly 255 for candidate subtraction; other source alpha and original Stage04 identity are protected. No new source pixels, no generated fill, no invented pose, no palette reassignment, no facial microfeatures, no modifications to Local Worker/web production/GitHub main. All candidate masks, original photos and private boards **remain in Google Drive, never public GitHub**.

## R26: original-source-only conservative right-arm subtraction (not approved)

Start from exact existing signed Stage04 right-arm masks, subtract only fully opaque exact source-border-connected background-RGB pixels, and create *separate* private research candidate. No other part masks are edited. Observe mask area, 2px eroded interior/boundary location, two-dimensional topology, and source color intersection.

| Original | Original signed right-arm pixels | Exact source-border RGB overlap | Fully opaque subtraction trial | Partly transparent pixels held unchanged | Removed pixels within arm interior | Remaining candidate pixels |
|---|---:|---:|---:|---:|---:|---:|
| GC001 | 6,486 | 533 | **520** | 13 | **494** | **5,966** |
| Raden | 9,870 | 3 | **3** | 0 | **1** | **9,867** |

GC001 removal is **494/520 inside the 2px eroded arm**, so it must not be marketed as a benign boundary tweak. Current candidates retain each original component count (GC001 1; Raden 2) but modify internal topology/contours. Approximate contour vertex count in the independent mask-to-SVG reconstruction **increases**: GC001 **199→242 (+43)**, Raden **167→174 (+7)**. The original signed Stage8 source ring budgets are unchanged and still fail GC001 **3,604 > 1,887** and Raden **2,370 > 1,412**.

These are observational candidate masks **only**. They do not prove anatomy or a better original source-owned right arm. The Raden near-zero observation is a strong warning against blanket generalization.

## R27: actual independent Chrome 340 / 680 candidate-mask SVG rendering

The study uses the existing canonical `_binary_mask_svg` source pixel contour serializer, including nested contour/hole roles, **as a diagnostic right-arm-only SVG**. This is **not** a new full-character release candidate, Stage8 official mask authority or an assertion of equivalence to the official complete SVG. Browser results from a genuine Windows Chrome host:

| Case | Signed right arm → candidate pixels | Chrome 340px changed | Chrome 340px changed outside deleted pixels | Chrome 680px changed | Chrome 680px changed outside deleted pixels |
|---|---:|---:|---:|---:|---:|
| GC001 | 6,486→5,966 | **549** | **35** | **2,232** | **164** |
| Raden | 9,870→9,867 | **5** | **3** | **23** | **13** |

Strict browser image compared to ideal signed 340px mask still differs, even before modification: GC001 215 pixels at 340 and 1,009 at 680; after: 244/1,161. Raden signed 254/871, after 256/882. Both actual candidate SVG serializations cause pixel changes **outside explicitly removed source pixels**. Thus no honest `ChromeExact=true` is possible and both are rejected for product promotion. This source-only diagnostic has real graphics differences even when original bitmap masks are perfectly isolated.

No embedded binary source image or new generated art is used in the SVG. `source geometry not invented` does NOT imply exact Chrome pixel parity.

## R28: independent two-original-source comparison and semantic abstention

- Neither subject has the required independently validated *source-photo-only* multi-observer semantic part anchor indicating whether the exact RGB connected pixels inside an arm belong to anatomy or background.
- GC001 has 520 proposed removed (494 within interior) but Raden only 3. Automatically applying the same rule would erase potentially valid arm pixels without source-grounded human or independent model certification.
- Protected signed face and left-arm masks were byte-locked and left unchanged, but unchanged masks are not an independent proof of semantic quality.
- Neither change touches clothing/tie/staff ownership. Those remain independently unverified. The face-hidden contract remains unchanged.
- R28 formal outcome: **`ABSTAIN_SEMANTIC_ANCHOR_MISSING`**. Neither candidate may be used in production.

## R29: fail-closed baseline-to-release integration

R29 requires the exact signed R25 SHA, original Stage8 11-owner/source pins, both independent original subject measurements, explicit browser diagnostics **at both sizes with nonzero pixel spill**, and the unchanged R6 eight-blocker verdict. Tampering any source SHA, claiming independent semantic approval without evidence, pretending the candidate is Chrome-exact or ignoring the unchanged original Stage8 cap fails the gate.

Formal state:
`R26=SOURCE_OPAQUE_RGB_CANDIDATE_MEASURED_NOT_ANATOMY`
`R27=CANONICAL_340_680_CHROME_MASK_RASTER_DIAGNOSTICS_MEASURED`
`R28=TWO_SIGNED_SOURCES_COMPARED_SEMANTIC_ABSTAIN`
`R29=EVIDENCE_PACKAGED_AND_PRODUCTION_NO_GO`.

No release authorization. R6 eight original BLOCKED remain including original Stage8 vertex cap, human Golden, Approved18/78, source arm/clothing/staff semantics, full-scene DPR2 Facet cross renderer, real physical iPhone Safari, MPL license review, and real production cache/rollback acceptance.

## Actual verification and artifact handling

- GitHub contains source-agnostic code, independent tests and this numeric report only: `scripts/verify_public_r26_r29_source_owner_candidates.py` and `tests/test_public_r26_r29_source_owner_candidates.py`.
- **176/176 selected Public R1–R29 and Local/Public regression tests PASS**, including 21 R26–R29 cases with genuine Chrome 340/DPR2, tampered source/owner, untrusted alpha mask, false semantic signoff, R6 blocked bypass and no route mutation.
- Two independent Chrome runs produced **five/five bitwise-identical private evidence files**: GC001/Raden masked source review boards (2), GC001/Raden grayscale candidate signed-right masks (2), exact coordinate-free R26–R29 JSON (1). JSON SHA-256: `b9bee5cecb6f80c4d8b6f14e645a5e1e3587f3b919d0f1a32079b997efbe235a`.
- Private artifacts are stored under `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R26_R29_20261010` with SHA readback. Never publish original-source RGB or derived masks in public GitHub. The baseline PNG and Stage8 signed files stay immutable.

**R30 follow-up**: obtain truly independent source-only semantic arm/garment anchors with weights/annotation provenances and licenses, preferably both cases, before proposing source-owner remapping. Separately investigate reproducing signed raster within Chrome in R27 without altering stage8/source. Candidate-specific visual Golden review needed before any promotion.
