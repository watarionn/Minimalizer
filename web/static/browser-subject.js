import * as ort from "./vendor/onnxruntime/ort.wasm.min.mjs";

const VERSION = "browser-subject-u2netp-v2";
const MODEL_SIZE = 320;
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

ort.env.wasm.wasmPaths = new URL("./vendor/onnxruntime/", import.meta.url).href;
ort.env.wasm.numThreads = 1;

let sessionPromise = null;

function canvasElement(width, height) {
  if (typeof document !== "undefined" && typeof document.createElement === "function") {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    return canvas;
  }
  if (typeof OffscreenCanvas !== "undefined") return new OffscreenCanvas(width, height);
  throw new Error("Canvas is unavailable for subject guidance.");
}

function context2d(canvas) {
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) throw new Error("2D canvas is unavailable for subject guidance.");
  return context;
}

function nativeImageRgb(image) {
  const canvas = canvasElement(image.width, image.height);
  const context = context2d(canvas);
  context.fillStyle = "rgb(255,255,255)";
  context.fillRect(0, 0, image.width, image.height);
  context.drawImage(image, 0, 0, image.width, image.height);
  const rgba = context.getImageData(0, 0, image.width, image.height).data;
  const rgb = new Uint8ClampedArray(image.width * image.height * 3);
  for (let index = 0; index < image.width * image.height; index += 1) {
    const ro = index * 4;
    const oo = index * 3;
    rgb[oo] = rgba[ro];
    rgb[oo + 1] = rgba[ro + 1];
    rgb[oo + 2] = rgba[ro + 2];
  }
  return rgb;
}

function canvasResizeRgb(image) {
  const canvas = canvasElement(MODEL_SIZE, MODEL_SIZE);
  const context = context2d(canvas);
  context.fillStyle = "rgb(255,255,255)";
  context.fillRect(0, 0, MODEL_SIZE, MODEL_SIZE);
  context.imageSmoothingEnabled = true;
  if ("imageSmoothingQuality" in context) context.imageSmoothingQuality = "high";
  context.drawImage(image, 0, 0, image.width, image.height, 0, 0, MODEL_SIZE, MODEL_SIZE);
  const rgba = context.getImageData(0, 0, MODEL_SIZE, MODEL_SIZE).data;
  const rgb = new Uint8ClampedArray(MODEL_SIZE * MODEL_SIZE * 3);
  for (let index = 0; index < MODEL_SIZE * MODEL_SIZE; index += 1) {
    const ro = index * 4;
    const oo = index * 3;
    rgb[oo] = rgba[ro];
    rgb[oo + 1] = rgba[ro + 1];
    rgb[oo + 2] = rgba[ro + 2];
  }
  return rgb;
}

function imageToTensor(image, nativePixelLimit = 12000000) {
  const sourcePixels = image.width * image.height;
  let rgb;
  let resizeMethod;
  if (
    sourcePixels <= nativePixelLimit
    && globalThis.MinimalizerPillowLanczos
    && typeof globalThis.MinimalizerPillowLanczos.resizeRgb === "function"
  ) {
    const nativeRgb = nativeImageRgb(image);
    rgb = globalThis.MinimalizerPillowLanczos.resizeRgb(
      nativeRgb,
      image.width,
      image.height,
      MODEL_SIZE,
      MODEL_SIZE,
    );
    resizeMethod = "pillow-lanczos";
  } else {
    rgb = canvasResizeRgb(image);
    resizeMethod = "canvas-large-source";
  }

  let maximum = 1;
  for (const value of rgb) maximum = Math.max(maximum, value);
  const plane = MODEL_SIZE * MODEL_SIZE;
  const input = new Float32Array(plane * 3);
  for (let index = 0; index < plane; index += 1) {
    const offset = index * 3;
    for (let channel = 0; channel < 3; channel += 1) {
      input[channel * plane + index] = (
        rgb[offset + channel] / maximum - MEAN[channel]
      ) / STD[channel];
    }
  }
  return { input, resizeMethod };
}

function normalizedMask(output) {
  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  for (const value of output) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }
  const span = Math.max(maximum - minimum, 1e-12);
  const mask = new Uint8ClampedArray(output.length);
  for (let index = 0; index < output.length; index += 1) {
    mask[index] = Math.floor(255 * (output[index] - minimum) / span);
  }
  return { mask, minimum, maximum };
}

