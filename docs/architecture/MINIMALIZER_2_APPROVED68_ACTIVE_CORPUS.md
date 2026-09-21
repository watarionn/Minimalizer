# Approved-68 Active Evaluation Corpus

Status: ACTIVE calibration corpus
Updated: 2026-09-20

Approved-78 remains the provenance/source corpus. Cases 59-68 are retired from active quality scoring because their approved references use a distinct compact composition regime (subject height approximately 33-35% of canvas), unlike the remaining corpus where subject height is generally near full-frame.

Active evaluation set: 68 cases
Retired from active scoring: 10 cases (#59-68)
- Akai Haato
- Yuzuki Choco
- Shiranui Flare
- Anya Melfissa
- Ayunda Risu
- Ichijou Ririka
- Mizumiya Su
- Rindo Chihaya
- Hanazono Sayaka
- Kazeshiro Yuki

Policy:
- Do not delete the retired references. Preserve them for provenance and composition research.
- Do not tune production behavior to reproduce the retired batch-specific scale.
- Engine quality gates and future calibration use Approved-68 unless a test explicitly studies composition.
- The hierarchy-cut 40-shape decision remains valid; all 68 active cases still select exactly 40 regions in the current guided evaluation.

Current guided + Subject Class Conflict Gate diagnostic on Approved-68:
- color similarity mean: 0.933399
- edge IoU mean: 0.080978
- silhouette IoU mean: 0.747955
- selected regions mean: 40.0
- visible groups mean: 24.808824

The isolated Subject Class Conflict Gate A/B has now been completed with the same rembg guidance and evaluator; results are recorded below.

## Subject Class Conflict Gate adoption result (2026-09-20)

Approved-68 controlled A/B with identical rembg isnet-anime guidance and Minimal 40-region cut.

Gate OFF -> ON: color 0.933149 -> 0.933399 (+0.000250); edge IoU 0.080981 -> 0.080978 (-0.000003); silhouette IoU 0.733598 -> 0.747955 (+0.014358); visible groups 24.3235 -> 24.8088; palette count 7.2500 -> 7.4559.

Silhouette outcomes: 26 improved / 38 unchanged / 4 regressed. Largest gains: Sorashina Sopia +0.183450 and Usada Pekora +0.137625. Largest regression: Hoshimachi Suisei -0.001394.

Decision: ACCEPT for the production guided V2 path. The gate prevents a palette hierarchy node from containing both confidently foreground (+1) and confidently background (-1) regions. It is inactive when subject guidance is absent or uncertain. Edge quality is effectively neutral while silhouette agreement improves materially.

Regression coverage: cross-class palette merge is blocked under confident subject guidance; unguided palette behavior remains merge-compatible; palette + hierarchy-cut focused suite 16/16 PASS.


## Production rembg model selection (2026-09-20)

Production guidance was evaluated against the Railway-class 1 GiB memory envelope.

Approved-68, Subject Class Conflict Gate ON:
- isnet-anime: color 0.933399, edge IoU 0.080978, silhouette IoU 0.747955, mean runtime 4.698 s.
- u2netp: color 0.933428, edge IoU 0.082518, silhouette IoU 0.745789, mean runtime 3.948 s.
- u2netp - isnet-anime: color +0.000030, edge IoU +0.001541, silhouette IoU -0.002167, runtime -0.750 s.

Against the isnet-anime Gate-OFF baseline, u2netp + Gate ON still improves color by +0.000279, edge IoU by +0.001538, and silhouette IoU by +0.012191.

Runtime/memory validation:
- isnet-anime model artifact is about 176 MB and exceeded the 1 GiB container envelope during real inference; the constrained run exited 137.
- u2netp model artifact is about 4.57 MB.
- u2netp completed rembg guidance -> Minimalizer V2 -> Subject Class Conflict Gate -> PNG export under a 1 GiB container limit.
- default ONNX Runtime allocation reached roughly 979 MiB after repeated requests, leaving too little headroom for a 1 GiB service.
- production ONNX Runtime session options disable the CPU memory arena and memory pattern, use one intra-op/inter-op thread, and use BASIC graph optimization. The exported PNG stayed byte-identical for the checked sample while post-request memory fell to about 475-501 MiB.

Decision: use u2netp for the production V2 guidance bridge. Keep isnet-anime as a higher-memory evaluation/reference provider, not the default hosted model.


Production-container smoke:
- Docker image built successfully on python:3.12-slim with rembg 2.0.84 and onnxruntime 1.26.0.
- u2netp weights are baked at build time under REMBG_HOME and load successfully with --network none as the non-root runtime user.
- /health returned HTTP 200.
- /api/v2/minimalize completed a real Approved-corpus image with HTTP 200 under --memory 1g --memory-swap 1g.
- with the production low-memory ONNX Runtime session, observed post-request memory was about 475 MiB after the first request and about 501 MiB after the second request under the 1 GiB limit.
- the first lazy-session request took about 34.0 s on the local Docker host; the next warm request took about 4.75 s. The cold-start value is tracked separately from steady-state processing latency.
- repeated sample outputs were byte-identical (same SHA-256) across cold/warm requests.
- with the production one-slot setting, an overlapping second V2 request returned HTTP 429 in about 0.06 s while the accepted request completed with HTTP 200.
- `/api/info` reports `max_concurrent_jobs=1`; `/api/v2/info` reports `hosted_default_analysis_max_side=400`.


## Structure Track: background-color collision rescue (2026-09-21)

A representative failure was confirmed on Otonose Kanade: a large hair region remained present through Region Merge but was absorbed into a background-colored palette group because its subject ratio was high (0.908) while subject confidence was only 0.714. The hair sample color was effectively identical to a confident background sample (Delta E 0.0).

A broad confidence-threshold reduction from 0.80 to 0.70 improved mean silhouette but caused avoidable color regressions, including Houshou Marine. That global relaxation was rejected.

The accepted calibration candidate is deliberately narrow:

- keep the normal subject/background classification at confidence >= 0.80
- only consider rescue for uncertain regions with subject ratio >= 0.90 and confidence in [0.70, 0.80)
- require a confident background region whose sampled color is nearly identical (Delta E <= 2.0)
- rescue only the subject side; do not symmetrically relax background classification

Approved-68 production-model A/B, u2netp guidance, Minimal 40-region cut:

- baseline: color 0.933428373, edge IoU 0.082518442, silhouette IoU 0.745788874
- collision rescue: color 0.933414182, edge IoU 0.082536358, silhouette IoU 0.745892808
- delta: color -0.000014191, edge +0.000017916, silhouette +0.000103934

Only two of 68 cases changed under the existing comparison metrics:

- Otonose Kanade: color -0.001072700; edge unchanged; legacy silhouette metric unchanged
- Shirakami Fubuki: color +0.000107709; edge +0.001218260; silhouette +0.007067536
- the other 66 cases were metric-identical

The legacy silhouette metric is not reliable for the Kanade failure because the light beige background is counted as foreground by the simple RGB threshold. A case-specific border-connected background diagnostic was therefore used as an additional visibility check:

- old visible non-background area: 54.9135%
- rescue visible non-background area: 60.8564%
- visible-area gain: +5.9429 percentage points
- newly visible pixels: 6,870
- newly background pixels: 0

This diagnostic is not a replacement for the corpus metric. It is evidence that the targeted palette collision was actually removed in the representative failure case.

Decision: ACCEPT as a Structure Track adoption candidate. Repository-wide regression completed with 572 passed, 2 failed, 1 warning; the two failures are the pre-existing missing fixture tests for tests/assets/false_face_phase85.png. No new Structure Track regression was introduced. The rule is intentionally collision-specific so it does not turn into a general confidence-threshold relaxation.
