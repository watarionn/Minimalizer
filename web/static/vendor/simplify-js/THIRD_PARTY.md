# Simplify.js browser research dependency

- Package: `simplify-js@1.2.4`
- Upstream: https://github.com/mourner/simplify-js
- License: **BSD-2-Clause**, mandatory attribution in the adjacent `LICENSE` file.
- Original npm archive's `package/simplify.js` SHA-256: `e4c7a1a8a141d47103eb82c64eb5286b483ed0efae28ecd238f6232b6d0b7b85`.
- The JavaScript committed to GitHub is the original 123-line 3,195-byte LF package file. On Windows, Git's local checkout may normalize LF to CRLF (3,318 bytes), so compare normalized logical source or the Git blob, not a Windows checkout byte hash.
- Self-hosted only by `web/static/index.html` (Public static build). No CDN, external worker, Python runtime or Local route use.
- Normal Public conversions do not invoke the simplifier. To opt into read-only geometry research, open Public with `?publicSimplifyResearch=1`.
- The companion `public-simplify-research.js` uses the real Simplify.js and the existing Public OpenCV-compatible mask rasterizer. A proposed contour reduction is counted only after **whole-owner mask bit equality** at the existing Public raster resolution. The proposed rings are **never applied to the PNG or SVG output**.