function maskCanvas(mask, width, height) {
  const canvas = canvasElement(width, height);
  const context = context2d(canvas);
  const image = context.createImageData(width, height);
  for (let index = 0; index < mask.length; index += 1) {
    const value = mask[index];
    const offset = index * 4;
    image.data[offset] = value;
    image.data[offset + 1] = value;
    image.data[offset + 2] = value;
    image.data[offset + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  return canvas;
}

function resizeMaskToSource(mask, sourceWidth, sourceHeight) {
  if (sourceWidth === MODEL_SIZE && sourceHeight === MODEL_SIZE) return mask.slice();
  if (
    globalThis.MinimalizerPillowLanczos
    && typeof globalThis.MinimalizerPillowLanczos.resizeGray === "function"
  ) {
    return globalThis.MinimalizerPillowLanczos.resizeGray(
      mask,
      MODEL_SIZE,
      MODEL_SIZE,
      sourceWidth,
      sourceHeight,
    );
  }
  const source = maskCanvas(mask, MODEL_SIZE, MODEL_SIZE);
  const canvas = canvasElement(sourceWidth, sourceHeight);
  const context = context2d(canvas);
  context.imageSmoothingEnabled = true;
  if ("imageSmoothingQuality" in context) context.imageSmoothingQuality = "high";
  context.drawImage(source, 0, 0, MODEL_SIZE, MODEL_SIZE, 0, 0, sourceWidth, sourceHeight);
  const rgba = context.getImageData(0, 0, sourceWidth, sourceHeight).data;
  const output = new Uint8ClampedArray(sourceWidth * sourceHeight);
  for (let index = 0; index < output.length; index += 1) output[index] = rgba[index * 4];
  return output;
}

function resizeMaskArea(mask, sourceWidth, sourceHeight, targetWidth, targetHeight) {
  if (sourceWidth === targetWidth && sourceHeight === targetHeight) {
    const result = new Float32Array(mask.length);
    for (let i = 0; i < mask.length; i += 1) result[i] = mask[i] / 255;
    return result;
  }
  if (
    globalThis.MinimalizerOpenCvAreaResize
    && typeof globalThis.MinimalizerOpenCvAreaResize.resizeRgba === "function"
  ) {
    const rgba = new Uint8ClampedArray(sourceWidth * sourceHeight * 4);
    for (let index = 0; index < mask.length; index += 1) {
      const value = mask[index];
      const offset = index * 4;
      rgba[offset] = value;
      rgba[offset + 1] = value;
      rgba[offset + 2] = value;
      rgba[offset + 3] = 255;
    }
    const resized = globalThis.MinimalizerOpenCvAreaResize.resizeRgba(
      rgba, sourceWidth, sourceHeight, targetWidth, targetHeight,
    );
    const result = new Float32Array(targetWidth * targetHeight);
    for (let index = 0; index < result.length; index += 1) result[index] = resized[index * 4] / 255;
    return result;
  }

  const source = maskCanvas(mask, sourceWidth, sourceHeight);
  const canvas = canvasElement(targetWidth, targetHeight);
  const context = context2d(canvas);
  context.drawImage(source, 0, 0, sourceWidth, sourceHeight, 0, 0, targetWidth, targetHeight);
  const data = context.getImageData(0, 0, targetWidth, targetHeight).data;
  const result = new Float32Array(targetWidth * targetHeight);
  for (let index = 0; index < result.length; index += 1) result[index] = data[index * 4] / 255;
  return result;
}

function subjectConfidence(probability) {
  const confidence = new Float32Array(probability.length);
  for (let index = 0; index < probability.length; index += 1) {
    const linear = Math.min(1, Math.max(0, 2 * Math.abs(probability[index] - 0.5)));
    confidence[index] = linear * linear;
  }
  return confidence;
}

async function getSession(modelUrl) {
  if (!sessionPromise) {
    sessionPromise = ort.InferenceSession.create(
      modelUrl || new URL("./models/u2netp.onnx", import.meta.url).href,
      { executionProviders: ["wasm"], graphOptimizationLevel: "all" },
    ).catch((error) => {
      sessionPromise = null;
      throw error;
    });
  }
  return await sessionPromise;
}

async function predict(image, options = {}) {
  const started = performance.now();
  const sourceWidth = image.width;
  const sourceHeight = image.height;
  const targetWidth = options.targetWidth || sourceWidth;
  const targetHeight = options.targetHeight || sourceHeight;
  const preparedInput = imageToTensor(
    image,
    options.nativeMaskPixelLimit || 12000000,
  );
  const input = preparedInput.input;

  const sessionStarted = performance.now();
  const session = await getSession(options.modelUrl);
  const sessionMs = performance.now() - sessionStarted;
  const tensor = new ort.Tensor("float32", input, [1, 3, MODEL_SIZE, MODEL_SIZE]);
  const inferenceStarted = performance.now();
  const outputs = await session.run({ [session.inputNames[0]]: tensor });
  const inferenceMs = performance.now() - inferenceStarted;
  const normalized = normalizedMask(outputs[session.outputNames[0]].data);

  let probability;
  let resizeMethod;
  const sourcePixels = sourceWidth * sourceHeight;
  const nativeMaskPixelLimit = options.nativeMaskPixelLimit || 12000000;
  if (sourcePixels <= nativeMaskPixelLimit) {
    const sourceMask = resizeMaskToSource(normalized.mask, sourceWidth, sourceHeight);
    probability = resizeMaskArea(sourceMask, sourceWidth, sourceHeight, targetWidth, targetHeight);
    resizeMethod = sourceWidth === targetWidth && sourceHeight === targetHeight
      ? "lanczos-source"
      : "lanczos-source+opencv-inter-area";
  } else {
    probability = resizeMaskArea(normalized.mask, MODEL_SIZE, MODEL_SIZE, targetWidth, targetHeight);
    resizeMethod = "large-source-direct-area";
  }

  return {
    probability,
    confidence: subjectConfidence(probability),
    provider: "browser-u2netp",
    model: "u2netp",
    sessionMs,
    inferenceMs,
    processingMs: performance.now() - started,
    resizeMethod: preparedInput.resizeMethod + "+" + resizeMethod,
    inputResizeMethod: preparedInput.resizeMethod,
    outputResizeMethod: resizeMethod,
    outputMin: normalized.minimum,
    outputMax: normalized.maximum,
  };
}

export const MinimalizerBrowserSubject = Object.freeze({
  VERSION,
  predict,
  _core: Object.freeze({
    nativeImageRgb,
    canvasResizeRgb,
    imageToTensor,
    normalizedMask,
    resizeMaskToSource,
    resizeMaskArea,
    subjectConfidence,
  }),
});

globalThis.MinimalizerBrowserSubject = MinimalizerBrowserSubject;
