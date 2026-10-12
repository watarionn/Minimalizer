# MinimalizerPublic P0 Stage16 CI / secure browser boundary

Date: 2026-10-11 JST. Research-only PR #390; no main/Local Worker/production edits.

## GitHub Actions PASS

New research workflow `.github/workflows/minimalizerpublic-p0-research.yml` executes Node 22, without dependencies or privileged GitHub permissions. Initial Stage12–15 18-test run **38109343104 PASS**. Updated workflow enumerates all seven source-only Stage1–15 test files and full cross-stage regression run **38109402058 completed SUCCESS** at commit `718c4f025b9cea31a3ce3f641a27197db3a169d0`. The first and second workflow conclusions were read back via GitHub connector. Do not infer exact testcase counts from the GitHub run conclusion without checking job logs; local Stage12–15 has 18 independent PASS.

## Secure-origin native browser remains NOT VERIFIED

An isolated Python `ThreadingHTTPServer` on 127.0.0.1 was launched to test actual imported Stage12 ES module and native `crypto.subtle` on a browser trusted origin. Chromium navigation was denied with `Page.goto: net::ERR_BLOCKED_BY_ADMINISTRATOR`. The module import and WebCrypto test did not run. This is a test-environment navigation limitation, NOT a browser WebCrypto PASS, and NOT a defect in the module proven by this attempt. Native trusted domain, real production route, full-character SVG/clip, iPhone Safari and human Golden are still HOLD.

## Next

Do not pursue additional micro-pixel contour tolerances before major body structure/owner semantics. Prioritize 2-source signed silhouette and arm/sleeve/ruffle/collar masks and source-respecting z-order. Raden/GC001 exact source-only SVG foreground module is usable in research but cannot pass original Stage8 geometry cap or replace independent user visual review.
