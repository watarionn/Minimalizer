// Local PWA research-only SVG candidate bank. Never mutates production Minimalizer output.
import { readVTracerControls, writeVTracerControls, VTRACER_DEFAULTS } from "./vtracer-demo-options.mjs";
// ImageTracerJS: pinned locally to v1.2.6 (Unlicense).
// VTracer: uses the already-vendored browser WASM (release audit remains separate).
const $ = (id) => document.getElementById(id);
const IDS = ["vtracer", "imagetracer", "primitive", "geometrize", "primeval"];
const LOCAL_ENGINES = ["vtracer", "imagetracer"];
const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;
const MAX_SVG_BYTES = 2 * 1024 * 1024;
const state = { source: null, sourceFile: null, sha: null, results: new Map(), busy: false };
let vtracerInitPromise = null;
let autoVTracerTimer = null;
let pendingVTracerRun = false;

// Keep untrusted imported SVGs out of the DOM. Preview only as isolated <img> blob URLs.
function validatedSvg(value) {
  if (typeof value !== "string" || value.length > MAX_SVG_BYTES || value.length < 40)
    throw new Error("SVGのファイルサイズが範囲外です");
  const forbidden = /<\s*(?:!DOCTYPE|!ENTITY|script|foreignObject|image|iframe|object|embed|style|link|animate|set|use|filter|feImage|audio|video)\b|\bon[a-z]+\s*=|\b(?:xlink:href|href|src|style)\s*=|url\s*\(|@import|javascript\s*:/i;
  if (forbidden.test(value)) throw new Error("外部参照または実行可能なSVG要素を含んでいます");
  const doc = new DOMParser().parseFromString(value, "image/svg+xml");
  if (doc.querySelector("parsererror") || doc.documentElement?.localName !== "svg")
    throw new Error("正しいSVG文書ではありません");
  if (doc.documentElement.namespaceURI !== "http://www.w3.org/2000/svg")
    throw new Error("SVG名前空間が正しくありません");
  const allowed = new Set(["svg","g","path","polygon","polyline","rect","circle","ellipse","line","defs","clipPath","linearGradient","radialGradient","stop","title","desc"]);
  for (const element of doc.getElementsByTagName("*")) {
    if (!allowed.has(element.localName) || element.namespaceURI !== "http://www.w3.org/2000/svg")
      throw new Error("許可されていないSVG要素: " + element.localName);
    for (const attr of element.attributes) {
      if (attr.name.startsWith("on") || attr.name === "style" || /^(href|src|xlink:href)$/i.test(attr.name) ||
          /url\s*\(|javascript\s*:|@import/i.test(attr.value))
        throw new Error("SVGに許可されていない属性があります");
    }
  }
  return value;
}
function shapeCount(svg) {
  return (svg.match(/<(?:path|polygon|polyline|rect|ellipse|circle|line)\b/g) || []).length;
}
function setStatus(message, error = false) {
  const el = $("run-status");
  el.textContent = message;
  el.style.color = error ? "#ffd2a9" : "#bcdfdf";
}
function nextFrame() {
  return new Promise(resolve => requestAnimationFrame(() => setTimeout(resolve, 0)));
}
function blobURL(svg) {
  return URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
}
async function loadVectorImage(url) {
  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = () => reject(new Error("SVGのプレビューを読み込めません"));
    img.src = url;
  });
  return img;
}
function renderOriginal(canvas) {
  if (!state.source) return;
  canvas.width = state.source.width;
  canvas.height = state.source.height;
  canvas.getContext("2d", { willReadFrequently: true }).putImageData(state.source, 0, 0);
}
function clearCandidates() {
  clearTimeout(autoVTracerTimer);
  pendingVTracerRun = false;
  for (const candidate of state.results.values()) URL.revokeObjectURL(candidate.url);
  state.results.clear();
  for (const id of IDS) {
    const slot = document.querySelector('[data-slot="' + id + '"]');
    slot.replaceChildren();
  }
  const sel = $("select-candidate");
  sel.replaceChildren(new Option("先に候補を生成してね", ""));
  $("download-svg").disabled = true;
  $("download-manifest").disabled = true;
  $("selected-preview").hidden = true;
  $("selected-preview").removeAttribute("src");
  $("selected-metrics").textContent = "未選択";
}
async function imageSource(file) {
  if (!file) return;
  if (!["image/png","image/jpeg","image/webp"].includes(file.type) ||
      file.size < 1 || file.size > MAX_UPLOAD_BYTES)
    throw new Error("PNG/JPEG/WebP、20MB以内の画像を選んでね");
  const local = URL.createObjectURL(file);
  try {
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = () => reject(new Error("画像を読み込めません"));
      img.src = local;
    });
    if (!img.naturalWidth || !img.naturalHeight || img.naturalWidth > 8192 || img.naturalHeight > 8192)
      throw new Error("画像の縦横は8192px以内にしてね");
    const size = Number($("resolution").value);
    const ratio = Math.min(1, size / Math.max(img.naturalWidth, img.naturalHeight));
    const width = Math.max(1, Math.round(img.naturalWidth * ratio));
    const height = Math.max(1, Math.round(img.naturalHeight * ratio));
    const canvas = $("source-canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.clearRect(0,0,width,height);
    context.drawImage(img,0,0,width,height);
    const data = context.getImageData(0,0,width,height);
    const digest = await crypto.subtle.digest("SHA-256", data.data);
    const sha = Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2,"0")).join("");
    clearCandidates();
    state.source = data;
    state.sourceFile = file;
    state.sha = sha;
    renderOriginal($("comparison-canvas"));
    $("source-status").textContent = file.name + " / " + img.naturalWidth + "×" + img.naturalHeight +
      " → " + width + "×" + height + " px / RGBA SHA256 " + sha.slice(0,16) + "…";
    $("run-local").disabled = false;
    for (const b of document.querySelectorAll("[data-run]")) b.disabled = false;
    setStatus("比較用画像を読み込んだよ");
  } finally {
    URL.revokeObjectURL(local);
  }
}
async function runVTracer(settings) {
  if (!vtracerInitPromise) {
    vtracerInitPromise = (async () => {
      const mod = await import("../static/vendor/vtracer-wasm/vtracer.mjs");
      const response = await fetch("../static/vendor/vtracer-wasm/vtracer.wasm", { cache: "no-store" });
      if (!response.ok) throw new Error("WASMの取得に失敗");
      await mod.default({ module_or_path: new Uint8Array(await response.arrayBuffer()) });
      return mod.to_svg;
    })().catch(err => { vtracerInitPromise = null; throw err; });
  }
  const trace = await vtracerInitPromise;
  const src = state.source;
  return trace(new Uint8Array(src.data), src.width, src.height, settings);
}
function runImageTracer() {
  if (!window.ImageTracer || typeof window.ImageTracer.imagedataToSVG !== "function")
    throw new Error("ImageTracerJSのローカルライブラリを読み込めません");
  return window.ImageTracer.imagedataToSVG(state.source, {
    numberofcolors: Number($("colors").value), colorquantcycles: 3,
    pathomit: 8, ltres: 1, qtres: 1, scale: 1,
    linefilter: false, viewbox: true, strokewidth: 0,
    layering: 0, rightangleenhance: true
  });
}
async function assess(svg, url) {
  const image = await loadVectorImage(url);
  const original = state.source;
  const canvas = document.createElement("canvas");
  canvas.width = original.width;
  canvas.height = original.height;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(image,0,0,canvas.width,canvas.height);
  const observed = ctx.getImageData(0,0,canvas.width,canvas.height).data;
  let absolute = 0, changed = 0, alphaChanged = 0;
  for (let i=0;i<observed.length;i+=4) {
    let isDifferent = false;
    for(let k=0;k<4;k++){
      const v = Math.abs(observed[i+k]-original.data[i+k]);
      absolute += v;
      if(v) isDifferent = true;
    }
    if(isDifferent) changed++;
    if(observed[i+3]!==original.data[i+3]) alphaChanged++;
  }
  return {
    shapes: shapeCount(svg),
    svgBytes: new Blob([svg]).size,
    meanAbsRgba: Number((absolute / observed.length).toFixed(3)),
    changedPixels: changed, alphaChangedPixels: alphaChanged, totalPixels: original.width*original.height
  };
}
function updateSelector() {
  const sel = $("select-candidate");
  const value = sel.value;
  sel.replaceChildren(new Option("候補を選択", ""));
  for (const id of IDS) if (state.results.has(id)) sel.add(new Option(id, id));
  if(state.results.has(value)) sel.value = value;
  else if(state.results.size) sel.value = state.results.keys().next().value;
  showSelected();
  $("download-manifest").disabled = !state.results.size;
}
function updateCard(id) {
  const slot = document.querySelector('[data-slot="' + id + '"]');
  slot.replaceChildren();
  const candidate = state.results.get(id);
  if (!candidate) return;
  const img = document.createElement("img");
  img.src = candidate.url;
  img.alt = id + " SVG候補";
  const detail = document.createElement("p");
  detail.className = "stat";
  detail.textContent = "図形要素 " + candidate.metrics.shapes +
    " / RGBA平均絶対差 " + candidate.metrics.meanAbsRgba +
    " / alpha差 " + candidate.metrics.alphaChangedPixels + "px";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = "これを比較";
  btn.addEventListener("click", () => { $("select-candidate").value = id; showSelected(); });
  slot.append(img,detail,btn);
}
async function registerCandidate(id, raw, source, settings = null) {
  const svg = validatedSvg(raw);
  const url = blobURL(svg);
  let metrics;
  try { metrics = await assess(svg, url); }
  catch(err) { URL.revokeObjectURL(url); throw err; }
  const old = state.results.get(id);
  if (old) URL.revokeObjectURL(old.url);
  state.results.set(id, {svg,url,metrics,source,sha:state.sha,settings});
  updateCard(id);
  updateSelector();
}
function showSelected() {
  const result = state.results.get($("select-candidate").value);
  const img = $("selected-preview");
  img.hidden = !result;
  $("download-svg").disabled = !result;
  if (!result) { img.removeAttribute("src"); $("selected-metrics").textContent = "未選択"; return; }
  img.src = result.url;
  $("selected-metrics").textContent =
    "図形 " + result.metrics.shapes + " / SVG " + result.metrics.svgBytes + " bytes / " +
    "RGBA平均絶対差 " + result.metrics.meanAbsRgba + " / 差分 " +
    result.metrics.changedPixels + "/" + result.metrics.totalPixels +
    " pixels （画像の意味的な正しさの評価ではない）";
}
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.hidden = true; document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}
async function runOne(id) {
  if(!state.source || state.busy || !LOCAL_ENGINES.includes(id)) return;
  state.busy = true;
  $("run-local").disabled = true;
  for(const b of document.querySelectorAll("[data-run]")) b.disabled = true;
  setStatus(id + " を実行中…");
  await nextFrame();
  try {
    const sha = state.sha;
    const settings = id === "vtracer" ? readVTracerControls() : null;
    const svg = id === "vtracer" ? await runVTracer(settings) : runImageTracer();
    if(sha !== state.sha) throw new Error("入力画像が途中で変更された");
    await registerCandidate(id, svg, "local", settings);
    setStatus(id + " の研究候補を生成したよ");
  } catch(err) {
    setStatus(id + ": " + (err?.message || String(err)), true);
  } finally {
    state.busy = false;
    $("run-local").disabled = !state.source;
    for(const b of document.querySelectorAll("[data-run]")) b.disabled = !state.source;
    if (pendingVTracerRun && state.source) {
      pendingVTracerRun = false;
      // Do not run VTracer recursively while another conversion is finishing.
      setTimeout(() => { if (state.source) runOne("vtracer"); }, 0);
    }
  }
}
$("run-local").addEventListener("click", async () => {
  for(const id of LOCAL_ENGINES) await runOne(id);
});
for(const button of document.querySelectorAll("[data-run]"))
  button.addEventListener("click",() => runOne(button.dataset.run));
