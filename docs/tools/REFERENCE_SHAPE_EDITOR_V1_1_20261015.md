# Reference Shape Editor v1.1 sync (2026-10-15)

The human-operated polygon tracing tool is independent of the Minimalizer conversion pipeline and Golden approvals.

- Portable standalone: `web/static/reference-shape-editor.html`, version `1.1.0`, Git blob SHA `61661a7b13bc5799b8ad1d9267c81e7121842257`.
- Public website authored source: `watarionn/portfolio-site/tools/reference-shape-editor/{index.html,styles.css,app.js}`; registration No.034 via portfolio-site PR #201. Intended route: `https://cf278796.cloudfree.jp/reference-shape-editor/`.
- Offline editable source archive: `chatGPT及びCodex用/Minimalizer/ReferenceShapeEditor_v1_1_20261015.zip` (private Drive, includes code and tests but **not** user input images).
- v1.1 behavior: the SVG workspace fills the available screen; portrait sources open width-fit and wheel pans vertically; Ctrl/Meta/Alt-wheel zooms; top controls provide fit-all, width-fit and +/− zoom; a range slider navigates long images. Source coordinates, shared vertex IDs, JSON v1 schema, and source-only transparent SVG/PNG exports are unchanged.
- Synthetic Chromium E2E: 8/8 PASS, Node `--check` PASS; independently reopened the actual user's three-polygon H04 v1 project and verified an exact JSON shape/vertex/canvas roundtrip (private inputs never committed).
- Do **not** embed H04/GC001 signed original pictures, human project JSON/SVG or inferred source coordinates in GitHub. Never interpret this tool publication as MinimalizerLocal L02 Golden PASS or a Public/C08 release gate.
- GitHub merge does not by itself prove web-host production deployment. The production route should only be called live after an actual HTTP byte check.

**Source hierarchy:** the portfolio-site repo owns deployable web assets and No.034 index; Minimalizer maintains a byte-identical standalone convenience copy for researchers. The HTML is not wired into the MinimalizerPublic conversion runtime.
