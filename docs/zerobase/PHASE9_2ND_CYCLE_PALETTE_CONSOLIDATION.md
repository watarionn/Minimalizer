# Phase 9 — Palette Consolidation

Status: **IMPLEMENTED / READY FOR RINKA REVIEW**

Date: 2026-09-29

## Goal

Reduce shading and wrinkle color variation without changing Phase 7 mass geometry, semantic ownership, or Phase 8 `protect / keep / prune` decisions.

Phase 9 consumes the SHA-bound Phase 7 masses and Phase 8 omission metadata. It produces a deterministic part-aware palette and one material assignment per mass.

## Canonical rules

- palette merge is allowed only inside one bound semantic part;
- face, hair, major clothing, and accessory/held-object use the stricter near-color threshold and contrast guard;
- `protect` masses are ordered before `keep` masses and therefore become representative anchors;
- every unbound mass remains ownerless and receives an isolated palette entry;
- every `prune` mass remains omitted and receives no palette entry;
- representative RGB is the observed source-pixel mode, with ties resolved nearest to the Phase 7 source-derived mass mean;
- synthetic average color, semantic reinterpretation, geometry changes, generated pixels, inpainting, and hidden completion are forbidden.

## Outputs

- `09_palette.json`
- `09_palette_preview.png`
- `09_palette_strip.png`
- `preview.png`
- `metrics.json`
- `stage.json`

`09_palette.json` retains each mass ID, semantic owner, binding status, Phase 8 action, bbox, source representative RGB and coordinate, palette assignment, color distance, and merge rationale. Pruned masses remain represented in metadata with a null palette reference so omission cannot be silently reversed.

## Negative fixtures

Synthetic tests fail closed for:

- cross-part merge;
- missing face/accessory protected anchors;
- unbound merge or reinterpretation;
- prune resurrection;
- critical-contrast collapse;
- synthetic representative strategies;
- Phase 7/8 owner, action, label, and SHA drift.

## Diagnostic-2

### Hyakuto-Kyoko

- masses: 201
- active after Phase 8: 158
- Phase 8 prune preserved: 43
- palette entries: 76
- same-part near-color merges: 82
- palette reduction ratio: 0.518987
- cross-part / unbound / prune-resurrection violations: 0 / 0 / 0
- critical anchor / contrast violations: 0 / 0
- source-derived representative violations: 0
- provenance artifacts: 55
- provenance gate: PASS

Visual QA: PASS. Orange hair, skin, clothing masses, goggles, and green tie remain distinct. The first representative strategy over-selected white source pixels and visually failed; selecting the observed source pixel nearest the Phase 7 mean fixed the first-bad Phase 9 behavior without modifying upstream masks or masses.

### Juufuutei-Raden

- masses: 93
- active after Phase 8: 74
- Phase 8 prune preserved: 19
- palette entries: 65
- same-part near-color merges: 9
- palette reduction ratio: 0.121622
- cross-part / unbound / prune-resurrection violations: 0 / 0 / 0
- critical anchor / contrast violations: 0 / 0
- source-derived representative violations: 0
- provenance artifacts: 55
- provenance gate: PASS

Visual QA: PASS. Black hair, face, dark clothing/sleeves, raised arm, held rod, and decorative accent cluster remain readable. Similar dark shading is consolidated without merging semantic owners.

## Determinism

- Hyakuto-Kyoko: 6 / 6 Phase 9 artifact SHA matches
- Juufuutei-Raden: 6 / 6 Phase 9 artifact SHA matches

Final provenance hashes:

Hyakuto-Kyoko:

- `run.json`: `f56e5499282b22e776a169fa447357e82668a585478f80b4d4b3512359ca5b21`
- `artifacts.json`: `864c19e25f89e8f1e065cc0bec9fad45692cd709db926a0374e8a50b5428c239`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

Juufuutei-Raden:

- `run.json`: `e2991bf14de70c50448c0861162591ccaa2054104355dd9f84f9dfae226a4dda`
- `artifacts.json`: `13acf39139d630f25621454de044b83f96cb72c2363c25c0a0cb1701ca2c0e7e`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

## Validation

- focused Phase 9 / Stage Contract Bridge: 23 passed
- full ZeroBase suite: 153 passed
- stable/Web regressions: 131 passed
- Phase 16 corpus gate: PASS
- real-server smoke: PASS
- final marker: `LOCAL_MERGE_VALIDATION_PASS`

## Provenance and safety boundary

The Stage Contract Bridge supports `max_phase=9`. Phase 9 SHA-binds all declared Phase 7 and Phase 8 outputs plus both stage manifests before writing output. The common artifact graph contains 55 verified records per Diagnostic-2 case.

Unchanged:

- Phase 3–8 artifact bytes;
- production Minimalizer 2.0 routing;
- semantic owner and geometry authority;
- generative/inpainting prohibition.

## Review boundary

Phase 9 is not CLOSED until Rinka independently reviews the code, negative fixtures, Diagnostic-2 visual artifacts, deterministic rerun, and Stage Contract Bridge chain. Phase 10 remains blocked until that review closes Phase 9.
