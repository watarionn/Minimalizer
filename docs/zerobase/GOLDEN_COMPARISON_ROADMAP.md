# Golden Comparison Development Roadmap

Status: G8 CONTRACT CLOSED / ADOPTION HOLD

G1 Golden Harness [CLOSED / PASS]: freeze source/golden/current triplet, schema, hashes, deterministic comparison report.
G2 Semantic Feature Manifest [CLOSED / PASS]: generic schema plus Case 001 benchmark manifest.
G3 Feature Survival Gate [CLOSED / PASS]: required/optional/forbidden semantics; fail-closed evidence.
G4 Semantic Feature Budgeter [CLOSED / PASS]: allocate primitive budget by semantic importance and recognizability rather than pixel area.
G5 Geometry Re-authoring PoC [CLOSED / PASS]: deterministic macro primitives and category compression grammar. VTracer may fit already-authorized masks, never decide semantics.
G6 Golden Gap Evaluator [CLOSED / PASS]: semantic, geometry, palette, composition, economy and orphan-contour dimensions. Add feature-level DINO evidence.
G7 Guarded DiffMin Integration [CLOSED / PASS]: refine accepted authored geometry only; same-renderer baseline; default OFF.
G8 Blind Generalization Gate [CLOSED / HOLD]: gate and sealed five-character blind corpus are fixed; adoption waits for production integration and real blind outputs.

## G1 closure

Merged by PR #72 at main commit `d0c20e896766768ccf22156ffa794edbb3e9781d`.

Canonical Golden Case 001 is bound by role, Drive file ID, and SHA-256 rather than filename alone. The harness is isolated from production behavior and treats the golden as evaluation-only evidence, never as a reconstruction input.

Validation on a clean detached worktree:
- focused Golden Harness tests: 4 passed
- full `tests/zerobase`: 255 passed
- `git diff --check`: PASS
- production behavior changes: none

## Parallel work
Nao: VTracer isolated PoC; feature-level DINO experiment; support G2/G3 schema/tests on feature branches.
Rinka: benchmark authority, visual review, architecture decisions, Golden Gap semantics, independent review and adoption.
Nao works on feature branches. Rinka reviews before merge.

## Research queue
P0 VTracer 1.0
P0 DINOv3 local feature evidence
P1 LIVE progressive allocation
P1 Layered Vectorization architecture study without SDS/generative component
P2 SuperSVG/Morphea comparison
P2 CLIPasso concepts only due licensing/fit constraints

## Gates every stage
focused tests; tests/zerobase regression; deterministic rerun hashes; git diff --check; visual artifact review; Drive preservation of visual/evaluation evidence.

## G2 closure

G2 adds a generic semantic feature manifest contract plus GC001 authority data without golden geometry coordinates. Required identity features are orange hair, goggles, green necktie, and navy-white uniform. Hair ornament is important/optional; badges and armband are symbolic/compressible; facial details are forbidden/omit. Semantic evaluation regions reference feature IDs only.

Validation before merge:
- focused semantic manifest tests: 8 passed
- full `tests/zerobase`: 263 passed
- `git diff --check`: PASS
- G1/G2 case identity linkage: PASS
- production behavior changes: none


## G3 closure

G3 adds a generic fail-closed Feature Survival Gate over the G2 semantic contract. Required features must be present; absent, unknown, or missing evidence hard-fails. Forbidden features must be absent; present or unknown evidence hard-fails. Optional features do not hard-fail when absent or unknown. Perceptual scores are recorded but cannot override hard failures, and observer confidence remains evidence rather than semantic authority.

Validation before merge:
- focused Feature Survival tests: 13 passed
- full `tests/zerobase`: 276 passed
- `git diff --check`: PASS
- perfect perceptual score cannot offset required-feature loss: PASS
- production behavior changes: none


## G4 closure

G4 adds a generic deterministic Semantic Feature Budgeter. Required features reserve their minimum primitive budget before optional features. Insufficient total budget fails closed rather than deleting required identity. Important optional features receive their minimum before compressible optional features; forbidden/omit features receive zero. After eligible optional minima are satisfied, surplus budget remains within the highest semantic tier instead of inflating low-value details. Allocation uses manifest semantics and stable feature IDs, never pixel area or Case-001 names/colors.

