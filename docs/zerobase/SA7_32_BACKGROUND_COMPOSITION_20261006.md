# SA7.32 Source-only Background / Composition Abstraction — 2026-10-06

Status: OBSERVER CONTRACT PASS / RENDERER NOT YET AUTHORIZED

SA7.32 promotes background/composition from an evaluation complement into explicit source-only evidence.

The observer records:
- subject bounding box and occupancy
- negative-space ratio
- border background ratio
- subject/background boundary complexity
- border-connected background field
- dominant source background color
- up to three dominant source background field palette roles

Golden and Browser fallback v12 are not inputs.

GC001 source-only observation:
- subject area ratio: 0.47615
- negative-space ratio: 0.52385
- border background ratio: 0.76401
- subject bbox: [0,0,323,340]
- boundary ratio: 0.09478
- dominant background field RGB: approximately [255,134,46]

Inspection confirmed that the orange field is present broadly in the source outside the current subject mask, including right/lower image areas. It must not be assumed to be foreground leakage merely because it resembles hair color.

Decision:
- merge the source-only background/composition observer.
- do not render a single flat background color.
- next stage must preserve a small number of large border-connected source fields rather than collapsing the background to one color.
- Golden remains evaluation-only.
