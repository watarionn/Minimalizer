(function (root) {
  "use strict";

  const VERSION = "browser-feature-palette-v1";
  const FAMILY_ANCHOR_RGB = Object.freeze({
    red: [220, 45, 45],
    orange: [235, 125, 35],
    yellow: [238, 205, 55],
    yellowgreen: [160, 190, 60],
    green: [55, 155, 85],
    cyan: [55, 190, 200],
    blue: [70, 115, 220],
    purple: [135, 85, 205],
    pink: [230, 105, 170],
  });

  function rgbToLab(rgb) {
    const values = [
      rgb[0] / 255,
      rgb[1] / 255,
      rgb[2] / 255,
    ];
    const linear = values.map((value) => (
      value <= 0.04045
        ? value / 12.92
        : Math.pow((value + 0.055) / 1.055, 2.4)
    ));
    let x = (
      linear[0] * 0.4124564
      + linear[1] * 0.3575761
      + linear[2] * 0.1804375
    ) / 0.95047;
    const y = (
      linear[0] * 0.2126729
      + linear[1] * 0.7151522
      + linear[2] * 0.0721750
    );
    let z = (
      linear[0] * 0.0193339
      + linear[1] * 0.1191920
      + linear[2] * 0.9503041
    ) / 1.08883;
    const epsilon = 216 / 24389;
    const kappa = 24389 / 27;
    const f = (value) => (
      value > epsilon
        ? Math.cbrt(value)
        : (kappa * value + 16) / 116
    );
    const fx = f(x), fy = f(y), fz = f(z);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }

  function labToRgb(lab) {
    const L = lab[0], a = lab[1], b = lab[2];
    const fy = (L + 16) / 116;
    const fx = fy + a / 500;
    const fz = fy - b / 200;
    const epsilon = 216 / 24389;
    const kappa = 24389 / 27;
    const finv = (value) => {
      const cube = value * value * value;
      return cube > epsilon ? cube : (116 * value - 16) / kappa;
    };
    const x = 0.95047 * finv(fx);
    const y = finv(fy);
    const z = 1.08883 * finv(fz);
    const linear = [
      3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
      -0.9692660 * x + 1.8760108 * y + 0.0415560 * z,
      0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
    ];
    return linear.map((value) => {
      const encoded = value <= 0.0031308
        ? 12.92 * value
        : 1.055 * Math.pow(Math.max(value, 0), 1 / 2.4) - 0.055;
      return Math.max(0, Math.min(255, Math.round(encoded * 255)));
    });
  }

  function deltaE(left, right) {
    return Math.hypot(
      left[0] - right[0],
      left[1] - right[1],
      left[2] - right[2],
    );
  }

  function makeRng(seed) {
    let state = seed >>> 0;
    return function () {
      state ^= state << 13;
      state ^= state >>> 17;
      state ^= state << 5;
      state >>>= 0;
      return state / 4294967296;
    };
  }

  function sampleIndices(indices, maximum, rng) {
    if (indices.length <= maximum) return indices.slice();
    const sample = indices.slice();
    for (let index = 0; index < maximum; index += 1) {
      const swapIndex = index + Math.floor(rng() * (sample.length - index));
      const old = sample[index];
      sample[index] = sample[swapIndex];
      sample[swapIndex] = old;
    }
    sample.length = maximum;
    return sample;
  }

  function quantizedKey(r, g, b) {
    return (Math.floor(r / 16) << 8) | (Math.floor(g / 16) << 4) | Math.floor(b / 16);
  }

  function median(values) {
    if (!values.length) return 0;
    values.sort((a, b) => a - b);
    const middle = Math.floor(values.length / 2);
    return values.length % 2
      ? values[middle]
      : (values[middle - 1] + values[middle]) / 2;
  }

  function estimateBackgroundMask(rgba, width, height) {
    const count = width * height;
    const band = Math.max(2, Math.floor(Math.min(width, height) * 0.045));
    const bins = new Map();
    const borderIndices = [];

    const addBorder = (x, y) => {
      const pixel = y * width + x;
      const offset = pixel * 4;
      if (rgba[offset + 3] <= 20) return;
      borderIndices.push(pixel);
      const key = quantizedKey(rgba[offset], rgba[offset + 1], rgba[offset + 2]);
      let bucket = bins.get(key);
      if (!bucket) {
        bucket = { count: 0, indices: [] };
        bins.set(key, bucket);
      }
      bucket.count += 1;
      bucket.indices.push(pixel);
    };

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        if (
          x < band || x >= width - band
          || y < band || y >= height - band
        ) addBorder(x, y);
      }
    }
    if (!borderIndices.length) return new Uint8Array(count);

    const top = Array.from(bins.values())
      .sort((left, right) => right.count - left.count)
      .slice(0, 5);
    const candidates = top.map((bucket) => {
      const rs = [], gs = [], bs = [];
      for (const pixel of bucket.indices) {
        const offset = pixel * 4;
        rs.push(rgba[offset]);
        gs.push(rgba[offset + 1]);
        bs.push(rgba[offset + 2]);
      }
      return rgbToLab([median(rs), median(gs), median(bs)]);
    });

    const borderLabs = borderIndices.map((pixel) => {
      const offset = pixel * 4;
      return rgbToLab([rgba[offset], rgba[offset + 1], rgba[offset + 2]]);
    });
    let backgroundLab = candidates[0];
    let bestCoverage = -1;
    for (const candidate of candidates) {
      let covered = 0;
      for (const lab of borderLabs) {
        if (deltaE(lab, candidate) < 17) covered += 1;
      }
      const coverage = covered / borderLabs.length;
      if (coverage > bestCoverage) {
        bestCoverage = coverage;
        backgroundLab = candidate;
      }
    }
    if (bestCoverage < 0.26) return new Uint8Array(count);

    const labs = new Float32Array(count * 3);
    const similar = new Uint8Array(count);
    for (let pixel = 0; pixel < count; pixel += 1) {
      const offset = pixel * 4;
      const lab = rgbToLab([rgba[offset], rgba[offset + 1], rgba[offset + 2]]);
      labs[pixel * 3] = lab[0];
      labs[pixel * 3 + 1] = lab[1];
      labs[pixel * 3 + 2] = lab[2];
      if (deltaE(lab, backgroundLab) < 17) similar[pixel] = 1;
    }

    const connected = new Uint8Array(count);
    const queue = new Int32Array(count);
    let head = 0, tail = 0;
    const enqueue = (pixel) => {
      if (!similar[pixel] || connected[pixel]) return;
      connected[pixel] = 1;
      queue[tail++] = pixel;
    };
    for (let x = 0; x < width; x += 1) {
      enqueue(x);
      if (height > 1) enqueue((height - 1) * width + x);
    }
    for (let y = 0; y < height; y += 1) {
      enqueue(y * width);
      if (width > 1) enqueue(y * width + width - 1);
    }

    while (head < tail) {
      const pixel = queue[head++];
      const x = pixel % width;
      const y = Math.floor(pixel / width);
      const base = pixel * 3;
      const neighbors = [];
      if (y > 0) neighbors.push(pixel - width);
      if (y + 1 < height) neighbors.push(pixel + width);
      if (x > 0) neighbors.push(pixel - 1);
      if (x + 1 < width) neighbors.push(pixel + 1);
      for (const next of neighbors) {
        if (!similar[next] || connected[next]) continue;
        const other = next * 3;
        const localDelta = Math.hypot(
          labs[base] - labs[other],
          labs[base + 1] - labs[other + 1],
          labs[base + 2] - labs[other + 2],
        );
        if (localDelta <= 7.5) {
          connected[next] = 1;
          queue[tail++] = next;
        }
      }
    }
    return connected;
  }

  function weightedKmeans(labs, k, iterations, rng) {
    const n = labs.length;
    if (n <= k) {
      return {
        centers: labs.map((lab) => lab.slice()),
        labels: labs.map((_, index) => index),
      };
    }
    const centers = [labs[Math.floor(rng() * n)].slice()];
    while (centers.length < k) {
      const weights = new Float64Array(n);
      let total = 0;
      for (let index = 0; index < n; index += 1) {
        let minimum = Number.POSITIVE_INFINITY;
        for (const center of centers) {
          const d = deltaE(labs[index], center);
          minimum = Math.min(minimum, d * d);
        }
        weights[index] = minimum;
        total += minimum;
      }
      let picked;
      if (total <= 0) {
        picked = Math.floor(rng() * n);
      } else {
        let threshold = rng() * total;
        picked = n - 1;
        for (let index = 0; index < n; index += 1) {
          threshold -= weights[index];
          if (threshold <= 0) {
            picked = index;
            break;
          }
        }
      }
      centers.push(labs[picked].slice());
    }

    let labels = new Int16Array(n);
    labels.fill(-1);
    for (let iteration = 0; iteration < iterations; iteration += 1) {
      const next = new Int16Array(n);
      let unchanged = true;
      const sums = Array.from({ length: k }, () => [0, 0, 0, 0]);
      for (let index = 0; index < n; index += 1) {
        let best = 0;
        let bestDistance = Number.POSITIVE_INFINITY;
        for (let center = 0; center < k; center += 1) {
          const lab = centers[center];
          const d0 = labs[index][0] - lab[0];
          const d1 = labs[index][1] - lab[1];
          const d2 = labs[index][2] - lab[2];
          const distance = d0 * d0 + d1 * d1 + d2 * d2;
          if (distance < bestDistance) {
            bestDistance = distance;
            best = center;
          }
        }
        next[index] = best;
        if (labels[index] !== best) unchanged = false;
        sums[best][0] += labs[index][0];
        sums[best][1] += labs[index][1];
        sums[best][2] += labs[index][2];
        sums[best][3] += 1;
      }
      labels = next;
      for (let center = 0; center < k; center += 1) {
        const sum = sums[center];
        if (sum[3] === 0) {
          centers[center] = labs[Math.floor(rng() * n)].slice();
        } else {
          centers[center] = [
            sum[0] / sum[3],
            sum[1] / sum[3],
            sum[2] / sum[3],
          ];
        }
      }
      if (unchanged) break;
    }
    return { centers, labels: Array.from(labels) };
  }

  function spatialSpread(xs, ys, width, height) {
    if (xs.length < 2) return 0;
    const meanX = xs.reduce((sum, value) => sum + value, 0) / xs.length;
    const meanY = ys.reduce((sum, value) => sum + value, 0) / ys.length;
    let vx = 0, vy = 0;
    for (let index = 0; index < xs.length; index += 1) {
      vx += (xs[index] - meanX) ** 2;
      vy += (ys[index] - meanY) ** 2;
    }
    const sx = Math.min(1, Math.sqrt(vx / xs.length) / Math.max(1, width * 0.22));
    const sy = Math.min(1, Math.sqrt(vy / ys.length) / Math.max(1, height * 0.22));
    return (sx + sy) / 2;
  }

  function labHueDeg(lab) {
    return (Math.atan2(lab[2], lab[1]) * 180 / Math.PI + 360) % 360;
  }

  const FAMILY_ANCHOR_LAB = Object.freeze(Object.fromEntries(
    Object.entries(FAMILY_ANCHOR_RGB).map(([name, rgb]) => [name, rgbToLab(rgb)])
  ));

  function colorFamily(lab, neutralKind) {
    const L = lab[0], a = lab[1], b = lab[2];
    const chroma = Math.hypot(a, b);
    const hue = labHueDeg(lab);
    if (neutralKind === "light") return "white";
    if (neutralKind === "dark") return "black";
    if (neutralKind === "neutral") return "gray";
    if (chroma < 28) {
      if (15 <= hue && hue < 75) return L >= 68 ? "beige" : "brown";
      if (75 <= hue && hue < 125) return L >= 72 ? "beige" : "yellow";
      if (125 <= hue && hue < 205) return L >= 72 ? "gray" : "green";
      if (205 <= hue && hue < 270) return L >= 72 ? "bluegray" : "blue";
      if (270 <= hue && hue < 330) return L >= 72 ? "mauve" : "purple";
      if (hue >= 330 || hue < 15) return L >= 70 ? "pink" : "red";
    }
    let bestName = "red";
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const [name, anchor] of Object.entries(FAMILY_ANCHOR_LAB)) {
      const dL = (L - anchor[0]) * (chroma < 38 ? 0.48 : 0.62);
      const da = a - anchor[1];
      const db = b - anchor[2];
      let distance = Math.hypot(dL, da, db);
      if (name === "pink" && (hue >= 325 || hue < 350)) distance *= 0.90;
      if (name === "red" && (hue >= 350 || hue < 22)) distance *= 0.91;
      if (name === "yellow" && 55 <= hue && hue <= 100) distance *= 0.88;
      if (name === "yellowgreen" && 90 <= hue && hue <= 125) distance *= 0.94;
      if (name === "cyan" && 170 <= hue && hue <= 220) distance *= 0.90;
      if (name === "blue" && 220 <= hue && hue <= 285) distance *= 0.91;
      if (name === "purple" && 285 <= hue && hue <= 325) distance *= 0.91;
      if (distance < bestDistance) {
        bestName = name;
        bestDistance = distance;
      }
    }
    return bestName;
  }

  function diversityMultiplier(candidate, selected) {
    if (!selected.length) return 1;
    let minimum = Number.POSITIVE_INFINITY;
    for (const item of selected) {
      minimum = Math.min(minimum, deltaE(candidate.lab, item.lab));
    }
    return 0.12 + 0.88 * Math.min(1, Math.max(0, (minimum - 9) / 30));
  }

  function roleSelect(merged, nColors) {
    if (!merged.length || nColors <= 0) return [];
    const remaining = merged.slice();
    const selected = [];
    const take = (item, role, finalScore) => {
      const picked = Object.assign({}, item, { role, finalScore });
      selected.push(picked);
      remaining.splice(remaining.indexOf(item), 1);
    };

    let main = remaining[0];
    let mainScore = -1;
    for (const candidate of remaining) {
      const score = candidate.score * (
        0.80 + 1.20 * Math.min(1, candidate.area / 0.24)
      );
      if (score > mainScore) {
        main = candidate;
        mainScore = score;
      }
    }
    take(main, "main", mainScore);
    if (selected.length >= nColors) return selected;

    if (main.neutral === "color" && nColors >= 4) {
      const neutrals = remaining.filter((candidate) => (
        candidate.neutral !== "color" && candidate.area >= 0.035
      ));
      if (neutrals.length) {
        let winner = neutrals[0];
        let winnerScore = -1;
        for (const candidate of neutrals) {
          const score = candidate.score * (
            0.85 + 0.55 * Math.min(1, candidate.area / 0.16)
          );
          if (score > winnerScore) {
            winner = candidate;
            winnerScore = score;
          }
        }
        take(winner, "neutral", winnerScore);
      }
    }

    if (selected.length < nColors) {
      const chromatic = remaining.filter((candidate) => (
        candidate.neutral === "color" && candidate.area >= 0.006
      ));
      if (chromatic.length) {
        const seenFamilies = new Set(selected.map((item) => colorFamily(item.lab, item.neutral)));
        const metric = (candidate) => {
          const familyBonus = seenFamilies.has(colorFamily(candidate.lab, candidate.neutral))
            ? 0.72
            : 1.18;
          let chromaBonus = 0.45 + 1.75 * Math.min(1, candidate.chroma / 58);
          if (candidate.chroma >= 28) chromaBonus *= 1.20;
          else if (candidate.chroma < 20) chromaBonus *= 0.72;
          const rarityBonus = 1.16 - 0.28 * Math.min(1, candidate.area / 0.18);
          return (
            candidate.score
            * chromaBonus
            * rarityBonus
            * familyBonus
            * diversityMultiplier(candidate, selected)
          );
        };
        let winner = chromatic[0], winnerScore = metric(winner);
        for (const candidate of chromatic.slice(1)) {
          const score = metric(candidate);
          if (score > winnerScore) {
            winner = candidate;
            winnerScore = score;
          }
        }
        take(winner, "accent", winnerScore);
      }
    }

    while (remaining.length && selected.length < nColors) {
      const seenFamilies = new Set(selected.map((item) => colorFamily(item.lab, item.neutral)));
      const metric = (candidate) => {
        const familyBonus = seenFamilies.has(colorFamily(candidate.lab, candidate.neutral))
          ? 0.62
          : 1.12;
        const areaBonus = 0.90 + 0.28 * Math.min(1, candidate.area / 0.14);
        const neutralPenalty = (
          candidate.neutral !== "color"
          && selected.some((item) => item.neutral !== "color")
        ) ? 0.78 : 1;
        return (
          candidate.score
          * familyBonus
          * areaBonus
          * neutralPenalty
          * diversityMultiplier(candidate, selected)
        );
      };
      let winner = remaining[0], winnerScore = metric(winner);
      for (const candidate of remaining.slice(1)) {
        const score = metric(candidate);
        if (score > winnerScore) {
          winner = candidate;
          winnerScore = score;
        }
      }
      take(winner, "support", winnerScore);
    }
    return selected;
  }

  function extract(rgba, width, height, nColors, options) {
    const config = Object.assign({
      removeBackground: true,
      sampleMax: 12000,
      clusters: 18,
      seed: 42,
    }, options || {});
    const count = width * height;
    let background = new Uint8Array(count);
    if (config.removeBackground) {
      background = estimateBackgroundMask(rgba, width, height);
    }

    const valid = [];
    for (let pixel = 0; pixel < count; pixel += 1) {
      if (rgba[pixel * 4 + 3] <= 20) continue;
      if (config.removeBackground && background[pixel]) continue;
      valid.push(pixel);
    }
    if (!valid.length) throw new Error("No foreground pixels were available for palette extraction.");

    const rng = makeRng(config.seed);
    const sampled = sampleIndices(valid, config.sampleMax, rng);
    const labs = new Array(sampled.length);
    const xs = new Int32Array(sampled.length);
    const ys = new Int32Array(sampled.length);
    for (let index = 0; index < sampled.length; index += 1) {
      const pixel = sampled[index];
      const offset = pixel * 4;
      labs[index] = rgbToLab([rgba[offset], rgba[offset + 1], rgba[offset + 2]]);
      xs[index] = pixel % width;
      ys[index] = Math.floor(pixel / width);
    }

    const k = Math.min(config.clusters, Math.max(6, Math.floor(sampled.length / 120)));
    const clustered = weightedKmeans(labs, k, 24, rng);
    const candidates = [];
    for (let center = 0; center < clustered.centers.length; center += 1) {
      const memberXs = [];
      const memberYs = [];
      let memberCount = 0;
      for (let index = 0; index < clustered.labels.length; index += 1) {
        if (clustered.labels[index] !== center) continue;
        memberCount += 1;
        memberXs.push(xs[index]);
        memberYs.push(ys[index]);
      }
      if (memberCount < Math.max(12, sampled.length * 0.0025)) continue;
      const area = memberCount / sampled.length;
      const lab = clustered.centers[center];
      const L = lab[0], a = lab[1], b = lab[2];
      const chroma = Math.hypot(a, b);
      const spread = spatialSpread(memberXs, memberYs, width, height);
      let neutral = "color";
      if (chroma < 13 && L > 76) neutral = "light";
      else if (chroma < 15 && L < 31) neutral = "dark";
      else if (chroma < 12) neutral = "neutral";

      let chromaTerm, lightTerm;
      const areaTerm = Math.pow(area, 0.56);
      if (neutral === "color") {
        chromaTerm = 0.70 + 0.55 * Math.min(1, chroma / 52);
        lightTerm = 0.90 + 0.10 * (1 - Math.abs(L - 58) / 58);
      } else if (neutral === "light") {
        chromaTerm = 0.96;
        lightTerm = L > 86 ? 1.11 : 1.02;
      } else if (neutral === "dark") {
        chromaTerm = 0.80;
        lightTerm = 0.82 + 0.55 * Math.min(1, area / 0.12);
      } else {
        chromaTerm = 0.78;
        lightTerm = 0.92;
      }
      const score = areaTerm * chromaTerm * lightTerm * (0.90 + 0.22 * spread);
      candidates.push({
        rgb: labToRgb(lab),
        lab: lab.slice(),
        area,
        chroma,
        spread,
        neutral,
        score,
      });
    }

    candidates.sort((left, right) => right.score - left.score);
    const merged = [];
    for (const candidate of candidates) {
      if (merged.some((item) => deltaE(candidate.lab, item.lab) < 13)) continue;
      merged.push(candidate);
    }
    return roleSelect(merged, nColors).map((item) => ({
      rgb: item.rgb.slice(),
      lab: item.lab.slice(),
      area: item.area,
      chroma: item.chroma,
      spread: item.spread,
      neutralKind: item.neutral,
      family: colorFamily(item.lab, item.neutral),
      score: item.finalScore,
      role: item.role,
    }));
  }

  const api = Object.freeze({
    VERSION,
    extract,
    _core: Object.freeze({
      rgbToLab,
      labToRgb,
      deltaE,
      estimateBackgroundMask,
      weightedKmeans,
      colorFamily,
      roleSelect,
    }),
  });

  root.MinimalizerBrowserFeaturePalette = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
