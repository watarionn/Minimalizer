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
const earcutResearch = new URLSearchParams(location.search).get("publicEarcutResearch") === "1";
const svgPathResearch = new URLSearchParams(location.search).get("publicSvgPathResearch") === "1";
const svgoResearch = new URLSearchParams(location.search).get("publicSvgoResearch") === "1";
const resvgResearch = new URLSearchParams(location.search).get("publicResvgResearch") === "1";
const clipper2Research = new URLSearchParams(location.search).get("publicClipper2Research") === "1";
const vtracerResearch = new URLSearchParams(location.search).get("publicVTracerResearch") === "1";
// Research-only PNG byte-level canary. No geometry/render/output modification.
const r5ShadowResearch = new URLSearchParams(location.search).get("publicR5Shadow") === "1";
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
    let svgoObserver = null;
    if (svgoResearch) {
      try {
        // Load SVGO only for explicitly opted-in Public research.
        svgoObserver = await import(new URL("static/public-svgo-research.mjs", document.baseURI).href);
      } catch (_) {
        // Optional observer unavailable: normal conversion must still succeed.
      }
    }
    let resvgObserver = null;
    if (resvgResearch) {
      try {
        resvgObserver = await import(new URL("static/public-resvg-research.mjs", document.baseURI).href);
      } catch (_) {
        // Optional independent oracle must not break the standard output.
      }
    }
    let clipper2Observer = null;
    if (clipper2Research) {
      try {
        clipper2Observer = await import(new URL("static/public-clipper2-research.mjs", document.baseURI).href);
      } catch (_) {
        // Opt-in WASM geometry observer unavailable: normal conversion continues.
      }
    }
    let vtracerObserver = null;
    if (vtracerResearch) {
      try {
        vtracerObserver = await import(new URL("static/public-vtracer-research.mjs", document.baseURI).href);
      } catch (_) {
        // VTracer is optional, diagnostics cannot break the normal converter.
      }
    }
    const result = await engine.minimalizeFile(file, {
      analysisMaxSide: 400, workMaxSide: 400, maxShapes: 40, slicIterations: 10, paletteTarget: 8,
      publicPolygonDiagnostics: true,
      publicSimplifyResearch: simplifyResearch,
      publicMeshResearch: meshResearch,
      publicEarcutResearch: earcutResearch,
      publicSvgPathResearch: svgPathResearch,
      publicSvgoResearch: svgoResearch,
      publicSvgoObserver: svgoObserver,
      publicResvgResearch: resvgResearch,
      publicResvgObserver: resvgObserver,
      publicClipper2Research: clipper2Research,
      publicClipper2Observer: clipper2Observer,
      publicVTracerResearch: vtracerResearch,
      publicVTracerObserver: vtracerObserver,
      structuralMode: p === "exact" ? "spectral-exact" : "l0-lite-jacobi",
      canonicalContourLite: ["sharp", "shape", "facet"].includes(p),
      geometryMode: p === "facet" ? "facet-safe" : p === "shape" ? "corner-aware" : "baseline",
    });
    if (r5ShadowResearch) {
      try {
        // The observer only clones a completed Response; it never replaces it.
        const observer = await import(new URL("static/public-r5-shadow-gate.mjs", document.baseURI).href);
        window.MinimalizerPublicR5ShadowLast = await observer.auditResponse(result.response);
      } catch (_) {
        window.MinimalizerPublicR5ShadowLast = Object.freeze({
          version:"public-r5-response-shadow-v1",status:"unavailable",
          applied:false,productionPromoted:false,mutationCount:0,
          sha256:null
        });
      }
    }
    return {response: result.response, compute: "browser", fallbackReason: "", qualityTier: "browser"};
  },
});
})();