Validation before merge:
- focused Semantic Feature Budgeter tests: 13 passed
- full `tests/zerobase`: 289 passed
- `git diff --check`: PASS
- synthetic non-GC001 manifest generalization: PASS
- feature-list reorder determinism: PASS
- production behavior changes: none


## G5 closure

G5 adds a deterministic semantic geometry grammar between the G4 budget and any concrete fitter. Supported families are polygon, ellipse, ring, ribbon, trapezoid, and Bezier silhouette. Known semantic roles receive category grammar; unknown roles use a deterministic generic fallback. Geometry plans contain semantic feature IDs, primitive families, ordinals, and provenance only, with no Golden coordinates, points, boxes, or raster reconstruction targets.

Authorized fitting is fail-closed: manifest owns semantic identity, G4 owns primitive count, grammar owns allowed primitive families, and a native/VTracer fitter may only fit an already-authorized semantic mask. The fitter cannot decide semantics.

Validation before merge:
- focused Geometry Grammar tests: 10 passed
- full `tests/zerobase`: 299 passed
- `git diff --check`: PASS
- manifest/allocation reorder determinism: PASS
- synthetic unknown-role fallback: PASS
- unauthorized VTracer mask/feature/primitive rejection: PASS
- production behavior changes: none


## G6 closure

G6 adds a diagnostic Golden Gap evaluator that preserves eight dimensions separately: semantic survival, recognizability, geometry abstraction, palette-role preservation, composition/negative space, primitive economy, orphan-contour penalty, and feature-local evidence. A diagnostic mean is reported for inspection only and cannot override G3 hard failures. Candidate comparisons expose every per-dimension delta and regression instead of hiding them behind an aggregate.

Feature-local DINO/observer evidence is explicitly non-authoritative and can be bound to manifest-authorized feature IDs; unknown feature evidence fails closed. Perfect diagnostic and DINO evidence cannot rescue a candidate with a required-feature hard failure.

Validation before merge:
- focused Golden Gap tests: 13 passed
- full `tests/zerobase`: 312 passed
- `git diff --check`: PASS
- perfect-score hard-fail override rejection: PASS
- per-dimension regression visibility: PASS
- unknown feature-local evidence rejection: PASS
- production behavior changes: none


## G7 closure

G7 adds a fail-closed Guarded DiffMin contract. DiffMin is default OFF. When explicitly enabled, it requires a pre-refinement G3 hard-gate PASS candidate and the same renderer for baseline and candidate. It may optimize parameters of existing authored geometry only; semantic-part creation/deletion/substitution and primitive count/identity changes are rejected before refinement and validated again after refinement. Duplicate primitive identities are rejected so set comparison cannot hide count changes. Post-refinement G3 hard gates must still PASS.

Validation before merge:
- focused Guarded DiffMin tests: 11 passed
- full `tests/zerobase`: 323 passed
- `git diff --check`: PASS
- default OFF: PASS
- pre/post hard-gate dominance: PASS
- same-renderer enforcement: PASS
- add/delete/substitute/duplicate primitive rejection: PASS
- production behavior changes: none


## G8 closure

G8 closes the Golden Comparison design/guardrail cycle with a fail-closed blind generalization gate and a sealed five-character corpus selected from the user-provided `HoloMenImages.zip`: AZKi, IRyS, Gawr Gura, Ceres Fauna, and Nanashi Mumei. The archive SHA-256 and each selected source SHA-256 are frozen in `benchmarks/golden/blind/GBLIND_HOLOMEN_20261005.json`. No blind case has a Golden image. G2-G7 rules were frozen at main `df3e757df697035ab3ac73b9f0fad6a5a3f06739` before the blind corpus was sealed.

Adoption decision: **HOLD**, not PASS and not REJECT. G2-G7 deliberately introduced no production behavior changes, so there is not yet an integrated candidate path from which real blind improvement can be demonstrated. The gate therefore refuses a false adoption. After the generic production bridge is implemented, the sealed cases must be run without changing G2-G7 rules. ADOPT requires every case to hard-PASS, have no dimension regression, and demonstrate improvement; one failed/regressed character blocks adoption and no aggregate score may hide it.

Validation before merge:
- focused Blind Generalization tests: 9 passed
- full `tests/zerobase`: 332 passed
- `git diff --check`: PASS
- minimum multi-character requirement: PASS
- Golden-free blind case enforcement: PASS
- per-character failure/regression visibility: PASS
- false adoption without production integration: blocked as HOLD

