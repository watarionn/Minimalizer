# SA10.60C / Campaign C02a: original GC001 Phase03→Phase04 owner provenance

Date: 2026-10-09 (JST). **READ-ONLY RESEARCH AUDIT PASS, C02 QUALITY STILL IN PROGRESS / NO-GO FOR PROMOTION.** The previous C01 finding that Phase04 was the *earliest examined* stage is historically retained, but **superseded for the examined chain** by newly recovered authentic Phase03 evidence. This is a source-bound image observation, **not** a proven complete semantic segmentation ground truth.

## Newly recovered signed stage authority

Unlike the earlier archived C01 candidate, this study retrieved the **actual original** GC001 Phase03 and Phase04 workspace artifacts and manifest files. The original local workspace was used **only** to recover them; a byte-pinned copy is now saved in the approved private Google Drive, not treated as local canonical truth:

`chatGPT及びCodex用/Minimalizer/Campaign_SA1060_to_Production_20261009/C02_Phase03_Phase04_Provenance_20261009/GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip`

The ZIP has 19 stage files and one manifest and is SHA-256 pinned to `89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434`. Every stage output is checked against its signed stage JSON and every embedded file against the ZIP manifest. The original GC001 RGBA source is independently pinned to `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. Phase04 stage JSON explicitly binds the unchanged Phase03 mask SHA `af694550c7e4d60524aed51df997ebd03ebb1f40cef7425aa975590245c2e7c7`.

Phase03 used `rembg / isnet-anime`, reported alpha foreground ratio **0.996816609** (uninformative), and selected the rembg canonical subject mask (foreground ratio **0.476150519**). Phase04 then used `rtmlib` whole-body structure, `mediapipe` selfie multiclass semantic hints, seeded hair color, and unknown-region rescue. These are factual configuration records, not a causal attribution to one model or heuristic. Raw Phase03 was **not** available during the original C01 source-ring analysis.

## Objective recorded source observations

A conservative four-connected exact RGB border flood, anchored to dominant opaque scene-border RGB and checked against original RGBA, counts **35,514** connected original pixels. This is a *background-color risk observer*; foreground hair may share this RGB, and no pixel is automatically deleted or relabelled. In the recovered original stages:

| Region | Total pixels | Exact RGB source-border-connected overlap |
| --- | ---: | ---: |
| Phase03 subject mask | **55,043** | **648** (635 opaque, 13 partial alpha) |
| Phase04 original right_arm | **6,486** | **533** (520 opaque, 13 partial alpha) |
| Phase04 original hair | **17,541** | **31** |
| Phase04 original left_arm | **2,330** | **0** |
| Phase04 original face | **4,937** | **0** |
| Phase04 original major_clothing | **3,217** | **0** |

All checked original Phase04 masks are subsets of the Phase03 subject. Therefore **the same 533 exact-connected source pixels counted in the Phase04 right arm were already admitted as Phase03 subject**, and the earliest *newly accessible examined* stage is **Phase03**, not Phase04. The extra 115 Phase03 RGB matches were distributed among other parts or unknowns. This neither proves the entire RGB-matched region is non-person nor establishes whether Phase03 input preprocessing, rembg output, pose, or unknown rescue caused the eventual arm label.

## Major historical provenance divergence: left arm

The SA10.41 signed Phase04-derived `left_arm` mask, already archived as the research authority, has **2,715** pixels, while the **currently recovered original Phase04 workspace** contains **2,330**. They are **385 pixels different**, all present only in the earlier signed historical mask (current is a strict subset of historical at binary-raster level). `right_arm` is 6,486 in both with **0 XOR**; `face` is 4,937 with **0 XOR**. The original source bytes remain the same, but the **source Stage04 provenance was not identical** across runs:

- Currently recovered Phase04 original left PNG SHA: `cb707edab78c6d0715de5fcb811f6e0595baa53c9f5c8cd3290be420ba06061d`.
- Historical original Phase04 left input SHA from the saved SA10.41 metrics: `303e52490b7ff9f04079682345e1822ac0cba90775df98b1ce7f23a7a0f95130`.
- Historical **re-encoded signed research PNG** SHA is `49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f`. Re-encoding explains the *bytes* mismatch for face/right arm but **cannot explain** the 385 changed left-arm mask pixels.

This is a source-version consistency HOLD. Never relabel the currently recovered Phase04 masks as interchangeable with the old signed research left arm or pass source-integrity gates by exchanging SHA fields. The old research Stage8/SVG/arms still follow their originally signed authorities; current raw workspace is an additional versioned source evidence branch.

## Engineering validation

- `tools/research/sa1060c_phase03_phase04_provenance.py` is a **read-only** pin-verified audit. It requires a separate original source, historical signed source assets, and the immutable new stage snapshot; rejects corrupted SHA, unbound stages, wrong role masks, forged release flag, missing data, and output to a signed-input directory.
- 12/12 focused tests PASS, including real original signed Phase03/04 replay and private review board output; deterministic two-run hash checks for board and both JSON reports included.
- Additional private board overlays **original source**, **Phase03 subject**, **current Phase04 right arm** and **the 385-pixel historical left-arm difference**. Actual mask polygons/positions and input image remain private. GitHub exposes only source-independent verifier, tests, this sanitized report and coordinate-free metrics.
- Source image never embedded in SVG; no generated fill, no face microfeatures, no production renderer, no visual candidate promoted, no Stage8 policy relaxation.

## Decision and next

**C02a original-stage provenance and first-checked-stage correction: COMPLETE. C02 artistic reconstruction/quality recovery: IN PROGRESS / visual HOLD.** Before any revised painter is promoted, distinguish genuine arm from flowing side hair, sleeves and background using original RGB/alpha plus model output and source/topology evidence; design an independent **source-frozen versioned Phase03/Phase04 candidate**, then test Raden and additional signed holdouts, full Chromium at real vertex budget, and authentic human Golden. The private Stage03/04 source copy is accessible via Google Drive so repeated RDC is unnecessary.

**C03 historic source Stage8 rings** still FAIL (Raden 2,370/1,412; GC001 3,604/1,887). **C04 human Golden and Approved-18/78** still PENDING. C05–C08 cannot be marked completed or deployed by these numerical audits. Production remains unchanged.
