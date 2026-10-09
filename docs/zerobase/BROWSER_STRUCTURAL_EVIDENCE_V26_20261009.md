# BrowserFallback v26: source-backed structural evidence (research HOLD)

Date: 2026-10-09
Stage decision: **READ-ONLY OBSERVER PASS / SEMANTIC OWNER HOLD**
PR: https://github.com/watarionn/Minimalizer/pull/293 (Draft, unmerged)
Branch: research/browser-structural-evidence-v26-20261009
Verified code commit: 469098407c81bf6c155c8712bb37c15923461c8b
Base: held v25 PR #290. Public Facet v15 / Local Worker unchanged.

## Goal and evidence boundaries

v25 RGB-only corrections changed just 11–46 rendered pixels and did not improve visible clothes or arms. V26 moves upstream to detecting original source-image boundaries that are missing inside Facet color planes.

Canonical project files reviewed: AGENTS.md, ZEROBASE_2ND_CYCLE_DESIGN.md, PHASE4_2ND_CYCLE_SEMANTIC_PARTS.md and PHASE6_2ND_CYCLE_REGION_TO_PART_BINDING.md. These require semantic-first, ambiguity preservation and no source-color-only binding. The checked web/static/browser-subject.js exports U2NetP foreground probability/confidence only. It does NOT export true left/right-arm, clothing or hair-part masks. The Python ZeroBase RTMLib/MediaPipe path is a separate environment and cannot be assumed available in the non-local browser.

## Implementation

web/static/browser-structural-evidence-v26.js is a standalone, read-only browser observer. Inputs: original decoded RGBA, actual Facet raster, aligned native browser U2NetP foreground/confidence. It detects source RGB contrast absent from flat Facet paint under a high-confidence subject gate, groups into deterministic eight-connected areas, and outputs evidence pixel indices, bounds, settings and provenance.

All detected segments have semantic owner **unbound** and semantic confidence **0**; known arm and garment segment counts are both 0. Missing/mismatched U2NetP evidence fails closed. No new colors, region labels, visible rendering authority, created facial features or package dependencies. Existing browser modes and app.js routing remain unchanged. The new observer runs only when explicitly called; merely loading its script does not modify the image.

## Real Chrome 154 source review (original 340x340)

| Case | High-confidence foreground pixels | Raw lost-edge pixels | Retained components | Retained edge pixels | Edge pixels at y>=45% image height |
|---|---:|---:|---:|---:|---:|
| Kyoko | 45841 | 16057 | 60 | 15750 | 9876 |
| Noel | 56184 | 20475 | 74 | 20009 | 12773 |
| Ririka | 72099 | 16723 | 83 | 16355 | 10779 |

The lower-image statistic is spatial only, NOT a torso/arm/garment classification.

Actual browser forced Facet output matches the frozen v25 Facet PNG byte-for-byte in all 3 cases, including full-color palette and silhouette. Source/Facet/foreground/edge-overlay visual collage was independently reviewed: the observer finds abundant lost original edges, including jacket, sleeve and garment detail, but also hair and facial detail. Foreground masking does not distinguish semantic part ownership. **No display-quality improvement may be claimed.**

The bright-pink preview is an independent diagnostic marking existing RGB contrasts, not any synthesized or final Minimalizer output. Audit validates exact all-opaque RGB pixels outside marked sites. Nonopaque input RGB may change on drawImage canvas premultiplication; alpha is preserved and no opaque unmarked pixels change. This was investigated and explicitly encoded in the external audit, not silently ignored.

## Verification

Real Chrome 154 / actual app.js forced Facet route: PASS for 3/3.
Frozen baseline SHA parity: 3/3 Facet PNGs byte-exact.
Mandatory per-source stage includes stage.json, preview.png, metrics.json, source.png, facet.png, subject_probability.png.
Second completely independent Chrome run: **18/18 mandatory stage files SHA byte-exact**, including source, Facet, preview, probability, metrics and stage JSON for all three.
Tests: **49 pytest PASS** (4 new v26 and inherited v13-v25), JS syntax, Python script compilation, GitHub workflow PASS on code commit 4690984. Existing v25 workflow extended rather than a new workflow.

## Gate and next steps

**V26 structural lost-boundary diagnostic COMPLETE; semantic arm/garment separation HOLD.** No unverified edge labels, no automatic geometry repair, no production change, no merge to main.

v27 prerequisite: browser-compatible non-generative semantic part evidence with explicit producer, model, source dimensions, provenance and confidence. Candidate arm/clothing masks must be independently corroborated (semantic/graph/geometry); color evidence alone cannot authorize ownership. Unsupported candidates remain unknown/unbound. Then evaluate source-bound, meaningful garment/arm color planes while keeping silhouette, protected tie/sleeve/staff and intentional absent facial internals intact.

## Preserve / reproduce

Private canonical Drive under chatGPT及びCodex用/Minimalizer:
https://drive.google.com/drive/folders/1TYHumto_ZKn9p5vFGxJdQ9MLEkT54knG

Files: v26_original_facet_foreground_lost_edges.png, v26_stages_and_metrics.zip, v26_metrics.json/csv, v26_report.md, v26_replay_sha_verify.json, v26_evidence_manifest.json, and the browser observer, real Chrome runner, Python auditor and Node-backed tests. Drive read-after-write SHA verifies 10 evidence files plus manifest.

The source was the frozen v25 comparison archive on Drive, never an invented replacement. The local checkout was temporary and not designated as canonical.
