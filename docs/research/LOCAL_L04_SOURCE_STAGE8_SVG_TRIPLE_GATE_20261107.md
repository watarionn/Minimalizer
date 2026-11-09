# Local L04 source / Stage8 / expanded SVG lineage gate (2026-11-07)

**Source-free implementation and synthetic verification only. Formal L04: HOLD; Golden and production: NO_GO.**

The private Local L04 acceptance boundary now has a fail-closed read-only gate in
`tools/research/local_l04_source_stage8_svg_triple_gate.py`. It requires the
owner-side receipt to provide exact SHA-256 values for all three private
artifacts: the signed original image, the Stage8 JSON and the expanded SVG.
The Stage8 JSON must cross-link the signed-image and expanded-SVG hashes. The
gate also rejects empty artifacts, invalid Stage8 schema/measurements, unsafe
DTD/entity markup, and non-SVG XML roots.

The numerical checks preserve independent ledgers for the original Stage8 ring
budget, expanded SVG vertex budget, source owner exactness, protected face/arm
owner exactness, and source silhouette equality. A numerical pass only produces
an independently-reviewable candidate; the result always reports `L04_formal:
HOLD`, `release_authorized: false`, and `production_release: NO_GO`.

The expanded SVG parser is also fail-closed against executable or embedded
content: DTD/entities, script-like tags, raster/media/embed elements, inline
event attributes, and non-fragment `href`/`src` references are rejected.
Internal fragment references remain parseable, but they do not create formal
acceptance.

Synthetic source-free tests in
`tests/test_local_l04_source_stage8_svg_triple_gate.py` cover exact-triple
readback, SVG content isolation, signed-source tamper, expanded-SVG tamper,
manifest cross-link mismatch, unsafe SVG markup, and failed quality metrics. No private
image, Stage8 JSON, mask, coordinate, or SVG was copied into GitHub, and no
Public/C08, Golden, Local production, or iPhone state was changed.

The formal owner-side gate remains pending until the actual private three-point
set and its independent receipt are available. Do not infer a formal L04 pass
from this source-free test result.

Implementation commit: `20e2e2be` (PR #451, Draft; not merged).

## 2026-11-09 read-only Drive intake reconciliation

A read-only fetch of the owner-private receipt
`Minimalizer_LaneB_L04_RealSourceBytes_IntakeReceipt_20261025_1021.md`
confirmed the byte identity of the genuine Local research originals, without
copying any private image, mask, coordinate, JSON, or SVG into this repository:

- H06 signed original SHA-256:
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`
- H08 signed original SHA-256:
  `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`
- The receipt explicitly classifies the result as source-byte consistency only,
  not official Stage8 acceptance.
- Its real-byte negative intake returned `HOLD` with
  `NOT_PROVEN_LOCAL_ORIGIN`; the reviewed annotation JSON/SVG was not relabeled
  as the official Stage8 source-ring pair.

The formal L04 owner operation is therefore unchanged: provide owner-authorized
linkage to one exact source SHA, the authentic Stage8 source-ring JSON, the
authentic expanded SVG, and an independently attested provenance/equivalence
receipt. Until those four items are read back and verified, L04 remains
`HOLD` and production remains `NO_GO`.