Next production milestone: generic G2-G7 production bridge [IMPLEMENTED / DEFAULT OFF] -> authorized geometry fitting/rendering -> sealed blind execution -> Rinka visual review -> ADOPT or REJECT. Blind outcomes are evaluation evidence, not tuning targets.



## Production Bridge closure

The generic production candidate bridge connects G3 Feature Survival, G4 Semantic Budget, G5 Geometry Grammar, and G7 Guarded DiffMin under one fail-closed runtime-facing contract. It is default OFF and does not alter the existing ProductionPipeline route. A G3 hard failure blocks authorization before budget or geometry creation. DiffMin remains separately opt-in. Golden raster input is rejected at the API boundary as evaluation-only evidence.

Validation before merge:
- focused Production Bridge tests: 6 passed
- full `tests/zerobase`: 338 passed
- `git diff --check`: PASS
- generic non-GC001 manifest: PASS
- Golden raster production-input rejection: PASS
- existing production route behavior: unchanged

Next: authorized geometry fitting/rendering [IMPLEMENTED] -> bind upstream semantic observation/masks for the sealed five-character G8 corpus -> same-renderer baseline/candidate execution -> Rinka visual review -> ADOPT or REJECT.


## Authorized Geometry Fitting / Rendering closure

A deterministic fitting layer now consumes only the G5-authorized geometry plan, explicitly authorized semantic masks, and palette assignments bound to those same authorized features. Missing, unauthorized, extra, or duplicate semantic identities fail closed. Native and VTracer-labelled fitting paths share the exact same semantic/primitive authority; the fitter cannot decide feature existence or primitive count. Output is rendered through the canonical SvgRenderer and records that no Golden raster was used.

Validation before merge:
- focused Authorized Geometry tests: 7 passed
- full `tests/zerobase`: 345 passed
- `git diff --check`: PASS
- deterministic same-renderer SVG: PASS
- unauthorized/extra mask rejection: PASS
- unauthorized palette-feature rejection: PASS
- fitter semantic/count invariance: PASS

Next: blind semantic observation/mask binding [IMPLEMENTED / OBSERVER CAPABILITY HOLD] -> connect a real frozen semantic observer runtime -> sealed five-character same-renderer execution. Frozen G2-G7 rules remain untuned.


## Blind Semantic Observation / Mask Binding closure

A fail-closed binding layer now converts observer evidence into Golden Comparison feature evidence and authorized masks. Exactly one observer record must carry the manifest semantic role plus valid geometry before a feature can become present. Missing, unlabeled, ambiguous, or geometry-less observations become unknown and receive no mask. Manual semantic labels and Golden images are not part of the binding path.

Repository capability audit found region-level SLIC evidence and existing part-binding infrastructure, but no connected real runtime that assigns arbitrary blind images the Golden Comparison semantic roles required by the frozen manifests. DINO/SAM remain observer/hypothesis contracts, not semantic authority. Therefore real sealed-corpus execution remains HOLD rather than contaminating the blind benchmark with human labels.

Validation before merge:
- focused blind observation tests: 5 passed
- full `tests/zerobase`: 350 passed
- `git diff --check`: PASS
- unlabeled/ambiguous observation -> unknown: PASS
- manual semantic label path: absent
- Golden usage: absent

Next: frozen Grounded-SAM semantic observer [CONNECTED] -> run sealed five-character observer corpus -> bind untouched evidence -> same-renderer baseline/candidate execution.


## Frozen Grounded-SAM Observer connection

The previously validated Phase E Grounded-SAM stack is now the frozen real semantic observer for Golden blind evaluation. The model pair and thresholds are unchanged: IDEA-Research/grounding-dino-tiny + facebook/sam-vit-base, active semantic threshold 0.20. A ZeroBase adapter converts thresholded semantic confidence maps into immutable labelled bbox Evidence for the blind binder. It cannot lower the threshold or invent finer semantic labels; for example accessory remains accessory rather than being guessed as goggles/ribbon/etc.

Local runtime smoke validation on the existing isolated observer environment:
- Python environment: C:\\Work\\SharedAI\\minimalizer-observers
- PyTorch: 2.11.0+cu128
- CUDA available: true
- Transformers: 5.17.0
- Grounding-DINO tiny load: PASS
- SAM ViT-B load: PASS
- GPU frozen observer runtime: READY

