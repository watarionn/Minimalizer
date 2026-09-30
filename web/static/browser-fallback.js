(function (root) {
  "use strict";

  const VERSION = "browser-fallback-v1";
  const DEFAULTS = Object.freeze({
    analysisMaxSide: 400,
    workMaxSide: 192,
    paletteSize: 12,
    kmeansIterations: 6,
    smoothPasses: 2,
    minComponentRatio: 0.0012,
    maxShapes: 40,
    alphaThreshold: 8,
    contourFidelity: 0.94,
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

  function analyzeRgba(rgba, width, height, options) {
    const config = Object.assign({}, DEFAULTS, options || {});
    const entries = buildHistogram(rgba, config.alphaThreshold);
    const centers = refineCenters(
      entries,
      seedCenters(entries, config.paletteSize),
      config.kmeansIterations,
    );
    let labels = assignLabels(rgba, width, height, centers, config.alphaThreshold);
    labels = smoothLabels(labels, width, height, centers.length, config.smoothPasses);
    const minPixels = Math.max(2, Math.round(width * height * config.minComponentRatio));
    labels = mergeTinyComponents(labels, rgba, width, height, minPixels, 2);

    const reduced = reduceComponentsToBudget(
      labels,
      rgba,
      width,
      height,
      config.maxShapes,
    );
    const built = reduced.built;
    const ranked = built.components
      .slice()
      .sort((left, right) => right.count - left.count || right.borderTouches - left.borderTouches || left.id - right.id);

    let contourIoUSum = 0;
    let vertexCount = 0;
    const shapes = ranked.map((component) => {
      const geometry = componentGeometry(
        component,
        built.componentIds,
        width,
        height,
        config.contourFidelity,
      );
      contourIoUSum += geometry.contourIoU;
      vertexCount += geometry.rings.reduce((sum, ring) => sum + ring.length, 0);
      return {
        id: component.id,
        count: component.count,
        rgb: component.rgb,
        borderTouches: component.borderTouches,
        polygon: geometry.polygon,
        rings: geometry.rings,
        contourIoU: geometry.contourIoU,
        contourEpsilon: geometry.epsilon,
      };
    });

    return {
      version: VERSION,
      centers,
      shapes,
      background: borderColor(rgba, width, height, config.alphaThreshold),
      metrics: {
        budgetMergeCount: reduced.mergeCount,
        componentCount: built.components.length,
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
      analyzeRgba,
      renderAnalysis,
    }),
  });

  root.MinimalizerBrowserFallback = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof window !== "undefined" ? window : globalThis));
