# Goggle Rim Source Connectivity (2026-10-09)

Real GC001 source comparison and frozen 614-pixel pale-rim candidate mask were audited. Original mask consists of **3 separate 8-connected components**, with areas **264, 177, 173** pixels. Their source bboxes are [113,68,31,25], [148,50,18,14], [178,35,17,30]. Using the same pale-silver original RGB constraint in the immediate 2px neighborhood, an additional **121 observed source-pale pixels** were found, split into **7 components**. These are candidate pixels, not independently verified goggles material. No original candidate mask pixels were altered and no disconnected component was artificially bridged. Comparison source overlay visually inspected.

`tools/research/goggle_rim_connectivity.py` plus `tests/test_goggle_rim_connectivity.py`: **69 related tests PASS**. Source overlay, separate extension candidate mask and manifest saved under approved `chatGPT及びCodex用/Minimalizer/GoggleRimConnectivity_20261009`, Drive folder `1HhtUuH6f5QS4LJNakpimkU4SdtfR44SI`.

Status: source topology inspection PASS; independent full frame/left/right lens semantic material verification and filled SVG **HOLD**. Next should examine source-visible material connectivity along top frame and lens border with explicit hat/hair exclusions. No production Local/Public change, no face/skin plate, no invented fill.
