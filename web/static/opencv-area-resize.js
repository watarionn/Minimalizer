(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.MinimalizerOpenCvAreaResize = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const EPSILON = 1.0e-3;

  function f32(value) {
    return Math.fround(value);
  }

  function cvRoundPositive(value) {
    if (!Number.isFinite(value)) return 0;
    const lower = Math.floor(value);
    const fraction = value - lower;
    if (fraction < 0.5) return lower;
    if (fraction > 0.5) return lower + 1;
    return (lower & 1) === 0 ? lower : lower + 1;
  }

  function saturateU8(value) {
    return Math.max(0, Math.min(255, cvRoundPositive(value)));
  }

  function computeResizeAreaTab(sourceSize, destinationSize) {
    if (!Number.isInteger(sourceSize) || sourceSize <= 0) {
      throw new Error("sourceSize must be a positive integer");
    }
    if (!Number.isInteger(destinationSize) || destinationSize <= 0) {
      throw new Error("destinationSize must be a positive integer");
    }
    if (destinationSize > sourceSize) {
      throw new Error("INTER_AREA compatibility path supports downscale only");
    }

    const scale = sourceSize / destinationSize;
    const entries = [];
    for (let destination = 0; destination < destinationSize; destination += 1) {
      const start = destination * scale;
      const end = start + scale;
      const cellWidth = Math.min(scale, sourceSize - start);

      let sourceStart = Math.ceil(start);
      let sourceEnd = Math.floor(end);
      sourceEnd = Math.min(sourceEnd, sourceSize - 1);
      sourceStart = Math.min(sourceStart, sourceEnd);

      if (sourceStart - start > EPSILON) {
        entries.push({
          destination,
          source: sourceStart - 1,
          alpha: f32((sourceStart - start) / cellWidth),
        });
      }

      for (let source = sourceStart; source < sourceEnd; source += 1) {
        entries.push({
          destination,
          source,
          alpha: f32(1.0 / cellWidth),
        });
      }

      if (end - sourceEnd > EPSILON) {
        entries.push({
          destination,
          source: sourceEnd,
          alpha: f32(
            Math.min(Math.min(end - sourceEnd, 1.0), cellWidth) / cellWidth,
          ),
        });
      }
    }
    return entries;
  }

  function resizeRgba(source, sourceWidth, sourceHeight, destinationWidth, destinationHeight) {
    if (!(source instanceof Uint8Array) && !(source instanceof Uint8ClampedArray)) {
      throw new Error("source must be an 8-bit RGBA array");
    }
    if (source.length !== sourceWidth * sourceHeight * 4) {
      throw new Error("source RGBA length does not match dimensions");
    }
    if (destinationWidth > sourceWidth || destinationHeight > sourceHeight) {
      throw new Error("OpenCV INTER_AREA compatibility path only downsizes");
    }

    if (destinationWidth === sourceWidth && destinationHeight === sourceHeight) {
      const copy = new Uint8ClampedArray(source.length);
      copy.set(source);
      return copy;
    }

    const xTable = computeResizeAreaTab(sourceWidth, destinationWidth);
    const yTable = computeResizeAreaTab(sourceHeight, destinationHeight);
    const rowWidth = destinationWidth * 3;
    const horizontal = new Float32Array(rowWidth);
    const vertical = new Float32Array(rowWidth);
    const output = new Uint8ClampedArray(destinationWidth * destinationHeight * 4);

    let previousDestinationY = yTable.length > 0 ? yTable[0].destination : 0;

    function buildHorizontal(sourceY) {
      horizontal.fill(0);
      const rowBase = sourceY * sourceWidth * 4;
      for (let k = 0; k < xTable.length; k += 1) {
        const entry = xTable[k];
        const sourceOffset = rowBase + entry.source * 4;
        const destinationOffset = entry.destination * 3;
        const alpha = entry.alpha;

        horizontal[destinationOffset] = f32(
          horizontal[destinationOffset] + f32(source[sourceOffset] * alpha),
        );
        horizontal[destinationOffset + 1] = f32(
          horizontal[destinationOffset + 1] + f32(source[sourceOffset + 1] * alpha),
        );
        horizontal[destinationOffset + 2] = f32(
          horizontal[destinationOffset + 2] + f32(source[sourceOffset + 2] * alpha),
        );
      }
    }

    function storeRow(destinationY) {
      for (let x = 0; x < destinationWidth; x += 1) {
        const sourceOffset = x * 3;
        const destinationOffset = (destinationY * destinationWidth + x) * 4;
        output[destinationOffset] = saturateU8(vertical[sourceOffset]);
        output[destinationOffset + 1] = saturateU8(vertical[sourceOffset + 1]);
        output[destinationOffset + 2] = saturateU8(vertical[sourceOffset + 2]);
        output[destinationOffset + 3] = 255;
      }
    }

    for (let j = 0; j < yTable.length; j += 1) {
      const entry = yTable[j];
      buildHorizontal(entry.source);
      const beta = entry.alpha;

      if (entry.destination !== previousDestinationY) {
        storeRow(previousDestinationY);
        for (let offset = 0; offset < rowWidth; offset += 1) {
          vertical[offset] = f32(horizontal[offset] * beta);
        }
        previousDestinationY = entry.destination;
      } else {
        for (let offset = 0; offset < rowWidth; offset += 1) {
          vertical[offset] = f32(
            vertical[offset] + f32(horizontal[offset] * beta),
          );
        }
      }
    }

    if (yTable.length > 0) storeRow(previousDestinationY);
    return output;
  }

  return Object.freeze({
    version: "opencv-inter-area-u8-v1",
    computeResizeAreaTab,
    resizeRgba,
    _cvRoundPositive: cvRoundPositive,
  });
}));
