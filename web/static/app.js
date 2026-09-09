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
  downloadRow: document.querySelector("#download-row"),
  downloadSvg: document.querySelector("#download-svg"),
  downloadPng: document.querySelector("#download-png"),
  minimalizeButton: document.querySelector("#minimalize-button"),
  modeInputs: Array.from(document.querySelectorAll('input[name="mode"]')),
  modeDescription: document.querySelector("#mode-description"),
  advancedControls: document.querySelector("#advanced-controls"),
  controlCard: document.querySelector(".control-card"),
  levelControl: document.querySelector("#level-control"),
  level: document.querySelector("#level-select"),
  colors: document.querySelector("#colors-input"),
  maxShapes: document.querySelector("#max-shapes-input"),
  background: document.querySelector("#background-select"),
  colorStripControls: document.querySelector("#color-strip-controls"),
  stripColors: document.querySelector("#strip-colors-select"),
  colorSimilarity: document.querySelector("#color-similarity-range"),
  colorSimilarityOutput: document.querySelector("#color-similarity-output"),
  status: document.querySelector("#status-message"),
  engineBadge: document.querySelector("#engine-badge"),
};

const state = {
  file: null,
  sourceUrl: null,
  resultUrl: null,
  resultBlob: null,
  resultFilename: "minimalized.svg",
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

function similarityLabel(value) {
  const numeric = Number(value);
  if (numeric <= 10) return "細かい";
  if (numeric <= 15) return "やや細かい";
  if (numeric <= 21) return "標準";
  if (numeric <= 26) return "やや大まか";
  return "大まか";
}

function updateSimilarityLabel() {
  elements.colorSimilarityOutput.textContent = similarityLabel(elements.colorSimilarity.value);
}

function updateModeUi() {
  const mode = currentMode();
  const rinka = mode === "rinka_reference";
  const colorStrip = mode === "color_strip";
  elements.controlCard.classList.toggle("is-rinka", rinka);
  elements.controlCard.classList.toggle("is-color-strip", colorStrip);

  if (rinka) {
    elements.modeDescription.textContent = "完成済みの凛夏手本版 Phase 6。検証済みのミニマル度4・専用プロファイルを固定で使用します。";
    elements.minimalizeButton.textContent = "凛夏手本版でミニマル化";
  } else if (colorStrip) {
    elements.modeDescription.textContent = "画像から代表色を3〜5色だけ抽出し、使用量の少ない色から等しい太さのバーとして縦に並べます。";
    elements.minimalizeButton.textContent = "Color Stripを生成";
  } else {
    elements.modeDescription.textContent = "通常のMinimalizer。ミニマル度や詳細設定を調整できます。";
    elements.minimalizeButton.textContent = "ミニマル化";
  }

  if (rinka) {
    elements.level.value = "4";
    elements.colors.value = "";
    elements.maxShapes.value = "";
    elements.background.value = "";
    elements.advancedControls.open = false;
  }
  if (colorStrip) elements.advancedControls.open = false;

  elements.levelControl.hidden = colorStrip;
  elements.colorStripControls.hidden = !colorStrip;
  elements.advancedControls.hidden = colorStrip;

  elements.level.disabled = state.busy || rinka || colorStrip;
  elements.colors.disabled = state.busy || rinka || colorStrip;
  elements.maxShapes.disabled = state.busy || rinka || colorStrip;
  elements.background.disabled = state.busy || rinka || colorStrip;
  elements.stripColors.disabled = state.busy || !colorStrip;
  elements.colorSimilarity.disabled = state.busy || !colorStrip;
  elements.advancedControls.setAttribute("aria-disabled", rinka ? "true" : "false");
  const advancedSummary = elements.advancedControls.querySelector("summary");
  if (advancedSummary) advancedSummary.setAttribute("aria-disabled", rinka ? "true" : "false");

  if (colorStrip) {
    elements.processingTitle.textContent = "色を抽出しています";
    elements.processingCopy.textContent = "代表色をまとめてColor Stripを生成中…";
  } else {
    elements.processingTitle.textContent = "ミニマル化しています";
    elements.processingCopy.textContent = rinka ? "凛夏手本版プロファイルで整理中…" : "画像の構造を整理中…";
  }
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
  state.resultFilename = "minimalized.svg";
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
  setStatus(currentMode() === "color_strip" ? "画像を読み込みました。Color Stripを生成できます。" : "画像を読み込みました。ミニマル化できます。");
}

function buildFormData(outputFormat) {
  const form = new FormData();
  form.append("file", state.file, state.file.name || "image");
  const mode = currentMode();
  form.append("mode", mode);
  form.append("level", mode === "standard" ? elements.level.value : "4");
  form.append("output_format", outputFormat);

  if (mode === "standard") {
    if (elements.colors.value) form.append("colors", elements.colors.value);
    if (elements.maxShapes.value) form.append("max_shapes", elements.maxShapes.value);
    if (elements.background.value) form.append("background", elements.background.value);
  } else if (mode === "color_strip") {
    form.append("colors", elements.stripColors.value);
    form.append("color_similarity", elements.colorSimilarity.value);
  }
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
  const stem = currentMode() === "color_strip" ? "color-strip" : "minimalized";
  return `${stem}.${outputFormat}`;
}

async function requestMinimalize(outputFormat, { preview = false, download = false } = {}) {
  if (!state.file || state.busy) return;

  const label = outputFormat.toUpperCase();
  const colorStrip = currentMode() === "color_strip";
  const action = colorStrip ? "Color Stripを生成しています…" : "画像をミニマル化しています…";
  setBusy(true, download ? `${label}を生成しています…` : action);
  if (preview) {
    elements.resultEmpty.hidden = true;
    elements.resultPreview.hidden = true;
  }

  try {
    const response = await fetch("/api/minimalize", {
      method: "POST",
      body: buildFormData(outputFormat),
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
      const shapes = response.headers.get("x-minimalizer-shape-count");
      const colorCount = response.headers.get("x-minimalizer-color-count");
      const size = response.headers.get("x-minimalizer-analysis-size");
      const modeLabel = responseMode === "rinka_reference"
        ? "凛夏手本版"
        : responseMode === "color_strip" ? "Color Strip" : "";
      elements.resultMeta.textContent = [
        modeLabel,
        responseMode === "color_strip" && colorCount ? `${colorCount} colors` : shapes ? `${shapes} shapes` : "",
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

elements.minimalizeButton.addEventListener("click", () => {
  requestMinimalize("svg", { preview: true });
});

elements.downloadSvg.addEventListener("click", () => {
  if (state.resultBlob) downloadBlob(state.resultBlob, state.resultFilename);
});

elements.downloadPng.addEventListener("click", () => {
  requestMinimalize("png", { download: true });
});

for (const control of [elements.level, elements.colors, elements.maxShapes, elements.background, elements.stripColors]) {
  control.addEventListener("change", invalidateAfterSettingChange);
}

elements.colorSimilarity.addEventListener("input", () => {
  updateSimilarityLabel();
  invalidateAfterSettingChange();
});

for (const input of elements.modeInputs) {
  input.addEventListener("change", () => {
    invalidateAfterSettingChange();
    updateModeUi();
    if (!state.resultBlob) {
      if (currentMode() === "rinka_reference") {
        setStatus("凛夏手本版を選択しました。完成プロファイルでミニマル化します。");
      } else if (currentMode() === "color_strip") {
        setStatus("Color Stripを選択しました。代表色だけを抽出して並べます。");
      } else {
        setStatus("通常モードを選択しました。");
      }
    }
  });
}

elements.advancedControls.querySelector("summary")?.addEventListener("click", (event) => {
  if (currentMode() === "rinka_reference") event.preventDefault();
});

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
