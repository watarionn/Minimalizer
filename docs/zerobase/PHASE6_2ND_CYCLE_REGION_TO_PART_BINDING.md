# ZeroBase 2nd Cycle Phase 6 — Region-to-Part Binding

Status: **IMPLEMENTED / READY FOR RINKA REVIEW**

## Objective

Phase 6 is the first stage that formally connects image regions to the semantic structure established by Phase 4 and Phase 5. Phase 4 masks and the Phase 5 graph remain immutable, SHA-bound inputs. Production remains Minimalizer 2.0.

## Implementation

The implementation is split into pure binding logic, artifact persistence, and CLI orchestration.

- `minimalizer_zerobase/binding/region_binding.py`
  - generates deterministic SLIC region evidence inside the Phase 4 subject
  - splits SLIC regions at the immutable Phase 4 exclusive semantic boundaries
  - preserves the parent SLIC label for every resulting region fragment
  - binds only from Phase 4 mask overlap and winner margin
  - retains Phase 5 graph relations, source color statistics, geometry, row-run pixel support, and region adjacency as evidence
  - never uses color as the sole binding authority
  - leaves externally supplied ambiguous regions `unbound` rather than forcing a part
- `minimalizer_zerobase/binding/artifacts.py`
  - writes canonical binding data, a 16-bit region-label map, mandatory visual artifacts, metrics, and a bound stage manifest
- `scripts/zerobase2_phase6_binding.py`
  - verifies the canonical source SHA
  - verifies all Phase 4 mask SHAs
  - verifies the Phase 5 graph SHA and all Phase 4 hashes recorded by Phase 5
  - reads Phase 4/5 only and writes exclusively to `phase_06`

The semantic-boundary split is deliberate. A global SLIC region may cross hair and clothing even when their colors are similar. Phase 6 intersects such evidence with the already-established Phase 4 ownership boundary before binding, while preserving the original SLIC label as provenance. This keeps thin identity features such as Raden's held object from disappearing into a larger region and prevents dark hair from acquiring dark-clothing ownership.

## Binding record

Each canonical region record retains:

- deterministic region ID and parent SLIC label
- semantic part ID or `unbound`
- binding confidence, basis, and reasons
- pixel count, bounding box, centroid, and row-run pixel support
- mean and standard deviation RGB evidence
- Phase 4 raw and exclusive overlap evidence for candidate parts
- boundary contact and neighboring region evidence
- relevant Phase 5 relation IDs
- upstream evidence references

`unbound` remains a valid result in the pure binding API when overlap or winner margin is insufficient. The canonical Diagnostic-2 run produced no unbound fragments because every semantic-boundary fragment was fully supported by an immutable Phase 4 owner; the mandatory unbound overlay is still emitted and was checked to show no hidden swallowed regions.

## Artifact contract

Runtime artifacts:

`artifacts/zerobase2/<case_id>/phase_06/`

- `06_region_bindings.json`
- `06_region_labels.png`
- `06_region_binding.png`
- `06_unbound_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

Persistent diagnostic snapshots:

`docs/zerobase/diagnostics/phase06/<case_id>/`

## Diagnostic-2

### Hyakuto Kyoko

- Regions: 476
- Bound regions: 476
- Unbound regions: 0
- Subject pixel coverage: 1.0
- Hair/clothing forced bindings: 0
- Color-only bindings: 0
- Accessory regions: 5
- Visual QA: **PASS (Codex review)**

The face remains aligned to the reviewed Phase 4 face, hair and clothing ownership remain distinct, and the green tie/accent remains separately readable.

### Juufuutei Raden

- Regions: 334
- Bound regions: 334
- Unbound regions: 0
- Subject pixel coverage: 1.0
- Hair/clothing forced bindings: 0
- Color-only bindings: 0
- Accessory regions: 3
- Visual QA: **PASS (Codex review)**

The corrected face remains aligned, dark hair does not leak into the dark outfit, the sleeves remain arm/clothing structure rather than hair, and the thin held-object evidence remains distinct where Phase 4 supports it.

## Determinism

All seven Phase 6 artifacts were generated twice with the identical command and matched byte-for-byte for both Diagnostic-2 cases: **14/14 SHA MATCH**.

Kyoko:

- binding data: `0153b1153361d67534e6436094d128955b06eb781706423042b4614484cd9683`
- region labels: `0d9c21edfe8c832c28959ba6391119b23289ba0a5de9693add826476545d860f`
- binding overlay / preview: `5c26c99a8ea885e2c6e210dfa20cea1fa90d2a17bd52839d3567f6d9b5088502`
- unbound overlay: `c08587c44485d8cedb401484b03f5afce9bd8dfd6bca71a623c9f281ee6ddc67`
- metrics: `2147921c4f7e0839a8f63a966c2c435dbbce97f99ebbf506eaeef918e702a906`
- stage: `9f8fda866fd3a368026155e83cbf57d174897774818def955337277ca907a554`

Raden:

- binding data: `38e6b005b3eb2cd0cefe645a3dc7dd9f88d02676310951db9da5e9d9d443ee87`
- region labels: `7bc70ccf672f19ff6bf87a86eff7f88595bf3ed5d038ce7c9b06c360dde95322`
- binding overlay / preview: `c32c18f0cd78fd2e4e87d580289e1565c89831c2c272d88f192e6fe171ba0153`
- unbound overlay: `9c962830c17264e417ace229385ac74a064a4a7160b5e497f3950583b627d370`
- metrics: `0e320ce5a5c4aa5da79332c586d583635f8cf8fb32c97e064c1ba4db5c813228`
- stage: `13157bcdc028717263d7d0c78ed071d014ae79a52212d82823c7abff2ca42368`

## Tests and review boundary

- Phase 6 focused tests: **8 passed**
- Full ZeroBase suite: **93 passed**
- Diagnostic-2 visual QA: **2/2 PASS (Codex review)**
- Deterministic artifact rerun: **14/14 SHA MATCH**
- Stable regression/Web set: **131 passed** (one pre-existing Starlette deprecation warning)
- Phase 16 corpus local gate: **PASS**
- Real-server local smoke: **PASS**
- `LOCAL_MERGE_VALIDATION_PASS`
- `git diff --check`: **PASS**

Final merge-readiness results, commit SHA, Drive status, and any HOLD items are reported in the Discussion #177 handoff. Rinka retains independent review authority and decides whether Phase 6 may be marked `CLOSED / PASS`.
