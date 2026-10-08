# Goggle Contour Candidate Selection (2026-10-09)

**Completed actual source-trace shortlist; semantic goggles contour acceptance HOLD. No production change.**

Source GC001 SHA `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, and the previously preserved `GoggleSourceContourTrace_20261009/source_edge_traces.json`, were loaded without rerunning detection. Source SHA in frozen trace JSON was verified.

Actual review-only edge selection:

| Review region | Source curves | Candidate open strokes | Rejected |
| --- | ---: | ---: | ---: |
| Left lens | 13 | 8 | 5 |
| Right lens | 17 | 10 | 7 |
| Frame | 36 | 20 | 16 |
| **Total** | **66** | **38** | **28** |

Excluded curves that are too small/linear and 6 frame curves entering known nearby fringe-risk coordinates. This filtering **does not establish semantic truth**: actual comparison shows several apparent hair/hat lines retained. These 38 curves are diagnostic open polylines with `fill="none"`, NEVER filled frame/lens masks. Saved reference PNG and **open stroke diagnostic SVG** are not a goggle render or an approved addition to character SVG.

Code `tools/research/goggle_contour_candidate_selection.py`, tests `tests/test_goggle_contour_candidate_selection.py`; **58 tests PASS** with previous related observer, no-face-plate and certified-fringe research gates. Character and production Local/Public unchanged.

Artifacts saved under `chatGPT及びCodex用/Minimalizer/GoggleContourCandidateSelection_20261009`, canonical Drive folder ID `13dSFYjH7PTgJ7k7kDh2LiD0ZM1dUAaSV`: source comparison PNG, open polyline SVG, JSON manifest with input and artifact SHA256.

**Next substantive requirement**: human-review actual individual source-following boundary curves and identify which are white rim, colored lens boundary, hat/hair, glare. This cannot be authorized by bounding box, source edge geometry, HSV or approximate GrabCut alone. Once verified, build individual material polygons without filling hidden areas, then render isolated source-validated goggles with accessory/front-back and fringe gates. Full-character Golden remains NO-GO.