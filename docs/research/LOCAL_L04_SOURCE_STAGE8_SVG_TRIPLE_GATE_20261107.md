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

Synthetic source-free tests in
`tests/test_local_l04_source_stage8_svg_triple_gate.py` passed **6/6**. They
cover exact-triple readback, signed-source tamper, expanded-SVG tamper, manifest
cross-link mismatch, unsafe SVG markup, and failed quality metrics. No private
image, Stage8 JSON, mask, coordinate, or SVG was copied into GitHub, and no
Public/C08, Golden, Local production, or iPhone state was changed.

The formal owner-side gate remains pending until the actual private three-point
set and its independent receipt are available. Do not infer a formal L04 pass
from this source-free test result.

Implementation commit: `20e2e2be` (PR #451, Draft; not merged).
