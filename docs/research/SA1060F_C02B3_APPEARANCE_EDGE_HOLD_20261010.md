# C02b3 appearance-edge research

Status: RESEARCH HOLD. No production change.

The pinned GC001 right-arm mask has 6486 pixels. A five-iteration OpenCV GrabCut observation with three erosion seeds (2/4/6) retained 2542/2543/2527 pixels, respectively. It removed 788/787/790 of 1353 original-source Canny edge pixels. Connected-component count remained one. Only 16 owner pixels differed between the three observations.

Conclusion: parameter stability and connectivity do not establish anatomical validity. Do not promote appearance-only pruning. Raden original-file checksum was checked, but independent Raden owner-mask comparison was not performed. Real Chromium, original Stage8 cap, expanded SVG budget, and human Golden remain pending.

Engineering validation: the committed test file defines **8 tests total** (5 synthetic, 3 requiring signed private inputs). The earlier `13/13 signed-input tests` claim was incorrect and is withdrawn. Prior run reported 8/8 PASS with signed inputs; independent CI on public checkout will report 5 PASS / 3 SKIP until signed inputs are provided. Tests passing does not imply visual approval. No source or mask was overwritten.
