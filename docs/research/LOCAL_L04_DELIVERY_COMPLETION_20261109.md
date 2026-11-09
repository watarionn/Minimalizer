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
