# Real observer runtime gate

This directory is research-only. It must not modify Minimalizer production requirements.

## Reuse before install

Minimalizer already validated an isolated RTX 5060 semantic observer environment in Calibration 06 Phase E:
Python 3.11.9, Torch 2.11 CUDA 12.8, Transformers 5.17, Grounding-DINO tiny + SAM ViT-B. Reuse cached model assets/environment when present rather than duplicating the ~4.47 GB environment.

## Required real evidence

P5 adoption remains HOLD until Diagnostic-2 (Hyakuto Kyoko / Raden) has:
1. real frozen semantic features from a pretrained observer;
2. real semantic-region masks from an analysis-only segmentation observer;
3. baseline and refined renders bound to the same source;
4. deterministic repeat;
5. machine A/B result plus mandatory human visual QA.

Synthetic/injected test observations never count as corpus evidence.


## Recovery probe 2026-10-03

A narrow local search found a pre-existing non-Minimalizer environment at `C:\\Work\\Benchmarks\\memory-compare-20260928\\.venv` whose installed package tree includes Torch, Transformers, and Transformers SAM/SAM2/SAM3 modules. This is a **reuse candidate only**, not a canonical dependency. Direct read-only execution of that environment was blocked by the remote-operation safety gate, so no mutation, package install, or model download was attempted.

The expected Hugging Face cache directories for `IDEA-Research/grounding-dino-tiny` and `facebook/sam-vit-base` were not confirmed by the narrow probe. Therefore the old Phase E model weights must not be assumed present.

Recovery policy: do not bind Minimalizer to the benchmark environment. If execution access is later available, inspect its exact Torch/Transformers/CUDA versions and cached model availability read-only. Reuse only shared model/cache assets or reproduce a dedicated observer environment from a pinned manifest. Production requirements remain unchanged.


## Reuse decision 2026-10-03

Read-only inspection shows the benchmark venv is Python 3.11.9 but Torch 2.14.0+cpu with no CUDA build, and Transformers 5.15.1. It is rejected as the Phase E GPU observer runtime. The standard Hugging Face hub cache also does not contain the Phase E Grounding-DINO tiny or SAM ViT-B model directories.

A research-only observer-runtime.lock now records the previously validated Phase E target versions and model IDs. DINOv3 stays unresolved until an official compatible model identifier is verified rather than guessed.

Gate result: environment/cache recovery is complete. Existing assets cannot close the runtime gate. Next is one shared observer environment from the pinned target, followed by Diagnostic-2 real measurements.


## Runtime smoke 2026-10-04

- Shared environment: `C:\\Work\\SharedAI\\minimalizer-observers` (research-only; production requirements unchanged).
- PyTorch 2.11.0+cu128 on NVIDIA GeForce RTX 5060: PASS; real CUDA tensor computation completed.
- Transformers 5.17.0: PASS.
- Grounding-DINO `IDEA-Research/grounding-dino-tiny`: PASS; real model loaded on CUDA, about 660 MiB allocated at smoke point.
- SAM `facebook/sam-vit-base`: PASS; real model loaded on CUDA, about 358 MiB allocated at smoke point.
- DINOv3 `facebook/dinov3-convnext-tiny-pretrain-lvd1689m`: HOLD. The official Hugging Face repository is gated and returned HTTP 401 without user authentication. Meta's official DINOv3 README likewise requires obtaining model-weight access before pretrained-weight use. No credential was requested, stored, or bypassed.

Gate decision: observer runtime infrastructure PASS for CUDA + Grounding-DINO + SAM; DINOv3 pretrained semantic observer remains HOLD on an external access prerequisite. Diagnostic-2 may exercise the regional observer path now, but a DINOv3-backed adoption decision remains fail-closed until official pretrained weights are legitimately available.


## Diagnostic-2 source binding 2026-10-04

Canonical source identity was resolved without using the dirty local repository as authority.

- Hyakuto-Kyoko: `Hyakuto-Kyoko_list_thumb.png`, 340x340 RGBA, SHA-256 `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`.
- Juufuutei-Raden: `Juufuutei-Raden_list_thumb.png`, 340x340 RGBA, SHA-256 `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`.
- GitHub stage manifests supplied the canonical names and hashes.
- Google Drive supplied the binary PNGs.
- Both downloaded binaries were independently SHA-256 verified and exactly match the GitHub stage-manifest hashes.

This closes the Diagnostic-2 source-provenance gate. Observer measurements must bind evidence to these hashes; filename-only selection is prohibited.


## Diagnostic-2 real Grounded-SAM observation 2026-10-04

The shared observer runtime was verified on the RTX 5060 with Python 3.11, torch 2.11.0+cu128, CUDA available, and Transformers 5.17.0. Cached observer weights were reused with local-files-only for the final two-case run.

The exact SHA-bound Diagnostic-2 inputs were evaluated with `IDEA-Research/grounding-dino-tiny` + `facebook/sam-vit-base` using the existing Phase E prompt and rembg subject authority.

Results:

- Hyakuto-Kyoko active-area ratios: hair 0.0501903, face-skin 0.0291003, limb 0.0151298, accessory 0.0768339; 20 accepted detections, 0 oversize rejects; 1.100 s.
- Juufuutei-Raden active-area ratios: hair 0.1448270, face-skin 0.0241436, limb 0.1239792, accessory 0.0215225; 19 accepted detections, 2 oversize rejects; 0.263 s.
- Two-case mean inference time: 0.681693 s/image.
- Peak CUDA memory: 1378.613 MB.
- No zero-area semantic channel for hair, face-skin, limb, or accessory.
- Spatial confidence maps were emitted as per-case NPZ files plus a contact sheet and report JSON in the isolated local evidence directory.

Interpretation: real regional observation is now operational on Diagnostic-2 and is no longer represented only by injected test fixtures. This is observation evidence, not yet an adoption PASS. The current `RegionObservation` coverage contract still cannot prove spatial IoU/shape retention, so the next evaluation step must bind these spatial maps to an immutable overlap descriptor before any strong regional-retention claim.
