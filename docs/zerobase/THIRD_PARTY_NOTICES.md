# ZeroBase Third-Party Notices and Model Provenance Policy

This file records the release-gate policy for third-party components used by Minimalizer ZeroBase.
Code-package licenses and model/checkpoint licenses are tracked independently.
No model weights are redistributed merely because a wrapper library has a permissive license.

## Baseline code dependencies

- OpenCV: Apache-2.0. Deterministic classical CV and geometry utilities.
- scikit-image: BSD-3-Clause. SLIC, region, morphology, and evaluation utilities.
- MediaPipe repository code: Apache-2.0. Optional structural evidence only; selected model assets require separate verification.
- rembg package: MIT. Optional foreground evidence only; bundled/downloaded model assets require separate provenance/license verification.
- SAM 2 code/checkpoints: Apache-2.0 per upstream project, optional promptable segmentation Adapter.

## Experimental dependencies

SAM 3.x/3.1 and Grounded SAM 2 remain experimental only. They are not required by the deterministic baseline. Exact selected versions, composed dependencies, model/checkpoint terms, and redistribution rights must be audited before production promotion.

## Release rule

A future release that adds or changes a third-party package, model, checkpoint, or redistributed asset must update this notice with the exact selected artifact and applicable terms. Missing provenance or ambiguous redistribution rights fail closed and block promotion of that capability.
