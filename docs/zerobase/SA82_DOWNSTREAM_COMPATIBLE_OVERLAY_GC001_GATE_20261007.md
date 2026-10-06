# SA8.2 Downstream-Compatible Overlay GC001 Gate — 2026-10-07
Status: **HOLD / NOT MERGED**

Synthetic validation: focused 12/12 PASS; full ZeroBase 753/753 PASS; compileall PASS.

Fresh GC001: hard gate PASS; Feature Survival 16/16, missing=0; Forbidden Face Detail 0.00%.
Visual delta vs adopted 13.8279%.
Evaluation-only Golden Lab: SA8.2 94.6476; SA7.44 51.4763; v12 33.4426.
Golden/v12 were never inference inputs.

SA8.2 improves slightly over SA8.1 (95.3020 -> 94.6476) but remains a severe regression. Decision HOLD.

Conclusion: smarter preselection is insufficient while SA8 owns a dedicated draw pass. Next experiment should remove special draw authority and feed SA8 source evidence into the existing perceptual-region competition, under the existing global budget.
