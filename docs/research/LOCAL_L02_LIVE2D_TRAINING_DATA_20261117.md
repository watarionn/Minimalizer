# L02 observer training data boundary (2026-11-17)

## Purpose

This document records the source-free import boundary for a future L02
observer trained on characters other than H04/H06/H08. It is not a Phase4
receipt, a Golden approval, or production authorization.

## Source and extraction route

The private dataset may be prepared from the official Live2D sample models
using `CubismPartExtr`. The extractor can render the final character and
individual drawable/part images with a part hierarchy and vertex metadata.
The Live2D SDK and extracted pixels remain private; only metadata and SHA
receipts may enter this repository.

The extractor output alone is not a six-capability annotation. A private
annotation manifest must additionally identify:

- person-level instances;
- outerwear, underlayer, sleeve, and arm owners;
- the three pairwise occlusion relations;
- a separate unknown region;
- the signed source receipt and annotation-manifest SHA.

The part names from a model file are therefore evidence for preparing the
dataset, not automatic permission to promote pixels to an observer owner.

## Repository gate

`tools/research/import_live2d_training_catalog.py` accepts only metadata with
schema `minimalizer/l02/live2d_training_catalog/v1`. It requires all six
capability roles, all three occlusion pairs, at least one person instance,
private source/annotation URIs, a source-signature receipt SHA, and
`labels_in_inference_input=false`.

It then delegates to the shared training-manifest validator, which enforces:

- H04/H06/H08 source SHA values are holdout-only;
- source SHA cannot cross train/validation/holdout splits;
- character identity cannot cross train/validation or enter holdout;
- unknown remains separate from negative;
- both train and validation are non-empty.

The importer reads the catalog JSON only. It does not open private images,
masks, annotations, or model weights, and it does not run inference.

## Current status

- The importer and tests are research-only and source-free.
- No six-capability training run has been claimed.
- No H04/H06/H08 mask or review result has been used as training input.
- Phase4 remains HOLD until a real private catalog, an independently fixed
  observer run, and the required visual/structural evaluation exist.
