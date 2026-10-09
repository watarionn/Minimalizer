# Stage8 source-owner topology gate, research extension (2026-10-09)

The signed GC001/Raden original Stage8 rasterizer was restored on the parent research branch (PR #333), with 11/11 alpha-visible owner masks exact for both characters. Prior **candidate evidence**, NOT production-selected geometry: remove 13 GC001 micro-rings (14 vertices) and 6 Raden micro-rings (9 vertices), yielding zero changed source-owner pixels both before and after source-alpha masking when grouped per-owner.

This follow-up adds a **separate fail-closed topology equivalence check** to that candidate acceptance process. Requirements are (1) verify original PNG SHA-256; (2) verify individually SHA-signed owner-mask bytes; (3) reproduce the baseline from official single-call OpenCV FILLED even-odd contours; (4) test single deletions; (5) test jointly selected removals; (6) require **exact unguarded binary pixels**, 0 changes for owner; (7) compare connected-component count and RETR_TREE contour hierarchy. It never edits source originals and does not authorize promotion merely because image center pixels match.

Code: `tools/research/public_geometry_js/stage8_micro_topology_gate.py`, `test_stage8_micro_topology_gate.py`.

Windows regression: 2/2 PASS for raster/connected-component/hierarchy equivalence and hole-loss negative control. These are **synthetic regression cases**. A new real-input re-run of the 23 candidate vertices with this script is still pending, so do not claim this stage has independently certified topology on real data.

The original Stage8 hard caps remain GC001 3,604 > 1,887 and Raden 2,370 > 1,412. Even eventual acceptance of all 23 candidate vertices leaves 3,590 and 2,361 respectively, well over caps. Prior faceless/no-generated-source policy remains unchanged; human Golden, mobile Safari and production gates HOLD.

Next prioritize major hair and unbound source-ring compression with original Stage8 raster semantics. Do not imply the existence of automatic budget relief when the theoretical upper bound of available micro-ring candidates is 23 vertices.
