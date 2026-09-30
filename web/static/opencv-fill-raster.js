(function (root) {
  "use strict";

  // Deterministic compatibility implementation of the non-antialiased polygon
  // scan conversion used by OpenCV fillPoly for Minimalizer's 2x mask contract.
  // It intentionally keeps only the small subset needed by Browser Fallback.
  const VERSION = "opencv-fillpoly-2x-v1";
  const XY_SHIFT = 16;
  const XY_ONE = 1 << XY_SHIFT;

  function truncDiv(left, right) {
    return Math.trunc(left / right);
  }

  function line8(mask, width, height, point0, point1) {
    let x0 = point0[0];
    let y0 = point0[1];
    const x1 = point1[0];
    const y1 = point1[1];
    let dx = x1 - x0;
    let dy = y1 - y0;
    let deltaX = 1;
    let deltaY = 1;

    if (dx < 0) {
      dx = -dx;
      dy = -dy;
      x0 = x1;
      y0 = y1;
    }
    if (dy < 0) {
      dy = -dy;
      deltaY = -1;
    }

    const vertical = dy > dx;
    if (vertical) {
      const oldDx = dx;
      dx = dy;
      dy = oldDx;
      const oldDeltaX = deltaX;
      deltaX = deltaY;
      deltaY = oldDeltaX;
    }

    let error = dx - (dy + dy);
    const plusDelta = dx + dx;
    const minusDelta = -(dy + dy);
    let minusShift = deltaX;
    let plusShift = 0;
    let minusStep = 0;
    let plusStep = deltaY;

    if (vertical) {
      let swap = plusStep;
      plusStep = plusShift;
      plusShift = swap;
      swap = minusStep;
      minusStep = minusShift;
      minusShift = swap;
    }

    let x = x0;
    let y = y0;
    for (let index = 0; index < dx + 1; index += 1) {
      if (x >= 0 && x < width && y >= 0 && y < height) {
        mask[y * width + x] = 1;
      }
      const bitMask = error < 0 ? -1 : 0;
      error += minusDelta + (plusDelta & bitMask);
      x += minusShift + (plusShift & bitMask);
      y += minusStep + (plusStep & bitMask);
    }
  }

  function fillPolyBinary(mask, width, height, points) {
    if (!points || points.length < 3) return;
    const edges = [];
    let previous = points[points.length - 1];

    for (const current of points) {
      line8(mask, width, height, previous, current);
      if (previous[1] !== current[1]) {
        const fixedX0 = previous[0] * XY_ONE;
        const fixedX1 = current[0] * XY_ONE;
        const dx = truncDiv(
          fixedX1 - fixedX0,
          current[1] - previous[1],
        );
        if (previous[1] < current[1]) {
          edges.push({
            y0: previous[1],
            y1: current[1],
            x: fixedX0,
            dx,
          });
        } else {
          edges.push({
            y0: current[1],
            y1: previous[1],
            x: fixedX1,
            dx,
          });
        }
      }
      previous = current;
    }

    if (edges.length < 2) return;
    edges.sort((left, right) => (
      left.y0 - right.y0
      || left.x - right.x
      || left.dx - right.dx
    ));

    const yMin = Math.min(...edges.map((edge) => edge.y0));
    const yMax = Math.min(
      Math.max(...edges.map((edge) => edge.y1)),
      height,
    );
    const roundUpDelta = XY_ONE - 1;

    for (let y = yMin; y < yMax; y += 1) {
      if (y < 0) continue;
      const active = [];
      for (const edge of edges) {
        if (edge.y0 <= y && y < edge.y1) {
          active.push({
            x: edge.x + (y - edge.y0) * edge.dx,
            dx: edge.dx,
          });
        }
      }
      active.sort((left, right) => left.x - right.x || left.dx - right.dx);

      for (let index = 0; index + 1 < active.length; index += 2) {
        const first = active[index].x;
        const second = active[index + 1].x;
        let x1 = Math.floor(
          (Math.min(first, second) + roundUpDelta) / XY_ONE
        );
        let x2 = Math.floor(Math.max(first, second) / XY_ONE);
        x1 = Math.max(0, x1);
        x2 = Math.min(width - 1, x2);
        for (let x = x1; x <= x2; x += 1) {
          mask[y * width + x] = 1;
        }
      }
    }
  }

  function rasterizeLoops(loops, width, height, scale) {
    const rasterScale = scale == null ? 2 : scale;
    if (!Number.isInteger(rasterScale) || rasterScale < 2) {
      throw new Error("raster scale must be an integer >= 2");
    }
    const highWidth = width * rasterScale + 1;
    const highHeight = height * rasterScale + 1;
    const high = new Uint8Array(highWidth * highHeight);

    for (const loop of loops || []) {
      if (!loop || loop.length < 3) continue;
      const local = new Uint8Array(high.length);
      const polygon = loop.map((point) => [
        Math.round(point[0] * rasterScale),
        Math.round(point[1] * rasterScale),
      ]);
      fillPolyBinary(local, highWidth, highHeight, polygon);
      for (let index = 0; index < high.length; index += 1) {
        high[index] ^= local[index];
      }
    }

    const output = new Uint8Array(width * height);
    const offset = Math.floor(rasterScale / 2);
    for (let y = 0; y < height; y += 1) {
      const highY = y * rasterScale + offset;
      for (let x = 0; x < width; x += 1) {
        output[y * width + x] = high[
          highY * highWidth + x * rasterScale + offset
        ];
      }
    }
    return output;
  }

  function scaledLoops(loops, scaleX, scaleY) {
    if (scaleX === 1 && scaleY === 1) return loops;
    return (loops || []).map((loop) => loop.map((point) => [
      point[0] * scaleX,
      point[1] * scaleY,
    ]));
  }

  function renderShapesRgba(shapes, width, height, scaleX, scaleY, scale) {
    const rgba = new Uint8ClampedArray(width * height * 4);
    for (let index = 0; index < width * height; index += 1) {
      const offset = index * 4;
      rgba[offset] = 255;
      rgba[offset + 1] = 255;
      rgba[offset + 2] = 255;
      rgba[offset + 3] = 255;
    }

    const ordered = (shapes || []).slice().sort((left, right) => (
      left.id - right.id
    ));
    for (const shape of ordered) {
      const sourceRings = (
        shape.rings && shape.rings.length > 0
          ? shape.rings
          : [shape.polygon]
      );
      const rings = scaledLoops(
        sourceRings,
        scaleX == null ? 1 : scaleX,
        scaleY == null ? 1 : scaleY,
      );
      const mask = rasterizeLoops(rings, width, height, scale == null ? 2 : scale);
      for (let index = 0; index < mask.length; index += 1) {
        if (!mask[index]) continue;
        const offset = index * 4;
        rgba[offset] = shape.rgb[0];
        rgba[offset + 1] = shape.rgb[1];
        rgba[offset + 2] = shape.rgb[2];
      }
    }
    return rgba;
  }

  const api = Object.freeze({
    VERSION,
    rasterizeLoops,
    renderShapesRgba,
    _core: Object.freeze({
      line8,
      fillPolyBinary,
      scaledLoops,
    }),
  });

  root.MinimalizerOpenCvRaster = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof window !== "undefined" ? window : globalThis));