for(const element of document.querySelectorAll("[data-import]"))
  element.addEventListener("change", async () => {
    const file = element.files?.[0];
    if(!file || !state.source) { setStatus("先に同じ元画像を選択してね", true); return; }
    try {
      if(file.size > MAX_SVG_BYTES || file.size < 40) throw new Error("SVGは2MB以内にしてね");
      await registerCandidate(element.dataset.import, await file.text(), "import");
      setStatus(element.dataset.import + " のSVG候補を読み込んだよ");
    } catch(err) { setStatus(err?.message || String(err), true); }
    element.value = "";
  });
$("image-file").addEventListener("change", async event => {
  if(state.busy) return;
  try { await imageSource(event.target.files?.[0]); }
  catch(err) { $("source-status").textContent = err?.message || String(err); }
});
$("resolution").addEventListener("change", () => {
  if(state.sourceFile && !state.busy) imageSource(state.sourceFile).catch(err => setStatus(err.message,true));
});
$("colors").addEventListener("change", () => {
  if(!state.busy && state.source) {
    clearCandidates();
    setStatus("色数が変わったので候補をリセットしたよ");
  }
});
$("select-candidate").addEventListener("change", showSelected);
$("download-svg").addEventListener("click", () => {
  const id = $("select-candidate").value;
  const candidate = state.results.get(id);
  if(candidate) download(new Blob([candidate.svg], {type:"image/svg+xml"}), "minimalizer-lab-" + id + ".svg");
});
$("download-manifest").addEventListener("click", () => {
  if(!state.source || !state.results.size) return;
  const payload = {
    schema: "minimalizer/local-pwa-five-engine-lab/v1",
    kind: "research-only-not-golden",
    sourceRgbaSha256: state.sha,
    width: state.source.width,
    height: state.source.height,
    candidates: Object.fromEntries(Array.from(state.results,([id,value]) =>
      [id,{source:value.source,metrics:value.metrics,settings:value.settings}]))
  };
  download(new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json"}),"minimalizer-lab-comparison.json");
});

function refreshVTracerControls() {
  for (const field of document.querySelectorAll("#vtracer-settings input[type=range]")) {
    const label = document.getElementById(field.id + "-value");
    if (label) label.textContent = field.value;
  }
  const bw = $("vtracer-color-mode").value === "bw";
  const spline = $("vtracer-mode").value === "spline";
  for (const field of document.querySelectorAll('[data-condition="color"]')) field.hidden = bw;
  for (const field of document.querySelectorAll('[data-condition="spline"]')) field.hidden = !spline;
}
function scheduleVTracerUpdate() {
  clearTimeout(autoVTracerTimer);
  if (!state.source) return;
  setStatus("VTracerの設定を変更したよ。再変換すると反映されるよ。");
  if (!$("vtracer-auto-update").checked) return;
  autoVTracerTimer = setTimeout(() => {
    if (state.busy) { pendingVTracerRun = true; return; }
    runOne("vtracer");
  }, 350);
}
for (const control of document.querySelectorAll("#vtracer-settings input, #vtracer-settings select")) {
  control.addEventListener("input", refreshVTracerControls);
  control.addEventListener("change", () => { refreshVTracerControls(); scheduleVTracerUpdate(); });
}
$("vtracer-reset").addEventListener("click", () => {
  writeVTracerControls(document, VTRACER_DEFAULTS);
  refreshVTracerControls();
  scheduleVTracerUpdate();
});
$("vtracer-auto-update").addEventListener("change", () => {
  if ($("vtracer-auto-update").checked) scheduleVTracerUpdate();
  else clearTimeout(autoVTracerTimer);
});
refreshVTracerControls();
