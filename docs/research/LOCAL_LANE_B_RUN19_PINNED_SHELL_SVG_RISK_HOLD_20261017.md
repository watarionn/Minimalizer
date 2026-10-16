# Lane B Run19 research-only HOLD (2026-10-17 JST)

Scope: L04 Stage8/SVG non-destructive diagnostics and L07 private PWA Service Worker. No lane A, Public/C08, production LocalWorker, Golden, release or signed original modification.

GitHub main pinned at `4b1f6dc65a1b166966d88fdb24be013a5a480218`; B branch before this note `6935b15b506b43020e2b87b7ad10a9d1e71f7d3b`, 9 ahead/0 behind. Main SW blob `9dcf1b658e7c4160a4ce7d9efd0e91242559cbe2` still has foreign-cache deletion, unscoped match and query-shell interception. PR #417 static privacy audit does not repair the runtime SW.

Run18 ZIP and handoff were restored to the established Google Drive folder and provider-readback SHA/byte matched.

Run19 new research only:
- L07 v10 read-only shell byte verifier: requires a separately trusted canonical eight-asset manifest SHA before cache reads, bounded 2 MiB streaming clone digest, no cache mutation. A caller-controlled manifest and fake trust digest remain an explicit HOLD witness. Atomic cache install/collision/quota/rollback and approved deployment manifest unresolved.
- L04 SHA-bound SVG structural risk inventory: rejects noncanonical XML/namespace/DTD/PI; counts root/group visual overrides, foreign/animated/script nodes, paint, unsupported paths. It never authorizes owner, silhouette, or Golden.
- Fresh extraction tests: Node 118/118 and Python 40/40 PASS, synthetic/VM only. Real Chromium probe timed out; Safari/iPhone/Tailscale/Worker not accepted.
- Official signed Local Stage8 source image+JSON+expanded SVG triple not established; Public Stage8 not substituted. Source ring vertices and expanded SVG bytes/endpoints remain distinct.
- ZIP SHA256 `d51544d37f5aaf3207c52561b0e98ec1ab67ec4fea22ba44033d2f355fa82584` (32-file manifest verified).

No deploy, no Golden promotion, no production merge. L02/L04/L07/Golden HOLD, production NO_GO.
