# ZeroBase 2nd Cycle Phase 6 — Region-to-Part Binding

Status: **IMPLEMENTED / READY FOR RINKA REVIEW**

## Objective and review history

Phase 6 connects image regions to the semantic structure established by Phase 4 and Phase 5. Phase 4 masks and the Phase 5 graph remain immutable, SHA-bound inputs. Production remains Minimalizer 2.0.

The first independent review was `HOLD / CHANGES REQUESTED` because semantic-boundary splitting removed the ambiguity of the original parent SLIC and effectively promoted the Phase 4 display owner to truth. Revision 1.1 corrects that architectural problem instead of tuning Diagnostic-2 thresholds.

## Revision 1.1 implementation

- Generate deterministic SLIC evidence inside the Phase 4 subject.
- Preserve the original parent SLIC map and compute its pre-split overlap, winner, margin, and ambiguity reasons.
- Split regions at Phase 4 exclusive semantic boundaries only for spatial representation; a child fragment inherits its parent's uncertainty.
- Score candidates from child overlap, parent overlap, Phase 5 graph support, boundary support, part-centroid geometry, and source-color support.
- Require Phase 5 graph support plus boundary or geometry corroboration when the parent is ambiguous or the child owner differs from the parent winner.
- Keep source color non-authoritative: it contributes to a score but can never resolve a parent ambiguity by itself.
- Fail closed for hair/clothing candidates whose parent SLIC crosses both semantic families.
- Preserve valid accessory evidence independently. Raden's held-linear object remains three bound regions because its Phase 5 relation and spatial evidence support it.
- Allow `unbound` through the canonical `build_region_bindings()` path.

Phase 4/5 inputs are read-only and verified by SHA before Phase 6 runs. The runner writes only `phase_06`.

## Binding record

Each region retains:

- child and parent region labels
- parent pixel count, winner, overlap ratio, margin, ambiguity flag, and reasons
- child and parent overlap values for every candidate
- graph relation IDs and graph support
- boundary and geometry support
- source RGB statistics, color distance, and non-authoritative color support
- weighted decision score, confidence, decision basis, and decision reasons
- geometry, row-run pixel support, and adjacency
- upstream evidence references

The binding JSON schema is `1.1`. Artifact producer version is `1.1`.

## Synthetic acceptance coverage

Focused tests verify that:

- a parent SLIC crossing hair/clothing remains ambiguous after semantic splitting
- color match without graph support cannot resolve a parent tie
- graph relation plus boundary/geometry support can resolve a tie
- Phase 4 display-priority overlap alone does not produce confidence 1.0
- the canonical builder can emit real `unbound` regions
- upstream Phase 4 masks and the Phase 5 graph remain unchanged
- dark hair and dark clothing are not cross-bound by color
- artifacts remain SHA-bound to their inputs

## Diagnostic-2

### Hyakuto Kyoko

- regions: 476
- bound / unbound: 446 / 30
- unbound pixels: 2,194
- bound pixel ratio: 0.959706
- mean bound confidence: 0.798162
- parent-ambiguous child regions: 99
- hair/clothing crossing unbound regions: 30
- hair/clothing forced bindings: 0
- display-priority-only bindings: 0
- color-only bindings: 0
- accessory regions: 5
- visual QA: **PASS (Codex review)**

Face, hair, clothing, and green accent remain readable. Unbound highlighting is limited to uncertain hair/clothing boundary fragments and does not hide a major identity feature.

### Juufuutei Raden

- regions: 334
- bound / unbound: 296 / 38
- unbound pixels: 6,232
- bound pixel ratio: 0.910272
- mean bound confidence: 0.847216
- parent-ambiguous child regions: 84
- hair/clothing crossing unbound regions: 38
- hair/clothing forced bindings: 0
- display-priority-only bindings: 0
- color-only bindings: 0
- accessory regions: 3
- visual QA: **PASS (Codex review)**

Dark hair and black clothing remain separated without forced cross-binding. The face remains aligned, sleeves remain distinct, and the held-linear object remains bound and visible. The unbound overlay exposes uncertainty along hair/clothing crossings rather than concealing it.

## Artifacts

Runtime:

`artifacts/zerobase2/<case_id>/phase_06/`

Persistent diagnostics:

`docs/zerobase/diagnostics/phase06/<case_id>/`

Each case contains:

- `06_region_bindings.json`
- `06_region_labels.png`
- `06_region_binding.png`
- `06_unbound_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

## Determinism

All seven artifacts were regenerated and matched byte-for-byte for both cases: **14/14 SHA MATCH**.

Kyoko:

- binding data: `c4db5b636efd68619bd31ac63d1188b2b98138e9a153b50ed5fe0d6edf5acc8e`
- region labels: `0d9c21edfe8c832c28959ba6391119b23289ba0a5de9693add826476545d860f`
- binding overlay / preview: `ed4fd447a9c2cd88d8232faaa998cf0b7848cf89703a09c91ceab587291fe2e2`
- unbound overlay: `8481c51d759e9f62eb5ed54a3a4f133f11034406c0f1db88e89e0dc1676eccbc`
- metrics: `5b1a3d5f80afb074b41f754afbca3c22ebc279adf0e237b8ddfc87df72c182b5`
- stage: `4cd9358e289bfe30800c9f49795a779915cd268ab5cc110599d884e74c146f4c`

Raden:

- binding data: `1e67848cc5c6b8468ad47f7fa9b4f566723c9c50ef6885ef87e9833f1416fcf9`
- region labels: `7bc70ccf672f19ff6bf87a86eff7f88595bf3ed5d038ce7c9b06c360dde95322`
- binding overlay / preview: `3665325dc16c80816c21d54c872de3e96ee1cd3663bd42f88faeff1232e32b2e`
- unbound overlay: `4dbd6aad063273391982367bf6c50050bde9cd6b9f71992bca1a5c28797aadec`
- metrics: `1bd0bf3c3c9ce9e38ba0ccbd9cfe5eb96b05592d1ae320296beb2219b6e083dc`
- stage: `b43b0774c7eefcc9adcc18ce4399e2c2c0bf62a0889d07a5b0218c97757e0322`

## Tests and review boundary

- Phase 6 focused tests: **13 passed**
- Full ZeroBase suite: **98 passed**
- Diagnostic-2 visual QA: **2/2 PASS (Codex review)**
- Deterministic artifact rerun: **14/14 SHA MATCH**
- Stable regression/Web set: **131 passed** (one pre-existing Starlette/httpx deprecation warning)
- Phase 16 corpus local gate: **PASS**
- Real-server local smoke: **PASS**
- Local merge readiness: **LOCAL_MERGE_VALIDATION_PASS**
- `git diff --check`: **PASS**

Rinka independent re-review: **CLOSED / PASS**. Code and synthetic tests, Diagnostic-2 visual artifacts, 14/14 deterministic SHA rerun, Phase 4/5 read-only provenance, stable/Web regression, Phase 16 corpus gate, real-server smoke, and local merge readiness were independently rechecked. Phase 7 may begin only after this closure is merged to canonical main.
