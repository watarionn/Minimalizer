# MinimalizerLocal Lane A L02: H08 sleeve shape cleanup (2026-10-25)

**Research-only Draft. No semantic owner promotion. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / Local production NO_GO.**

## Goal and visible finding

The already integrated source-bound H08 contact-density/palette sleeve proposal adds 6,023 original-alpha pixels, but 17 reviewed arm pixels become coat/jacket owner. A fixed 3x3 binary opening applied to the **full proposed owner silhouette**, followed by 4-neighbour source-seed reachability, retains a visibly fuller patterned sleeve while removing thin unsupported additions. Opening only the sparse new-pixel delta was independently rejected: it removes all 6,023 candidate pixels. No labels, human polygon coordinates, private masks, image synthesis, inpainting, or face drawing are inference inputs.

## Authenticated signed replay, and an important baseline limitation

Canonical non-shared Drive ZIPs ReviewedEvidence, Run30 OwnerMasks, SleeveSemanticIndependent and AnimeSeg Offline384 matched their pinned SHA-256. Reviewed/Run30/AnimeSeg internal manifests matched 19/7/5. H08 signed source SHA-256 was independently checked. The A-only source-free 2026-10-23 composed replay code reconstructed **an older** H08 owner SHA-256 `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a`. This does **not** match the current pinned H08 owner, and cannot be used to certify a new improvement over latest main. The earlier H06 composed owner **did** match its pinned SHA `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`.

On that explicitly older H08 baseline, the source-only proposal was frozen and hashed **before** human labels were opened. Original H08 reviewed score: TP 136,780 / known FP 0 / FN 19,790. Existing contact-density/palette proposal: +6,023 source pixels, +5,583 reviewed outerwear, +17 reviewed arm FP, +423 unreviewed. New 3x3 full-owner cleanup: **+5,778 original source pixels**, comprising **+5,402 reviewed outerwear, 0 known false owner, 376 unknown**, TP **142,182**, known FP **0**, FN **14,388**. Frozen new owner SHA-256: `0f6bd044578989851df40fa87ab4861ced905dbf24f6fdd025782270e2b4ff8e`. The 245 rejected pixels include the prior 17 arm false owners. This is a meaningful **known-case provisional** sleeve recovery, not a blind PASS or accepted improvement over the current frontier.

H06 pinned composed owner remained byte-identical after the same research postfilter, TP 294,020 / known FP 1,077 / FN 20,803. H04 was not replayed. Private visual comparison shows fuller H08 patterned sleeves but remaining gaps. No private source, NPZ, masks, review geometry or images are in this PR.

## Code and verification

New A-only research module `tools/research/local_l02_contact_morphology_shadow.py` calls the existing contact-density/palette shadow. It preserves frozen owner pixels, forbids alpha escape and non-class32 promotions, verifies 4/8 component identity and no new cross-owner contacts, and returns explicit FAIL/HOLD receipt fields. Source-free targeted regression tests: 3 PASS. This is **not** full repository CI. The local research replay used source-free modules from a prior authenticated Drive snapshot, not a GitHub-exact latest-main dependency tree.

**Integration decision:** Draft only. Before merging or promoting, rerun this exact GitHub head against the current H08 composed→strict→single-anchor→contact-density→class30 opt-in pinned owner SHA `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`, compare latest-frontier TP/FP/FN and private visual quality, run H04/H06 regression and repository CI, and verify the 3 GitHub blobs against tested bytes. Do not treat old H08 improvement as a new accepted P0/P1 improvement. New **accepted** P0/P1 cases: **0/0**; three known P0 cases remain unresolved. Unknown signed blind: PENDING.

No Lane B L04/L07, Public/C08, production LocalWorker, Golden or release changes.
