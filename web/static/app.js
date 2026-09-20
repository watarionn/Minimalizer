const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;
const SUPPORTED_MIME_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

const elements = {
  dropZone: document.querySelector("#drop-zone"),
  dropEmpty: document.querySelector("#drop-empty"),
  fileInput: document.querySelector("#file-input"),
  sourcePreview: document.querySelector("#source-preview"),
  fileMeta: document.querySelector("#file-meta"),
  fileName: document.querySelector("#file-name"),
  fileSize: document.querySelector("#file-size"),
  replaceButton: document.querySelector("#replace-button"),
  resultEmpty: document.querySelector("#result-empty"),
  resultPreview: document.querySelector("#result-preview"),
  processing: document.querySelector("#processing"),
  processingTitle: document.querySelector("#processing-title"),
  processingCopy: document.querySelector("#processing-copy"),
  resultMeta: document.querySelector("#result-meta"),
  resultTitle: document.querySelector("#result-title"),
  downloadRow: document.querySelector("#download-row"),
  downloadSvg: document.querySelector("#download-svg"),
  downloadPng: document.querySelector("#download-png"),
  minimalizeButton: document.querySelector("#minimalize-button"),
  modeInputs: Array.from(document.querySelectorAll('input[name="mode"]')),
  modeDescription: document.querySelector("#mode-description"),
  controlCard: document.querySelector(".control-card"),
  colorStripControls: document.querySelector("#color-strip-controls"),
  colorStripOptions: document.querySelector("#color-strip-options"),
  stripColors: document.querySelector("#strip-colors-select"),
  colorSimilarity: document.querySelector("#color-similarity-range"),
  colorSimilarityOutput: document.querySelector("#color-similarity-output"),
  stripSelectionMode: document.querySelector("#strip-selection-mode-select"),
  stripSizeMode: document.querySelector("#strip-size-mode-select"),
  stripOrder: document.querySelector("#strip-order-select"),
  stripOrientation: document.querySelector("#strip-orientation-select"),
  status: document.querySelector("#status-message"),
  engineBadge: document.querySelector("#engine-badge"),
};

const state = {
  file: null,
  sourceUrl: null,
  resultUrl: null,
  resultBlob: null,
  resultFilename: "minimalized.png",
  busy: false,
};

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setStatus(message = "", isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("is-error", isError);
}

function currentMode() {
  return elements.modeInputs.find((input) => input.checked)?.value || "standard";
}

function isColorStripMode() {
  return currentMode() === "color_strip";
}

function similarityLabel(value) {
  const numeric = Number(value);
  if (numeric <= 10) return "細かい";
  if (numeric <= 15) return "やや細かい";
  if (numeric <= 21) return "標準";
  if (numeric <= 26) return "やや大まか";
  return "大まか";
}

function isCharacteristicSelection() {
  return elements.stripSelectionMode.value === "characteristic";
}

function updateSimilarityLabel() {
  elements.colorSimilarityOutput.textContent = isCharacteristicSelection()
    ? "v5で自動"
    : similarityLabel(elements.colorSimilarity.value);
}

function updateModeUi() {
  const colorStrip = isColorStripMode();
  elements.controlCard.classList.toggle("is-color-strip", colorStrip);

  if (colorStrip) {
    elements.modeDescription.textContent = "画像から代表色を3〜5色だけ抽出してストリップ化します。";
    elements.resultTitle.textContent = "Color Strip結果";
    elements.minimalizeButton.textContent = "Color Stripを生成";
    elements.processingTitle.textContent = "色を抽出しています";
    elements.processingCopy.textContent = isCharacteristicSelection()
      ? "背景と色ファミリーを整理し、特徴色 v5でColor Stripを生成中…"
      : "代表色と特徴色を評価してColor Stripを生成中…";
  } else {
    elements.modeDescription.textContent = "現在の高精度Minimalizer 2.0でミニマル化します。方式を選ぶ必要はありません。";
    elements.resultTitle.textContent = "ミニマル化結果";
    elements.minimalizeButton.textContent = "ミニマル化";
    elements.processingTitle.textContent = "ミニマル化しています";
    elements.processingCopy.textContent = "人物と背景の構造を解析し、必要なかたちだけに整理中…";
    elements.colorStripOptions.open = false;
  }

  elements.colorStripControls.hidden = !colorStrip;
  elements.colorStripOptions.hidden = !colorStrip;
  elements.downloadSvg.hidden = !colorStrip;

  elements.stripColors.disabled = state.busy || !colorStrip;
  elements.colorSimilarity.disabled = state.busy || !colorStrip || isCharacteristicSelection();
  elements.stripSelectionMode.disabled = state.busy || !colorStrip;
  elements.stripSizeMode.disabled = state.busy || !colorStrip;
  elements.stripOrder.disabled = state.busy || !colorStrip;
  elements.stripOrientation.disabled = state.busy || !colorStrip;
  updateSimilarityLabel();
}

