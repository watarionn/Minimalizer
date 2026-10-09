// Public adapter. Always use Browser compute; never contact LocalWorker.
(function () {
"use strict";
const KEY = "minimalizer.browserFallbackQuality";
const options = ["exact", "sharp", "shape", "facet", "lite"];
const query = new URLSearchParams(location.search).get("browserFallbackQuality");
if (options.includes(query)) localStorage.setItem(KEY, query);
const profile = () => options.includes(localStorage.getItem(KEY)) ? localStorage.getItem(KEY) : "lite";
// Opt-in research only. Normal Public processing does NOT execute contour experiments.
const simplifyResearch = new URLSearchParams(location.search).get("publicSimplifyResearch") === "1";
// Public-only opt-in: never generate/apply mesh in default conversions.
const meshResearch = new URLSearchParams(location.search).get("publicMeshResearch") === "1";
window.MinimalizerComputeRoute = Object.freeze({
  label: "Minimalizer Public · Browser",
  description: "画像はこのブラウザ内で処理されます。外部の計算サーバーには送信しません。",
  processingCopy: "ブラウザ内で輪郭と色を整理中…",
  initialStatus: "Browser版です。ミニマル化はこの端末内で実行されます。",
  resultLabel(response) {
    const p = response.headers.get("x-minimalizer-browser-quality-profile") || profile();
    return "Minimalizer Public · " + p.toUpperCase();
  },
  successMessage() { return "Browserでミニマル化が完了しました。"; },
  async minimalize(file) {
    const engine = window.MinimalizerBrowserFallback;
    if (!engine || typeof engine.minimalizeFile !== "function") {
      throw new Error("Browserエンジンを読み込めませんでした。ページを更新してください。");
    }
    const p = profile();
    const result = await engine.minimalizeFile(file, {
      analysisMaxSide: 400, workMaxSide: 400, maxShapes: 40, slicIterations: 10, paletteTarget: 8,
      publicPolygonDiagnostics: true,
      publicSimplifyResearch: simplifyResearch,
      publicMeshResearch: meshResearch,
      structuralMode: p === "exact" ? "spectral-exact" : "l0-lite-jacobi",
      canonicalContourLite: ["sharp", "shape", "facet"].includes(p),
      geometryMode: p === "facet" ? "facet-safe" : p === "shape" ? "corner-aware" : "baseline",
    });
    return {response: result.response, compute: "browser", fallbackReason: "", qualityTier: "browser"};
  },
});
})();
