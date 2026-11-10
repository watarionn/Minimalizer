# Local L04 source / Stage8 / expanded SVG lineage gate (2026-11-07, revised 2026-11-10)

**Vertex-count cap removed from Local L04. Source-free implementation and
synthetic verification only. Formal L04 and production remain separate gates.**

The private Local L04 acceptance boundary now has a fail-closed read-only gate in
`tools/research/local_l04_source_stage8_svg_triple_gate.py`. It requires the
owner-side receipt to provide exact SHA-256 values for all three private
artifacts: the signed original image, the Stage8 JSON and the expanded SVG.
The Stage8 JSON must cross-link the signed-image and expanded-SVG hashes. The
gate also rejects empty artifacts, invalid Stage8 schema/measurements, unsafe
DTD/entity markup, and non-SVG XML roots.

The gate records original Stage8 and expanded-SVG vertex counts as diagnostics,
but does not enforce a vertex-count cap. The old `1887`/`1412` values were
historical case-specific references, not a Local runtime limit or image-quality
criterion. The active checks are source owner exactness, protected face/arm
owner exactness, and source silhouette equality. Resource safety is a separate
operational measurement: bytes, parse/render time, memory, and timeout may be
introduced only from measured Local behavior.

The gate remains non-promoting: it reports exact triple integrity and candidate
eligibility, while human review, production activation, and rollback remain
separate gates.

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

The formal owner-side gate still requires the actual private three-point set and
its independent receipt. The adopted no-vertex-cap policy does not itself prove
browser or production acceptance.

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

## Lane boundary

The no-cap lineage result above is the active Local policy: vertex counts are
diagnostic measurements and are not an L04 acceptance condition. The separate
Lane B delivery audit in `LOCAL_L04_DELIVERY_COMPLETION_20261109.md` verifies
only exact triple linkage, safe SVG content, and browser display. It reports
`B_L04_delivery=PASS` without judging A-owned image quality, owner semantics,
Golden quality, or release authorization.