function setBusy(busy, message = "") {
  state.busy = busy;
  elements.processing.hidden = !busy;
  elements.minimalizeButton.disabled = busy || !state.file;
  elements.downloadSvg.disabled = busy;
  elements.downloadPng.disabled = busy;
  elements.fileInput.disabled = busy;
  elements.replaceButton.disabled = busy;
  for (const input of elements.modeInputs) input.disabled = busy;
  updateModeUi();
  if (message) setStatus(message);
}

function clearResult(message = "") {
  if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
  state.resultUrl = null;
  state.resultBlob = null;
  state.resultFilename = isColorStripMode() ? "color-strip.svg" : "minimalized.png";
  elements.resultPreview.removeAttribute("src");
  elements.resultPreview.hidden = true;
  elements.resultEmpty.hidden = false;
  elements.downloadRow.hidden = true;
  elements.resultMeta.textContent = "";
  if (message) setStatus(message);
}

function setFile(file) {
  if (!file) return;

  if (file.size === 0) {
    setStatus("空のファイルは使用できません。", true);
    return;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    setStatus("画像サイズは20MB以下にしてください。", true);
    return;
  }
  if (!SUPPORTED_MIME_TYPES.has(file.type)) {
    setStatus("PNG・JPEG・WebPの画像を選択してください。", true);
    return;
  }

  if (state.sourceUrl) URL.revokeObjectURL(state.sourceUrl);
  state.file = file;
  state.sourceUrl = URL.createObjectURL(file);

  elements.sourcePreview.src = state.sourceUrl;
  elements.sourcePreview.hidden = false;
  elements.dropEmpty.hidden = true;
  elements.fileMeta.hidden = false;
  elements.replaceButton.hidden = false;
  elements.fileName.textContent = file.name || "image";
  elements.fileSize.textContent = formatBytes(file.size);
  elements.minimalizeButton.disabled = false;
  clearResult();
  setStatus(isColorStripMode()
    ? "画像を読み込みました。Color Stripを生成できます。"
    : "画像を読み込みました。ミニマル化できます。");
}

function buildV2FormData() {
  const form = new FormData();
  form.append("file", state.file, state.file.name || "image");
  form.append("preset", "minimal");
  form.append("include_facets", "true");
  return form;
}

function buildColorStripFormData(outputFormat) {
  const form = new FormData();
  form.append("file", state.file, state.file.name || "image");
  form.append("mode", "color_strip");
  form.append("level", "4");
  form.append("output_format", outputFormat);
  form.append("colors", elements.stripColors.value);
  if (!isCharacteristicSelection()) {
    form.append("color_similarity", elements.colorSimilarity.value);
  }
  form.append("color_selection_mode", elements.stripSelectionMode.value);
  form.append("color_size_mode", elements.stripSizeMode.value);
  form.append("color_order", elements.stripOrder.value);
  form.append("color_orientation", elements.stripOrientation.value);
  return form;
}

