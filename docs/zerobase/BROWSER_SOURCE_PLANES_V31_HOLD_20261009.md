# BrowserFallback v31: Source-observed garment plane diagnostic (HOLD)

Date: 2026-10-09
Branch: research/browser-source-planes-v31-20261009
Base: held v30 PR #301.
Decision: **SOURCE RGB MATERIAL PROPOSAL PASS / VISIBLE QUALITY PROMOTION HOLD**.

## Experiment

Using the exact SHA-pinned Noel/Ririka sources, unmodified Facet outputs and actual AnimeSeg v3 CPU-generated class masks from v30, construct **research-only** 8×8 source-medoid color planes. Every proposed color is an RGB value occurring in the original source; it is assigned only to pixels classified clothes by AnimeSeg (class RGB 180,0,255) that also have fully opaque original source, and preserves each original Facet alpha. Pixel shape and source mask provenance are source-only. This is a **diagnostic**, not a new Minimalizer output mode or a browser-native solver.

| Case | Observed usable garment px | Source medoid tiles | Diagnostic raster changes | Facet source RGB MAE on observed garment | Diagnostic RGB MAE |
|---|---:|---:|---:|---:|---:|
| Noel | 21,777 | 455 | 21,635 | 32.975 | 20.901 |
| Ririka | 45,121 | 812 | 44,131 | 19.104 | 9.113 |

Zero pixels outside mask changed, zero alpha/silhouette changes. These are **in-mask measurement** results; they must not be advertised as overall image fidelity, semantics quality or successful arm repair. The masks themselves contain accessory or limb ambiguity; RGB fidelity against the source cannot certify their semantic correctness.

## Visual assessment

The actual original / Facet / AnimeSeg / tile montage shows previously flattened garment colors can be recovered from the source without img2img or generative fill, but **block discontinuities** and 8×8 pixelated checkering are conspicuous. Some sleeve/arm/accessory ownership is unverified, and the existing poor face/hair representation remains. This is NOT a production-grade improvement. No facial eyes/mouth/nose added.

## Gates

- Pass: original sources and class mask hashes exact from v30; no new colors; changed pixels are a subset of source-opaque AnimeSeg garment pixels; source medoid samples; 100% alpha preservation; measured in-mask source RGB MAE decreases.
- Hold: visual garment smoothness, 3-case Kyoko+Noel+Ririka regression, reliable left/right arm and accessories, browser ONNX/WASM model portability, full body source-bound semantic validation and production performance.
- The prior v29 5GiB free RAM restriction remains removed by user instruction. v31 performs no model inference.

Next engineering stage: replace grid tiled planes with topology-aware connected contiguous contour planes (source-bound Bezier/shared-edge geometry), improve seam continuity and protect accessories, then independent visuals across 3 Golden sources. Do not merge a diagnostic experiment to Public Facet v15 or Local Worker.

Canonical archive: chatGPT及びCodex用/Minimalizer/SourcePlanesV31_20261009.
