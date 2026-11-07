# L02 PR #445: real signed-input adapter replay, historical Run30 (2026-10-27)

**Research/HOLD only. No accepted P0/P1 visual repair.** This note and the accompanying code/pins contain no original pixels, human masks, NPZ, coordinates or private image exports. Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD / production NO_GO.

## Provenance and replay boundary

GitHub main was read as 4a4348990084848c981811b414e6221411271f84 before this A-only PR update. Canonical private Drive was checked. Historical source-free staging archive SHA-256 c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc passed 98/98 internal SHA checks; its 235 tests and 31 subtests passed locally. This is not current-main CI.

Authenticated private ZIP digests: ReviewedEvidence 6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598; Run30 owner 6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c; independent SleeveSemantic a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7. ReviewedEvidence 19/19 and Run30 7/7 internal entries matched. Only original source bytes, class IDs and frozen owner were passed to inference; no human annotation or mask was passed.

Source-free manifest SHA-256 pins:
- H06 LOCAL_L02_PR445_H06_RUN30_PIN_20261027.json: b91a139d075ae8e725db63e1a9f6f98f7fe29f12f3484e75deae9f89e7d24e0d
- H08 LOCAL_L02_PR445_H08_RUN30_PIN_20261027.json: 40d0864e7b1d6ed581617d3335c419a5ca6346454ebbb95d37ef2292405dbc24

Decoded-RGBA pins were derived only after independently verifying the encoded source SHA. Class and owner pins were derived from verified private ZIPs. These are historical Run30 pins, not current-main composed owner pins.

## Actual signed adapter replay

The new A-only runner tools/research/local_l02_dual_owner_signed_replay.py executes the existing PR #445 signed adapter, requiring an externally supplied manifest SHA and source/class/owner digest pins. It rejects wrong-stage, wrong-source, wrong-class, wrong-owner, malformed NPZ and oversized decompression; stdout contains a source-free receipt only. No owner image or private source is saved.

| Historical signed case | Frozen owner SHA-256 | Proposal SHA-256 | New class32 source pixels |
| --- | --- | --- | ---: |
| H06 | 4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317 | unchanged | 0 |
| H08 | 43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52 | b4e5201e22bef51b14e6aa814b745653cc91449b6d7427fc9eae7751ac351291 | 3,356 |

H06 single-owner abstention is not a passed dual-owner contact audit; receipt audits are null. H08 frozen-owner and new cross-owner 4/diagonal-edge audits returned zero violations. **The 3,356 H08 additions are unscored in this replay.** Earlier known Run30 review found 3,355 known positives and one unknown; this is neither unseen-character nor current-main evidence. Large sleeve/shoulder gaps remain; H06 underlayer and H04 false-owner P0 remain.

Six new runner contract tests, including corrupt NPZ rejection, passed locally. Combined isolated staging suite passed 241 tests and 31 subtests. This is not exact remote PR-head CI or Phase4 semantic PASS.

## Safe invocation and remaining gates

With independently authenticated private source, class NPZ, owner NPZ and the exact pinned manifest, invoke the runner using --source, --classes, --owner, --manifest and --manifest-sha256, with the external SHA above. Never calculate the expected manifest SHA from the untrusted file supplied in the same invocation. The runner accepts no private output path.

Next: integrate current-main composed-owner dependencies without overwriting the authoritative frozen-owner/contact audits; perform H04/H06/H08 complete signed regression and independent sleeve/arm/underlayer semantic checks. Unknown-character blind, full PR CI, Phase4 exclusivity/topology/critical-part quality, Phase5, Golden and physical iPhone acceptance remain open. **Accepted P0/P1 fixes 0/0; unresolved H04/H06/H08 = 3.** No B L04/L07, Public/C08, LocalWorker production or Golden changes.
