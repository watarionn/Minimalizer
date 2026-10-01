(function (root) {
  "use strict";

  const VERSION = "browser-color-strip-v1";
  const ANALYSIS_MAX_SIDE = 512;
  const OUTPUT_MAX_SIDE = 2048;

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function fitSize(width, height, maxSide) {
    if (Math.max(width, height) <= maxSide) return { width: width, height: height };
    const scale = maxSide / Math.max(width, height);
    return {
      width: Math.max(1, Math.round(width * scale)),
      height: Math.max(1, Math.round(height * scale)),
    };
  }

  function canvasElement(width, height) {
    if (typeof OffscreenCanvas !== "undefined") return new OffscreenCanvas(width, height);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    return canvas;
  }

  function context2d(canvas) {
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) throw new Error("2D canvas is unavailable.");
    return context;
  }

  async function decodeFile(file) {
    if (typeof createImageBitmap === "function") return await createImageBitmap(file);
    const url = URL.createObjectURL(file);
    try {
      const image = new Image();
      image.decoding = "async";
      image.src = url;
      await image.decode();
      return image;
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function sampleRgba(image, width, height) {
    const canvas = canvasElement(width, height);
    const context = context2d(canvas);
    context.imageSmoothingEnabled = false;
    context.clearRect(0, 0, width, height);
    context.drawImage(image, 0, 0, width, height);
    return context.getImageData(0, 0, width, height).data;
  }

  function rgbToLab(rgb) {
    const linear = rgb.map(function (value) {
      const s = value / 255;
      return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    let x = linear[0] * 0.4124564 + linear[1] * 0.3575761 + linear[2] * 0.1804375;
    let y = linear[0] * 0.2126729 + linear[1] * 0.7151522 + linear[2] * 0.0721750;
    let z = linear[0] * 0.0193339 + linear[1] * 0.1191920 + linear[2] * 0.9503041;
    x /= 0.95047;
    z /= 1.08883;
    const delta = 6 / 29;
    function f(value) {
      return value > Math.pow(delta, 3)
        ? Math.cbrt(value)
        : value / (3 * delta * delta) + 4 / 29;
    }
    const fx = f(x), fy = f(y), fz = f(z);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }

  function labDistance(left, right) {
    return Math.hypot(
      left[0] - right[0],
      left[1] - right[1],
      left[2] - right[2]
    );
  }

  function buildCandidates(rgba, width, height, alphaThreshold) {
    const bins = new Map();
    let totalVisible = 0;
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const offset = (y * width + x) * 4;
        if (rgba[offset + 3] <= alphaThreshold) continue;
        totalVisible += 1;
        const r = rgba[offset], g = rgba[offset + 1], b = rgba[offset + 2];
        const key = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3);
        let entry = bins.get(key);
        if (!entry) {
          entry = { key: key, count: 0, r: 0, g: 0, b: 0, x: 0, y: 0, x2: 0, y2: 0 };
          bins.set(key, entry);
        }
        entry.count += 1;
        entry.r += r; entry.g += g; entry.b += b;
        entry.x += x; entry.y += y; entry.x2 += x * x; entry.y2 += y * y;
      }
    }
    const entries = Array.from(bins.values()).map(function (entry) {
      const rgb = [
        Math.round(entry.r / entry.count),
        Math.round(entry.g / entry.count),
        Math.round(entry.b / entry.count),
      ];
      const meanX = entry.x / entry.count;
      const meanY = entry.y / entry.count;
      const varX = Math.max(0, entry.x2 / entry.count - meanX * meanX);
      const varY = Math.max(0, entry.y2 / entry.count - meanY * meanY);
      return {
        key: entry.key,
        count: entry.count,
        rgb: rgb,
        lab: rgbToLab(rgb),
        spread: (
          Math.min(1, Math.sqrt(varX) / Math.max(1, width * 0.22))
          + Math.min(1, Math.sqrt(varY) / Math.max(1, height * 0.22))
        ) / 2,
      };
    });
    entries.sort(function (a, b) { return b.count - a.count || a.key - b.key; });
    return { entries: entries, totalVisible: totalVisible };
  }

  function mergeCandidates(entries, similarity) {
    const clusters = [];
    for (const entry of entries) {
      let best = -1;
      let bestDistance = Number.POSITIVE_INFINITY;
      for (let index = 0; index < clusters.length; index += 1) {
        const distance = labDistance(entry.lab, clusters[index].lab);
        if (distance < bestDistance) {
          bestDistance = distance;
          best = index;
        }
      }
      if (best >= 0 && bestDistance <= similarity) {
        const cluster = clusters[best];
        const oldCount = cluster.count;
        const nextCount = oldCount + entry.count;
        cluster.rgb = [
          (cluster.rgb[0] * oldCount + entry.rgb[0] * entry.count) / nextCount,
          (cluster.rgb[1] * oldCount + entry.rgb[1] * entry.count) / nextCount,
          (cluster.rgb[2] * oldCount + entry.rgb[2] * entry.count) / nextCount,
        ];
        cluster.spread = (cluster.spread * oldCount + entry.spread * entry.count) / nextCount;
        cluster.count = nextCount;
        cluster.lab = rgbToLab(cluster.rgb);
      } else {
        clusters.push({
          count: entry.count,
          rgb: entry.rgb.slice(),
          lab: entry.lab.slice(),
          spread: entry.spread,
        });
      }
    }
    return clusters.map(function (cluster) {
      return {
        count: cluster.count,
        rgb: cluster.rgb.map(function (value) { return Math.round(clamp(value, 0, 255)); }),
        lab: cluster.lab,
        spread: cluster.spread,
      };
    }).sort(function (a, b) { return b.count - a.count; });
  }

  function borderLabs(rgba, width, height) {
    const bins = new Map();
    const band = Math.max(2, Math.floor(Math.min(width, height) * 0.045));
    function add(x, y) {
      const offset = (y * width + x) * 4;
      if (rgba[offset + 3] <= 20) return;
      const r = rgba[offset], g = rgba[offset + 1], b = rgba[offset + 2];
      const key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4);
      let item = bins.get(key);
      if (!item) item = { count: 0, r: 0, g: 0, b: 0 };
      item.count += 1; item.r += r; item.g += g; item.b += b;
      bins.set(key, item);
    }
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        if (x < band || y < band || x >= width - band || y >= height - band) add(x, y);
      }
    }
    const top = Array.from(bins.values()).sort(function (a, b) {
      return b.count - a.count;
    }).slice(0, 5);
    const total = top.reduce(function (sum, item) { return sum + item.count; }, 0);
    if (!top.length || top[0].count / Math.max(total, 1) < 0.26) return [];
    return top.map(function (item) {
      return rgbToLab([item.r / item.count, item.g / item.count, item.b / item.count]);
    });
  }

  function reassignCounts(rgba, width, height, selected, alphaThreshold) {
    const counts = new Array(selected.length).fill(0);
    const labs = selected.map(function (item) { return rgbToLab(item.rgb); });
    for (let index = 0; index < width * height; index += 1) {
      const offset = index * 4;
      if (rgba[offset + 3] <= alphaThreshold) continue;
      const lab = rgbToLab([rgba[offset], rgba[offset + 1], rgba[offset + 2]]);
      let best = 0;
      let bestDistance = Number.POSITIVE_INFINITY;
      for (let center = 0; center < labs.length; center += 1) {
        const distance = labDistance(lab, labs[center]);
        if (distance < bestDistance) {
          bestDistance = distance;
          best = center;
        }
      }
      counts[best] += 1;
    }
    return selected.map(function (item, index) {
      return { rgb: item.rgb.slice(), count: counts[index] };
    });
  }

  function selectFeatured(merged, totalVisible, colorCount) {
    const slots = Math.max(1, colorCount - 1);
    const selected = merged.slice(0, slots);
    const selectedLabs = selected.map(function (item) { return item.lab; });
    let winner = null;
    let winnerScore = -1;
    for (const candidate of merged.slice(slots)) {
      const share = candidate.count / Math.max(totalVisible, 1);
      if (share < 0.005) continue;
      const dominantDistance = selectedLabs.length
        ? Math.min.apply(null, selectedLabs.map(function (lab) { return labDistance(candidate.lab, lab); }))
        : 60;
      if (dominantDistance < 12) continue;
      const chroma = Math.hypot(candidate.lab[1], candidate.lab[2]);
      const score = (
        0.45 * Math.min(dominantDistance / 60, 1)
        + 0.35 * Math.min(chroma / 80, 1)
        + 0.20 * Math.min(share / 0.05, 1)
      );
      if (score > winnerScore) {
        winnerScore = score;
        winner = candidate;
      }
    }
    if (winner) selected.push(winner);
    for (const candidate of merged) {
      if (selected.length >= colorCount) break;
      if (selected.indexOf(candidate) < 0) selected.push(candidate);
    }
    return selected.slice(0, colorCount);
  }

  function selectCharacteristic(entries, totalVisible, colorCount, backgrounds) {
    let source = entries.filter(function (entry) {
      if (!backgrounds.length) return true;
      const distance = Math.min.apply(null, backgrounds.map(function (lab) {
        return labDistance(entry.lab, lab);
      }));
      return distance >= 17 || entry.spread < 0.22;
    });
    if (source.length < colorCount) source = entries.slice();

    const candidates = source.slice(0, Math.min(96, source.length)).map(function (item) {
      const area = item.count / Math.max(totalVisible, 1);
      const chroma = Math.hypot(item.lab[1], item.lab[2]);
      const lightness = item.lab[0];
      let neutral = "color";
      if (chroma < 13 && lightness > 76) neutral = "light";
      else if (chroma < 15 && lightness < 31) neutral = "dark";
      else if (chroma < 12) neutral = "neutral";
      let chromaTerm = 0.78, lightTerm = 0.92;
      if (neutral === "color") {
        chromaTerm = 0.70 + 0.55 * Math.min(1, chroma / 52);
        lightTerm = 0.90 + 0.10 * (1 - Math.abs(lightness - 58) / 58);
      } else if (neutral === "light") {
        chromaTerm = 0.96;
        lightTerm = lightness > 86 ? 1.11 : 1.02;
      } else if (neutral === "dark") {
        chromaTerm = 0.80;
        lightTerm = 0.82 + 0.55 * Math.min(1, area / 0.12);
      }
      const score = Math.pow(Math.max(area, 1e-9), 0.56)
        * chromaTerm * lightTerm * (0.90 + 0.22 * item.spread);
      return {
        count: item.count, rgb: item.rgb.slice(), lab: item.lab.slice(),
        spread: item.spread, area: area, chroma: chroma, neutral: neutral, score: score,
      };
    }).sort(function (a, b) { return b.score - a.score; });

    const merged = [];
    for (const candidate of candidates) {
      if (merged.some(function (item) { return labDistance(candidate.lab, item.lab) < 13; })) continue;
      merged.push(candidate);
    }
    if (!merged.length) return entries.slice(0, colorCount);

    const selected = [];
    function take(item) {
      selected.push(item);
      merged.splice(merged.indexOf(item), 1);
    }
    let main = merged[0], mainMetric = -1;
    for (const item of merged) {
      const metric = item.score * (0.80 + 1.20 * Math.min(1, item.area / 0.24));
      if (metric > mainMetric) { mainMetric = metric; main = item; }
    }
    take(main);

    if (selected.length < colorCount && colorCount >= 4 && main.neutral === "color") {
      const neutrals = merged.filter(function (item) {
        return item.neutral !== "color" && item.area >= 0.035;
      }).sort(function (a, b) {
        const am = a.score * (0.85 + 0.55 * Math.min(1, a.area / 0.16));
        const bm = b.score * (0.85 + 0.55 * Math.min(1, b.area / 0.16));
        return bm - am;
      });
      if (neutrals.length) take(neutrals[0]);
    }

    if (selected.length < colorCount) {
      function accentScore(item) {
        const distance = Math.min.apply(null, selected.map(function (other) {
          return labDistance(item.lab, other.lab);
        }));
        const diversity = 0.12 + 0.88 * Math.min(1, Math.max(0, (distance - 9) / 30));
        let chromaBonus = 0.45 + 1.75 * Math.min(1, item.chroma / 58);
        if (item.chroma >= 28) chromaBonus *= 1.20;
        else if (item.chroma < 20) chromaBonus *= 0.72;
        const rarity = 1.16 - 0.28 * Math.min(1, item.area / 0.18);
        return item.score * chromaBonus * rarity * diversity;
      }
      const chromatic = merged.filter(function (item) {
        return item.neutral === "color" && item.area >= 0.006;
      }).sort(function (a, b) { return accentScore(b) - accentScore(a); });
      if (chromatic.length) take(chromatic[0]);
    }

    while (merged.length && selected.length < colorCount) {
      function supportScore(item) {
        const distance = Math.min.apply(null, selected.map(function (other) {
          return labDistance(item.lab, other.lab);
        }));
        const diversity = 0.12 + 0.88 * Math.min(1, Math.max(0, (distance - 9) / 30));
        const areaBonus = 0.90 + 0.28 * Math.min(1, item.area / 0.14);
        const neutralPenalty = item.neutral !== "color"
          && selected.some(function (x) { return x.neutral !== "color"; })
          ? 0.78 : 1;
        return item.score * areaBonus * neutralPenalty * diversity;
      }
      merged.sort(function (a, b) { return supportScore(b) - supportScore(a); });
      take(merged[0]);
    }
    return selected;
  }

  function equalBounds(count, length) {
    const result = [];
    for (let index = 0; index < count; index += 1) {
      const start = Math.round(index * length / count);
      result.push([start, Math.max(start + 1, Math.round((index + 1) * length / count))]);
    }
    return result;
  }

  function proportionalBounds(colors, length) {
    if (!colors.length) return [];
    if (length < colors.length) return equalBounds(colors.length, length);
    const total = colors.reduce(function (sum, item) { return sum + item.share; }, 0);
    const remaining = length - colors.length;
    const weighted = colors.map(function (item) {
      return total > 0 ? item.share / total * remaining : remaining / colors.length;
    });
    const extras = weighted.map(Math.floor);
    let remainder = remaining - extras.reduce(function (sum, value) { return sum + value; }, 0);
    const rank = weighted.map(function (value, index) {
      return { index: index, fraction: value - extras[index] };
    }).sort(function (a, b) { return b.fraction - a.fraction || a.index - b.index; });
    for (let index = 0; index < remainder; index += 1) extras[rank[index].index] += 1;
    let cursor = 0;
    return extras.map(function (extra) {
      const start = cursor;
      cursor += 1 + extra;
      return [start, cursor];
    });
  }

  function colorHex(rgb) {
    return "#" + rgb.map(function (value) {
      return Math.round(value).toString(16).padStart(2, "0");
    }).join("");
  }

  async function canvasToBlob(canvas) {
    if (typeof canvas.convertToBlob === "function") return await canvas.convertToBlob({ type: "image/png" });
    return await new Promise(function (resolve, reject) {
      canvas.toBlob(function (blob) {
        if (blob) resolve(blob);
        else reject(new Error("PNG encoding failed."));
      }, "image/png");
    });
  }

  async function create(file, options) {
    const config = Object.assign({
      colorCount: 5,
      similarity: 18,
      sizeMode: "equal",
      order: "least_first",
      orientation: "vertical",
      selectionMode: "dominant",
      outputFormat: "png",
    }, options || {});

    if (config.colorCount < 3 || config.colorCount > 5) throw new Error("Color count must be between 3 and 5.");
    if (config.similarity < 6 || config.similarity > 30) throw new Error("Similarity must be between 6 and 30.");

    const started = performance.now();
    const image = await decodeFile(file);
    const sourceWidth = image.width, sourceHeight = image.height;
    const analysis = fitSize(sourceWidth, sourceHeight, ANALYSIS_MAX_SIDE);
    const output = fitSize(sourceWidth, sourceHeight, OUTPUT_MAX_SIDE);
    const rgba = sampleRgba(image, analysis.width, analysis.height);
    if (typeof image.close === "function") image.close();

    const alphaThreshold = config.selectionMode === "characteristic" ? 20 : 0;
    const built = buildCandidates(rgba, analysis.width, analysis.height, alphaThreshold);
    if (!built.entries.length || !built.totalVisible) throw new Error("Color Strip requires visible pixels.");

    let selected;
    if (config.selectionMode === "characteristic") {
      selected = selectCharacteristic(
        built.entries, built.totalVisible, config.colorCount,
        borderLabs(rgba, analysis.width, analysis.height)
      );
    } else {
      const merged = mergeCandidates(built.entries, config.similarity);
      selected = config.selectionMode === "featured"
        ? selectFeatured(merged, built.totalVisible, config.colorCount)
        : merged.slice(0, config.colorCount);
    }

    let colors = reassignCounts(
      rgba, analysis.width, analysis.height, selected.slice(0, config.colorCount), alphaThreshold
    ).filter(function (item) { return item.count > 0; });
    const reassignedTotal = colors.reduce(function (sum, item) { return sum + item.count; }, 0);
    colors = colors.map(function (item) {
      return {
        rgb: item.rgb.map(Math.round),
        count: item.count,
        share: item.count / Math.max(reassignedTotal, 1),
      };
    }).sort(function (a, b) {
      return config.order === "most_first" ? b.count - a.count : a.count - b.count;
    });

    const length = config.orientation === "vertical" ? output.height : output.width;
    const bounds = config.sizeMode === "proportional"
      ? proportionalBounds(colors, length)
      : equalBounds(colors.length, length);

    let body, contentType;
    if (config.outputFormat === "svg") {
      const lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + output.width
          + '" height="' + output.height + '" viewBox="0 0 ' + output.width + ' ' + output.height + '">'
      ];
      colors.forEach(function (color, index) {
        const start = bounds[index][0], end = bounds[index][1];
        if (config.orientation === "vertical") {
          lines.push('  <rect x="0" y="' + start + '" width="' + output.width
            + '" height="' + (end - start) + '" fill="' + colorHex(color.rgb) + '"/>');
        } else {
          lines.push('  <rect x="' + start + '" y="0" width="' + (end - start)
            + '" height="' + output.height + '" fill="' + colorHex(color.rgb) + '"/>');
        }
      });
      lines.push("</svg>");
      body = lines.join("\n");
      contentType = "image/svg+xml";
    } else {
      const canvas = canvasElement(output.width, output.height);
      const context = context2d(canvas);
      colors.forEach(function (color, index) {
        const start = bounds[index][0], end = bounds[index][1];
        context.fillStyle = "rgb(" + color.rgb.join(",") + ")";
        if (config.orientation === "vertical") context.fillRect(0, start, output.width, end - start);
        else context.fillRect(start, 0, end - start, output.height);
      });
      body = await canvasToBlob(canvas);
      contentType = "image/png";
    }

    const elapsed = performance.now() - started;
    const headers = new Headers({
      "Content-Type": contentType,
      "X-Minimalizer-Mode": "color_strip",
      "X-Minimalizer-Compute": "browser",
      "X-Minimalizer-Color-Count": String(colors.length),
      "X-Minimalizer-Color-Selection-Mode": config.selectionMode,
      "X-Minimalizer-Color-Size-Mode": config.sizeMode,
      "X-Minimalizer-Color-Order": config.order,
      "X-Minimalizer-Color-Orientation": config.orientation,
      "X-Minimalizer-Analysis-Size": analysis.width + "x" + analysis.height,
      "X-Minimalizer-Processing-Ms": elapsed.toFixed(1),
      "X-Minimalizer-Color-Strip-Version": VERSION,
    });
    return {
      response: new Response(body, { status: 200, headers: headers }),
      metadata: {
        version: VERSION,
        sourceWidth: sourceWidth,
        sourceHeight: sourceHeight,
        analysisWidth: analysis.width,
        analysisHeight: analysis.height,
        outputWidth: output.width,
        outputHeight: output.height,
        colors: colors,
        processingMs: elapsed,
      },
    };
  }

  const api = Object.freeze({
    VERSION: VERSION,
    create: create,
    _core: Object.freeze({
      fitSize: fitSize,
      rgbToLab: rgbToLab,
      labDistance: labDistance,
      buildCandidates: buildCandidates,
      mergeCandidates: mergeCandidates,
      selectFeatured: selectFeatured,
      selectCharacteristic: selectCharacteristic,
      equalBounds: equalBounds,
      proportionalBounds: proportionalBounds,
    }),
  });

  root.MinimalizerBrowserColorStrip = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
