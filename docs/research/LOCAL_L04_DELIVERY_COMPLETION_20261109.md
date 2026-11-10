# Local L04 delivery contract (2026-11-09)

Lane B L04 receives A-owned artifacts. Its responsibility is limited to the
exact signed source / Stage8 JSON / expanded-SVG linkage, safe SVG content and
real-browser display. It does not repair or approve silhouette, arms, clothing,
owner semantics, Golden quality, or a source/expanded vertex policy.

`tools/research/local_l04_delivery_triple_audit.py` reuses the fail-closed
lineage and SVG safety checks, then emits a separate delivery receipt. Vertex
counts are recorded as measurements only; they cannot cause B to alter A's
image or silently change the governing policy.

A private Chromium render of the exact expanded SVG is required for each
accepted triple. The resulting PNG stays in the owner-private evidence store;
GitHub receives only code and source-free hashes/measurements.

`B_L04_delivery=PASS` means the supplied A triple can be safely checked and
displayed by Lane B. It never means `A_L04_quality=PASS` or release approval.

## Completed private delivery receipt

The owner-private H06 and H08 triples were checked with the delivery audit and
rendered by isolated Chromium. Both cases passed triple linkage, safe-SVG and
browser-render checks. The private receipt SHA-256 is
`0fb0f12029bab9109e157e62dc2cc73adabbba89b129151b37b8edd6ad57d591`.
Source images, Stage8 JSON, SVG coordinates and browser PNGs remain in the
private evidence store. The receipt records the observed vertex counts as
measurements, not a B delivery veto.

## 2026-11-10 merged-main branch readback

The delivery audit was rerun from the merged B branch against the private
three-point candidates. No private bytes were copied into GitHub.

| Case | Source SHA-256 | Stage8 JSON SHA-256 | Expanded SVG SHA-256 | SVG vertices | Chrome PNG SHA-256 | Result |
|---|---|---|---|---:|---|---|
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `a446b2772509730f6f6f6fe99f56fba7d81c1c671440577e34e0901f17f79151` | `95a02a56a378759599aeb765d35a18c464fa8dcb8f50a7a65713b42cf0bf7296` | 72,201 | `074bd61b95f7aefb7143a56740b7e1f17fd1a8c4fb961f93ae4e7086bab4f174` | PASS |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `e1f044cdf0f6855b5c27d3391b534bc3709831dc96df40bc85109d12f6e4397b` | `410267167396abf0dacb3dcde28872d1bd3e9de3d40ee6f0f8f87028b3e4bb28` | 56,249 | `2917b4f13927c043242057d49131542f5c4f4f807ad731e7a4e3c0e32f48188c` | PASS |

Both results were `B_L04_delivery=PASS`, `A_L04_quality=NOT_JUDGED`, with
`vertex_policy=OUT_OF_SCOPE_FOR_LANE_B_DELIVERY` and
`release_authorized=false`. The no-cap policy therefore remains explicit at
the B delivery boundary as well as in the lineage gate.
