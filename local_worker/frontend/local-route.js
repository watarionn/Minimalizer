// Private adapter. Same-origin LocalWorker only; never downgrade to Browser.
(function () {
"use strict";
function payload(file) {
  const body = new FormData();
  body.append("file", file, file.name || "image");
  body.append("preset", "minimal");
  body.append("include_facets", "true");
  return body;
}
async function checkReady() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch("/health", {signal: controller.signal, cache: "no-store"});
    if (!response.ok) throw new Error("health " + response.status);
    const state = await response.json();
    if (state.worker !== "local-compute-v1" || state.ready !== true)
      throw new Error("LocalWorkerの準備ができていません。");
  } finally { clearTimeout(timer); }
}
window.MinimalizerComputeRoute = Object.freeze({
  label: "Minimalizer Local · ZeroBase2 BEST",
  description: "本人専用LocalWorkerでZeroBase2 BESTを優先し、必要に応じてLocal V2で処理します。",
  processingCopy: "LocalWorkerで画像の構造を解析中…",
  initialStatus: "本人専用LocalWorkerです。Browserへの自動切り替えは行いません。",
  resultLabel(response) {
    return response.headers.get("x-minimalizer-route") === "zerobase2"
      ? "Minimalizer Local · ZeroBase2 BEST" : "Minimalizer Local · V2 HIGH";
  },
  successMessage(response, reason) {
    return response.headers.get("x-minimalizer-route") === "zerobase2"
      ? "ZeroBase2 BESTで処理が完了しました。"
      : (reason ? "ZeroBase2からLocal V2へ切り替えて処理しました (" + reason + ")。" : "Local V2で処理が完了しました。");
  },
  async minimalize(file, setStatus) {
    try { await checkReady(); }
    catch (error) {
      throw new Error("LocalWorkerへ接続できません。TailscaleとPC側Workerを確認してください。 " + (error.message || String(error)));
    }
    let reason = "";
    try {
      const best = await fetch("/api/zerobase2/minimalize", {method:"POST",body:payload(file),cache:"no-store"});
      if (best.ok || best.status === 400 || best.status === 415) {
        return {response:best,compute:"local-worker",fallbackReason:"",qualityTier:"best"};
      }
      reason = best.status === 422 && best.headers.get("x-minimalizer-failure-class") === "quality-gate"
        ? "quality-gate:" + (best.headers.get("x-minimalizer-failed-stage") || "unknown")
        : "zerobase2-" + best.status;
    } catch (_) { reason = "zerobase2-unavailable"; }
    setStatus("ZeroBase2が使用できないためLocal V2で再試行します。");
    let high;
    try { high = await fetch("/api/v2/minimalize", {method:"POST",body:payload(file),cache:"no-store"}); }
    catch (_) { throw new Error("Local V2にも接続できませんでした。Browserへは切り替えません。"); }
    return {response:high,compute:"local-worker",fallbackReason:reason,qualityTier:"high"};
  },
});
if ("serviceWorker" in navigator) {
  addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
})();
