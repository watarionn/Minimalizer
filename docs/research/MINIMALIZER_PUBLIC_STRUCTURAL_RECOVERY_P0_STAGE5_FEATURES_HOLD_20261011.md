# MinimalizerPublic StructuralRecovery P0 Stage5 — source-grounded feature surfaces (2026-10-11)

**Research implementation and two independent 340×340 source replays PASS. Human Golden, structural quality, formal semantic authority, and production integration HOLD.** Continues the rejected arm brightness-only Stage5 triage. Does NOT promote the mistaken skin-as-sleeve hypothesis.

## Engineering result

Added opt-in `web/static/public-source-feature-preservation-p0.mjs`, and `tests/js/test_public_source_feature_preservation_p0.mjs`. Frozen Public Facet40 is read-only; original RGBA, baseline RGBA, independently historical signed Stage04 face mask, and each separately observed feature-class mask must match pinned SHA-256 before operations. A feature is limited to a small source-observed region, source RGB class, 0/255 mask, non-overlap, fully opaque source pixels and strict mask pixel budget. A new output color must be a **medoid that actually occurs in those original source pixels**. No source textures, prompt, segmentation model, generated areas, shape imagination, LocalWorker or regular Public route changes. If local source-color squared error worsens, the candidate abstains. All records explicitly deny production authorization; RGB-color evidence **never constitutes an independent signature for a named costume part**.

The **private** hand-inspected ROI observer (`observe_real_source_features.py`) is a validation fixture, not a universal user-facing semantic segmentation system. ROI and color components are not canonical/attested clothing-owner masks. This is the crucial nonpromotion limit.

## Frozen two-case results

| Source-locked original | Applied source class candidate | Changed RGB px | Whole-frame source RGB squared-error gain | Golden |
| --- | --- | ---: | ---: | --- |
| GC001 | bright goggle frame from `high_neutral` pixels (1,173) | 1,173 | 0.150% | HOLD |
| Raden | bow midtone (1,130), bow shadow (3,140), lacing midtone (779) | 5,049 | 2.806% | HOLD |

True original PNG and unmodified Facet40 SHA-256 matched previously frozen independent cases, and historical source face mask PNG SHA-256 matched. Each run repeated twice with identical output bytes and audit. Original inputs remain unchanged. **Pixel differences are not a quality score**. Visuals have some recovered broad eyewear/bow contours, but bow/lacing still overly fragmented; shirts, outer silhouette, arm attachment, ruffles and face-like external patches remain wrong. This tool cannot claim independently resolved geometry.

## Browser evidence

A real isolated Chromium rendering of the **real, dynamically imported Stage5 JavaScript module** ran on both cases at DPR1/340px and DPR2/680px with zero output-byte disagreement against Node, and zero Canvas screenshot pixel discrepancy. The harness used an in-memory `data:` module and a **Python SHA-256 delegate** because browser navigation to localhost/file/data URLs was administrator-blocked and the opaque `about:blank` context lacks native WebCrypto. **This is not a native browser WebCrypto, normal network/module fetch, SVG/resvg or live-Public route PASS.** See private `PRIVATE_STAGE5_CHROME_SANDBOX_PARITY.json` for limitations; no tool bypass or network/production host modifications.

## Remaining gate

Require human-attested source semantic masks/overlap (especially Raden bow/ruffles/corset vs hair/skin and GC001 goggles), a clean small-primitive contour rather than color-fragment restoration, strict source alpha and signed face-only paint, owner vertex budget and real SVG clip, true secure browser WebCrypto, true Public E2E Chrome/iPhone, and human Golden. Original Stage8 caps GC001 3604>1887, Raden 2370>1412 remain HOLD. Keep this work in Draft PR, not main.
