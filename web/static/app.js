const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

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
  resultMeta: document.querySelector("#result-meta"),
  downloadRow: document.querySelector("#download-row"),
  downloadSvg: document.querySelector("#download-svg"),
  downloadPng: document.querySelector("#download-png"),
  minimalizeButton: document.querySelector("#minimalize-button"),
  level: document.querySelector("#level-select"),
  colors: document.querySelector("#colors-input"),
  maxShapes: document.querySelector("#max-shapes-input"),
  background: document.querySelector("#background-select"),
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

function setBusy(busy, message = "") {
  state.busy = busy;
  elements.processing.hidden = !busy;
  elements.minimalizeButton.disabled = busy || !state.file;
  elements.downloadSvg.disabled = busy;
  elements.downloadPng.disabled = busy;
  elements.fileInput.disabled = busy;
  elements.replaceButton.disabled = busy;
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
  if (file.type && !file.type.startsWith("image/")) {
    setStatus("画像ファイルを選択してください。", true);
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
  setStatus("画像を読み込みました。ミニマル化できます。");
}

function buildFormData(outputFormat) {
  const form = new FormData();
  form.append("file", state.file, state.file.name || "image");
  form.append("level", elements.level.value);
  form.append("output_format", outputFormat);

  if (elements.colors.value) form.append("colors", elements.colors.value);
  if (elements.maxShapes.value) form.append("max_shapes", elements.maxShapes.value);
  if (elements.background.value) form.append("background", elements.background.value);
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

async function requestMinimalize(outputFormat, { preview = false, download = false } = {}) {
  if (!state.file || state.busy) return;

  const label = outputFormat.toUpperCase();
  setBusy(true, download ? `${label}を生成しています…` : "画像をミニマル化しています…");
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
    const filename = outputFormat === "png" ? "minimalized.png" : "minimalized.svg";

    if (preview) {
      if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
      state.resultBlob = blob;
      state.resultFilename = filename;
      state.resultUrl = URL.createObjectURL(blob);
      elements.resultPreview.src = state.resultUrl;
      elements.resultPreview.hidden = false;
      elements.resultEmpty.hidden = true;
      elements.downloadRow.hidden = false;

      const shapes = response.headers.get("x-minimalizer-shape-count");
      const size = response.headers.get("x-minimalizer-analysis-size");
      elements.resultMeta.textContent = [shapes ? `${shapes} shapes` : "", size || ""]
        .filter(Boolean)
        .join(" · ");
    }

    if (download) downloadBlob(blob, filename);
    setStatus(download ? `${label}を保存しました。` : "ミニマル化が完了しました。");
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
  if (state.resultBlob) clearResult("設定が変更されました。もう一度ミニマル化してください。");
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

for (const control of [elements.level, elements.colors, elements.maxShapes, elements.background]) {
  control.addEventListener("change", invalidateAfterSettingChange);
}

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
