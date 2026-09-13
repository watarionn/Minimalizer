(() => {
  const selection = document.querySelector("#strip-selection-mode-select");
  const similarity = document.querySelector("#color-similarity-range");
  const similarityOutput = document.querySelector("#color-similarity-output");
  const modeDescription = document.querySelector("#mode-description");
  const processingCopy = document.querySelector("#processing-copy");

  if (!selection || !similarity || !similarityOutput) return;

  const isCharacteristic = () => selection.value === "characteristic";

  const baseBuildFormData = buildFormData;
  buildFormData = function buildFeaturePaletteFormData(outputFormat) {
    const form = baseBuildFormData(outputFormat);
    if (currentMode() === "color_strip" && isCharacteristic()) {
      form.delete("color_similarity");
    }
    return form;
  };

  const baseColorStripOptionLabel = colorStripOptionLabel;
  colorStripOptionLabel = function featurePaletteOptionLabel(selectionMode, sizeMode, order, orientation) {
    if (selectionMode !== "characteristic") {
      return baseColorStripOptionLabel(selectionMode, sizeMode, order, orientation);
    }
    const sizeLabel = sizeMode === "proportional" ? "使用量比例" : "均等";
    const orderLabel = order === "most_first" ? "多→少" : "少→多";
    const orientationLabel = orientation === "horizontal" ? "横" : "縦";
    return `特徴色 v5 · ${sizeLabel} · ${orderLabel} · ${orientationLabel}`;
  };

  const baseUpdateModeUi = updateModeUi;
  updateModeUi = function updateFeaturePaletteModeUi() {
    baseUpdateModeUi();
    syncCharacteristicUi();
  };

  function syncCharacteristicUi() {
    const colorStrip = currentMode() === "color_strip";
    const characteristic = colorStrip && isCharacteristic();

    similarity.disabled = state.busy || !colorStrip || characteristic;
    similarityOutput.textContent = characteristic
      ? "v5で自動"
      : similarityLabel(similarity.value);

    if (!colorStrip) return;

    if (characteristic) {
      modeDescription.textContent = "特徴色 v5は、背景・色ファミリー・面積・彩度・差し色をまとめて評価し、人が見たときの代表色を3〜5色に絞ります。";
      processingCopy.textContent = "背景と色ファミリーを整理し、特徴色 v5でColor Stripを生成中…";
    } else {
      modeDescription.textContent = "画像から代表色を3〜5色だけ抽出してストリップ化します。使用量順・特徴色優先・特徴色 v5を比較できます。";
      processingCopy.textContent = "代表色と特徴色を評価してColor Stripを生成中…";
    }
  }

  selection.addEventListener("change", syncCharacteristicUi);
  syncCharacteristicUi();
})();
