# C02b4/b5/b6: signed owner alpha and provenance gate (2026-10-10)

Status **C02 SOURCE SEMANTIC QUALITY HOLD**, no source edits or production promotion.

## Independently verified completed research

- C02b4: GC001 original Stage8 right-arm mask 6510 pixels; 533 exact source-border RGB intersections (520 opaque, 13 partial alpha, 0 alpha-zero). Raden right/left intersections 2/7; Raden left owner covers 74 alpha-zero and 38 partial original pixels. **15/15 real signed-source tests PASS**, 3/3 deterministic evidence outputs. Alpha and exact RGB cannot establish semantic arm/background ownership. Original signed comparison boards archived privately. See Drive archive `Minimalizer_C02B4_Alpha_Owner_Research_20261010.zip` SHA `025df669b37e54fcea8b7cde6379564b2390c1d0085ec0c0ee6226bf3f6dfa74`.
- C02b5: historical SA10.41 signed Phase04 left 2715 pixels, currently recovered Phase04 left 2330, signed Stage8 left 2718. Historical/current XOR 385 (historical only); historical/Stage8 XOR 5, current/Stage8 XOR 390. Right arm 6486/6486/6510 with historical/current XOR0, face 4937 all 3 versions XOR0. **15/15 signed-source tests PASS**, 2/2 reproducible private artifacts. Source revision mismatch strongly supported, exact historical producer/config not recovered. Drive `Minimalizer_C02B5_Phase04_Lineage_20261010.zip` SHA `78a8dbbf346d6be1c630f7a7ac49dc688a381d4e7a424f6dbb7bd06e308d5ac0`.
- C02b6: the GC001 signed Phase03 stage SHA `c1485333f581e26ca75e2d425cc09f061ff06d721839777300ee73da829d460c` is the Phase04 recorded upstream input; Phase04 stage SHA `7a73dc4ae03fd4a5d5789a7d0bc8e0103f480cb3ae44a88badc28f06db56ff0e`; original source SHA matches in both; original stored part-mask output hashes verified. **9/9 local signed-source tests PASS** including intentional tamper rejection and deterministic second run. Private ZIP omits an otherwise declared `preview.png`, so the auditor marks it `not_archived` rather than pretending it was validated. Actual Stage8 `source_evidence_refs` stores `phase04:part_masks/...` path strings for left/right/face, **without the source Phase04 artifact SHA**. The exact historic Phase04 producer/config that Stage8 used is therefore **UNPROVEN**. Close mask resemblance is not equivalent to cryptographic input authority. The 385/390 pixel difference remains a research question, not a bug fix.

C02b6 validated using signed GC001 original + immutable private Phase03/04 snapshot SHA `89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434` and Stage8 scene SHA `7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08`. Non-sensitive aggregate evidence is in the companion coordinate-free JSON. Code and private originals remain outside GitHub until approved archival/write path is available; old b4/b5 code and tests are preserved in the two above immutable private archives.

## Critical boundary

These engineering PASS results are not artistic quality PASS. Stage8 original ring budgets GC001 3604/1887, Raden 2370/1412 remain **HOLD**; C04 human signed Golden 12 criteria remain PENDING. C05-C08 BLOCKED. `release_authorized=false`, `deployment_verified=false`, `production_changed=false`. No generation/inpainting, face details remain OFF.

## Next C02b7

Recover historical Phase04 config/build SHA if possible; introduce SHA-aware producer sidecar for future Stage8 inputs (without retroactively rewriting signed evidence); only then try source-grounded semantic owner candidates with independently verified Raden/Approved holdouts and actual Chromium before human Golden. Never automatically prefer current or historical mask, use RGB/alpha as semantic ground truth, or promote a source-inconsistent Stage8 ring.

Canonical research archive (signed private test scripts, synthetic + real test suite, numeric outputs, no original source images): https://drive.google.com/file/d/1eQA0oklXLqch8doVXv_CHs9SauKmtGQ7/view . Archive SHA256 7901d23af6d726e7c96b90b3b8ab268475dbb704bb0701d4479e779257c3340c. Source and Stage8 original signed assets remain separately private. No public inference for missing SHA authority.