Repository validation:
- focused frozen-observer + blind-binding tests: 10 passed
- full `tests/zerobase`: 355 passed
- `git diff --check`: PASS

Sealed five-character Frozen Observer run: COMPLETE. Promotion into per-character feature binding is HOLD because no per-character semantic feature manifests were frozen before the first blind outcomes. Creating them now would contaminate the blind gate. Next: define a fresh blind suite with pre-frozen evaluation manifests, then execute it once through observer -> binder -> production candidate -> renderer.


## Sealed five-character Frozen Observer run

The frozen GBLIND_HOLOMEN_20261005 corpus was executed once without changing prompts, thresholds, G2-G7 rules, or source membership. Archive SHA-256 and all five member SHA-256 values matched the sealed manifest before inference.

Frozen Grounded-SAM completed 5/5 on CUDA. Hair, face-skin, limb, and accessory all had non-zero active evidence on all five cases. Mean inference time was 0.567 s/image, peak allocated CUDA memory 1378.6 MB, and one oversized IRyS hair detection was rejected by the already-frozen Phase E guard.

Machine-readable summary: `benchmarks/golden/blind/GBLIND_HOLOMEN_20261005_OBSERVER_RUN.json`.
Full NPZ evidence, contact sheet, rembg masks, report, and input manifest are preserved in Google Drive as `GBLIND_HOLOMEN_20261005_frozen_observer_run.zip` with SHA-256 `de498aa0769c7aa48665d93dc4b603d69123247d69e3a48fa514ad942ea14892`.

Binding/adoption remains HOLD. The original G8 freeze did not include per-character semantic feature manifests. Creating those after seeing this blind run would leak outcome knowledge into the benchmark. The gap and prevention rule are recorded in `docs/incidents/INC-20261005-golden-blind-manifest-freeze-gap.md`.

No human labels were substituted and no post-outcome tuning was performed.


## G9 Pre-frozen Blind Semantic Template

G9 repairs the evaluation-order gap found after the first G8 observer run. A generic semantic evaluation template is now frozen before any fresh blind corpus membership is selected.

Frozen template: `benchmarks/golden/blind/GBLIND_GENERIC_V1.semantic.json`
SHA-256: `8933fbcda7d7723f7ce21ba8d1aed118b0c8a0295297368359a2ad9554e1ccc0`

The template contains only the four roles already supported by the frozen Grounded-SAM observer: hair, face-skin, limb, and accessory. It contains no character names, colors, coordinates, source paths, Golden images, or post-outcome knowledge. Fresh cases may vary only in case ID and sealed source hash; semantic policy is inherited mechanically.

Validation:
- focused G9 template tests: 3 passed
- full `tests/zerobase`: 358 passed
- `git diff --check`: PASS
- template SHA-256 frozen before fresh source selection: PASS

Next: select and seal a fresh Golden-free multi-character corpus without changing this template, then execute exactly once through frozen observer -> binder -> production bridge -> authorized geometry -> same renderer.


## G9 Fresh Blind Corpus Seal

A fresh five-character corpus was selected only after the G9 generic semantic template had been frozen on main. No candidate image was visually inspected for selection. Selection is deterministic: consider archive `list_thumb` PNG/JPG/JPEG members, exclude the five previous G8 basenames, sort by source SHA-256 ascending, take the first five.

Sealed cases: Isaki Riona, Cecilia Immergreen, Takanashi Kiara, Nakiri Ayame, and Nekomata Okayu.

Corpus manifest: `benchmarks/golden/blind/GBLIND_G9_FRESH_20261005.json`
Corpus manifest SHA-256: `d5fa283982e1fc003f4d09c58bb5b64222b9f8c52c50804be1dd9ddab8b0ae45`
Source archive SHA-256: `ef5c0e7a79640dda6b955adc24971dabc6d2b2797949142640f3c0f72b1352e9`
Pre-frozen evaluation template SHA-256: `8933fbcda7d7723f7ce21ba8d1aed118b0c8a0295297368359a2ad9554e1ccc0`

Validation before first observer execution:
- focused G9 freeze tests: 6 passed
- full `tests/zerobase`: 361 passed
- `git diff --check`: PASS
- source selection visual inspection: none
- observer runs on fresh corpus: zero

Next: after this seal is merged to main, execute the first and only untuned frozen-observer run, then bind the inherited generic manifest and continue to production candidate rendering.
