# MinimalizerLocal Lane B Run10: strict retry and cache ownership (research-only)

Canonical baseline: main `4b1f6dc65a1b166966d88fdb24be013a5a480218`, B branch `c4e4613cebdcde1b8583fbbc5ef3f7277a6c0afd` at inspection. Run9 checkpoint verified 53/53 SHA-256 members.

## L07 diagnostics
- BEST ambiguous network completion: do not double-upload. Proposed v4 only allows V2 fallback for explicit backend 422 quality-gate or 503 route-disabled/runtime signals; 401/403/404/500/gateway and contradictory errors fail closed.
- Proposed v4 requires matching route/mode/tier, V2 compute identity, and image/png response MIME; all requests set redirect:error to prohibit 307/308 forwarding.
- SW v4 research proposal enumerates exact legacy cache keys (v1-v3) rather than wildcard deletion. New static and stateful tests cover foreign caches, API/image bypass and shell.
- Local source-free replay: Node 182/182 PASS, Python 252/252 PASS, total 434/434 scoped. Not repo CI, not Chromium/Safari, not live Tailscale/Worker. Main runtime and Public/C08 unchanged.

## L04
Existing SHA/owner/ring and source Stage8 vs expanded SVG research tests replayed; no actual signed Local Stage8 source+SVG trio independently attested. Historical Public Stage8 is not Local Golden. L04 remains HOLD.

Research ZIP SHA-256 `e043b428280d4996df5c5c8f2dc42900d13b4052ebdaa87bfc193e139bc4ccc1`. No private user images or masks in the source-free ZIP. A separate code review is required before integrating runtime changes.

L02 HOLD / L04 HOLD / L07 HOLD / Golden HOLD / production NO_GO. Next: recover signed Local Stage8 evidence; run private live browser/Worker/Origin tests; preserve and independently review candidate v4. No Golden or iPhone acceptance assumed.
