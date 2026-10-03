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