async function responseError(response) {
  try {
    const payload = await response.json();
    if (payload && typeof payload.detail === "string") return payload.detail;
  } catch (_) {
    // Fall back to the status code below.
  }
  return `処理に失敗しました (${response.status})`;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function resultFilename(outputFormat) {
  const stem = isColorStripMode() ? "color-strip" : "minimalized";
  return `${stem}.${outputFormat}`;
}

function colorStripOptionLabel(selectionMode, sizeMode, order, orientation) {
  const selectionLabel = selectionMode === "characteristic"
    ? "特徴色 v5"
    : selectionMode === "featured" ? "特徴色優先" : "使用量順";
  const sizeLabel = sizeMode === "proportional" ? "使用量比例" : "均等";
  const orderLabel = order === "most_first" ? "多→少" : "少→多";
  const orientationLabel = orientation === "horizontal" ? "横" : "縦";
  return `${selectionLabel} · ${sizeLabel} · ${orderLabel} · ${orientationLabel}`;
}

async function requestMinimalize(outputFormat, { preview = false, download = false } = {}) {
  if (!state.file || state.busy) return;

  const colorStrip = isColorStripMode();
  if (!colorStrip) outputFormat = "png";

  const label = outputFormat.toUpperCase();
  const action = colorStrip ? "Color Stripを生成しています…" : "画像をミニマル化しています…";
  setBusy(true, download ? `${label}を生成しています…` : action);

  if (preview) {
    elements.resultEmpty.hidden = true;
    elements.resultPreview.hidden = true;
  }

  try {
    const response = await fetch(colorStrip ? "/api/minimalize" : "/api/v2/minimalize", {
      method: "POST",
      body: colorStrip ? buildColorStripFormData(outputFormat) : buildV2FormData(),
    });
    if (!response.ok) throw new Error(await responseError(response));

    const blob = await response.blob();
    const filename = resultFilename(outputFormat);

    if (preview) {
      if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
      state.resultBlob = blob;
      state.resultFilename = filename;
      state.resultUrl = URL.createObjectURL(blob);
      elements.resultPreview.src = state.resultUrl;
      elements.resultPreview.hidden = false;
      elements.resultEmpty.hidden = true;
      elements.downloadRow.hidden = false;

      const responseMode = response.headers.get("x-minimalizer-mode");
      const v2Contract = response.headers.get("x-minimalizer-v2-contract-version");
      const shapes = response.headers.get("x-minimalizer-shape-count");
      const colorCount = response.headers.get("x-minimalizer-color-count");
      const size = response.headers.get("x-minimalizer-analysis-size");
      const colorSelectionMode = response.headers.get("x-minimalizer-color-selection-mode");
      const colorSizeMode = response.headers.get("x-minimalizer-color-size-mode");
      const colorOrder = response.headers.get("x-minimalizer-color-order");
      const colorOrientation = response.headers.get("x-minimalizer-color-orientation");
      const modeLabel = v2Contract
        ? "Minimalizer 2.0"
        : responseMode === "color_strip" ? "Color Strip" : "Minimalizer";

      const colorOptionLabel = responseMode === "color_strip"
        ? colorStripOptionLabel(colorSelectionMode, colorSizeMode, colorOrder, colorOrientation)
        : "";

      elements.resultMeta.textContent = [
        modeLabel,
        responseMode === "color_strip" && colorCount ? `${colorCount} colors` : shapes ? `${shapes} shapes` : "",
        colorOptionLabel,
        size || "",
      ].filter(Boolean).join(" · ");
    }

    if (download) downloadBlob(blob, filename);
    if (download) {
      setStatus(`${label}を保存しました。`);
    } else {
      setStatus(colorStrip ? "Color Stripが完成しました。" : "ミニマル化が完了しました。");
    }
  } catch (error) {
    if (preview && !state.resultBlob) {
      elements.resultEmpty.hidden = false;
      elements.resultPreview.hidden = true;
    }
    setStatus(error instanceof Error ? error.message : "処理に失敗しました。", true);
  } finally {
    setBusy(false);
  }
}

function invalidateAfterSettingChange() {
  if (state.resultBlob) clearResult("設定が変更されました。もう一度生成してください。");
}

elements.dropZone.addEventListener("click", () => {
  if (!state.busy) elements.fileInput.click();
});

elements.dropZone.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && !state.busy) {
    event.preventDefault();
    elements.fileInput.click();
  }
});

elements.fileInput.addEventListener("change", () => setFile(elements.fileInput.files?.[0]));
elements.replaceButton.addEventListener("click", () => elements.fileInput.click());

for (const eventName of ["dragenter", "dragover"]) {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (!state.busy) elements.dropZone.classList.add("is-dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.remove("is-dragging");
  });
}

elements.dropZone.addEventListener("drop", (event) => {
  if (!state.busy) setFile(event.dataTransfer?.files?.[0]);
});

function downloadOrRequest(outputFormat) {
  if (!isColorStripMode() && outputFormat === "svg") return;

  if (state.resultBlob && state.resultFilename.endsWith(`.${outputFormat}`)) {
    downloadBlob(state.resultBlob, state.resultFilename);
    setStatus(`${outputFormat.toUpperCase()}を保存しました。`);
    return;
  }
  requestMinimalize(outputFormat, { download: true });
}

elements.minimalizeButton.addEventListener("click", () => {
  requestMinimalize(isColorStripMode() ? "svg" : "png", { preview: true });
});

elements.downloadSvg.addEventListener("click", () => downloadOrRequest("svg"));
elements.downloadPng.addEventListener("click", () => downloadOrRequest("png"));

for (const control of [
  elements.stripColors,
  elements.stripSelectionMode,
  elements.stripSizeMode,
  elements.stripOrder,
  elements.stripOrientation,
]) {
  control.addEventListener("change", invalidateAfterSettingChange);
}

elements.stripSelectionMode.addEventListener("change", updateModeUi);

elements.colorSimilarity.addEventListener("input", () => {
  updateSimilarityLabel();
  invalidateAfterSettingChange();
});

for (const input of elements.modeInputs) {
  input.addEventListener("change", () => {
    invalidateAfterSettingChange();
    updateModeUi();
    if (!state.resultBlob) {
      setStatus(isColorStripMode()
        ? "Color Stripを選択しました。代表色や特徴色を抽出して並べます。"
        : "ミニマル化を選択しました。高精度エンジンを自動で使用します。");
    }
  });
}

updateModeUi();

window.addEventListener("beforeunload", () => {
  if (state.sourceUrl) URL.revokeObjectURL(state.sourceUrl);
  if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
});

fetch("/health")
  .then((response) => response.ok ? response.json() : null)
  .then((payload) => {
    if (payload?.engine_version) elements.engineBadge.textContent = `Engine v${payload.engine_version}`;
  })
  .catch(() => {});
