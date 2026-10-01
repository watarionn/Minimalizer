(function (root) {
  "use strict";

  // Compatibility subset of Pillow's 8bpc LANCZOS resampler.
  // Source contract: Pillow src/libImaging/Resample.c, support radius 3.
  const VERSION = "pillow-lanczos-8bpc-v1";
  const SUPPORT = 3.0;
  const PRECISION_BITS = 22;
  const PRECISION = 1 << PRECISION_BITS;

  function sinc(value) {
    if (value === 0) return 1;
    const x = value * Math.PI;
    return Math.sin(x) / x;
  }

  function lanczos(value) {
    if (-3 <= value && value < 3) {
      return sinc(value) * sinc(value / 3);
    }
    return 0;
  }

  function fixedCoefficient(value) {
    return value < 0
      ? Math.trunc(-0.5 + value * PRECISION)
      : Math.trunc(0.5 + value * PRECISION);
  }

  function precomputeCoefficients(inputSize, outputSize) {
    const scale = inputSize / outputSize;
    const filterScale = Math.max(scale, 1);
    const support = SUPPORT * filterScale;
    const kernelSize = Math.ceil(support) * 2 + 1;
    const inverseFilterScale = 1 / filterScale;
    const bounds = new Int32Array(outputSize * 2);
    const coefficients = new Int32Array(outputSize * kernelSize);

    for (let output = 0; output < outputSize; output += 1) {
      const center = (output + 0.5) * scale;
      let xmin = Math.trunc(center - support + 0.5);
      if (xmin < 0) xmin = 0;
      let xmaxAbsolute = Math.trunc(center + support + 0.5);
      if (xmaxAbsolute > inputSize) xmaxAbsolute = inputSize;
      const count = xmaxAbsolute - xmin;
      const weights = new Float64Array(count);
      let total = 0;
      for (let index = 0; index < count; index += 1) {
        const weight = lanczos(
          (index + xmin - center + 0.5) * inverseFilterScale
        );
        weights[index] = weight;
        total += weight;
      }
      if (total !== 0) {
        for (let index = 0; index < count; index += 1) {
          weights[index] /= total;
        }
      }
      const offset = output * kernelSize;
      for (let index = 0; index < count; index += 1) {
        coefficients[offset + index] = fixedCoefficient(weights[index]);
      }
      bounds[output * 2] = xmin;
      bounds[output * 2 + 1] = count;
    }
    return { bounds, coefficients, kernelSize };
  }

  function clipFixed(sum) {
    // Equivalent to Pillow's arithmetic right shift followed by 8-bit clip.
    const value = Math.floor(sum / PRECISION);
    if (value <= 0) return 0;
    if (value >= 255) return 255;
    return value;
  }

  function horizontal(source, inputWidth, inputHeight, outputWidth, channels) {
    const table = precomputeCoefficients(inputWidth, outputWidth);
    const output = new Uint8ClampedArray(outputWidth * inputHeight * channels);
    const rounding = 1 << (PRECISION_BITS - 1);

    for (let y = 0; y < inputHeight; y += 1) {
      for (let x = 0; x < outputWidth; x += 1) {
        const xmin = table.bounds[x * 2];
        const count = table.bounds[x * 2 + 1];
        const coefficientOffset = x * table.kernelSize;
        for (let channel = 0; channel < channels; channel += 1) {
          let sum = rounding;
          for (let index = 0; index < count; index += 1) {
            const sourceOffset = (
              (y * inputWidth + xmin + index) * channels + channel
            );
            sum += source[sourceOffset] * table.coefficients[coefficientOffset + index];
          }
          output[(y * outputWidth + x) * channels + channel] = clipFixed(sum);
        }
      }
    }
    return output;
  }

  function vertical(source, width, inputHeight, outputHeight, channels) {
    const table = precomputeCoefficients(inputHeight, outputHeight);
    const output = new Uint8ClampedArray(width * outputHeight * channels);
    const rounding = 1 << (PRECISION_BITS - 1);

    for (let y = 0; y < outputHeight; y += 1) {
      const ymin = table.bounds[y * 2];
      const count = table.bounds[y * 2 + 1];
      const coefficientOffset = y * table.kernelSize;
      for (let x = 0; x < width; x += 1) {
        for (let channel = 0; channel < channels; channel += 1) {
          let sum = rounding;
          for (let index = 0; index < count; index += 1) {
            const sourceOffset = (
              ((ymin + index) * width + x) * channels + channel
            );
            sum += source[sourceOffset] * table.coefficients[coefficientOffset + index];
          }
          output[(y * width + x) * channels + channel] = clipFixed(sum);
        }
      }
    }
    return output;
  }

  function resize(source, inputWidth, inputHeight, outputWidth, outputHeight, channels) {
    if (
      inputWidth <= 0 || inputHeight <= 0
      || outputWidth <= 0 || outputHeight <= 0
      || channels <= 0
    ) {
      throw new Error("Pillow Lanczos dimensions must be positive.");
    }
    if (source.length !== inputWidth * inputHeight * channels) {
      throw new Error("Pillow Lanczos source length mismatch.");
    }
    if (inputWidth === outputWidth && inputHeight === outputHeight) {
      return new Uint8ClampedArray(source);
    }
    let current = source;
    let width = inputWidth;
    let height = inputHeight;
    if (width !== outputWidth) {
      current = horizontal(current, width, height, outputWidth, channels);
      width = outputWidth;
    }
    if (height !== outputHeight) {
      current = vertical(current, width, height, outputHeight, channels);
      height = outputHeight;
    }
    return current;
  }

  function resizeRgb(source, inputWidth, inputHeight, outputWidth, outputHeight) {
    return resize(source, inputWidth, inputHeight, outputWidth, outputHeight, 3);
  }

  function resizeGray(source, inputWidth, inputHeight, outputWidth, outputHeight) {
    return resize(source, inputWidth, inputHeight, outputWidth, outputHeight, 1);
  }

  const api = Object.freeze({
    VERSION,
    resizeRgb,
    resizeGray,
    _core: Object.freeze({
      sinc,
      lanczos,
      fixedCoefficient,
      precomputeCoefficients,
      horizontal,
      vertical,
      resize,
    }),
  });

  root.MinimalizerPillowLanczos = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
