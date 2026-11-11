# Minimalizer Local PWA: 5-Engine Candidate Lab (2026-11-11)

Status: **RESEARCH CANDIDATE / NO PRODUCTION PROMOTION / NO DEPLOYMENT / OWNER iPHONE QA REQUIRED**.

## Goal
Allow the owner to experience and compare VTracer, ImageTracerJS, Primitive,
Geometrize and Primeval using the same image in the private Local PWA, without
replacing ZeroBase2 or V2. This is the first opt-in candidate-bank milestone
toward an eventual semantic-part-aware ensemble, **not** a five-engine unified
production converter.

## Implementation
- Entry is **Local PWA only**: `/local-static/five-engine-lab.html`.
  Link lives in `local_worker/frontend/index.html`. No Public home or
  Public builder changes. The route uses existing StaticFiles, same-origin.
- In-browser real conversion: VTracer (existing opt-in research WebAssembly,
  read from `/static/vendor/vtracer-wasm/`), ImageTracerJS (pinned unmodified
  v1.2.6 locally in `/local-static/vendor/`, upstream Unlicense).
- Primitive / Geometrize / Primeval: open their published demos separately;
  user exports SVG and explicitly imports a candidate back into the Lab.
  **Those engines do not execute in the PWA in this milestone**; do not claim
  their implementations are integrated.
- Source image capped at 20MB, dimensions 8192 each; comparison pixels
  downscaled to a maximum of 128/192/256 px by owner choice.
- Every generated/imported candidate is an independent SVG with engine
  provenance (local/import), shape-element count, SVG size, RGBA mean absolute
  difference and alpha-difference count. The reference is the downscaled image
  from this **same** session. No cross-image comparisons.
- SVG preview uses a private Blob URL as `<img>`, never `innerHTML` or an
  inline SVG node. Imported SVG is strict-validated: root/namespace, tag
  allowlist, no DTD/entities, script/event handlers, foreignObject, inline
  CSS or external references. Unsupported exports fail closed.
- All images and generated SVGs remain in browser memory. Nothing is
  automatically uploaded or cached by the Service Worker; external demo sites
  are optional explicit navigation, not background network dependencies.
- Export selected candidate as SVG or comparison metrics as source-free JSON
  with a hash of the working-resolution RGBA; original bytes are never saved
  in the report.

## Provenance, licensing and gates
- ImageTracerJS copied from
  https://github.com/jankovicsandras/imagetracerjs/blob/master/imagetracer_v1.2.6.js
  with its unmodified **Unlicense / public domain** notice.
- VTracer binary is already present in the repository as a research-only
  third-party bundle. Audit
  `web/static/vendor/vtracer-wasm/THIRD_PARTY.md`:
  **full dependency/license notices were not yet fully audited**.
  No Public distribution/promotion is authorized by this change.
- External sites and their SVG exports have independent license and privacy
  terms. Do not bundle their source/weights/binaries without a separate review.
- Face feature suppression, part owner protection, original alpha boundary,
  topology, holes, stage provenance, Stage8 geometry, C08, Golden and Local
  ZeroBase2/V2 are **not** bypassed. In this research lab raw candidates may
  contain eye/mouth details: they are explicitly **not approved production
  images**. Never automatically paste a raw whole-image SVG into the
  production scene.
- No LocalWorker API, owner identity config, origin/HTTPS, PWA cache list,
  production route, pinned source masks, private Golden images, or PR from
  other development lanes were changed.

## Next stage for an actual hybrid engine
1. Get source-signed semantic part/owner masks from Local Phase 4/5 with
   uncertainty preserved, never from a generated SVG.
2. Execute each third-party geometry optimizer inside a resource-bounded
   process or browser worker **per authorized part**, with pinned version,
   deterministic seed and source-supported color/shape candidates.
3. Normalize outputs into an engine-agnostic candidate schema. Evaluate
   owner exclusivity, 4/8-connectivity, holes, alpha, silhouette, character
   identity, face-neutralization, color provenance, topology and z-order.
4. Accept candidates only after positive real-image/holdout evaluation.
   Avoid selecting based solely on RGBA error or smaller SVG byte count.
5. Review/ship after independent regression, license checks, owner PC
   private HTTPS, iPhone Safari/PWA/exports and owner Golden signoff.

## Verification evidence for this PR
- Pinned ImageTracerJS source and Local link read back on GitHub.
- The Lab module passed V8 syntax compilation, and the pinned ImageTracerJS
  successfully generated a real SVG from synthetic 16x16 RGBA input in V8
  (two paths). This is **not** an actual browser E2E or VTracer runtime test.
- Static isolation and pinned vendor checks live in
  `tests/test_local_five_engine_lab.py`.
- **Not performed yet:** LocalWorker HTTP smoke, real VTracer/ImageTracerJS
  conversion on Safari/Chrome, pytest inside a repository checkout, full
  third-party VTracer dependency notice audit, iPhone QA, merge, rollout.
