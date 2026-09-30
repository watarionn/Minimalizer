(function (root) {
  "use strict";

  const VERSION = "browser-fallback-v2";
  const DEFAULTS = Object.freeze({
    analysisMaxSide: 400,
    workMaxSide: 400,
    paletteSize: 12,
    kmeansIterations: 6,
    smoothPasses: 2,
    minComponentRatio: 0.0012,
    maxShapes: 40,
    alphaThreshold: 8,
    contourFidelity: 0.94,
    slicIterations: 10,
    slicTargetMin: 400,
    slicTargetMax: 1200,
    slicMinAverageArea: 64,
    paletteTarget: 8,
    edgeCoverageThreshold: 0.75,
    retryScale: 0.80,
    maxRetryTargetFactor: 2.5,
  });

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function fitSize(width, height, maxSide) {
    if (Math.max(width, height) <= maxSide) {
      return { width, height };
    }
    const scale = maxSide / Math.max(width, height);
    return {
      width: Math.max(1, Math.round(width * scale)),
      height: Math.max(1, Math.round(height * scale)),
    };
  }

  function rgbDistanceSq(a, b) {
    const dr = a[0] - b[0];
    const dg = a[1] - b[1];
    const db = a[2] - b[2];
    return dr * dr + dg * dg + db * db;
  }

  function nearestCenter(rgb, centers) {
    let best = 0;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (let i = 0; i < centers.length; i += 1) {
      const distance = rgbDistanceSq(rgb, centers[i]);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = i;
      }
    }
    return best;
  }

  function buildHistogram(rgba, alphaThreshold) {
    const bins = new Map();
    for (let offset = 0; offset < rgba.length; offset += 4) {
      const alpha = rgba[offset + 3];
      if (alpha <= alphaThreshold) continue;
      const r = rgba[offset];
      const g = rgba[offset + 1];
      const b = rgba[offset + 2];
      const key = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3);
      let entry = bins.get(key);
      if (!entry) {
        entry = { key, count: 0, r: 0, g: 0, b: 0 };
        bins.set(key, entry);
      }
      entry.count += 1;
      entry.r += r;
      entry.g += g;
      entry.b += b;
    }
    return Array.from(bins.values()).map((entry) => ({
      key: entry.key,
      count: entry.count,
      rgb: [
        entry.r / entry.count,
        entry.g / entry.count,
        entry.b / entry.count,
      ],
    }));
  }

  function seedCenters(entries, paletteSize) {
    if (entries.length === 0) return [[255, 255, 255]];
    const ranked = entries
      .slice()
      .sort((left, right) => right.count - left.count || left.key - right.key);
    const candidates = ranked.slice(0, Math.min(256, ranked.length));
    const centers = [candidates[0].rgb.slice()];
    while (centers.length < Math.min(paletteSize, candidates.length)) {
      let winner = null;
      let winnerScore = -1;
      for (const candidate of candidates) {
        let minDistance = Number.POSITIVE_INFINITY;
        for (const center of centers) {
          minDistance = Math.min(minDistance, rgbDistanceSq(candidate.rgb, center));
        }
        const score = minDistance * Math.sqrt(candidate.count);
        if (score > winnerScore) {
          winnerScore = score;
          winner = candidate;
        }
      }
      if (!winner) break;
      if (centers.some((center) => rgbDistanceSq(center, winner.rgb) < 1)) break;
      centers.push(winner.rgb.slice());
    }
    return centers;
  }

  function refineCenters(entries, initialCenters, iterations) {
    let centers = initialCenters.map((center) => center.slice());
    for (let iteration = 0; iteration < iterations; iteration += 1) {
      const sums = centers.map(() => [0, 0, 0, 0]);
      for (const entry of entries) {
        const index = nearestCenter(entry.rgb, centers);
        const sum = sums[index];
        sum[0] += entry.rgb[0] * entry.count;
        sum[1] += entry.rgb[1] * entry.count;
        sum[2] += entry.rgb[2] * entry.count;
        sum[3] += entry.count;
      }
      centers = centers.map((center, index) => {
        const sum = sums[index];
        if (sum[3] <= 0) return center;
        return [sum[0] / sum[3], sum[1] / sum[3], sum[2] / sum[3]];
      });
    }
    return centers.map((center) => center.map((value) => Math.round(clamp(value, 0, 255))));
  }

  function assignLabels(rgba, width, height, centers, alphaThreshold) {
    const labels = new Int16Array(width * height);
    labels.fill(-1);
    for (let index = 0; index < width * height; index += 1) {
      const offset = index * 4;
      if (rgba[offset + 3] <= alphaThreshold) continue;
      labels[index] = nearestCenter(
        [rgba[offset], rgba[offset + 1], rgba[offset + 2]],
        centers,
      );
    }
    return labels;
  }

  function smoothLabels(labels, width, height, paletteSize, passes) {
    let current = labels;
    for (let pass = 0; pass < passes; pass += 1) {
      const next = new Int16Array(current);
      for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
          const index = y * width + x;
          const own = current[index];
          if (own < 0) continue;
          const counts = new Uint8Array(paletteSize);
          for (let dy = -1; dy <= 1; dy += 1) {
            const ny = y + dy;
            if (ny < 0 || ny >= height) continue;
            for (let dx = -1; dx <= 1; dx += 1) {
              const nx = x + dx;
              if (nx < 0 || nx >= width) continue;
              const label = current[ny * width + nx];
              if (label >= 0) counts[label] += 1;
            }
          }
          let winner = own;
          let winnerCount = counts[own];
          for (let label = 0; label < paletteSize; label += 1) {
            if (counts[label] > winnerCount) {
              winner = label;
              winnerCount = counts[label];
            }
          }
          if (winner !== own && winnerCount >= 5) next[index] = winner;
        }
      }
      current = next;
    }
    return current;
  }

  function buildComponents(labels, rgba, width, height) {
    const visited = new Uint8Array(width * height);
    const componentIds = new Int32Array(width * height);
    componentIds.fill(-1);
    const components = [];
    const stack = [];

    for (let start = 0; start < labels.length; start += 1) {
      if (visited[start] || labels[start] < 0) continue;
      const label = labels[start];
      const id = components.length;
      const pixels = [];
      let r = 0;
      let g = 0;
      let b = 0;
      let minX = width;
      let minY = height;
      let maxX = 0;
      let maxY = 0;
      let borderTouches = 0;
      stack.length = 0;
      stack.push(start);
      visited[start] = 1;

      while (stack.length > 0) {
        const index = stack.pop();
        componentIds[index] = id;
        pixels.push(index);
        const x = index % width;
        const y = Math.floor(index / width);
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
        if (x === 0 || y === 0 || x === width - 1 || y === height - 1) borderTouches += 1;

        const offset = index * 4;
        r += rgba[offset];
        g += rgba[offset + 1];
        b += rgba[offset + 2];

        if (x > 0) {
          const next = index - 1;
          if (!visited[next] && labels[next] === label) {
            visited[next] = 1;
            stack.push(next);
          }
        }
        if (x + 1 < width) {
          const next = index + 1;
          if (!visited[next] && labels[next] === label) {
            visited[next] = 1;
            stack.push(next);
          }
        }
        if (y > 0) {
          const next = index - width;
          if (!visited[next] && labels[next] === label) {
            visited[next] = 1;
            stack.push(next);
          }
        }
        if (y + 1 < height) {
          const next = index + width;
          if (!visited[next] && labels[next] === label) {
            visited[next] = 1;
            stack.push(next);
          }
        }
      }

      const count = pixels.length;
      components.push({
        id,
        label,
        pixels,
        count,
        minX,
        minY,
        maxX,
        maxY,
        borderTouches,
        rgb: [Math.round(r / count), Math.round(g / count), Math.round(b / count)],
      });
    }
    return { components, componentIds };
  }

  function mergeTinyComponents(labels, rgba, width, height, minPixels, passes) {
    let current = labels;
    for (let pass = 0; pass < passes; pass += 1) {
      const built = buildComponents(current, rgba, width, height);
      const tiny = built.components.filter((component) => component.count < minPixels);
      if (tiny.length === 0) break;
      const next = new Int16Array(current);
      let changed = false;

      for (const component of tiny) {
        const counts = new Map();
        for (const index of component.pixels) {
          const x = index % width;
          const y = Math.floor(index / width);
          const neighbors = [];
          if (x > 0) neighbors.push(index - 1);
          if (x + 1 < width) neighbors.push(index + 1);
          if (y > 0) neighbors.push(index - width);
          if (y + 1 < height) neighbors.push(index + width);
          for (const neighbor of neighbors) {
            const label = current[neighbor];
            if (label < 0 || label === component.label) continue;
            counts.set(label, (counts.get(label) || 0) + 1);
          }
        }
        let winner = -1;
        let winnerCount = 0;
        for (const [label, count] of counts.entries()) {
          if (count > winnerCount || (count === winnerCount && label < winner)) {
            winner = label;
            winnerCount = count;
          }
        }
        if (winner >= 0) {
          for (const index of component.pixels) next[index] = winner;
          changed = true;
        }
      }
      current = next;
      if (!changed) break;
    }
    return current;
  }

  function pointSegmentDistance(point, start, end) {
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    if (dx === 0 && dy === 0) {
      return Math.hypot(point[0] - start[0], point[1] - start[1]);
    }
    const t = clamp(
      ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy),
      0,
      1,
    );
    return Math.hypot(
      point[0] - (start[0] + t * dx),
      point[1] - (start[1] + t * dy),
    );
  }

  function simplifyOpen(points, epsilon) {
    if (points.length <= 2) return points.slice();
    let maxDistance = 0;
    let maxIndex = 0;
    const start = points[0];
    const end = points[points.length - 1];
    for (let i = 1; i < points.length - 1; i += 1) {
      const distance = pointSegmentDistance(points[i], start, end);
      if (distance > maxDistance) {
        maxDistance = distance;
        maxIndex = i;
      }
    }
    if (maxDistance <= epsilon) return [start, end];
    const left = simplifyOpen(points.slice(0, maxIndex + 1), epsilon);
    const right = simplifyOpen(points.slice(maxIndex), epsilon);
    return left.slice(0, -1).concat(right);
  }

  function simplifyClosed(points, epsilon) {
    if (points.length <= 4) return points.slice();
    let splitIndex = 1;
    let maxDistance = 0;
    for (let i = 1; i < points.length; i += 1) {
      const distance = Math.hypot(points[i][0] - points[0][0], points[i][1] - points[0][1]);
      if (distance > maxDistance) {
        maxDistance = distance;
        splitIndex = i;
      }
    }
    const first = simplifyOpen(points.slice(0, splitIndex + 1), epsilon);
    const second = simplifyOpen(points.slice(splitIndex).concat([points[0]]), epsilon);
    const merged = first.slice(0, -1).concat(second.slice(0, -1));
    return merged.length >= 3 ? merged : points.slice();
  }

  function ringArea(ring) {
    let area = 0;
    for (let i = 0; i < ring.length; i += 1) {
      const next = ring[(i + 1) % ring.length];
      area += ring[i][0] * next[1] - next[0] * ring[i][1];
    }
    return area / 2;
  }

  function pointInRing(x, y, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
      const xi = ring[i][0];
      const yi = ring[i][1];
      const xj = ring[j][0];
      const yj = ring[j][1];
      const intersects = ((yi > y) !== (yj > y))
        && x < ((xj - xi) * (y - yi)) / ((yj - yi) || Number.EPSILON) + xi;
      if (intersects) inside = !inside;
    }
    return inside;
  }

  function pointInRings(x, y, rings) {
    let inside = false;
    for (const ring of rings) {
      if (pointInRing(x, y, ring)) inside = !inside;
    }
    return inside;
  }

  function edgeKey(point) {
    return point[0] + "," + point[1];
  }

  function boundaryRings(component, componentIds, width, height) {
    const edges = [];
    function addEdge(start, end, direction) {
      edges.push({ start, end, direction });
    }

    for (const index of component.pixels) {
      const x = index % width;
      const y = Math.floor(index / width);
      const top = y === 0 || componentIds[index - width] !== component.id;
      const right = x === width - 1 || componentIds[index + 1] !== component.id;
      const bottom = y === height - 1 || componentIds[index + width] !== component.id;
      const left = x === 0 || componentIds[index - 1] !== component.id;
      if (top) addEdge([x, y], [x + 1, y], 0);
      if (right) addEdge([x + 1, y], [x + 1, y + 1], 1);
      if (bottom) addEdge([x + 1, y + 1], [x, y + 1], 2);
      if (left) addEdge([x, y + 1], [x, y], 3);
    }

    edges.sort((a, b) => (
      a.start[1] - b.start[1]
      || a.start[0] - b.start[0]
      || a.direction - b.direction
    ));
    const outgoing = new Map();
    for (let i = 0; i < edges.length; i += 1) {
      const key = edgeKey(edges[i].start);
      if (!outgoing.has(key)) outgoing.set(key, []);
      outgoing.get(key).push(i);
    }
    const used = new Uint8Array(edges.length);
    const rings = [];
    const turnRank = [1, 0, 3, 2];

    function nextEdgeIndex(current) {
      const candidates = outgoing.get(edgeKey(current.end)) || [];
      let best = -1;
      let bestRank = Number.POSITIVE_INFINITY;
      for (const index of candidates) {
        if (used[index]) continue;
        const delta = (edges[index].direction - current.direction + 4) % 4;
        const rank = turnRank.indexOf(delta);
        if (rank < bestRank || (rank === bestRank && index < best)) {
          best = index;
          bestRank = rank;
        }
      }
      return best;
    }

    for (let startIndex = 0; startIndex < edges.length; startIndex += 1) {
      if (used[startIndex]) continue;
      const ring = [];
      let edgeIndex = startIndex;
      const startPoint = edges[startIndex].start;
      let closed = false;
      for (let guard = 0; guard <= edges.length + 1; guard += 1) {
        if (edgeIndex < 0 || used[edgeIndex]) break;
        const edge = edges[edgeIndex];
        used[edgeIndex] = 1;
        if (ring.length === 0) ring.push(edge.start);
        ring.push(edge.end);
        if (edge.end[0] === startPoint[0] && edge.end[1] === startPoint[1]) {
          closed = true;
          break;
        }
        edgeIndex = nextEdgeIndex(edge);
      }
      if (!closed || ring.length < 4) continue;
      ring.pop();
      if (ring.length >= 3 && Math.abs(ringArea(ring)) >= 0.5) rings.push(ring);
    }

    return rings.sort((a, b) => Math.abs(ringArea(b)) - Math.abs(ringArea(a)));
  }

  function componentContourIoU(rings, component, componentIds, width, height) {
    let intersection = 0;
    let union = 0;
    for (let y = component.minY; y <= component.maxY; y += 1) {
      for (let x = component.minX; x <= component.maxX; x += 1) {
        const actual = componentIds[y * width + x] === component.id;
        const predicted = pointInRings(x + 0.5, y + 0.5, rings);
        if (actual && predicted) intersection += 1;
        if (actual || predicted) union += 1;
      }
    }
    return union > 0 ? intersection / union : 1;
  }

  function componentGeometry(component, componentIds, width, height, fidelity) {
    const rawRings = boundaryRings(component, componentIds, width, height);
    if (rawRings.length === 0) {
      const ring = [
        [component.minX, component.minY],
        [component.maxX + 1, component.minY],
        [component.maxX + 1, component.maxY + 1],
        [component.minX, component.maxY + 1],
      ];
      return { polygon: ring, rings: [ring], contourIoU: 1, epsilon: 0 };
    }

    const diagonal = Math.hypot(
      component.maxX - component.minX + 1,
      component.maxY - component.minY + 1,
    );
    let epsilon = Math.max(0.5, diagonal * 0.012);
    let rings = rawRings.map((ring) => simplifyClosed(ring, epsilon));
    let contourIoU = componentContourIoU(rings, component, componentIds, width, height);

    while (contourIoU < fidelity && epsilon > 0.26) {
      epsilon *= 0.5;
      rings = rawRings.map((ring) => simplifyClosed(ring, epsilon));
      contourIoU = componentContourIoU(rings, component, componentIds, width, height);
    }

    const polygon = rings[0] || rawRings[0];
    return { polygon, rings, contourIoU, epsilon };
  }

  function buildComponentAdjacency(built, width, height) {
    const adjacency = built.components.map(() => new Map());
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const id = built.componentIds[index];
        if (id < 0) continue;
        if (x + 1 < width) {
          const right = built.componentIds[index + 1];
          if (right >= 0 && right !== id) {
            adjacency[id].set(right, (adjacency[id].get(right) || 0) + 1);
            adjacency[right].set(id, (adjacency[right].get(id) || 0) + 1);
          }
        }
        if (y + 1 < height) {
          const bottom = built.componentIds[index + width];
          if (bottom >= 0 && bottom !== id) {
            adjacency[id].set(bottom, (adjacency[id].get(bottom) || 0) + 1);
            adjacency[bottom].set(id, (adjacency[bottom].get(id) || 0) + 1);
          }
        }
      }
    }
    return adjacency;
  }

  function chooseGroupMergeTarget(source, groups) {
    let winner = null;
    for (const [targetId, sharedBoundary] of source.adjacency.entries()) {
      const target = groups[targetId];
      if (!target || !target.active || target.id === source.id) continue;
      const distance = rgbDistanceSq(source.rgb, target.rgb);
      const candidate = { target, sharedBoundary, distance };
      if (
        winner === null
        || candidate.sharedBoundary > winner.sharedBoundary
        || (
          candidate.sharedBoundary === winner.sharedBoundary
          && candidate.target.count > winner.target.count
        )
        || (
          candidate.sharedBoundary === winner.sharedBoundary
          && candidate.target.count === winner.target.count
          && candidate.distance < winner.distance
        )
        || (
          candidate.sharedBoundary === winner.sharedBoundary
          && candidate.target.count === winner.target.count
          && candidate.distance === winner.distance
          && candidate.target.id < winner.target.id
        )
      ) {
        winner = candidate;
      }
    }
    if (winner) return winner.target;

    for (const target of groups) {
      if (!target.active || target.id === source.id) continue;
      const distance = rgbDistanceSq(source.rgb, target.rgb);
      const dx = ((source.minX + source.maxX) - (target.minX + target.maxX)) / 2;
      const dy = ((source.minY + source.maxY) - (target.minY + target.maxY)) / 2;
      const spatial = dx * dx + dy * dy;
      const candidate = { target, distance, spatial };
      if (
        winner === null
        || candidate.distance < winner.distance
        || (
          candidate.distance === winner.distance
          && candidate.spatial < winner.spatial
        )
        || (
          candidate.distance === winner.distance
          && candidate.spatial === winner.spatial
          && candidate.target.id < winner.target.id
        )
      ) {
        winner = candidate;
      }
    }
    return winner ? winner.target : null;
  }

  function reduceComponentsToBudget(labels, rgba, width, height, maxShapes) {
    const initial = buildComponents(labels, rgba, width, height);
    if (initial.components.length <= maxShapes) {
      return { labels, built: initial, mergeCount: 0 };
    }

    const adjacency = buildComponentAdjacency(initial, width, height);
    const groups = initial.components.map((component) => ({
      id: component.id,
      active: true,
      label: component.label,
      pixels: component.pixels.slice(),
      count: component.count,
      minX: component.minX,
      minY: component.minY,
      maxX: component.maxX,
      maxY: component.maxY,
      borderTouches: component.borderTouches,
      rgb: component.rgb.slice(),
      adjacency: new Map(adjacency[component.id]),
    }));

    let activeCount = groups.length;
    let mergeCount = 0;
    while (activeCount > maxShapes) {
      const source = groups
        .filter((group) => group.active)
        .sort((a, b) => a.count - b.count || a.borderTouches - b.borderTouches || a.id - b.id)[0];
      if (!source) break;
      const target = chooseGroupMergeTarget(source, groups);
      if (!target) break;

      const total = source.count + target.count;
      target.rgb = [
        Math.round((target.rgb[0] * target.count + source.rgb[0] * source.count) / total),
        Math.round((target.rgb[1] * target.count + source.rgb[1] * source.count) / total),
        Math.round((target.rgb[2] * target.count + source.rgb[2] * source.count) / total),
      ];
      target.count = total;
      target.pixels.push(...source.pixels);
      target.minX = Math.min(target.minX, source.minX);
      target.minY = Math.min(target.minY, source.minY);
      target.maxX = Math.max(target.maxX, source.maxX);
      target.maxY = Math.max(target.maxY, source.maxY);
      target.borderTouches += source.borderTouches;

      target.adjacency.delete(source.id);
      for (const [neighborId, sharedBoundary] of source.adjacency.entries()) {
        if (neighborId === target.id) continue;
        const neighbor = groups[neighborId];
        if (!neighbor || !neighbor.active) continue;
        const combined = (target.adjacency.get(neighborId) || 0) + sharedBoundary;
        target.adjacency.set(neighborId, combined);
        neighbor.adjacency.delete(source.id);
        neighbor.adjacency.set(target.id, combined);
      }

      source.active = false;
      source.adjacency.clear();
      activeCount -= 1;
      mergeCount += 1;
    }

    const active = groups
      .filter((group) => group.active)
      .sort((a, b) => a.id - b.id);
    const componentIds = new Int32Array(width * height);
    componentIds.fill(-1);
    const finalLabels = new Int16Array(width * height);
    finalLabels.fill(-1);
    const components = active.map((group, index) => {
      for (const pixel of group.pixels) {
        componentIds[pixel] = index;
        finalLabels[pixel] = index;
      }
      return {
        id: index,
        label: index,
        pixels: group.pixels,
        count: group.count,
        minX: group.minX,
        minY: group.minY,
        maxX: group.maxX,
        maxY: group.maxY,
        borderTouches: group.borderTouches,
        rgb: group.rgb,
      };
    });

    return {
      labels: finalLabels,
      built: { components, componentIds },
      mergeCount,
    };
  }

  function borderColor(rgba, width, height, alphaThreshold) {
    let r = 0;
    let g = 0;
    let b = 0;
    let count = 0;
    function add(index) {
      const offset = index * 4;
      if (rgba[offset + 3] <= alphaThreshold) return;
      r += rgba[offset];
      g += rgba[offset + 1];
      b += rgba[offset + 2];
      count += 1;
    }
    for (let x = 0; x < width; x += 1) {
      add(x);
      if (height > 1) add((height - 1) * width + x);
    }
    for (let y = 1; y + 1 < height; y += 1) {
      add(y * width);
      if (width > 1) add(y * width + width - 1);
    }
    if (count === 0) return [255, 255, 255];
    return [Math.round(r / count), Math.round(g / count), Math.round(b / count)];
  }

  function srgbChannelToLinear(value) {
    const normalized = value / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  }

  function labPivot(value) {
    const delta = 6 / 29;
    const threshold = delta * delta * delta;
    if (value > threshold) return Math.cbrt(value);
    return value / (3 * delta * delta) + 4 / 29;
  }

  function rgbToLab(r, g, b) {
    const lr = srgbChannelToLinear(r);
    const lg = srgbChannelToLinear(g);
    const lb = srgbChannelToLinear(b);
    const x = (0.4124564 * lr + 0.3575761 * lg + 0.1804375 * lb) / 0.95047;
    const y = 0.2126729 * lr + 0.7151522 * lg + 0.0721750 * lb;
    const z = (0.0193339 * lr + 0.1191920 * lg + 0.9503041 * lb) / 1.08883;
    const fx = labPivot(x);
    const fy = labPivot(y);
    const fz = labPivot(z);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }

  function rgbaToLab(rgba, width, height) {
    const lab = new Float32Array(width * height * 3);
    for (let index = 0; index < width * height; index += 1) {
      const offset = index * 4;
      const converted = rgbToLab(rgba[offset], rgba[offset + 1], rgba[offset + 2]);
      lab[index * 3] = converted[0];
      lab[index * 3 + 1] = converted[1];
      lab[index * 3 + 2] = converted[2];
    }
    return lab;
  }

  function structuralEdgeMap(lab, width, height) {
    const edge = new Float32Array(width * height);
    let maximum = 0;
    function lightness(x, y) {
      const cx = clamp(x, 0, width - 1);
      const cy = clamp(y, 0, height - 1);
      return lab[(cy * width + cx) * 3];
    }
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const gx = (
          -lightness(x - 1, y - 1) + lightness(x + 1, y - 1)
          - 2 * lightness(x - 1, y) + 2 * lightness(x + 1, y)
          - lightness(x - 1, y + 1) + lightness(x + 1, y + 1)
        );
        const gy = (
          -lightness(x - 1, y - 1) - 2 * lightness(x, y - 1) - lightness(x + 1, y - 1)
          + lightness(x - 1, y + 1) + 2 * lightness(x, y + 1) + lightness(x + 1, y + 1)
        );
        const magnitude = Math.hypot(gx, gy);
        edge[y * width + x] = magnitude;
        maximum = Math.max(maximum, magnitude);
      }
    }
    if (maximum > 1e-9) {
      for (let i = 0; i < edge.length; i += 1) edge[i] /= maximum;
    }
    return edge;
  }

  function targetSuperpixelCount(width, height, config) {
    const area = width * height;
    const requested = clamp(
      Math.round(area / 900),
      config.slicTargetMin,
      config.slicTargetMax,
    );
    const areaLimited = Math.max(1, Math.floor(area / config.slicMinAverageArea));
    return Math.max(1, Math.min(requested, areaLimited));
  }

  function regionSizeForTarget(width, height, targetCount) {
    return Math.max(1, Math.round(Math.sqrt((width * height) / targetCount)));
  }

  function moveCenterToLowEdge(y, x, edge, width, height) {
    let bestX = x;
    let bestY = y;
    let bestValue = Number.POSITIVE_INFINITY;
    for (let dy = -1; dy <= 1; dy += 1) {
      const ny = y + dy;
      if (ny < 0 || ny >= height) continue;
      for (let dx = -1; dx <= 1; dx += 1) {
        const nx = x + dx;
        if (nx < 0 || nx >= width) continue;
        const value = edge[ny * width + nx];
        if (
          value < bestValue
          || (value === bestValue && (ny < bestY || (ny === bestY && nx < bestX)))
        ) {
          bestValue = value;
          bestX = nx;
          bestY = ny;
        }
      }
    }
    return [bestY, bestX];
  }

  function initialSlicoCenters(lab, edge, width, height, regionSize) {
    const centers = [];
    const offset = Math.max(0, Math.floor(regionSize / 2));
    const ys = [];
    const xs = [];
    for (let y = offset; y < height; y += regionSize) ys.push(y);
    for (let x = offset; x < width; x += regionSize) xs.push(x);
    if (ys.length === 0) ys.push(Math.floor(height / 2));
    if (xs.length === 0) xs.push(Math.floor(width / 2));
    for (const y of ys) {
      for (const x of xs) {
        const moved = moveCenterToLowEdge(y, x, edge, width, height);
        const cy = moved[0];
        const cx = moved[1];
        const offsetLab = (cy * width + cx) * 3;
        centers.push({
          l: lab[offsetLab],
          a: lab[offsetLab + 1],
          b: lab[offsetLab + 2],
          y: cy,
          x: cx,
          colorScale: 5000,
        });
      }
    }
    return centers;
  }

  function splitDisconnectedLabelsJs(labels, width, height) {
    const output = new Int32Array(labels.length);
    output.fill(-1);
    let nextId = 0;
    const queue = new Int32Array(labels.length);
    for (let start = 0; start < labels.length; start += 1) {
      if (output[start] >= 0) continue;
      const sourceLabel = labels[start];
      let head = 0;
      let tail = 0;
      queue[tail++] = start;
      output[start] = nextId;
      while (head < tail) {
        const index = queue[head++];
        const x = index % width;
        const y = Math.floor(index / width);
        if (x > 0) {
          const neighbor = index - 1;
          if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
            output[neighbor] = nextId;
            queue[tail++] = neighbor;
          }
        }
        if (x + 1 < width) {
          const neighbor = index + 1;
          if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
            output[neighbor] = nextId;
            queue[tail++] = neighbor;
          }
        }
        if (y > 0) {
          const neighbor = index - width;
          if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
            output[neighbor] = nextId;
            queue[tail++] = neighbor;
          }
        }
        if (y + 1 < height) {
          const neighbor = index + width;
          if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
            output[neighbor] = nextId;
            queue[tail++] = neighbor;
          }
        }
      }
      nextId += 1;
    }
    return { labels: output, regionCount: nextId };
  }

  function runSlicoLite(lab, edge, width, height, regionSize, iterations) {
    let centers = initialSlicoCenters(lab, edge, width, height, regionSize);
    const clusterCount = centers.length;
    const labels = new Int32Array(width * height);
    const distances = new Float32Array(width * height);
    const spatialScale = Math.max(regionSize * regionSize, 1);

    for (let iteration = 0; iteration < iterations; iteration += 1) {
      labels.fill(-1);
      distances.fill(Number.POSITIVE_INFINITY);

      for (let clusterId = 0; clusterId < clusterCount; clusterId += 1) {
        const center = centers[clusterId];
        const y0 = Math.max(0, Math.floor(center.y - regionSize));
        const y1 = Math.min(height - 1, Math.ceil(center.y + regionSize));
        const x0 = Math.max(0, Math.floor(center.x - regionSize));
        const x1 = Math.min(width - 1, Math.ceil(center.x + regionSize));
        for (let y = y0; y <= y1; y += 1) {
          for (let x = x0; x <= x1; x += 1) {
            const index = y * width + x;
            const offsetLab = index * 3;
            const dl = lab[offsetLab] - center.l;
            const da = lab[offsetLab + 1] - center.a;
            const db = lab[offsetLab + 2] - center.b;
            const dc2 = dl * dl + da * da + db * db;
            const dy = y - center.y;
            const dx = x - center.x;
            const ds2 = dy * dy + dx * dx;
            const distance = dc2 / Math.max(center.colorScale, 1) + ds2 / spatialScale;
            if (distance < distances[index]) {
              distances[index] = distance;
              labels[index] = clusterId;
            }
          }
        }
      }

      for (let index = 0; index < labels.length; index += 1) {
        if (labels[index] >= 0) continue;
        const x = index % width;
        const y = Math.floor(index / width);
        let winner = 0;
        let winnerDistance = Number.POSITIVE_INFINITY;
        for (let clusterId = 0; clusterId < clusterCount; clusterId += 1) {
          const center = centers[clusterId];
          const spatial = (x - center.x) ** 2 + (y - center.y) ** 2;
          if (spatial < winnerDistance) {
            winner = clusterId;
            winnerDistance = spatial;
          }
        }
        labels[index] = winner;
      }

      const counts = new Int32Array(clusterCount);
      const sums = Array.from({ length: clusterCount }, () => [0, 0, 0, 0, 0]);
      for (let index = 0; index < labels.length; index += 1) {
        const clusterId = labels[index];
        const x = index % width;
        const y = Math.floor(index / width);
        const offsetLab = index * 3;
        counts[clusterId] += 1;
        sums[clusterId][0] += lab[offsetLab];
        sums[clusterId][1] += lab[offsetLab + 1];
        sums[clusterId][2] += lab[offsetLab + 2];
        sums[clusterId][3] += y;
        sums[clusterId][4] += x;
      }

      centers = centers.map((center, clusterId) => {
        const count = counts[clusterId];
        if (count <= 0) return center;
        return {
          l: sums[clusterId][0] / count,
          a: sums[clusterId][1] / count,
          b: sums[clusterId][2] / count,
          y: sums[clusterId][3] / count,
          x: sums[clusterId][4] / count,
          colorScale: 5000,
        };
      });

      const colorScales = new Float32Array(clusterCount);
      colorScales.fill(5000);
      for (let index = 0; index < labels.length; index += 1) {
        const clusterId = labels[index];
        const center = centers[clusterId];
        const offsetLab = index * 3;
        const dl = lab[offsetLab] - center.l;
        const da = lab[offsetLab + 1] - center.a;
        const db = lab[offsetLab + 2] - center.b;
        const dc2 = dl * dl + da * da + db * db;
        if (dc2 > colorScales[clusterId]) colorScales[clusterId] = dc2;
      }
      centers = centers.map((center, clusterId) => ({
        ...center,
        colorScale: Math.max(5000, colorScales[clusterId]),
      }));
    }

    return splitDisconnectedLabelsJs(labels, width, height);
  }

  function oversegmentSpatial(lab, edge, width, height, config) {
    const targetCount = targetSuperpixelCount(width, height, config);
    const regionSize = regionSizeForTarget(width, height, targetCount);
    const initial = runSlicoLite(
      lab,
      edge,
      width,
      height,
      regionSize,
      config.slicIterations,
    );
    const initialCoverage = structuralEdgeCoverageJs(
      initial.labels,
      edge,
      width,
      height,
    );

    if (initialCoverage >= config.edgeCoverageThreshold || regionSize <= 1) {
      return {
        ...initial,
        targetCount,
        regionSize,
        edgeCoverage: initialCoverage,
        retried: false,
        initialEdgeCoverage: initialCoverage,
      };
    }

    let retrySize = Math.max(1, Math.round(regionSize * config.retryScale));
    if (retrySize >= regionSize) retrySize = regionSize - 1;
    const retry = runSlicoLite(
      lab,
      edge,
      width,
      height,
      retrySize,
      config.slicIterations,
    );
    const retryCoverage = structuralEdgeCoverageJs(
      retry.labels,
      edge,
      width,
      height,
    );
    const countLimit = Math.max(
      initial.regionCount,
      Math.ceil(targetCount * config.maxRetryTargetFactor),
    );
    const keepRetry = (
      retryCoverage > initialCoverage
      && retry.regionCount <= countLimit
    );
    if (keepRetry) {
      return {
        ...retry,
        targetCount,
        regionSize: retrySize,
        edgeCoverage: retryCoverage,
        retried: true,
        initialRegionCountBeforeRetry: initial.regionCount,
        initialEdgeCoverage: initialCoverage,
      };
    }
    return {
      ...initial,
      targetCount,
      regionSize,
      edgeCoverage: initialCoverage,
      retried: false,
      initialRegionCountBeforeRetry: initial.regionCount,
      initialEdgeCoverage: initialCoverage,
    };
  }

  function labelBoundaryMask(labels, width, height) {
    const boundary = new Uint8Array(labels.length);
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        if (x + 1 < width && labels[index] !== labels[index + 1]) {
          boundary[index] = 1;
          boundary[index + 1] = 1;
        }
        if (y + 1 < height && labels[index] !== labels[index + width]) {
          boundary[index] = 1;
          boundary[index + width] = 1;
        }
      }
    }
    return boundary;
  }

  function structuralEdgeCoverageJs(labels, edge, width, height) {
    let total = 0;
    let covered = 0;
    const boundary = labelBoundaryMask(labels, width, height);
    for (let index = 0; index < edge.length; index += 1) {
      const weight = edge[index];
      total += weight;
      if (weight <= 0) continue;
      const x = index % width;
      const y = Math.floor(index / width);
      let near = false;
      for (let dy = -1; dy <= 1 && !near; dy += 1) {
        const ny = y + dy;
        if (ny < 0 || ny >= height) continue;
        for (let dx = -1; dx <= 1; dx += 1) {
          const nx = x + dx;
          if (nx < 0 || nx >= width) continue;
          if (boundary[ny * width + nx]) {
            near = true;
            break;
          }
        }
      }
      if (near) covered += weight;
    }
    return total > 1e-12 ? covered / total : 1;
  }

  function buildSpatialGroups(labels, rgba, lab, edge, width, height) {
    let maxLabel = -1;
    for (let index = 0; index < labels.length; index += 1) {
      if (labels[index] > maxLabel) maxLabel = labels[index];
    }
    const regionCount = maxLabel + 1;
    const groups = Array.from({ length: regionCount }, (_, id) => ({
      id,
      active: true,
      pixels: [],
      count: 0,
      minX: width,
      minY: height,
      maxX: 0,
      maxY: 0,
      borderTouches: 0,
      perimeter: 0,
      rgbSum: [0, 0, 0],
      labSum: [0, 0, 0],
      rgb: [0, 0, 0],
      lab: [0, 0, 0],
      adjacency: new Map(),
    }));

    for (let index = 0; index < labels.length; index += 1) {
      const id = labels[index];
      const group = groups[id];
      const x = index % width;
      const y = Math.floor(index / width);
      const offsetRgba = index * 4;
      const offsetLab = index * 3;
      group.pixels.push(index);
      group.count += 1;
      group.minX = Math.min(group.minX, x);
      group.minY = Math.min(group.minY, y);
      group.maxX = Math.max(group.maxX, x);
      group.maxY = Math.max(group.maxY, y);
      if (x === 0 || y === 0 || x === width - 1 || y === height - 1) group.borderTouches += 1;
      group.rgbSum[0] += rgba[offsetRgba];
      group.rgbSum[1] += rgba[offsetRgba + 1];
      group.rgbSum[2] += rgba[offsetRgba + 2];
      group.labSum[0] += lab[offsetLab];
      group.labSum[1] += lab[offsetLab + 1];
      group.labSum[2] += lab[offsetLab + 2];
    }

    for (const group of groups) {
      group.rgb = group.rgbSum.map((sum) => Math.round(sum / Math.max(group.count, 1)));
      group.lab = group.labSum.map((sum) => sum / Math.max(group.count, 1));
      group.perimeter = group.count * 4;
    }

    function addAdjacency(a, b, edgeValue) {
      if (a === b) return;
      const map = groups[a].adjacency;
      let item = map.get(b);
      if (!item) {
        item = { shared: 0, edgeSum: 0 };
        map.set(b, item);
      }
      item.shared += 1;
      item.edgeSum += edgeValue;
    }

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const id = labels[index];
        if (x + 1 < width) {
          const other = labels[index + 1];
          if (other === id) {
            groups[id].perimeter -= 2;
          } else {
            const edgeValue = (edge[index] + edge[index + 1]) * 0.5;
            addAdjacency(id, other, edgeValue);
            addAdjacency(other, id, edgeValue);
          }
        }
        if (y + 1 < height) {
          const other = labels[index + width];
          if (other === id) {
            groups[id].perimeter -= 2;
          } else {
            const edgeValue = (edge[index] + edge[index + width]) * 0.5;
            addAdjacency(id, other, edgeValue);
            addAdjacency(other, id, edgeValue);
          }
        }
      }
    }
    return groups;
  }

  function spatialMergeCost(left, right, relation, imageArea) {
    const dl = left.lab[0] - right.lab[0];
    const da = left.lab[1] - right.lab[1];
    const db = left.lab[2] - right.lab[2];
    const deltaE = Math.hypot(dl, da, db);
    const colorCost = 1 - Math.exp(-(deltaE * deltaE) / (25 * 25));
    const boundaryCost = clamp(relation.edgeSum / Math.max(relation.shared, 1), 0, 1);
    const sharedRatio = clamp(
      relation.shared / Math.max(1, Math.min(left.perimeter, right.perimeter)),
      0,
      1,
    );
    const topologyCost = clamp(Math.exp(-sharedRatio / 0.15), 0, 1);
    const smallerRatio = Math.min(left.count, right.count) / imageArea;
    const majorProtection = 0.20 * Math.min(1, smallerRatio / 0.03);
    const smallness = Math.exp(-smallerRatio / 0.01);
    const redundancy = (
      smallness
      * (1 - colorCost)
      * (1 - boundaryCost)
      * Math.min(1, sharedRatio / 0.50)
    );
    return (
      0.30 * colorCost
      + 0.25 * boundaryCost
      + 0.10 * topologyCost
      + majorProtection
      - 0.15 * redundancy
    );
  }

  function mergeSpatialGroupsToBudget(groups, width, height, maxShapes) {
    let activeCount = groups.length;
    let mergeCount = 0;
    const imageArea = width * height;

    while (activeCount > maxShapes) {
      let best = null;
      for (const left of groups) {
        if (!left.active) continue;
        for (const [rightId, relation] of left.adjacency.entries()) {
          if (rightId <= left.id) continue;
          const right = groups[rightId];
          if (!right || !right.active) continue;
          const cost = spatialMergeCost(left, right, relation, imageArea);
          const smallerCount = Math.min(left.count, right.count);
          const candidate = { left, right, relation, cost, smallerCount };
          if (
            best === null
            || candidate.cost < best.cost
            || (
              candidate.cost === best.cost
              && candidate.smallerCount < best.smallerCount
            )
            || (
              candidate.cost === best.cost
              && candidate.smallerCount === best.smallerCount
              && candidate.left.id < best.left.id
            )
            || (
              candidate.cost === best.cost
              && candidate.smallerCount === best.smallerCount
              && candidate.left.id === best.left.id
              && candidate.right.id < best.right.id
            )
          ) {
            best = candidate;
          }
        }
      }
      if (!best) break;

      const left = best.left;
      const right = best.right;
      const target = left.count >= right.count ? left : right;
      const source = target === left ? right : left;
      const total = target.count + source.count;

      target.rgb = [
        Math.round((target.rgb[0] * target.count + source.rgb[0] * source.count) / total),
        Math.round((target.rgb[1] * target.count + source.rgb[1] * source.count) / total),
        Math.round((target.rgb[2] * target.count + source.rgb[2] * source.count) / total),
      ];
      target.lab = [
        (target.lab[0] * target.count + source.lab[0] * source.count) / total,
        (target.lab[1] * target.count + source.lab[1] * source.count) / total,
        (target.lab[2] * target.count + source.lab[2] * source.count) / total,
      ];
      target.count = total;
      target.pixels.push(...source.pixels);
      target.minX = Math.min(target.minX, source.minX);
      target.minY = Math.min(target.minY, source.minY);
      target.maxX = Math.max(target.maxX, source.maxX);
      target.maxY = Math.max(target.maxY, source.maxY);
      target.borderTouches += source.borderTouches;
      target.perimeter = target.perimeter + source.perimeter - 2 * best.relation.shared;

      target.adjacency.delete(source.id);
      for (const [neighborId, relation] of source.adjacency.entries()) {
        if (neighborId === target.id) continue;
        const neighbor = groups[neighborId];
        if (!neighbor || !neighbor.active) continue;
        const existing = target.adjacency.get(neighborId) || { shared: 0, edgeSum: 0 };
        const combined = {
          shared: existing.shared + relation.shared,
          edgeSum: existing.edgeSum + relation.edgeSum,
        };
        target.adjacency.set(neighborId, combined);
        neighbor.adjacency.delete(source.id);
        neighbor.adjacency.set(target.id, combined);
      }
      source.active = false;
      source.adjacency.clear();
      activeCount -= 1;
      mergeCount += 1;
    }

    const active = groups.filter((group) => group.active).sort((a, b) => a.id - b.id);
    const labels = new Int32Array(width * height);
    labels.fill(-1);
    const components = active.map((group, id) => {
      for (const pixel of group.pixels) labels[pixel] = id;
      return {
        id,
        label: id,
        pixels: group.pixels,
        count: group.count,
        minX: group.minX,
        minY: group.minY,
        maxX: group.maxX,
        maxY: group.maxY,
        borderTouches: group.borderTouches,
        rgb: group.rgb,
        lab: group.lab,
      };
    });

    return {
      labels,
      built: { components, componentIds: labels },
      groups: components,
      mergeCount,
    };
  }

  function consolidateShapePalette(groups, targetCount) {
    if (groups.length === 0) return { colors: [], assignments: [], palette: [] };
    const count = Math.max(1, Math.min(targetCount, groups.length));
    const ranked = groups
      .slice()
      .sort((a, b) => b.count - a.count || a.id - b.id);
    const centers = [ranked[0].lab.slice()];

    while (centers.length < count) {
      let winner = null;
      let winnerScore = -1;
      for (const group of ranked) {
        let minDistance = Number.POSITIVE_INFINITY;
        for (const center of centers) {
          minDistance = Math.min(
            minDistance,
            Math.hypot(
              group.lab[0] - center[0],
              group.lab[1] - center[1],
              group.lab[2] - center[2],
            ),
          );
        }
        const score = minDistance * Math.sqrt(group.count);
        if (score > winnerScore) {
          winnerScore = score;
          winner = group;
        }
      }
      if (!winner) break;
      centers.push(winner.lab.slice());
    }

    let refined = centers;
    for (let iteration = 0; iteration < 6; iteration += 1) {
      const sums = refined.map(() => [0, 0, 0, 0]);
      for (const group of groups) {
        let best = 0;
        let bestDistance = Number.POSITIVE_INFINITY;
        for (let i = 0; i < refined.length; i += 1) {
          const distance = Math.hypot(
            group.lab[0] - refined[i][0],
            group.lab[1] - refined[i][1],
            group.lab[2] - refined[i][2],
          );
          if (distance < bestDistance) {
            bestDistance = distance;
            best = i;
          }
        }
        sums[best][0] += group.lab[0] * group.count;
        sums[best][1] += group.lab[1] * group.count;
        sums[best][2] += group.lab[2] * group.count;
        sums[best][3] += group.count;
      }
      refined = refined.map((center, i) => (
        sums[i][3] > 0
          ? [sums[i][0] / sums[i][3], sums[i][1] / sums[i][3], sums[i][2] / sums[i][3]]
          : center
      ));
    }

    const palette = refined.map((center, paletteId) => {
      let representative = groups[0];
      let bestDistance = Number.POSITIVE_INFINITY;
      for (const group of groups) {
        const distance = Math.hypot(
          group.lab[0] - center[0],
          group.lab[1] - center[1],
          group.lab[2] - center[2],
        );
        if (
          distance < bestDistance
          || (distance === bestDistance && group.count > representative.count)
          || (
            distance === bestDistance
            && group.count === representative.count
            && group.id < representative.id
          )
        ) {
          representative = group;
          bestDistance = distance;
        }
      }
      return { id: paletteId, lab: center, rgb: representative.rgb.slice() };
    });

    const assignments = groups.map((group) => {
      let best = 0;
      let bestDistance = Number.POSITIVE_INFINITY;
      for (let i = 0; i < palette.length; i += 1) {
        const distance = Math.hypot(
          group.lab[0] - palette[i].lab[0],
          group.lab[1] - palette[i].lab[1],
          group.lab[2] - palette[i].lab[2],
        );
        if (distance < bestDistance) {
          bestDistance = distance;
          best = i;
        }
      }
      return best;
    });

    return {
      palette,
      assignments,
      colors: assignments.map((id) => palette[id].rgb.slice()),
    };
  }

  function analyzeRgba(rgba, width, height, options) {
    const config = Object.assign({}, DEFAULTS, options || {});
    const lab = rgbaToLab(rgba, width, height);
    const edge = structuralEdgeMap(lab, width, height);
    const segmented = oversegmentSpatial(
      lab,
      edge,
      width,
      height,
      config,
    );
    const targetCount = segmented.targetCount;
    const regionSize = segmented.regionSize;
    const edgeCoverage = segmented.edgeCoverage;
    const initialGroups = buildSpatialGroups(
      segmented.labels,
      rgba,
      lab,
      edge,
      width,
      height,
    );
    const reduced = mergeSpatialGroupsToBudget(
      initialGroups,
      width,
      height,
      config.maxShapes,
    );
    const palette = consolidateShapePalette(reduced.groups, config.paletteTarget);

    let contourIoUSum = 0;
    let vertexCount = 0;
    const shapes = reduced.built.components.map((component, index) => {
      const geometry = componentGeometry(
        component,
        reduced.built.componentIds,
        width,
        height,
        config.contourFidelity,
      );
      contourIoUSum += geometry.contourIoU;
      vertexCount += geometry.rings.reduce((sum, ring) => sum + ring.length, 0);
      return {
        id: component.id,
        count: component.count,
        sourceRgb: component.rgb,
        rgb: palette.colors[index] || component.rgb,
        paletteId: palette.assignments[index] ?? 0,
        borderTouches: component.borderTouches,
        polygon: geometry.polygon,
        rings: geometry.rings,
        contourIoU: geometry.contourIoU,
        contourEpsilon: geometry.epsilon,
      };
    });

    return {
      version: VERSION,
      centers: palette.palette.map((entry) => entry.rgb),
      shapes,
      background: borderColor(rgba, width, height, config.alphaThreshold),
      metrics: {
        targetSuperpixels: targetCount,
        regionSize,
        initialRegionCount: segmented.regionCount,
        edgeCoverage,
        budgetMergeCount: reduced.mergeCount,
        componentCount: reduced.built.components.length,
        paletteCount: palette.palette.length,
        retried: segmented.retried,
        initialEdgeCoverage: segmented.initialEdgeCoverage,
        initialRegionCountBeforeRetry: segmented.initialRegionCountBeforeRetry ?? segmented.regionCount,
        meanContourIoU: shapes.length > 0 ? contourIoUSum / shapes.length : 1,
        vertexCount,
      },
    };
  }

  function canvasElement(width, height) {
    if (typeof document !== "undefined" && typeof document.createElement === "function") {
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      return canvas;
    }
    if (typeof OffscreenCanvas !== "undefined") {
      return new OffscreenCanvas(width, height);
    }
    throw new Error("Canvas is unavailable.");
  }

  function context2d(canvas) {
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) throw new Error("2D canvas is unavailable.");
    return context;
  }

  async function decodeFile(file) {
    if (typeof createImageBitmap === "function") {
      return await createImageBitmap(file);
    }
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

  function renderAnalysis(analysis, analysisWidth, analysisHeight, workWidth, workHeight) {
    const outputCanvas = canvasElement(analysisWidth, analysisHeight);
    const outputContext = context2d(outputCanvas);
    outputContext.fillStyle = "rgb(255,255,255)";
    outputContext.fillRect(0, 0, analysisWidth, analysisHeight);

    const scaleX = analysisWidth / workWidth;
    const scaleY = analysisHeight / workHeight;
    const shapes = analysis.shapes
      .slice()
      .sort((left, right) => right.count - left.count || left.id - right.id);
    for (const shape of shapes) {
      const rings = shape.rings && shape.rings.length > 0 ? shape.rings : [shape.polygon];
      outputContext.beginPath();
      for (const ring of rings) {
        if (!ring || ring.length < 3) continue;
        outputContext.moveTo(ring[0][0] * scaleX, ring[0][1] * scaleY);
        for (let i = 1; i < ring.length; i += 1) {
          outputContext.lineTo(ring[i][0] * scaleX, ring[i][1] * scaleY);
        }
        outputContext.closePath();
      }
      outputContext.fillStyle = "rgb(" + shape.rgb[0] + "," + shape.rgb[1] + "," + shape.rgb[2] + ")";
      outputContext.fill("evenodd");
    }
    return { canvas: outputCanvas, shapes };
  }

  async function canvasToBlob(canvas) {
    if (typeof canvas.convertToBlob === "function") {
      return await canvas.convertToBlob({ type: "image/png" });
    }
    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error("PNG encoding failed."));
      }, "image/png");
    });
  }

  async function minimalizeFile(file, options) {
    const started = performance.now();
    const config = Object.assign({}, DEFAULTS, options || {});
    const image = await decodeFile(file);
    const analysisSize = fitSize(image.width, image.height, config.analysisMaxSide);
    const analysisCanvas = canvasElement(analysisSize.width, analysisSize.height);
    const analysisContext = context2d(analysisCanvas);
    analysisContext.clearRect(0, 0, analysisSize.width, analysisSize.height);
    analysisContext.drawImage(image, 0, 0, analysisSize.width, analysisSize.height);
    if (typeof image.close === "function") image.close();

    const workSize = fitSize(analysisSize.width, analysisSize.height, config.workMaxSide);
    const workCanvas = canvasElement(workSize.width, workSize.height);
    const workContext = context2d(workCanvas);
    workContext.drawImage(analysisCanvas, 0, 0, workSize.width, workSize.height);
    const workImage = workContext.getImageData(0, 0, workSize.width, workSize.height);
    const analysis = analyzeRgba(
      workImage.data,
      workSize.width,
      workSize.height,
      config,
    );

    const rendered = renderAnalysis(
      analysis,
      analysisSize.width,
      analysisSize.height,
      workSize.width,
      workSize.height,
    );
    const outputCanvas = rendered.canvas;
    const shapes = rendered.shapes;
    const blob = await canvasToBlob(outputCanvas);
    const elapsed = performance.now() - started;
    const headers = new Headers({
      "Content-Type": "image/png",
      "X-Minimalizer-Mode": VERSION,
      "X-Minimalizer-Compute": "browser",
      "X-Minimalizer-Analysis": "deterministic-js",
      "X-Minimalizer-Shape-Count": String(shapes.length),
      "X-Minimalizer-Analysis-Size": analysisSize.width + "x" + analysisSize.height,
      "X-Minimalizer-Processing-Ms": elapsed.toFixed(1),
      "X-Minimalizer-Browser-Fallback-Version": VERSION,
      "X-Minimalizer-Contour-IoU": analysis.metrics.meanContourIoU.toFixed(4),
      "X-Minimalizer-Budget-Merges": String(analysis.metrics.budgetMergeCount),
      "X-Minimalizer-Superpixel-Count": String(analysis.metrics.initialRegionCount),
      "X-Minimalizer-Edge-Coverage": analysis.metrics.edgeCoverage.toFixed(4),
      "X-Minimalizer-Palette-Count": String(analysis.metrics.paletteCount),
      "X-Minimalizer-SLIC-Retried": analysis.metrics.retried ? "1" : "0",
    });
    return {
      response: new Response(blob, { status: 200, headers }),
      metadata: {
        version: VERSION,
        width: analysisSize.width,
        height: analysisSize.height,
        workWidth: workSize.width,
        workHeight: workSize.height,
        shapeCount: shapes.length,
        processingMs: elapsed,
        meanContourIoU: analysis.metrics.meanContourIoU,
        budgetMergeCount: analysis.metrics.budgetMergeCount,
        vertexCount: analysis.metrics.vertexCount,
        initialRegionCount: analysis.metrics.initialRegionCount,
        edgeCoverage: analysis.metrics.edgeCoverage,
        paletteCount: analysis.metrics.paletteCount,
        regionSize: analysis.metrics.regionSize,
        retried: analysis.metrics.retried,
        initialEdgeCoverage: analysis.metrics.initialEdgeCoverage,
      },
    };
  }

  const api = Object.freeze({
    VERSION,
    DEFAULTS,
    minimalizeFile,
    _core: Object.freeze({
      fitSize,
      buildHistogram,
      seedCenters,
      refineCenters,
      assignLabels,
      smoothLabels,
      mergeTinyComponents,
      buildComponents,
      simplifyClosed,
      boundaryRings,
      componentGeometry,
      reduceComponentsToBudget,
      rgbToLab,
      rgbaToLab,
      structuralEdgeMap,
      targetSuperpixelCount,
      regionSizeForTarget,
      runSlicoLite,
      oversegmentSpatial,
      splitDisconnectedLabelsJs,
      structuralEdgeCoverageJs,
      buildSpatialGroups,
      mergeSpatialGroupsToBudget,
      consolidateShapePalette,
      analyzeRgba,
      renderAnalysis,
    }),
  });

  root.MinimalizerBrowserFallback = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof window !== "undefined" ? window : globalThis));
