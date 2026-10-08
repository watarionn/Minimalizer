(function (root) {
  "use strict";

  const VERSION = "browser-fallback-v12";
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
    paletteTargetMin: 6,
    paletteTargetMax: 9,
    paletteMaxSamplesPerRegion: 1024,
    paletteMedoidCandidateCount: 64,
    paletteColorDistanceScale: 25.0,
    paletteContrastOriginalDeltaE: 12.0,
    paletteContrastAssignedDeltaE: 5.0,
    paletteSignificantDeltaL: 12.0,
    paletteMajorRegionAreaRatio: 0.03,
    paletteSubjectRescueHighThreshold: 0.90,
    paletteSubjectRescueConfidenceThreshold: 0.70,
    paletteSubjectRescueColorDeltaE: 2.0,
    edgeCoverageThreshold: 0.75,
    retryScale: 0.80,
    maxRetryTargetFactor: 2.5,
    gradientBins: 32,
    colorTau: 25.0,
    hullInflationTau: 0.25,
    thinNeckTau: 0.15,
    colorWeight: 0.30,
    boundaryWeight: 0.25,
    structureWeight: 0.15,
    topologyWeight: 0.10,
    geometryWeight: 0.10,
    redundancyWeight: 0.15,
    majorMassRatio: 0.03,
    majorMassWeight: 0.20,
    safeAreaRatio: 0.0008,
    safeColorCost: 0.08,
    safeBoundaryCost: 0.15,
    safeStructureCost: 0.05,
    safeTopologyCost: 0.25,
    safeSharedBoundaryRatio: 0.35,
    safeSoftProtection: 0.02,
    subjectHighThreshold: 0.80,
    backgroundLowThreshold: 0.20,
    subjectConfidenceThreshold: 0.80,
    subjectProtectionWeight: 0.25,
    hierarchyTargetMin: 24,
    hierarchyTargetMax: 40,
    maxHierarchyHeight: 1.00,
    cutComplexityLambda: 1.10,
    cutTargetWeight: 1.10,
    l0Lambda: 0.010,
    l0Kappa: 2.0,
    l0BetaMax: 100.0,
    l0JacobiIterations: 16,
    l0JacobiOmega: 0.80,
    structuralMode: "l0-lite-jacobi",
    spectralL0BetaMax: 1.0e5,
    canonicalContourLite: false,
    geometryMode: "baseline",
    nativeRgbaMaxPixels: 12000000,
    sourcePixelHardLimit: 100000000,
    sourceFileByteLimit: 67108864,
    browserSubjectGuidance: true,
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

  function shouldUseLargeSourceSampling(
    sourceWidth,
    sourceHeight,
    analysisWidth,
    analysisHeight,
    config,
  ) {
    const sourcePixels = sourceWidth * sourceHeight;
    return (
      sourcePixels > config.nativeRgbaMaxPixels
      && (analysisWidth !== sourceWidth || analysisHeight !== sourceHeight)
    );
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
    if (
      typeof globalThis !== "undefined"
      && globalThis.MinimalizerOpenCvLab
      && typeof globalThis.MinimalizerOpenCvLab.rgbaToLab === "function"
    ) {
      return globalThis.MinimalizerOpenCvLab.rgbaToLab(rgba, width, height);
    }
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

  function approximateL0StructuralRgba(rgba, width, height, options) {
    const config = Object.assign({}, DEFAULTS, options || {});
    const count = width * height;
    const channels = count * 3;
    const source = new Float32Array(channels);
    const result = new Float32Array(channels);
    for (let index = 0; index < count; index += 1) {
      const ro = index * 4;
      const so = index * 3;
      source[so] = rgba[ro] / 255;
      source[so + 1] = rgba[ro + 1] / 255;
      source[so + 2] = rgba[ro + 2] / 255;
      result[so] = source[so];
      result[so + 1] = source[so + 1];
      result[so + 2] = source[so + 2];
    }

    const horizontal = new Float32Array(channels);
    const vertical = new Float32Array(channels);
    const divergence = new Float32Array(channels);
    const rhs = new Float32Array(channels);
    let current = result;
    let next = new Float32Array(channels);
    let beta = 2 * config.l0Lambda;

    while (beta < config.l0BetaMax) {
      const threshold = config.l0Lambda / beta;
      for (let y = 0; y < height; y += 1) {
        const down = y + 1 < height ? y + 1 : 0;
        for (let x = 0; x < width; x += 1) {
          const right = x + 1 < width ? x + 1 : 0;
          const index = y * width + x;
          const rightIndex = y * width + right;
          const downIndex = down * width + x;
          const o = index * 3;
          const ro = rightIndex * 3;
          const vo = downIndex * 3;
          const h0 = current[ro] - current[o];
          const h1 = current[ro + 1] - current[o + 1];
          const h2 = current[ro + 2] - current[o + 2];
          const v0 = current[vo] - current[o];
          const v1 = current[vo + 1] - current[o + 1];
          const v2 = current[vo + 2] - current[o + 2];
          if (
            h0 * h0 + h1 * h1 + h2 * h2
            + v0 * v0 + v1 * v1 + v2 * v2
            < threshold
          ) {
            horizontal[o] = 0;
            horizontal[o + 1] = 0;
            horizontal[o + 2] = 0;
            vertical[o] = 0;
            vertical[o + 1] = 0;
            vertical[o + 2] = 0;
          } else {
            horizontal[o] = h0;
            horizontal[o + 1] = h1;
            horizontal[o + 2] = h2;
            vertical[o] = v0;
            vertical[o + 1] = v1;
            vertical[o + 2] = v2;
          }
        }
      }

      for (let y = 0; y < height; y += 1) {
        const up = y > 0 ? y - 1 : height - 1;
        for (let x = 0; x < width; x += 1) {
          const left = x > 0 ? x - 1 : width - 1;
          const index = y * width + x;
          const leftIndex = y * width + left;
          const upIndex = up * width + x;
          const o = index * 3;
          const lo = leftIndex * 3;
          const uo = upIndex * 3;
          for (let channel = 0; channel < 3; channel += 1) {
            const div = (
              horizontal[lo + channel] - horizontal[o + channel]
              + vertical[uo + channel] - vertical[o + channel]
            );
            divergence[o + channel] = div;
            rhs[o + channel] = source[o + channel] + beta * div;
          }
        }
      }

      const denominator = 1 + 4 * beta;
      for (let iteration = 0; iteration < config.l0JacobiIterations; iteration += 1) {
        for (let y = 0; y < height; y += 1) {
          const up = y > 0 ? y - 1 : height - 1;
          const down = y + 1 < height ? y + 1 : 0;
          for (let x = 0; x < width; x += 1) {
            const left = x > 0 ? x - 1 : width - 1;
            const right = x + 1 < width ? x + 1 : 0;
            const index = y * width + x;
            const o = index * 3;
            const lo = (y * width + left) * 3;
            const ro = (y * width + right) * 3;
            const uo = (up * width + x) * 3;
            const doff = (down * width + x) * 3;
            for (let channel = 0; channel < 3; channel += 1) {
              const candidate = (
                rhs[o + channel]
                + beta * (
                  current[lo + channel]
                  + current[ro + channel]
                  + current[uo + channel]
                  + current[doff + channel]
                )
              ) / denominator;
              next[o + channel] = (
                current[o + channel]
                + config.l0JacobiOmega * (candidate - current[o + channel])
              );
            }
          }
        }
        const swap = current;
        current = next;
        next = swap;
      }
      beta *= config.l0Kappa;
    }

    const output = new Uint8ClampedArray(count * 4);
    for (let index = 0; index < count; index += 1) {
      const so = index * 3;
      const ro = index * 4;
      output[ro] = Math.round(clamp(current[so], 0, 1) * 255);
      output[ro + 1] = Math.round(clamp(current[so + 1], 0, 1) * 255);
      output[ro + 2] = Math.round(clamp(current[so + 2], 0, 1) * 255);
      output[ro + 3] = rgba[ro + 3];
    }
    return output;
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

  function reflect101(value, size) {
    if (size <= 1) return 0;
    let v = value;
    while (v < 0 || v >= size) {
      if (v < 0) v = -v;
      if (v >= size) v = 2 * size - v - 2;
    }
    return v;
  }

  function percentileLinear(values, percentile) {
    const finite = Array.from(values).filter(Number.isFinite).sort((a, b) => a - b);
    if (finite.length === 0) return 0;
    const rank = (finite.length - 1) * percentile / 100;
    const low = Math.floor(rank);
    const high = Math.ceil(rank);
    if (low === high) return finite[low];
    const fraction = rank - low;
    return finite[low] + (finite[high] - finite[low]) * fraction;
  }

  function canonicalLabEdgeMap(lab, width, height, percentile) {
    const p = percentile == null ? 99 : percentile;
    const magnitude = new Float32Array(width * height);
    const kx = [
      [-1, 0, 1],
      [-2, 0, 2],
      [-1, 0, 1],
    ];
    const ky = [
      [-1, -2, -1],
      [0, 0, 0],
      [1, 2, 1],
    ];
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        let energy = 0;
        for (let channel = 0; channel < 3; channel += 1) {
          let gx = 0;
          let gy = 0;
          for (let dy = -1; dy <= 1; dy += 1) {
            const sy = reflect101(y + dy, height);
            for (let dx = -1; dx <= 1; dx += 1) {
              const sx = reflect101(x + dx, width);
              const sample = lab[(sy * width + sx) * 3 + channel];
              gx += sample * kx[dy + 1][dx + 1];
              gy += sample * ky[dy + 1][dx + 1];
            }
          }
          energy += gx * gx + gy * gy;
        }
        magnitude[y * width + x] = Math.sqrt(energy);
      }
    }
    const scale = percentileLinear(magnitude, p);
    if (!(scale > 1e-12)) return new Float32Array(width * height);
    for (let i = 0; i < magnitude.length; i += 1) {
      magnitude[i] = clamp(magnitude[i] / scale, 0, 1);
    }
    return magnitude;
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
    let maxLabel = -1;
    for (let index = 0; index < labels.length; index += 1) {
      if (labels[index] < 0) throw new Error("labels must be non-negative");
      if (labels[index] > maxLabel) maxLabel = labels[index];
    }

    const minX = new Int32Array(maxLabel + 1);
    const minY = new Int32Array(maxLabel + 1);
    const maxX = new Int32Array(maxLabel + 1);
    const maxY = new Int32Array(maxLabel + 1);
    const counts = new Int32Array(maxLabel + 1);
    minX.fill(width);
    minY.fill(height);
    maxX.fill(-1);
    maxY.fill(-1);

    for (let index = 0; index < labels.length; index += 1) {
      const label = labels[index];
      const x = index % width;
      const y = Math.floor(index / width);
      counts[label] += 1;
      if (x < minX[label]) minX[label] = x;
      if (x > maxX[label]) maxX[label] = x;
      if (y < minY[label]) minY[label] = y;
      if (y > maxY[label]) maxY[label] = y;
    }

    const output = new Int32Array(labels.length);
    output.fill(-1);
    const queue = new Int32Array(labels.length);
    let nextId = 0;

    // Match Python split_disconnected_labels():
    // np.unique(source) label order, then connected-component raster order.
    for (let sourceLabel = 0; sourceLabel <= maxLabel; sourceLabel += 1) {
      if (counts[sourceLabel] === 0) continue;
      for (let y = minY[sourceLabel]; y <= maxY[sourceLabel]; y += 1) {
        for (let x = minX[sourceLabel]; x <= maxX[sourceLabel]; x += 1) {
          const startIndex = y * width + x;
          if (labels[startIndex] !== sourceLabel || output[startIndex] >= 0) continue;

          let head = 0;
          let tail = 0;
          queue[tail++] = startIndex;
          output[startIndex] = nextId;
          while (head < tail) {
            const index = queue[head++];
            const cx = index % width;
            const cy = Math.floor(index / width);
            if (cx > 0) {
              const neighbor = index - 1;
              if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
                output[neighbor] = nextId;
                queue[tail++] = neighbor;
              }
            }
            if (cx + 1 < width) {
              const neighbor = index + 1;
              if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
                output[neighbor] = nextId;
                queue[tail++] = neighbor;
              }
            }
            if (cy > 0) {
              const neighbor = index - width;
              if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
                output[neighbor] = nextId;
                queue[tail++] = neighbor;
              }
            }
            if (cy + 1 < height) {
              const neighbor = index + width;
              if (output[neighbor] < 0 && labels[neighbor] === sourceLabel) {
                output[neighbor] = nextId;
                queue[tail++] = neighbor;
              }
            }
          }
          nextId += 1;
        }
      }
    }

    for (let index = 0; index < output.length; index += 1) {
      if (output[index] < 0) throw new Error("connectivity split left unlabeled pixels");
    }
    return { labels: output, regionCount: nextId };
  }

  function runSlicoLite(lab, edge, width, height, regionSize, iterations) {
    let centers = initialSlicoCenters(lab, edge, width, height, regionSize);
    const clusterCount = centers.length;
    const labels = new Int32Array(width * height);
    const distances = new Float64Array(width * height);
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

      const colorScales = new Float64Array(clusterCount);
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


  function canonicalEdgeKey(a, b) {
    return a < b ? a + ":" + b : b + ":" + a;
  }

  function histogramAdd(hist, value) {
    const clipped = clamp(value, 0, 1);
    const index = Math.min(hist.length - 1, Math.floor(clipped * hist.length));
    hist[index] += 1;
  }

  function histogramQuantile(hist, q) {
    let total = 0;
    for (let i = 0; i < hist.length; i += 1) total += hist[i];
    if (total <= 0) return 0;
    const target = q * (total - 1);
    let cumulative = 0;
    for (let i = 0; i < hist.length; i += 1) {
      cumulative += hist[i];
      if (cumulative >= target + 1) {
        return i / Math.max(1, hist.length - 1);
      }
    }
    return 1;
  }

  function hullCross(o, a, b) {
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  }

  function convexHullPoints(points) {
    const unique = new Map();
    for (const point of points) unique.set(point[0] + "," + point[1], point);
    const sorted = Array.from(unique.values()).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (sorted.length <= 2) return sorted;
    const lower = [];
    for (const point of sorted) {
      while (lower.length >= 2 && hullCross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) {
        lower.pop();
      }
      lower.push(point);
    }
    const upper = [];
    for (let i = sorted.length - 1; i >= 0; i -= 1) {
      const point = sorted[i];
      while (upper.length >= 2 && hullCross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) {
        upper.pop();
      }
      upper.push(point);
    }
    lower.pop();
    upper.pop();
    return lower.concat(upper);
  }

  function polygonArea(points) {
    if (!points || points.length < 3) return 0;
    let twice = 0;
    for (let i = 0; i < points.length; i += 1) {
      const next = points[(i + 1) % points.length];
      twice += points[i][0] * next[1] - next[0] * points[i][1];
    }
    return Math.abs(twice) * 0.5;
  }

  function canonicalRegionHull(group, labels, width, height) {
    const rings = boundaryRings(group, labels, width, height);
    const points = [];
    for (const ring of rings) for (const point of ring) points.push(point);
    if (points.length < 3) {
      return [
        [group.minX, group.minY],
        [group.maxX + 1, group.minY],
        [group.maxX + 1, group.maxY + 1],
        [group.minX, group.maxY + 1],
      ];
    }
    return convexHullPoints(points);
  }

  function buildCanonicalRegionGraph(labels, rgba, lab, rawEdge, structuralEdge, width, height, bins, subjectProb = null, subjectConfidence = null) {
    let maxLabel = -1;
    for (let i = 0; i < labels.length; i += 1) maxLabel = Math.max(maxLabel, labels[i]);
    const regionCount = maxLabel + 1;
    const nodes = new Map();
    for (let id = 0; id < regionCount; id += 1) {
      nodes.set(id, {
        id,
        pixels: [],
        count: 0,
        minX: width,
        minY: height,
        maxX: -1,
        maxY: -1,
        borderTouches: 0,
        perimeter: 0,
        sumLab: [0, 0, 0],
        sumSqLab: [0, 0, 0],
        rgbSum: [0, 0, 0],
        lab: [0, 0, 0],
        rgb: [0, 0, 0],
        hull: [],
        hullArea: 0,
        subjectProbSum: 0,
        subjectConfidenceSum: 0,
        subjectRatio: 0,
        subjectConfidence: 0,
      });
    }
    for (let index = 0; index < labels.length; index += 1) {
      const node = nodes.get(labels[index]);
      const x = index % width;
      const y = Math.floor(index / width);
      const lo = index * 3;
      const ro = index * 4;
      node.pixels.push(index);
      node.count += 1;
      node.minX = Math.min(node.minX, x);
      node.minY = Math.min(node.minY, y);
      node.maxX = Math.max(node.maxX, x);
      node.maxY = Math.max(node.maxY, y);
      if (x === 0 || y === 0 || x === width - 1 || y === height - 1) node.borderTouches += 1;
      for (let k = 0; k < 3; k += 1) {
        node.sumLab[k] += lab[lo + k];
        node.sumSqLab[k] += lab[lo + k] * lab[lo + k];
        node.rgbSum[k] += rgba[ro + k];
      }
      if (subjectProb) node.subjectProbSum += subjectProb[index];
      if (subjectConfidence) node.subjectConfidenceSum += subjectConfidence[index];
    }
    for (const node of nodes.values()) {
      node.lab = node.sumLab.map((v) => v / node.count);
      node.rgb = node.rgbSum.map((v) => Math.round(v / node.count));
      node.perimeter = node.count * 4;
      node.subjectRatio = node.subjectProbSum / node.count;
      node.subjectConfidence = node.subjectConfidenceSum / node.count;
    }

    const adjacency = new Map();
    for (const id of nodes.keys()) adjacency.set(id, new Set());
    const edges = new Map();
    function addPair(a, b, rawValue, structuralValue) {
      if (a === b) return;
      const key = canonicalEdgeKey(a, b);
      let edge = edges.get(key);
      if (!edge) {
        edge = {
          a: Math.min(a, b),
          b: Math.max(a, b),
          shared: 0,
          rawHist: new Int32Array(bins),
          structuralHist: new Int32Array(bins),
        };
        edges.set(key, edge);
      }
      edge.shared += 1;
      histogramAdd(edge.rawHist, rawValue);
      histogramAdd(edge.structuralHist, structuralValue);
      adjacency.get(a).add(b);
      adjacency.get(b).add(a);
    }

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const id = labels[index];
        if (x + 1 < width) {
          const other = labels[index + 1];
          if (other === id) {
            nodes.get(id).perimeter -= 2;
          } else {
            addPair(
              id,
              other,
              Math.max(rawEdge[index], rawEdge[index + 1]),
              Math.max(structuralEdge[index], structuralEdge[index + 1]),
            );
          }
        }
        if (y + 1 < height) {
          const other = labels[index + width];
          if (other === id) {
            nodes.get(id).perimeter -= 2;
          } else {
            addPair(
              id,
              other,
              Math.max(rawEdge[index], rawEdge[index + width]),
              Math.max(structuralEdge[index], structuralEdge[index + width]),
            );
          }
        }
      }
    }

    for (const node of nodes.values()) {
      node.hull = canonicalRegionHull(node, labels, width, height);
      node.hullArea = Math.max(1, polygonArea(node.hull));
    }
    return {
      nodes,
      adjacency,
      edges,
      nextRegionId: regionCount,
      initialLabels: new Int32Array(labels),
      initialRegionCount: regionCount,
      width,
      height,
    };
  }

  function canonicalColorCost(left, right, config) {
    const nLeft = left.count;
    const nRight = right.count;
    const dl = left.lab[0] - right.lab[0];
    const da = left.lab[1] - right.lab[1];
    const db = left.lab[2] - right.lab[2];
    const deltaSq = dl * dl + da * da + db * db;
    const deltaSse = (nLeft * nRight / (nLeft + nRight)) * deltaSq;
    const perPixel = deltaSse / (nLeft + nRight);
    return 1 - Math.exp(-perPixel / config.colorTau);
  }

  function canonicalBoundaryCost(edge) {
    const structural = (
      0.45 * histogramQuantile(edge.structuralHist, 0.75)
      + 0.55 * histogramQuantile(edge.structuralHist, 0.90)
    );
    const raw = (
      0.40 * histogramQuantile(edge.rawHist, 0.90)
      + 0.60 * histogramQuantile(edge.rawHist, 0.98)
    );
    return clamp(Math.max(structural, 0.35 * raw), 0, 1);
  }

  function canonicalSharedBoundaryRatio(left, right, edge) {
    return clamp(edge.shared / Math.max(1e-12, Math.min(left.perimeter, right.perimeter)), 0, 1);
  }

  function canonicalStructureCost(left, right) {
    const leftRatio = Number.isFinite(left.subjectRatio) ? left.subjectRatio : 0;
    const rightRatio = Number.isFinite(right.subjectRatio) ? right.subjectRatio : 0;
    const leftConfidence = Number.isFinite(left.subjectConfidence) ? left.subjectConfidence : 0;
    const rightConfidence = Number.isFinite(right.subjectConfidence) ? right.subjectConfidence : 0;
    return clamp(
      Math.abs(leftRatio - rightRatio) * Math.min(leftConfidence, rightConfidence),
      0,
      1,
    );
  }

  function canonicalSubjectBackgroundBlocked(left, right, config) {
    const leftRatio = Number.isFinite(left.subjectRatio) ? left.subjectRatio : 0;
    const rightRatio = Number.isFinite(right.subjectRatio) ? right.subjectRatio : 0;
    const leftConfidence = Number.isFinite(left.subjectConfidence) ? left.subjectConfidence : 0;
    const rightConfidence = Number.isFinite(right.subjectConfidence) ? right.subjectConfidence : 0;
    const leftConfident = leftConfidence >= config.subjectConfidenceThreshold;
    const rightConfident = rightConfidence >= config.subjectConfidenceThreshold;
    if (!leftConfident || !rightConfident) return false;
    const leftSubject = leftRatio >= config.subjectHighThreshold;
    const rightSubject = rightRatio >= config.subjectHighThreshold;
    const leftBackground = leftRatio <= config.backgroundLowThreshold;
    const rightBackground = rightRatio <= config.backgroundLowThreshold;
    return (
      (leftSubject && rightBackground)
      || (rightSubject && leftBackground)
    );
  }

  function canonicalTopologyCost(left, right, edge, config) {
    const ratio = canonicalSharedBoundaryRatio(left, right, edge);
    return clamp(Math.exp(-ratio / config.thinNeckTau), 0, 1);
  }

  function canonicalGeometryCost(left, right, config) {
    const mergedHull = convexHullPoints(left.hull.concat(right.hull));
    const mergedArea = Math.max(1, polygonArea(mergedHull));
    const baseArea = Math.max(1e-12, left.hullArea + right.hullArea);
    const inflation = Math.max(0, mergedArea - baseArea) / baseArea;
    return clamp(1 - Math.exp(-inflation / config.hullInflationTau), 0, 1);
  }

  function canonicalSoftProtection(left, right, imageArea, config) {
    const smallerRatio = Math.min(left.count, right.count) / imageArea;
    return Math.min(0.35, config.majorMassWeight * Math.min(1, smallerRatio / config.majorMassRatio));
  }

  function canonicalRedundancyReward(left, right, edge, imageArea, colorCost, boundaryCost) {
    const smallerRatio = Math.min(left.count, right.count) / imageArea;
    const smallness = Math.exp(-smallerRatio / 0.01);
    const similarity = 1 - colorCost;
    const weakBoundary = 1 - boundaryCost;
    const enclosure = Math.min(1, canonicalSharedBoundaryRatio(left, right, edge) / 0.50);
    return clamp(smallness * similarity * weakBoundary * enclosure, 0, 1);
  }

  function evaluateCanonicalMerge(left, right, edge, imageArea, config) {
    const colorCost = canonicalColorCost(left, right, config);
    const boundaryCost = canonicalBoundaryCost(edge);
    const structureCost = canonicalStructureCost(left, right);
    const topologyCost = canonicalTopologyCost(left, right, edge, config);
    const geometryCost = canonicalGeometryCost(left, right, config);
    const softProtection = canonicalSoftProtection(left, right, imageArea, config);
    const redundancyReward = canonicalRedundancyReward(
      left, right, edge, imageArea, colorCost, boundaryCost,
    );
    const blocked = canonicalSubjectBackgroundBlocked(left, right, config);
    const totalCost = blocked ? Number.POSITIVE_INFINITY : clamp(
      config.colorWeight * colorCost
      + config.boundaryWeight * boundaryCost
      + config.structureWeight * structureCost
      + config.topologyWeight * topologyCost
      + config.geometryWeight * geometryCost
      + softProtection
      - config.redundancyWeight * redundancyReward,
      0,
      1.35,
    );
    return {
      allowed: !blocked,
      totalCost,
      colorCost,
      boundaryCost,
      structureCost,
      topologyCost,
      geometryCost,
      softProtection,
      redundancyReward,
    };
  }

  function canonicalSafeCandidate(left, right, edge, evaluation, imageArea, config) {
    const areaRatio = Math.min(left.count, right.count) / imageArea;
    return (
      evaluation.allowed
      && areaRatio <= config.safeAreaRatio
      && evaluation.colorCost <= config.safeColorCost
      && evaluation.boundaryCost <= config.safeBoundaryCost
      && evaluation.structureCost <= config.safeStructureCost
      && evaluation.topologyCost <= config.safeTopologyCost
      && canonicalSharedBoundaryRatio(left, right, edge) >= config.safeSharedBoundaryRatio
      && evaluation.softProtection <= config.safeSoftProtection
    );
  }

  class CanonicalMinHeap {
    constructor() {
      this.items = [];
    }
    push(item) {
      const items = this.items;
      items.push(item);
      let index = items.length - 1;
      while (index > 0) {
        const parent = Math.floor((index - 1) / 2);
        if (this.compare(items[parent], items[index]) <= 0) break;
        [items[parent], items[index]] = [items[index], items[parent]];
        index = parent;
      }
    }
    pop() {
      const items = this.items;
      if (items.length === 0) return null;
      const first = items[0];
      const last = items.pop();
      if (items.length > 0) {
        items[0] = last;
        let index = 0;
        while (true) {
          const left = index * 2 + 1;
          const right = left + 1;
          let smallest = index;
          if (left < items.length && this.compare(items[left], items[smallest]) < 0) smallest = left;
          if (right < items.length && this.compare(items[right], items[smallest]) < 0) smallest = right;
          if (smallest === index) break;
          [items[index], items[smallest]] = [items[smallest], items[index]];
          index = smallest;
        }
      }
      return first;
    }
    get length() {
      return this.items.length;
    }
    compare(a, b) {
      return a.cost - b.cost || a.left - b.left || a.right - b.right;
    }
  }

  function mergeCanonicalEdge(edges, newId, neighborId) {
    let shared = 0;
    const rawHist = new Int32Array(edges[0].rawHist.length);
    const structuralHist = new Int32Array(edges[0].structuralHist.length);
    for (const edge of edges) {
      shared += edge.shared;
      for (let i = 0; i < rawHist.length; i += 1) {
        rawHist[i] += edge.rawHist[i];
        structuralHist[i] += edge.structuralHist[i];
      }
    }
    return {
      a: Math.min(newId, neighborId),
      b: Math.max(newId, neighborId),
      shared,
      rawHist,
      structuralHist,
    };
  }

  function mergeCanonicalNodes(graph, tree, leftId, rightId, evaluation, stage) {
    const left = graph.nodes.get(leftId);
    const right = graph.nodes.get(rightId);
    const separatingKey = canonicalEdgeKey(leftId, rightId);
    const separating = graph.edges.get(separatingKey);
    const newId = graph.nextRegionId++;
    const total = left.count + right.count;
    const mergedHull = convexHullPoints(left.hull.concat(right.hull));
    const node = {
      id: newId,
      pixels: left.pixels.concat(right.pixels),
      count: total,
      minX: Math.min(left.minX, right.minX),
      minY: Math.min(left.minY, right.minY),
      maxX: Math.max(left.maxX, right.maxX),
      maxY: Math.max(left.maxY, right.maxY),
      borderTouches: left.borderTouches + right.borderTouches,
      perimeter: left.perimeter + right.perimeter - 2 * separating.shared,
      sumLab: [
        left.sumLab[0] + right.sumLab[0],
        left.sumLab[1] + right.sumLab[1],
        left.sumLab[2] + right.sumLab[2],
      ],
      sumSqLab: [
        left.sumSqLab[0] + right.sumSqLab[0],
        left.sumSqLab[1] + right.sumSqLab[1],
        left.sumSqLab[2] + right.sumSqLab[2],
      ],
      rgbSum: [
        left.rgbSum[0] + right.rgbSum[0],
        left.rgbSum[1] + right.rgbSum[1],
        left.rgbSum[2] + right.rgbSum[2],
      ],
      lab: [0, 0, 0],
      rgb: [0, 0, 0],
      hull: mergedHull,
      hullArea: Math.max(1, polygonArea(mergedHull)),
      subjectProbSum: left.subjectProbSum + right.subjectProbSum,
      subjectConfidenceSum: left.subjectConfidenceSum + right.subjectConfidenceSum,
      subjectRatio: 0,
      subjectConfidence: 0,
    };
    node.lab = node.sumLab.map((v) => v / total);
    node.rgb = node.rgbSum.map((v) => Math.round(v / total));
    node.subjectRatio = node.subjectProbSum / total;
    node.subjectConfidence = node.subjectConfidenceSum / total;

    const neighbors = new Set([
      ...graph.adjacency.get(leftId),
      ...graph.adjacency.get(rightId),
    ]);
    neighbors.delete(leftId);
    neighbors.delete(rightId);

    const replacementEdges = [];
    for (const neighborId of neighbors) {
      const sourceEdges = [];
      const lk = canonicalEdgeKey(leftId, neighborId);
      const rk = canonicalEdgeKey(rightId, neighborId);
      if (graph.edges.has(lk)) sourceEdges.push(graph.edges.get(lk));
      if (graph.edges.has(rk)) sourceEdges.push(graph.edges.get(rk));
      replacementEdges.push([
        neighborId,
        mergeCanonicalEdge(sourceEdges, newId, neighborId),
      ]);
    }

    for (const regionId of [leftId, rightId]) {
      for (const neighborId of graph.adjacency.get(regionId)) {
        graph.edges.delete(canonicalEdgeKey(regionId, neighborId));
        if (graph.adjacency.has(neighborId)) graph.adjacency.get(neighborId).delete(regionId);
      }
      graph.adjacency.delete(regionId);
      graph.nodes.delete(regionId);
    }

    graph.nodes.set(newId, node);
    graph.adjacency.set(newId, new Set(neighbors));
    for (const [neighborId, edge] of replacementEdges) {
      graph.adjacency.get(neighborId).add(newId);
      graph.edges.set(canonicalEdgeKey(newId, neighborId), edge);
    }

    const leftTree = tree.nodes.get(leftId);
    const rightTree = tree.nodes.get(rightId);
    const hierarchyHeight = Math.max(
      evaluation.totalCost,
      leftTree.hierarchyHeight,
      rightTree.hierarchyHeight,
    );
    tree.nodes.set(newId, {
      id: newId,
      leftId,
      rightId,
      rawMergeCost: evaluation.totalCost,
      hierarchyHeight,
      stage,
      stats: node,
    });
    tree.roots.delete(leftId);
    tree.roots.delete(rightId);
    tree.roots.add(newId);
    tree.mergeSequence.push(newId);
    return newId;
  }

  function initializeCanonicalTree(graph) {
    const nodes = new Map();
    for (const [id, stats] of graph.nodes.entries()) {
      nodes.set(id, {
        id,
        leftId: null,
        rightId: null,
        rawMergeCost: 0,
        hierarchyHeight: 0,
        stage: "initial",
        stats,
      });
    }
    return {
      nodes,
      leafIds: new Set(graph.nodes.keys()),
      roots: new Set(graph.nodes.keys()),
      mergeSequence: [],
    };
  }

  function pushCanonicalCandidate(heap, graph, leftId, rightId, imageArea, config, safeOnly, metrics) {
    const key = canonicalEdgeKey(leftId, rightId);
    if (!graph.edges.has(key) || !graph.nodes.has(leftId) || !graph.nodes.has(rightId)) return;
    const evaluation = evaluateCanonicalMerge(
      graph.nodes.get(leftId),
      graph.nodes.get(rightId),
      graph.edges.get(key),
      imageArea,
      config,
    );
    metrics.evaluationCount += 1;
    if (!evaluation.allowed) {
      metrics.blockedEvaluationCount = (metrics.blockedEvaluationCount || 0) + 1;
      return;
    }
    const safe = canonicalSafeCandidate(
      graph.nodes.get(leftId),
      graph.nodes.get(rightId),
      graph.edges.get(key),
      evaluation,
      imageArea,
      config,
    );
    if (safe) metrics.safeCandidateCount += 1;
    if (!safeOnly || safe) {
      heap.push({
        cost: evaluation.totalCost,
        left: Math.min(leftId, rightId),
        right: Math.max(leftId, rightId),
      });
    }
  }

  function runCanonicalMergePass(graph, tree, imageArea, config, safeOnly, metrics) {
    const heap = new CanonicalMinHeap();
    for (const edge of graph.edges.values()) {
      pushCanonicalCandidate(heap, graph, edge.a, edge.b, imageArea, config, safeOnly, metrics);
    }
    let count = 0;
    while (heap.length) {
      const candidate = heap.pop();
      const key = canonicalEdgeKey(candidate.left, candidate.right);
      if (!graph.nodes.has(candidate.left) || !graph.nodes.has(candidate.right) || !graph.edges.has(key)) continue;
      const left = graph.nodes.get(candidate.left);
      const right = graph.nodes.get(candidate.right);
      const edge = graph.edges.get(key);
      const evaluation = evaluateCanonicalMerge(left, right, edge, imageArea, config);
      metrics.evaluationCount += 1;
      if (!evaluation.allowed) {
        metrics.blockedEvaluationCount = (metrics.blockedEvaluationCount || 0) + 1;
        continue;
      }
      const safe = canonicalSafeCandidate(left, right, edge, evaluation, imageArea, config);
      if (safe) metrics.safeCandidateCount += 1;
      if (safeOnly && !safe) continue;
      if (Math.abs(evaluation.totalCost - candidate.cost) > 1e-12) {
        heap.push({
          cost: evaluation.totalCost,
          left: candidate.left,
          right: candidate.right,
        });
        continue;
      }
      const newId = mergeCanonicalNodes(
        graph,
        tree,
        candidate.left,
        candidate.right,
        evaluation,
        safeOnly ? "safe" : "hierarchy",
      );
      count += 1;
      for (const neighborId of graph.adjacency.get(newId)) {
        pushCanonicalCandidate(heap, graph, newId, neighborId, imageArea, config, safeOnly, metrics);
      }
    }
    return count;
  }

  function cutCanonicalHierarchyToCount(tree, targetCount) {
    const active = new Set(tree.leafIds);
    if (active.size <= targetCount) return active;
    for (const regionId of tree.mergeSequence) {
      const node = tree.nodes.get(regionId);
      if (!active.has(node.leftId) || !active.has(node.rightId)) {
        throw new Error("Invalid canonical merge sequence.");
      }
      active.delete(node.leftId);
      active.delete(node.rightId);
      active.add(regionId);
      if (active.size === targetCount) return active;
    }
    return active;
  }

  function canonicalTargetPenalty(count, policy) {
    if (count >= policy.targetMin && count <= policy.targetMax) return 0;
    if (count < policy.targetMin) return (policy.targetMin - count) / policy.targetMin;
    return (count - policy.targetMax) / policy.targetMax;
  }

  function cutCanonicalHierarchyMinimal(tree, initialRegionCount, totalPixels, config) {
    const targetMax = Math.min(config.hierarchyTargetMax, initialRegionCount);
    const targetMin = Math.min(config.hierarchyTargetMin, targetMax);
    const policy = {
      targetMin,
      targetMax,
      maxHierarchyHeight: config.maxHierarchyHeight,
      complexityLambda: config.cutComplexityLambda,
      targetWeight: config.cutTargetWeight,
    };

    const losses = new Map();
    for (const leafId of tree.leafIds) losses.set(leafId, 0);
    for (const regionId of tree.mergeSequence) {
      const node = tree.nodes.get(regionId);
      const areaRatio = node.stats.count / totalPixels;
      const subjectConfidence = Number.isFinite(node.stats.subjectConfidence)
        ? node.stats.subjectConfidence
        : 0;
      const protectionWeight = 1 + config.subjectProtectionWeight * subjectConfidence;
      const mergeLoss = (
        node.rawMergeCost
        * Math.sqrt(Math.max(areaRatio, 0))
        * protectionWeight
      );
      losses.set(
        regionId,
        losses.get(node.leftId) + losses.get(node.rightId) + mergeLoss,
      );
    }

    const minimum = new Map();
    for (const leafId of tree.leafIds) minimum.set(leafId, 1);
    for (const regionId of tree.mergeSequence) {
      const node = tree.nodes.get(regionId);
      if (node.hierarchyHeight <= policy.maxHierarchyHeight) {
        minimum.set(regionId, 1);
      } else {
        minimum.set(regionId, minimum.get(node.leftId) + minimum.get(node.rightId));
      }
    }
    const rootIds = Array.from(tree.roots).sort((a, b) => a - b);
    const minCount = rootIds.reduce((sum, id) => sum + minimum.get(id), 0);
    const desiredCap = Math.max(policy.targetMax * 2, policy.targetMax + 64);
    let cap = Math.max(minCount, Math.min(initialRegionCount, desiredCap));

    function buildStates(activeCap) {
      const states = new Map();
      for (const leafId of tree.leafIds) {
        states.set(leafId, new Map([[1, {
          visualLoss: 0,
          selectSelf: true,
          leftCount: 0,
          rightCount: 0,
        }]]));
      }
      for (const regionId of tree.mergeSequence) {
        const node = tree.nodes.get(regionId);
        const left = states.get(node.leftId);
        const right = states.get(node.rightId);
        const merged = new Map();
        for (const [leftCount, leftPlan] of left.entries()) {
          for (const [rightCount, rightPlan] of right.entries()) {
            const count = leftCount + rightCount;
            if (count > activeCap) continue;
            const visualLoss = leftPlan.visualLoss + rightPlan.visualLoss;
            const current = merged.get(count);
            if (!current || visualLoss < current.visualLoss - 1e-15) {
              merged.set(count, {
                visualLoss,
                selectSelf: false,
                leftCount,
                rightCount,
              });
            }
          }
        }
        if (node.hierarchyHeight <= policy.maxHierarchyHeight) {
          const selected = {
            visualLoss: losses.get(regionId),
            selectSelf: true,
            leftCount: 0,
            rightCount: 0,
          };
          const current = merged.get(1);
          if (!current || selected.visualLoss < current.visualLoss) merged.set(1, selected);
        }
        if (merged.size === 0) throw new Error("No feasible hierarchy-cut state.");
        states.set(regionId, merged);
      }
      return states;
    }

    let states = buildStates(cap);
    let forest = new Map([[0, { visualLoss: 0, rootCounts: [] }]]);
    for (const rootId of rootIds) {
      const next = new Map();
      for (const [previousCount, previous] of forest.entries()) {
        for (const [rootCount, rootPlan] of states.get(rootId).entries()) {
          const count = previousCount + rootCount;
          if (count > cap) continue;
          const visualLoss = previous.visualLoss + rootPlan.visualLoss;
          const current = next.get(count);
          if (!current || visualLoss < current.visualLoss - 1e-15) {
            next.set(count, {
              visualLoss,
              rootCounts: previous.rootCounts.concat([[rootId, rootCount]]),
            });
          }
        }
      }
      forest = next;
    }
    if (forest.size === 0 && cap < initialRegionCount) {
      cap = initialRegionCount;
      states = buildStates(cap);
      forest = new Map([[0, { visualLoss: 0, rootCounts: [] }]]);
      for (const rootId of rootIds) {
        const next = new Map();
        for (const [previousCount, previous] of forest.entries()) {
          for (const [rootCount, rootPlan] of states.get(rootId).entries()) {
            const count = previousCount + rootCount;
            const visualLoss = previous.visualLoss + rootPlan.visualLoss;
            const current = next.get(count);
            if (!current || visualLoss < current.visualLoss - 1e-15) {
              next.set(count, {
                visualLoss,
                rootCounts: previous.rootCounts.concat([[rootId, rootCount]]),
              });
            }
          }
        }
        forest = next;
      }
    }

    const totalVisualLoss = rootIds.reduce((sum, id) => sum + losses.get(id), 0);
    let best = null;
    for (const [count, plan] of forest.entries()) {
      const normalizedLoss = totalVisualLoss > 1e-15 ? plan.visualLoss / totalVisualLoss : 0;
      const normalizedCount = count / initialRegionCount;
      const penalty = canonicalTargetPenalty(count, policy);
      const objective = (
        normalizedLoss
        + policy.complexityLambda * normalizedCount
        + policy.targetWeight * penalty
      );
      const candidate = {
        count,
        visualLoss: plan.visualLoss,
        normalizedLoss,
        penalty,
        objective,
        rootCounts: plan.rootCounts,
      };
      if (
        best === null
        || candidate.objective < best.objective - 1e-15
        || (
          Math.abs(candidate.objective - best.objective) <= 1e-15
          && candidate.penalty < best.penalty - 1e-15
        )
        || (
          Math.abs(candidate.objective - best.objective) <= 1e-15
          && Math.abs(candidate.penalty - best.penalty) <= 1e-15
          && candidate.count < best.count
        )
      ) {
        best = candidate;
      }
    }
    if (!best) throw new Error("No feasible canonical hierarchy cut.");

    const selected = new Set();
    const stack = best.rootCounts.slice();
    while (stack.length) {
      const [regionId, count] = stack.pop();
      const plan = states.get(regionId).get(count);
      if (plan.selectSelf) {
        selected.add(regionId);
        continue;
      }
      const node = tree.nodes.get(regionId);
      stack.push([node.leftId, plan.leftCount]);
      stack.push([node.rightId, plan.rightCount]);
    }
    let maxHeight = 0;
    for (const regionId of selected) {
      maxHeight = Math.max(maxHeight, tree.nodes.get(regionId).hierarchyHeight);
    }
    return {
      selectedIds: selected,
      regionCount: best.count,
      visualLoss: best.visualLoss,
      normalizedVisualLoss: best.normalizedLoss,
      objective: best.objective,
      maxSelectedHierarchyHeight: maxHeight,
    };
  }

  function materializeCanonicalCut(tree, selectedIds, width, height) {
    const labels = new Int32Array(width * height);
    labels.fill(-1);
    const selected = Array.from(selectedIds)
      .map((id) => tree.nodes.get(id).stats)
      .sort((a, b) => a.id - b.id);
    const components = selected.map((node, id) => {
      for (const pixel of node.pixels) labels[pixel] = id;
      return {
        id,
        sourceId: node.id,
        label: id,
        pixels: node.pixels,
        count: node.count,
        minX: node.minX,
        minY: node.minY,
        maxX: node.maxX,
        maxY: node.maxY,
        borderTouches: node.borderTouches,
        rgb: node.rgb,
        lab: node.lab,
      };
    });
    for (let i = 0; i < labels.length; i += 1) {
      if (labels[i] < 0) throw new Error("Canonical hierarchy cut left uncovered pixels.");
    }
    return {
      labels,
      built: { components, componentIds: labels },
      groups: components,
    };
  }

  function runCanonicalRegionHierarchy(labels, rgba, lab, rawEdge, structuralEdge, width, height, config) {
    const graph = buildCanonicalRegionGraph(
      labels, rgba, lab, rawEdge, structuralEdge,
      width, height, config.gradientBins,
      config.subjectProb || null,
      config.subjectConfidence || null,
    );
    const tree = initializeCanonicalTree(graph);
    const metrics = {
      initialEdgeCount: graph.edges.size,
      evaluationCount: 0,
      safeCandidateCount: 0,
    };
    const imageArea = width * height;
    const safeMergeCount = runCanonicalMergePass(
      graph, tree, imageArea, config, true, metrics,
    );
    const hierarchyMergeCount = runCanonicalMergePass(
      graph, tree, imageArea, config, false, metrics,
    );
    const cut = cutCanonicalHierarchyMinimal(
      tree,
      graph.initialRegionCount,
      imageArea,
      config,
    );
    const selectedIds = cut.selectedIds;
    const materialized = materializeCanonicalCut(tree, selectedIds, width, height);
    return {
      ...materialized,
      tree,
      safeMergeCount,
      hierarchyMergeCount,
      selectedCount: selectedIds.size,
      cutVisualLoss: cut.visualLoss,
      cutNormalizedVisualLoss: cut.normalizedVisualLoss,
      cutObjective: cut.objective,
      cutMaxHeight: cut.maxSelectedHierarchyHeight,
      finalRootCount: tree.roots.size,
      evaluationCount: metrics.evaluationCount,
      safeCandidateCount: metrics.safeCandidateCount,
      totalMergeCount: safeMergeCount + hierarchyMergeCount,
    };
  }

  function consolidateLegacyShapePalette(groups, targetCount) {
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


  function ciede2000Scalar(first, second) {
    const l1 = first[0], a1 = first[1], b1 = first[2];
    const l2 = second[0], a2 = second[1], b2 = second[2];
    const c1 = Math.hypot(a1, b1);
    const c2 = Math.hypot(a2, b2);
    const cbar = (c1 + c2) * 0.5;
    const cbar7 = Math.pow(cbar, 7);
    const g = 0.5 * (1 - Math.sqrt(cbar7 / (cbar7 + Math.pow(25, 7))));
    const a1p = (1 + g) * a1;
    const a2p = (1 + g) * a2;
    const c1p = Math.hypot(a1p, b1);
    const c2p = Math.hypot(a2p, b2);
    const degrees = (value) => value * 180 / Math.PI;
    const radians = (value) => value * Math.PI / 180;
    const hue = (bb, aa) => (degrees(Math.atan2(bb, aa)) + 360) % 360;
    const h1p = hue(b1, a1p);
    const h2p = hue(b2, a2p);
    const deltaLp = l2 - l1;
    const deltaCp = c2p - c1p;
    const hueDelta = h2p - h1p;
    const product = c1p * c2p;
    let deltaHp = 0;
    if (product !== 0) {
      if (Math.abs(hueDelta) <= 180) deltaHp = hueDelta;
      else if (hueDelta > 180) deltaHp = hueDelta - 360;
      else deltaHp = hueDelta + 360;
    }
    const deltaHpTerm = 2 * Math.sqrt(product) * Math.sin(radians(deltaHp * 0.5));
    const lbarp = (l1 + l2) * 0.5;
    const cbarp = (c1p + c2p) * 0.5;
    const hueSum = h1p + h2p;
    const hueAbs = Math.abs(h1p - h2p);
    let hbarp;
    if (product === 0) hbarp = hueSum;
    else if (hueAbs <= 180) hbarp = hueSum * 0.5;
    else if (hueSum < 360) hbarp = (hueSum + 360) * 0.5;
    else hbarp = (hueSum - 360) * 0.5;
    const t = (
      1
      - 0.17 * Math.cos(radians(hbarp - 30))
      + 0.24 * Math.cos(radians(2 * hbarp))
      + 0.32 * Math.cos(radians(3 * hbarp + 6))
      - 0.20 * Math.cos(radians(4 * hbarp - 63))
    );
    const deltaTheta = 30 * Math.exp(-Math.pow((hbarp - 275) / 25, 2));
    const cbarp7 = Math.pow(cbarp, 7);
    const rc = 2 * Math.sqrt(cbarp7 / (cbarp7 + Math.pow(25, 7)));
    const sl = 1 + 0.015 * Math.pow(lbarp - 50, 2) / Math.sqrt(20 + Math.pow(lbarp - 50, 2));
    const sc = 1 + 0.045 * cbarp;
    const sh = 1 + 0.015 * cbarp * t;
    const rt = -Math.sin(radians(2 * deltaTheta)) * rc;
    const lTerm = deltaLp / sl;
    const cTerm = deltaCp / sc;
    const hTerm = deltaHpTerm / sh;
    return Math.sqrt(Math.max(
      0,
      lTerm * lTerm + cTerm * cTerm + hTerm * hTerm + rt * cTerm * hTerm,
    ));
  }

  function medianNumber(values) {
    const ordered = values.slice().sort((a, b) => a - b);
    const middle = Math.floor(ordered.length / 2);
    if (ordered.length % 2) return ordered[middle];
    return (ordered[middle - 1] + ordered[middle]) * 0.5;
  }

  function deterministicPaletteIndices(indices, maximum) {
    if (indices.length <= maximum) return indices.slice();
    const sampled = new Array(maximum);
    const denominator = maximum - 1;
    const span = indices.length - 1;
    for (let i = 0; i < maximum; i += 1) {
      sampled[i] = indices[Math.floor(i * span / denominator)];
    }
    return sampled;
  }

  function sampleCanonicalPaletteRegions(labels, rgba, lab, width, height, regionCount, config) {
    const pixels = Array.from({ length: regionCount }, () => []);
    for (let index = 0; index < labels.length; index += 1) pixels[labels[index]].push(index);
    const samples = [];
    for (let regionId = 0; regionId < regionCount; regionId += 1) {
      const regionPixels = pixels[regionId];
      if (!regionPixels.length) throw new Error("palette region has no pixels");
      const selected = deterministicPaletteIndices(
        regionPixels,
        config.paletteMaxSamplesPerRegion,
      );
      const labs = selected.map((index) => {
        const offset = index * 3;
        return [lab[offset], lab[offset + 1], lab[offset + 2]];
      });
      const median = [
        medianNumber(labs.map((value) => value[0])),
        medianNumber(labs.map((value) => value[1])),
        medianNumber(labs.map((value) => value[2])),
      ];
      const orderedCandidates = labs
        .map((value, index) => ({
          index,
          distance: Math.hypot(
            value[0] - median[0],
            value[1] - median[1],
            value[2] - median[2],
          ),
        }))
        .sort((a, b) => a.distance - b.distance || a.index - b.index)
        .slice(0, Math.min(config.paletteMedoidCandidateCount, labs.length));
      let bestLocal = orderedCandidates[0].index;
      let bestTotal = Number.POSITIVE_INFINITY;
      for (const candidate of orderedCandidates) {
        let total = 0;
        for (const value of labs) total += ciede2000Scalar(labs[candidate.index], value);
        if (total < bestTotal) {
          bestTotal = total;
          bestLocal = candidate.index;
        }
      }
      const sourceIndex = selected[bestLocal];
      const x = sourceIndex % width;
      const y = Math.floor(sourceIndex / width);
      const ro = sourceIndex * 4;
      samples.push({
        regionId,
        lab: labs[bestLocal].slice(),
        rgb: [rgba[ro], rgba[ro + 1], rgba[ro + 2]],
        sourceXY: [x, y],
        pixelCount: regionPixels.length,
      });
    }
    return samples;
  }

  function canonicalPalettePairKey(a, b) {
    return a < b ? a + "," + b : b + "," + a;
  }

  function buildCanonicalPaletteRelationships(samples, labels, width, height, config) {
    const totalPixels = labels.length;
    const subjectStats = samples.map(() => ({ count: 0, prob: 0, confidence: 0 }));
    if (config.subjectProb && config.subjectConfidence) {
      for (let index = 0; index < labels.length; index += 1) {
        const regionId = labels[index];
        const stats = subjectStats[regionId];
        stats.count += 1;
        stats.prob += config.subjectProb[index];
        stats.confidence += config.subjectConfidence[index];
      }
      for (const stats of subjectStats) {
        if (stats.count > 0) {
          stats.prob /= stats.count;
          stats.confidence /= stats.count;
        }
      }
    }
    const major = new Set(
      samples
        .filter((sample) => sample.pixelCount / totalPixels >= config.paletteMajorRegionAreaRatio)
        .map((sample) => sample.regionId),
    );
    const pending = new Map();
    function add(a, b, reason, protection) {
      if (a === b) return;
      const left = Math.min(a, b), right = Math.max(a, b);
      const key = canonicalPalettePairKey(left, right);
      let item = pending.get(key);
      if (!item) {
        item = { a: left, b: right, reasons: new Set(), protection: 0 };
        pending.set(key, item);
      }
      item.reasons.add(reason);
      item.protection = Math.max(item.protection, protection);
    }
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const id = labels[index];
        if (x + 1 < width) {
          const other = labels[index + 1];
          if (id !== other) {
            if (major.has(id) && major.has(other)) add(id, other, "adjacent_major", 0.80);
            if (config.subjectProb && config.subjectConfidence) {
              const a = subjectStats[id], b = subjectStats[other];
              const subjectBackground = (
                a.confidence >= config.subjectConfidenceThreshold
                && b.confidence >= config.subjectConfidenceThreshold
                && (
                  (a.prob >= config.subjectHighThreshold && b.prob <= config.backgroundLowThreshold)
                  || (b.prob >= config.subjectHighThreshold && a.prob <= config.backgroundLowThreshold)
                )
              );
              if (subjectBackground) add(id, other, "subject_background", 1.00);
            }
          }
        }
        if (y + 1 < height) {
          const other = labels[index + width];
          if (id !== other) {
            if (major.has(id) && major.has(other)) add(id, other, "adjacent_major", 0.80);
            if (config.subjectProb && config.subjectConfidence) {
              const a = subjectStats[id], b = subjectStats[other];
              const subjectBackground = (
                a.confidence >= config.subjectConfidenceThreshold
                && b.confidence >= config.subjectConfidenceThreshold
                && (
                  (a.prob >= config.subjectHighThreshold && b.prob <= config.backgroundLowThreshold)
                  || (b.prob >= config.subjectHighThreshold && a.prob <= config.backgroundLowThreshold)
                )
              );
              if (subjectBackground) add(id, other, "subject_background", 1.00);
            }
          }
        }
      }
    }
    const majorIds = Array.from(major).sort((a, b) => a - b);
    for (let i = 0; i < majorIds.length; i += 1) {
      for (let j = i + 1; j < majorIds.length; j += 1) {
        const a = majorIds[i], b = majorIds[j];
        if (ciede2000Scalar(samples[a].lab, samples[b].lab) >= config.paletteContrastOriginalDeltaE) {
          add(a, b, "major_mass", 0.75);
        }
      }
    }
    return Array.from(pending.values())
      .sort((a, b) => a.a - b.a || a.b - b.b)
      .map((item) => ({
        regionA: item.a,
        regionB: item.b,
        originalDeltaE: ciede2000Scalar(samples[item.a].lab, samples[item.b].lab),
        originalDeltaL: samples[item.a].lab[0] - samples[item.b].lab[0],
        protection: item.protection,
        reasons: Array.from(item.reasons).sort(),
      }));
  }

  function buildCanonicalPaletteSubjectClasses(samples, labels, config) {
    if (!config.subjectProb) return null;
    const stats = samples.map(() => ({ count: 0, prob: 0, confidence: 0 }));
    const hasConfidence = Boolean(config.subjectConfidence);
    for (let index = 0; index < labels.length; index += 1) {
      const regionId = labels[index];
      const item = stats[regionId];
      item.count += 1;
      item.prob += config.subjectProb[index];
      item.confidence += hasConfidence ? config.subjectConfidence[index] : 1;
    }
    const classes = new Int8Array(samples.length);
    for (let regionId = 0; regionId < samples.length; regionId += 1) {
      const item = stats[regionId];
      if (item.count > 0) {
        item.prob /= item.count;
        item.confidence /= item.count;
      }
      if (item.confidence < config.subjectConfidenceThreshold) {
        classes[regionId] = 0;
      } else if (item.prob >= config.subjectHighThreshold) {
        classes[regionId] = 1;
      } else if (item.prob <= config.backgroundLowThreshold) {
        classes[regionId] = -1;
      } else {
        classes[regionId] = 0;
      }
    }
    const backgrounds = [];
    for (let regionId = 0; regionId < classes.length; regionId += 1) {
      if (classes[regionId] === -1) backgrounds.push(regionId);
    }
    if (backgrounds.length === 0) return classes;
    for (let regionId = 0; regionId < classes.length; regionId += 1) {
      if (classes[regionId] !== 0) continue;
      const item = stats[regionId];
      if (
        item.confidence < config.paletteSubjectRescueConfidenceThreshold
        || item.confidence >= config.subjectConfidenceThreshold
        || item.prob < config.paletteSubjectRescueHighThreshold
      ) continue;
      let closest = Number.POSITIVE_INFINITY;
      for (const backgroundId of backgrounds) {
        closest = Math.min(
          closest,
          ciede2000Scalar(samples[regionId].lab, samples[backgroundId].lab),
        );
      }
      if (closest <= config.paletteSubjectRescueColorDeltaE) classes[regionId] = 1;
    }
    return classes;
  }

  function canonicalPaletteSubjectConflict(first, second, subjectClasses) {
    if (!subjectClasses) return false;
    let hasSubject = false;
    let hasBackground = false;
    for (const regionId of first.memberRegions) {
      if (subjectClasses[regionId] === 1) hasSubject = true;
      else if (subjectClasses[regionId] === -1) hasBackground = true;
    }
    for (const regionId of second.memberRegions) {
      if (subjectClasses[regionId] === 1) hasSubject = true;
      else if (subjectClasses[regionId] === -1) hasBackground = true;
    }
    return hasSubject && hasBackground;
  }

  function canonicalPaletteRelationshipRisk(first, second, relationships, config) {
    let risk = 0;
    let blocked = false;
    for (const relationship of relationships) {
      const spans = (
        first.memberRegions.includes(relationship.regionA)
        && second.memberRegions.includes(relationship.regionB)
      ) || (
        first.memberRegions.includes(relationship.regionB)
        && second.memberRegions.includes(relationship.regionA)
      );
      if (!spans) continue;
      const contrast = Math.max(
        relationship.originalDeltaE / config.paletteContrastOriginalDeltaE,
        Math.abs(relationship.originalDeltaL) / config.paletteSignificantDeltaL,
      );
      risk = Math.max(risk, relationship.protection * Math.min(contrast, 1));
      if (
        relationship.protection >= 0.95
        && (
          relationship.originalDeltaE >= config.paletteContrastOriginalDeltaE
          || Math.abs(relationship.originalDeltaL) >= config.paletteSignificantDeltaL
        )
      ) blocked = true;
    }
    return { risk, blocked };
  }

  function canonicalPaletteRepresentative(memberRegions, samples, distances, count) {
    let minimum = Number.POSITIVE_INFINITY;
    let winner = memberRegions[0];
    for (const candidate of memberRegions) {
      let total = 0;
      for (const other of memberRegions) {
        total += distances[candidate * count + other] * samples[other].pixelCount;
      }
      if (
        total < minimum - 1e-12
        || (Math.abs(total - minimum) <= 1e-12 && candidate < winner)
      ) {
        minimum = total;
        winner = candidate;
      }
    }
    return winner;
  }

  function buildCanonicalPaletteHierarchy(samples, relationships, config, subjectClasses = null) {
    const count = samples.length;
    const distances = new Float64Array(count * count);
    for (let a = 0; a < count; a += 1) {
      for (let b = a + 1; b < count; b += 1) {
        const value = ciede2000Scalar(samples[a].lab, samples[b].lab);
        distances[a * count + b] = value;
        distances[b * count + a] = value;
      }
    }
    const nodes = new Map();
    const active = new Set();
    for (let regionId = 0; regionId < count; regionId += 1) {
      const sample = samples[regionId];
      nodes.set(regionId, {
        id: regionId,
        leftId: null,
        rightId: null,
        memberRegions: [regionId],
        representativeRegionId: regionId,
        lab: sample.lab.slice(),
        rgb: sample.rgb.slice(),
        sourceXY: sample.sourceXY.slice(),
        mergeCost: 0,
        hierarchyHeight: 0,
      });
      active.add(regionId);
    }
    const mergeSequence = [];
    let nextId = count;
    while (active.size > 1) {
      const ids = Array.from(active).sort((a, b) => a - b);
      let best = null;
      for (let i = 0; i < ids.length; i += 1) {
        for (let j = i + 1; j < ids.length; j += 1) {
          const leftId = ids[i], rightId = ids[j];
          const left = nodes.get(leftId), right = nodes.get(rightId);
          if (canonicalPaletteSubjectConflict(left, right, subjectClasses)) continue;
          const colorDistance = distances[
            left.representativeRegionId * count + right.representativeRegionId
          ];
          const colorCost = Math.min(colorDistance / config.paletteColorDistanceScale, 1);
          const relationship = canonicalPaletteRelationshipRisk(
            left, right, relationships, config,
          );
          if (relationship.blocked) continue;
          const totalCost = 0.65 * colorCost + 0.10 * relationship.risk;
          const candidate = { totalCost, leftId, rightId };
          if (
            best === null
            || candidate.totalCost < best.totalCost
            || (
              candidate.totalCost === best.totalCost
              && (candidate.leftId < best.leftId
                || (
                  candidate.leftId === best.leftId
                  && candidate.rightId < best.rightId
                ))
            )
          ) best = candidate;
        }
      }
      if (!best) break;
      const first = nodes.get(best.leftId), second = nodes.get(best.rightId);
      const members = first.memberRegions.concat(second.memberRegions).sort((a, b) => a - b);
      const representative = canonicalPaletteRepresentative(members, samples, distances, count);
      const sample = samples[representative];
      nodes.set(nextId, {
        id: nextId,
        leftId: best.leftId,
        rightId: best.rightId,
        memberRegions: members,
        representativeRegionId: representative,
        lab: sample.lab.slice(),
        rgb: sample.rgb.slice(),
        sourceXY: sample.sourceXY.slice(),
        mergeCost: best.totalCost,
        hierarchyHeight: Math.max(
          best.totalCost,
          first.hierarchyHeight,
          second.hierarchyHeight,
        ),
      });
      active.delete(best.leftId);
      active.delete(best.rightId);
      active.add(nextId);
      mergeSequence.push(nextId);
      nextId += 1;
    }
    return { nodes, mergeSequence, leafCount: count };
  }

  function cutCanonicalPaletteHierarchy(hierarchy, desiredCount) {
    const active = new Set();
    for (let id = 0; id < hierarchy.leafCount; id += 1) active.add(id);
    if (active.size <= desiredCount) return active;
    for (const nodeId of hierarchy.mergeSequence) {
      if (active.size <= desiredCount) break;
      const node = hierarchy.nodes.get(nodeId);
      if (!active.has(node.leftId) || !active.has(node.rightId)) {
        throw new Error("palette merge sequence is not replayable");
      }
      active.delete(node.leftId);
      active.delete(node.rightId);
      active.add(nodeId);
    }
    return active;
  }

  function canonicalPaletteRegionMapping(selected, hierarchy) {
    const mapping = new Int32Array(hierarchy.leafCount);
    mapping.fill(-1);
    for (const nodeId of selected) {
      for (const regionId of hierarchy.nodes.get(nodeId).memberRegions) mapping[regionId] = nodeId;
    }
    return mapping;
  }

  function canonicalPaletteRelationshipBroken(relationship, mapping, hierarchy, config) {
    const nodeAId = mapping[relationship.regionA];
    const nodeBId = mapping[relationship.regionB];
    const nodeA = hierarchy.nodes.get(nodeAId);
    const nodeB = hierarchy.nodes.get(nodeBId);
    const assignedDeltaE = ciede2000Scalar(nodeA.lab, nodeB.lab);
    const assignedDeltaL = nodeA.lab[0] - nodeB.lab[0];
    if (
      relationship.originalDeltaE >= config.paletteContrastOriginalDeltaE
      && assignedDeltaE <= config.paletteContrastAssignedDeltaE
    ) return true;
    if (
      Math.abs(relationship.originalDeltaL) >= config.paletteSignificantDeltaL
      && relationship.originalDeltaL * assignedDeltaL < 0
    ) return true;
    return false;
  }

  function splitCanonicalPaletteNode(selected, nodeId, hierarchy) {
    const node = hierarchy.nodes.get(nodeId);
    if (node.leftId === null || node.rightId === null) return false;
    selected.delete(nodeId);
    selected.add(node.leftId);
    selected.add(node.rightId);
    return true;
  }

  function repairCanonicalPaletteRelationships(selected, hierarchy, samples, relationships, config) {
    let repaired = 0;
    const maximumSteps = Math.max(hierarchy.nodes.size * 2, 1);
    for (let step = 0; step < maximumSteps; step += 1) {
      const mapping = canonicalPaletteRegionMapping(selected, hierarchy);
      const broken = relationships.find((relationship) => (
        canonicalPaletteRelationshipBroken(relationship, mapping, hierarchy, config)
      ));
      if (!broken) return { selected, repaired };
      const nodeAId = mapping[broken.regionA];
      const nodeBId = mapping[broken.regionB];
      if (nodeAId === nodeBId) {
        if (!splitCanonicalPaletteNode(selected, nodeAId, hierarchy)) {
          throw new Error("protected palette relationship collapsed inside leaf");
        }
        repaired += 1;
        continue;
      }
      const options = [];
      for (const [regionId, nodeId] of [
        [broken.regionA, nodeAId],
        [broken.regionB, nodeBId],
      ]) {
        const node = hierarchy.nodes.get(nodeId);
        if (node.leftId === null) continue;
        options.push({
          error: ciede2000Scalar(samples[regionId].lab, node.lab),
          nodeId,
        });
      }
      if (!options.length) throw new Error("palette relationship cannot be repaired");
      options.sort((a, b) => b.error - a.error || a.nodeId - b.nodeId);
      if (!splitCanonicalPaletteNode(selected, options[0].nodeId, hierarchy)) {
        throw new Error("failed to split canonical palette node");
      }
      repaired += 1;
    }
    throw new Error("palette relationship repair exceeded deterministic limit");
  }

  function consolidateCanonicalPalette(groups, labels, rgba, lab, width, height, config) {
    if (!groups.length) {
      return {
        colors: [],
        assignments: [],
        palette: [],
        relationshipCount: 0,
        repairedSplitCount: 0,
        method: "canonical-medoid-hierarchy",
      };
    }
    const samples = sampleCanonicalPaletteRegions(
      labels, rgba, lab, width, height, groups.length, config,
    );
    const relationships = buildCanonicalPaletteRelationships(
      samples, labels, width, height, config,
    );
    const subjectClasses = buildCanonicalPaletteSubjectClasses(
      samples, labels, config,
    );
    const hierarchy = buildCanonicalPaletteHierarchy(
      samples, relationships, config, subjectClasses,
    );
    const desiredCount = Math.max(
      1,
      Math.min(
        Math.floor((config.paletteTargetMin + config.paletteTargetMax) / 2),
        samples.length,
      ),
    );
    let selected = cutCanonicalPaletteHierarchy(hierarchy, desiredCount);
    const repaired = repairCanonicalPaletteRelationships(
      selected, hierarchy, samples, relationships, config,
    );
    selected = repaired.selected;
    const selectedIds = Array.from(selected).sort((a, b) => a - b);
    const palette = selectedIds.map((nodeId) => {
      const node = hierarchy.nodes.get(nodeId);
      return {
        id: nodeId,
        representativeRegionId: node.representativeRegionId,
        memberRegions: node.memberRegions.slice(),
        lab: node.lab.slice(),
        rgb: node.rgb.slice(),
        sourceXY: node.sourceXY.slice(),
      };
    });
    const mapping = canonicalPaletteRegionMapping(selected, hierarchy);
    const entryById = new Map(palette.map((entry) => [entry.id, entry]));
    const assignments = Array.from(mapping);
    return {
      palette,
      assignments,
      colors: assignments.map((id) => entryById.get(id).rgb.slice()),
      samples,
      relationships,
      relationshipCount: relationships.length,
      repairedSplitCount: repaired.repaired,
      method: "canonical-medoid-hierarchy",
    };
  }


  // v17: Selective region merge. Only merge two already-adjacent components
  // using the SAME accepted palette ID. It never recomputes the palette, and
  // never performs the unsafe global 40->30 hierarchy cut from v16.
  function mergeAcceptedPaletteRegions(hierarchy, palette, width, height, settings) {
    const config = Object.assign({
      maxMerges: 2, maxSmallFraction: 0.0015,
      maxSourceRgbDistance: 16, minSharedEdges: 5,
      minSharedRatio: 0.18, minBoundingSide: 5,
      maxAspectRatio: 3.0,
      allowNearPalette: false,
      maxPaletteRgbDistance: 18,
      maxChangedPixelFraction: 0.0015,
      maxRegionColorError: 8,
      protectedMinAreaFraction: 0.002,
      maxBoundaryColorDelta: 16,
    }, settings || {});
    const base = hierarchy.built.components;
    const labels = hierarchy.built.componentIds;
    const owners = base.map((component, id) => ({
      ...component, id, pixels: component.pixels.slice(),
      rgb: component.rgb.slice(), active: true,
      paletteId: palette.assignments[id],
      paletteRgb: palette.colors[id].slice(),
    }));
    const mergedFrom = owners.map((_, id) => [id]);
    let applied = 0, evaluated = 0, rejected = 0;
    let candidateNearPalette = 0, rejectedColorFidelity = 0;
    let cumulativeRecolored = 0;
    const rejectReasons={incompatiblePalette:0,donorAreaOrAspect:0,protectedArea:0,paletteDistance:0,recolorBudget:0,regionColorError:0,sourceColorDistance:0,boundaryWeakOrShort:0};
    const total = width * height;
    const ownerOf = new Int32Array(labels);

    function neighbors() {
      const edges = new Map();
      function add(a,b) {
        if (a===b) return;
        const lo=Math.min(a,b),hi=Math.max(a,b),key=lo+":"+hi;
        edges.set(key,(edges.get(key)||0)+1);
      }
      for (let y=0;y<height;y+=1) for(let x=0;x<width;x+=1) {
        const i=y*width+x,a=ownerOf[i];
        if(x+1<width)add(a,ownerOf[i+1]);
        if(y+1<height)add(a,ownerOf[i+width]);
      }
      return edges;
    }
    function validShape(g) {
      const w=g.maxX-g.minX+1,h=g.maxY-g.minY+1;
      return Math.min(w,h)>=config.minBoundingSide
        && Math.max(w/h,h/w)<=config.maxAspectRatio;
    }
    while(applied<config.maxMerges) {
      const possible=[];
      for(const [key,shared] of neighbors()) {
        evaluated+=1;
        const [aId,bId]=key.split(":").map(Number);
        const a=owners[aId],b=owners[bId];
        if(!a?.active||!b?.active) {rejected+=1;continue;}
        const crossPalette = a.paletteId!==b.paletteId;
        if(crossPalette&&!config.allowNearPalette){rejected+=1;rejectReasons.incompatiblePalette+=1;continue;}
        if(crossPalette) candidateNearPalette+=1;
        const small=a.count<=b.count?a:b;
        const large=small===a?b:a;
        if(small.count/total>config.maxSmallFraction||!validShape(small)) {rejected+=1;rejectReasons.donorAreaOrAspect+=1;continue;}
        const paletteDistance=Math.hypot(...small.paletteRgb.map((v,i)=>v-large.paletteRgb[i]));
        if(crossPalette) {
          let reason=null;
          if(small.count/total>=config.protectedMinAreaFraction) reason="protectedArea";
          else if(paletteDistance>config.maxPaletteRgbDistance) reason="paletteDistance";
          else if(small.count+cumulativeRecolored>total*config.maxChangedPixelFraction) reason="recolorBudget";
          else if(paletteDistance>config.maxRegionColorError) reason="regionColorError";
          if(reason){rejectReasons[reason]+=1;rejectedColorFidelity+=1;rejected+=1;continue;}
        }
        const dx=small.rgb[0]-large.rgb[0],dy=small.rgb[1]-large.rgb[1],dz=small.rgb[2]-large.rgb[2];
        const colorDelta=Math.hypot(dx,dy,dz);
        const perimeter=2*((small.maxX-small.minX+1)+(small.maxY-small.minY+1));
        if((crossPalette&&colorDelta>config.maxBoundaryColorDelta)
          ||colorDelta>config.maxSourceRgbDistance){rejected+=1;rejectReasons.sourceColorDistance+=1;continue;}
        if(shared<config.minSharedEdges||shared/perimeter<config.minSharedRatio){rejected+=1;rejectReasons.boundaryWeakOrShort+=1;continue;}
        possible.push({source:small.id,target:large.id,shared,colorDelta,area:small.count,
          crossPalette,paletteDistance});
      }
      possible.sort((a,b)=>a.area-b.area||a.colorDelta-b.colorDelta
        ||b.shared-a.shared||a.source-b.source||a.target-b.target);
      if(!possible.length) break;
      const winner=possible[0],source=owners[winner.source],target=owners[winner.target];
      if(winner.crossPalette)cumulativeRecolored+=source.count;
      const combined=source.count+target.count;
      target.rgb=target.rgb.map((v,j)=>Math.round((v*target.count+source.rgb[j]*source.count)/combined));
      target.count=combined;
      target.minX=Math.min(target.minX,source.minX);
      target.minY=Math.min(target.minY,source.minY);
      target.maxX=Math.max(target.maxX,source.maxX);
      target.maxY=Math.max(target.maxY,source.maxY);
      target.borderTouches+=source.borderTouches;
      target.pixels.push(...source.pixels);
      mergedFrom[target.id].push(...mergedFrom[source.id]);
      source.active=false;
      for(const pixel of source.pixels)ownerOf[pixel]=target.id;
      applied+=1;
    }
    if(applied===0) return {
      hierarchy,palette,metrics:{applied:0,evaluated,rejected,changedPixels:0,
        candidateNearPalette,rejectedColorFidelity,rejectReasons},
    };
    const retained=owners.filter(x=>x.active).sort((a,b)=>a.id-b.id);
    const finalLabels=new Int32Array(total);finalLabels.fill(-1);
    const finalComponents=retained.map((group,id)=>{
      for(const pixel of group.pixels)finalLabels[pixel]=id;
      return {
        id, sourceId:group.sourceId, label:id,
        pixels:group.pixels,count:group.count,minX:group.minX,minY:group.minY,
        maxX:group.maxX,maxY:group.maxY,borderTouches:group.borderTouches,
        rgb:group.rgb, lab:group.lab,
      };
    });
    if(finalLabels.some(x=>x<0)) throw Error("Selective region merge lost pixel coverage.");
    return {
      hierarchy:{
        ...hierarchy,
        built:{components:finalComponents,componentIds:finalLabels},
        groups:finalComponents,
        selectedCount:finalComponents.length,
      },
      palette:{
        ...palette,
        assignments:retained.map(g=>g.paletteId),
        colors:retained.map(g=>g.paletteRgb.slice()),
      },
      metrics:{applied,evaluated,rejected,changedPixels:cumulativeRecolored,
        candidateNearPalette,rejectedColorFidelity,rejectReasons},
    };
  }

  // Render-space verification, independent of the proposed label-area budget.
  // Reject geometry/paint changes that exceed any pixel, RGB or color-mass bound.
  function compareRegionRenderFidelity(baselineShapes, candidateShapes, width, height, options) {
    const cfg=Object.assign({maxChangedPixelFraction:0.0015,
      maxRgbMeanAbsoluteError:0.30,maxColorMassDeltaFraction:0.0015},options||{});
    const raster=typeof globalThis!=="undefined" && globalThis.MinimalizerOpenCvRaster;
    if(!raster||typeof raster.renderShapesRgba!=="function")
      return {pass:false,reason:"raster_missing",changedPixels:0};
    const oldPixels=raster.renderShapesRgba(baselineShapes,width,height,1,1,2);
    const newPixels=raster.renderShapesRgba(candidateShapes,width,height,1,1,2);
    if(oldPixels.length!==width*height*4||oldPixels.length!==newPixels.length)
      return {pass:false,reason:"invalid_raster",changedPixels:0};
    let changed=0,mae=0;
    const massDelta=new Map();
    for(let p=0;p<oldPixels.length;p+=4){
      const before=oldPixels[p]+","+oldPixels[p+1]+","+oldPixels[p+2];
      const after=newPixels[p]+","+newPixels[p+1]+","+newPixels[p+2];
      if(before!==after) {
        changed+=1;
        massDelta.set(before,(massDelta.get(before)||0)-1);
        massDelta.set(after,(massDelta.get(after)||0)+1);
      }
      for(let channel=0;channel<3;channel+=1)
        mae+=Math.abs(oldPixels[p+channel]-newPixels[p+channel]);
    }
    const maxMassDelta=Math.max(0,...Array.from(massDelta.values(),Math.abs));
    const changedFraction=changed/(width*height);
    const rgbMAE=mae/(width*height*3);
    const pass=changedFraction<=cfg.maxChangedPixelFraction
      &&rgbMAE<=cfg.maxRgbMeanAbsoluteError
      &&maxMassDelta/(width*height)<=cfg.maxColorMassDeltaFraction;
    return {pass,reason:pass?"pass":"render_delta",changedPixels:changed,
      changedFraction,rgbMAE,maxColorMassDelta:maxMassDelta};
  }

  function analyzeRgba(rgba, width, height, options) {
    const config = Object.assign({}, DEFAULTS, options || {});
    if (config.selectiveRegionMerge === true && (
      config.structuralMode !== "l0-lite-jacobi"
      || config.canonicalContourLite !== true
      || config.geometryMode !== "facet-safe"
    )) {
      throw new Error("Selective region merging requires Facet geometry and Lite preprocessing.");
    }
    if (
      (config.geometryMode === "corner-aware" || config.geometryMode === "facet-safe")
      && (config.canonicalContourLite !== true || config.structuralMode !== "l0-lite-jacobi")
    ) {
      throw new Error("Geometric Shape/Facet requires Lite preprocessing with canonical shared-boundary contours.");
    }
    if (config.canonicalContourLite === true) {
      const contourAvailable = typeof globalThis !== "undefined"
        && globalThis.MinimalizerCanonicalContour
        && typeof globalThis.MinimalizerCanonicalContour.simplifyLabels === "function";
      const rasterAvailable = typeof globalThis !== "undefined"
        && globalThis.MinimalizerOpenCvRaster
        && typeof globalThis.MinimalizerOpenCvRaster.renderShapesRgba === "function";
      if (!contourAvailable || !rasterAvailable) {
        throw new Error("Sharp Lite requires shared-boundary contour and OpenCV-compatible raster modules.");
      }
    }
    const lab = rgbaToLab(rgba, width, height);
    let structuralRgba;
    let structuralPreprocess = "l0-lite-jacobi";
    if (
      config.structuralMode === "spectral-exact"
      && typeof globalThis !== "undefined"
      && globalThis.MinimalizerSpectralFFT
      && typeof globalThis.MinimalizerSpectralFFT.exactL0StructuralRgba === "function"
    ) {
      structuralRgba = globalThis.MinimalizerSpectralFFT.exactL0StructuralRgba(
        rgba,
        width,
        height,
        {
          lambda: config.l0Lambda,
          kappa: config.l0Kappa,
          betaMax: config.spectralL0BetaMax,
        },
      );
      structuralPreprocess = "spectral-exact";
    } else {
      structuralRgba = approximateL0StructuralRgba(rgba, width, height, config);
    }
    const structuralLab = rgbaToLab(structuralRgba, width, height);
    const rawEdge = canonicalLabEdgeMap(lab, width, height, 99);
    const structuralEdge = canonicalLabEdgeMap(structuralLab, width, height, 99);
    const segmented = oversegmentSpatial(
      structuralLab,
      structuralEdge,
      width,
      height,
      config,
    );
    const targetCount = segmented.targetCount;
    const regionSize = segmented.regionSize;
    const edgeCoverage = segmented.edgeCoverage;
    const hierarchy = runCanonicalRegionHierarchy(
      segmented.labels,
      rgba,
      lab,
      rawEdge,
      structuralEdge,
      width,
      height,
      config,
    );
    let palette = consolidateCanonicalPalette(
      hierarchy.groups,
      hierarchy.built.componentIds,
      rgba,
      lab,
      width,
      height,
      config,
    );
    let selectedHierarchy = hierarchy;
    let selectiveMergeMetrics = {applied:0,evaluated:0,rejected:0,changedPixels:0,
      candidateNearPalette:0,rejectedColorFidelity:0,rejectReasons:{}};
    if (config.selectiveRegionMerge === true) {
      const selective = mergeAcceptedPaletteRegions(hierarchy,palette,width,height,config.selectiveMergeOptions);
      selectedHierarchy = selective.hierarchy;
      palette = selective.palette;
      selectiveMergeMetrics = selective.metrics;
    }

    let canonicalContour = null;
    if (
      (config.structuralMode === "spectral-exact" || config.canonicalContourLite === true)
      && typeof globalThis !== "undefined"
      && globalThis.MinimalizerCanonicalContour
      && typeof globalThis.MinimalizerCanonicalContour.simplifyLabels === "function"
    ) {
      canonicalContour = globalThis.MinimalizerCanonicalContour.simplifyLabels(
        selectedHierarchy.built.componentIds,
        width,
        height,
        selectedHierarchy.built.components.length,
        { geometryMode: config.geometryMode },
      );
    }

    let contourIoUSum = 0;
    let vertexCount = 0;
    const shapes = selectedHierarchy.built.components.map((component, index) => {
      let geometry;
      if (canonicalContour) {
        const rings = canonicalContour.loopsByRegion[index].map((ring) => (
          ring.map((point) => point.slice())
        ));
        geometry = {
          polygon: rings[0] || [],
          rings,
          contourIoU: canonicalContour.regionIoU[index],
          epsilon: null,
        };
      } else {
        geometry = componentGeometry(
          component,
          selectedHierarchy.built.componentIds,
          width,
          height,
          config.contourFidelity,
        );
      }
      contourIoUSum += geometry.contourIoU;
      vertexCount += geometry.rings.reduce((sum, ring) => sum + ring.length, 0);
      return {
        id: component.id,
        sourceId: component.sourceId,
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

    const result = {
      version: VERSION,
      centers: palette.palette.map((entry) => entry.rgb),
      shapes,
      background: borderColor(rgba, width, height, config.alphaThreshold),
      metrics: {
        targetSuperpixels: targetCount,
        regionSize,
        initialRegionCount: segmented.regionCount,
        edgeCoverage,
        budgetMergeCount: hierarchy.totalMergeCount,
        safeMergeCount: hierarchy.safeMergeCount,
        hierarchyMergeCount: hierarchy.hierarchyMergeCount,
        finalRootCount: hierarchy.finalRootCount,
        mergeEvaluationCount: hierarchy.evaluationCount,
        blockedMergeEvaluationCount: hierarchy.blockedEvaluationCount || 0,
        safeCandidateCount: hierarchy.safeCandidateCount,
        subjectGuidance: Boolean(config.subjectProb && config.subjectConfidence),
        componentCount: hierarchy.built.components.length,
        hierarchyCutCount: selectedHierarchy.selectedCount,
        selectiveMergeApplied: selectiveMergeMetrics.applied,
        selectiveMergeEvaluated: selectiveMergeMetrics.evaluated,
        selectiveMergeRejected: selectiveMergeMetrics.rejected,
        selectiveMergeRecoloredPixels: selectiveMergeMetrics.changedPixels,
        selectiveMergeNearPaletteCandidates: selectiveMergeMetrics.candidateNearPalette,
        selectiveMergeColorRejections: selectiveMergeMetrics.rejectedColorFidelity,
        selectiveMergeRejectReasons: selectiveMergeMetrics.rejectReasons,
        selectiveMergeRenderGate: "not_needed",
        selectiveMergeRenderChangedPixels: 0,
        cutObjective: hierarchy.cutObjective,
        cutNormalizedVisualLoss: hierarchy.cutNormalizedVisualLoss,
        cutMaxHeight: hierarchy.cutMaxHeight,
        structuralPreprocess,
        paletteCount: palette.palette.length,
        paletteMethod: palette.method,
        paletteRelationshipCount: palette.relationshipCount,
        paletteRepairCount: palette.repairedSplitCount,
        retried: segmented.retried,
        initialEdgeCoverage: segmented.initialEdgeCoverage,
        initialRegionCountBeforeRetry: segmented.initialRegionCountBeforeRetry ?? segmented.regionCount,
        meanContourIoU: shapes.length > 0 ? contourIoUSum / shapes.length : 1,
        vertexCount,
        contourMethod: canonicalContour ? canonicalContour.method : "legacy-independent-rings",
        contourGeometryMode: canonicalContour ? canonicalContour.metrics.geometryMode : "legacy",
        cornerPrunedVertices: canonicalContour ? canonicalContour.metrics.cornerPrunedVertices : 0,
        cornerPrunedChains: canonicalContour ? canonicalContour.metrics.cornerPrunedChains : 0,
        cornerRejectedCandidates: canonicalContour ? canonicalContour.metrics.cornerRejectedCandidates : 0,
        facetRemovedVertices: canonicalContour ? canonicalContour.metrics.facetRemovedVertices : 0,
        facetTrialCount: canonicalContour ? canonicalContour.metrics.facetTrialCount : 0,
        facetRefinedChains: canonicalContour ? canonicalContour.metrics.facetRefinedChains : 0,
        facetRejectedCandidates: canonicalContour ? canonicalContour.metrics.facetRejectedCandidates : 0,
        contourOriginalVertexCount: canonicalContour
          ? canonicalContour.metrics.originalVertexCount
          : vertexCount,
        contourSharedVertexCount: canonicalContour
          ? canonicalContour.metrics.simplifiedVertexCount
          : vertexCount,
        contourFallbackChainCount: canonicalContour
          ? canonicalContour.metrics.fallbackChainCount
          : 0,
        contourRejectedCandidateCount: canonicalContour
          ? canonicalContour.metrics.rejectedCandidateCount
          : 0,
        contourMinRegionIoU: canonicalContour
          ? canonicalContour.metrics.minRegionIoU
          : (shapes.length > 0 ? Math.min(...shapes.map((shape) => shape.contourIoU)) : 1),
      },
    };
    if(config.selectiveRegionMerge===true && selectiveMergeMetrics.applied>0) {
      const base=analyzeRgba(rgba,width,height,{...config,selectiveRegionMerge:false});
      const verified=compareRegionRenderFidelity(
        base.shapes,result.shapes,width,height,config.selectiveRenderGuard);
      if(!verified.pass) {
        base.metrics={...base.metrics,
          selectiveMergeApplied:0,
          selectiveMergeEvaluated:selectiveMergeMetrics.evaluated,
          selectiveMergeRejected:selectiveMergeMetrics.rejected,
          selectiveMergeNearPaletteCandidates:selectiveMergeMetrics.candidateNearPalette,
          selectiveMergeColorRejections:selectiveMergeMetrics.rejectedColorFidelity,
          selectiveMergeRejectReasons:selectiveMergeMetrics.rejectReasons,
          selectiveMergeRenderGate:"rejected:"+verified.reason,
          selectiveMergeRenderChangedPixels:verified.changedPixels};
        return base;
      }
      result.metrics.selectiveMergeRenderGate="pass";
      result.metrics.selectiveMergeRenderChangedPixels=verified.changedPixels;
    }
    return result;
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

  function nativeCompositeRgba(image) {
    const canvas = canvasElement(image.width, image.height);
    const context = context2d(canvas);
    context.fillStyle = "rgb(255,255,255)";
    context.fillRect(0, 0, image.width, image.height);
    context.drawImage(image, 0, 0, image.width, image.height);
    return context.getImageData(0, 0, image.width, image.height).data;
  }

  function compositeImageToRgba(image, width, height) {
    const canvas = canvasElement(width, height);
    const context = context2d(canvas);
    context.fillStyle = "rgb(255,255,255)";
    context.fillRect(0, 0, width, height);
    context.imageSmoothingEnabled = true;
    if ("imageSmoothingQuality" in context) context.imageSmoothingQuality = "high";
    context.drawImage(image, 0, 0, image.width, image.height, 0, 0, width, height);
    return context.getImageData(0, 0, width, height).data;
  }

  function resizeAnalysisRgba(sourceRgba, sourceWidth, sourceHeight, destinationWidth, destinationHeight) {
    if (sourceWidth === destinationWidth && sourceHeight === destinationHeight) {
      const copy = new Uint8ClampedArray(sourceRgba.length);
      copy.set(sourceRgba);
      return { rgba: copy, method: "native" };
    }

    if (
      typeof globalThis !== "undefined"
      && globalThis.MinimalizerOpenCvAreaResize
      && typeof globalThis.MinimalizerOpenCvAreaResize.resizeRgba === "function"
    ) {
      return {
        rgba: globalThis.MinimalizerOpenCvAreaResize.resizeRgba(
          sourceRgba,
          sourceWidth,
          sourceHeight,
          destinationWidth,
          destinationHeight,
        ),
        method: "opencv-inter-area",
      };
    }

    const sourceCanvas = canvasElement(sourceWidth, sourceHeight);
    const sourceContext = context2d(sourceCanvas);
    const sourceImage = sourceContext.createImageData(sourceWidth, sourceHeight);
    sourceImage.data.set(sourceRgba);
    sourceContext.putImageData(sourceImage, 0, 0);
    const canvas = canvasElement(destinationWidth, destinationHeight);
    const context = context2d(canvas);
    context.drawImage(
      sourceCanvas,
      0,
      0,
      sourceWidth,
      sourceHeight,
      0,
      0,
      destinationWidth,
      destinationHeight,
    );
    return {
      rgba: context.getImageData(0, 0, destinationWidth, destinationHeight).data,
      method: "canvas-fallback",
    };
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
    const scaleX = analysisWidth / workWidth;
    const scaleY = analysisHeight / workHeight;
    const canonicalRaster = (
      analysis.metrics.contourMethod === "canonical-shared-chain"
      && typeof globalThis !== "undefined"
      && globalThis.MinimalizerOpenCvRaster
      && typeof globalThis.MinimalizerOpenCvRaster.renderShapesRgba === "function"
    );

    if (canonicalRaster) {
      const shapes = analysis.shapes.slice().sort((left, right) => left.id - right.id);
      const rgba = globalThis.MinimalizerOpenCvRaster.renderShapesRgba(
        shapes,
        analysisWidth,
        analysisHeight,
        scaleX,
        scaleY,
        2,
      );
      outputContext.putImageData(
        new ImageData(rgba, analysisWidth, analysisHeight),
        0,
        0,
      );
      return {
        canvas: outputCanvas,
        shapes,
        rasterMethod: "opencv-fillpoly-2x",
      };
    }

    outputContext.fillStyle = "rgb(255,255,255)";
    outputContext.fillRect(0, 0, analysisWidth, analysisHeight);
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
    return {
      canvas: outputCanvas,
      shapes,
      rasterMethod: "canvas-evenodd",
    };
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
    if (file && Number.isFinite(file.size) && file.size > config.sourceFileByteLimit) {
      throw new Error("画像ファイルが大きすぎます。64MB以下の画像を使用してください。");
    }
    const image = await decodeFile(file);
    const sourceWidth = image.width;
    const sourceHeight = image.height;
    const sourcePixels = sourceWidth * sourceHeight;
    if (sourcePixels > config.sourcePixelHardLimit) {
      if (typeof image.close === "function") image.close();
      throw new Error("画像の解像度が大きすぎます。1億画素以下の画像を使用してください。");
    }
    const analysisSize = fitSize(sourceWidth, sourceHeight, config.analysisMaxSide);
    let analysisResize;
    if (shouldUseLargeSourceSampling(
      sourceWidth,
      sourceHeight,
      analysisSize.width,
      analysisSize.height,
      config,
    )) {
      analysisResize = {
        rgba: compositeImageToRgba(image, analysisSize.width, analysisSize.height),
        method: "canvas-large-source",
      };
    } else {
      const nativeRgba = nativeCompositeRgba(image);
      analysisResize = resizeAnalysisRgba(
        nativeRgba,
        sourceWidth,
        sourceHeight,
        analysisSize.width,
        analysisSize.height,
      );
    }
    const workSize = fitSize(analysisSize.width, analysisSize.height, config.workMaxSide);
    const workResize = resizeAnalysisRgba(
      analysisResize.rgba,
      analysisSize.width,
      analysisSize.height,
      workSize.width,
      workSize.height,
    );

    let subjectGuidance = null;
    let subjectGuidanceError = null;
    if (
      config.browserSubjectGuidance !== false
      && typeof globalThis !== "undefined"
      && globalThis.MinimalizerBrowserSubject
      && typeof globalThis.MinimalizerBrowserSubject.predict === "function"
    ) {
      try {
        subjectGuidance = await globalThis.MinimalizerBrowserSubject.predict(
          file,
          {
            targetWidth: workSize.width,
            targetHeight: workSize.height,
            nativeMaskPixelLimit: config.nativeRgbaMaxPixels,
          },
        );
        config.subjectProb = subjectGuidance.probability;
        config.subjectConfidence = subjectGuidance.confidence;
      } catch (error) {
        subjectGuidanceError = String(error);
        config.subjectProb = null;
        config.subjectConfidence = null;
      }
    }
    if (typeof image.close === "function") image.close();

    const analysis = analyzeRgba(
      workResize.rgba,
      workSize.width,
      workSize.height,
      config,
    );
    const resizeMethod = workResize.method === "native"
      ? analysisResize.method
      : analysisResize.method + "+" + workResize.method;

    const rendered = renderAnalysis(
      analysis,
      analysisSize.width,
      analysisSize.height,
      workSize.width,
      workSize.height,
    );
    const outputCanvas = rendered.canvas;
    const shapes = rendered.shapes;
    const rasterMethod = rendered.rasterMethod;
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
      "X-Minimalizer-Contour-Method": analysis.metrics.contourMethod,
      "X-Minimalizer-Browser-Quality-Profile": config.selectiveMergeOptions?.allowNearPalette === true ? "near" : config.selectiveRegionMerge === true ? "selective" : config.geometryMode === "facet-safe"
        ? "facet" : config.geometryMode === "corner-aware"
          ? "shape" : config.canonicalContourLite === true
          ? "sharp" : config.structuralMode === "spectral-exact" ? "exact" : "lite",
      "X-Minimalizer-Contour-Geometry-Mode": analysis.metrics.contourGeometryMode,
      "X-Minimalizer-Contour-Corner-Pruned-Vertices": String(analysis.metrics.cornerPrunedVertices),
      "X-Minimalizer-Contour-Facet-Removed-Vertices": String(analysis.metrics.facetRemovedVertices),
      "X-Minimalizer-Contour-Min-IoU": analysis.metrics.contourMinRegionIoU.toFixed(4),
      "X-Minimalizer-Raster-Method": rasterMethod,
      "X-Minimalizer-Budget-Merges": String(analysis.metrics.budgetMergeCount),
      "X-Minimalizer-Superpixel-Count": String(analysis.metrics.initialRegionCount),
      "X-Minimalizer-Edge-Coverage": analysis.metrics.edgeCoverage.toFixed(4),
      "X-Minimalizer-Palette-Count": String(analysis.metrics.paletteCount),
      "X-Minimalizer-Palette-Method": analysis.metrics.paletteMethod,
      "X-Minimalizer-Palette-Repairs": String(analysis.metrics.paletteRepairCount),
      "X-Minimalizer-SLIC-Retried": analysis.metrics.retried ? "1" : "0",
      "X-Minimalizer-Safe-Merges": String(analysis.metrics.safeMergeCount),
      "X-Minimalizer-Hierarchy-Merges": String(analysis.metrics.hierarchyMergeCount),
      "X-Minimalizer-Hierarchy-Cut": String(analysis.metrics.hierarchyCutCount),
      "X-Minimalizer-Selective-Merges": String(analysis.metrics.selectiveMergeApplied),
      "X-Minimalizer-Structural-Preprocess": analysis.metrics.structuralPreprocess,
      "X-Minimalizer-Analysis-Resize": resizeMethod,
      "X-Minimalizer-Source-Sampling": analysisResize.method,
      "X-Minimalizer-Subject-Guidance": subjectGuidance ? subjectGuidance.provider : "unguided",
      "X-Minimalizer-Subject-Model": subjectGuidance ? subjectGuidance.model : "none",
      "X-Minimalizer-Subject-Inference-Ms": subjectGuidance ? subjectGuidance.inferenceMs.toFixed(1) : "0.0",
      "X-Minimalizer-Subject-Decode": subjectGuidance ? subjectGuidance.decodeMethod : "none",
      "X-Minimalizer-L0-Jacobi-Iterations": String(
        analysis.metrics.structuralPreprocess === "l0-lite-jacobi"
          ? config.l0JacobiIterations
          : 0
      ),
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
        contourMethod: analysis.metrics.contourMethod,
        qualityProfile: config.selectiveMergeOptions?.allowNearPalette === true ? "near" : config.selectiveRegionMerge === true ? "selective" : config.geometryMode === "facet-safe"
          ? "facet" : config.geometryMode === "corner-aware"
            ? "shape" : config.canonicalContourLite === true
            ? "sharp" : config.structuralMode === "spectral-exact" ? "exact" : "lite",
        contourGeometryMode: analysis.metrics.contourGeometryMode,
        cornerPrunedVertices: analysis.metrics.cornerPrunedVertices,
        cornerPrunedChains: analysis.metrics.cornerPrunedChains,
        cornerRejectedCandidates: analysis.metrics.cornerRejectedCandidates,
        facetRemovedVertices: analysis.metrics.facetRemovedVertices,
        facetTrialCount: analysis.metrics.facetTrialCount,
        facetRefinedChains: analysis.metrics.facetRefinedChains,
        facetRejectedCandidates: analysis.metrics.facetRejectedCandidates,
        contourMinRegionIoU: analysis.metrics.contourMinRegionIoU,
        contourOriginalVertexCount: analysis.metrics.contourOriginalVertexCount,
        contourSharedVertexCount: analysis.metrics.contourSharedVertexCount,
        contourFallbackChainCount: analysis.metrics.contourFallbackChainCount,
        contourRejectedCandidateCount: analysis.metrics.contourRejectedCandidateCount,
        rasterMethod,
        budgetMergeCount: analysis.metrics.budgetMergeCount,
        vertexCount: analysis.metrics.vertexCount,
        initialRegionCount: analysis.metrics.initialRegionCount,
        edgeCoverage: analysis.metrics.edgeCoverage,
        paletteCount: analysis.metrics.paletteCount,
        paletteMethod: analysis.metrics.paletteMethod,
        paletteRelationshipCount: analysis.metrics.paletteRelationshipCount,
        paletteRepairCount: analysis.metrics.paletteRepairCount,
        regionSize: analysis.metrics.regionSize,
        retried: analysis.metrics.retried,
        initialEdgeCoverage: analysis.metrics.initialEdgeCoverage,
        safeMergeCount: analysis.metrics.safeMergeCount,
        hierarchyMergeCount: analysis.metrics.hierarchyMergeCount,
        hierarchyCutCount: analysis.metrics.hierarchyCutCount,
        selectiveMergeApplied: analysis.metrics.selectiveMergeApplied,
        selectiveMergeEvaluated: analysis.metrics.selectiveMergeEvaluated,
        selectiveMergeRejected: analysis.metrics.selectiveMergeRejected,
        selectiveMergeRecoloredPixels: analysis.metrics.selectiveMergeRecoloredPixels,
        selectiveMergeNearPaletteCandidates: analysis.metrics.selectiveMergeNearPaletteCandidates,
        selectiveMergeColorRejections: analysis.metrics.selectiveMergeColorRejections,
        selectiveMergeRejectReasons: analysis.metrics.selectiveMergeRejectReasons,
        selectiveMergeRenderGate: analysis.metrics.selectiveMergeRenderGate,
        selectiveMergeRenderChangedPixels: analysis.metrics.selectiveMergeRenderChangedPixels || 0,
        mergeEvaluationCount: analysis.metrics.mergeEvaluationCount,
        cutObjective: analysis.metrics.cutObjective,
        cutNormalizedVisualLoss: analysis.metrics.cutNormalizedVisualLoss,
        cutMaxHeight: analysis.metrics.cutMaxHeight,
        structuralPreprocess: analysis.metrics.structuralPreprocess,
        analysisResize: resizeMethod,
        sourceSampling: analysisResize.method,
        sourcePixels,
        subjectGuidance: subjectGuidance ? subjectGuidance.provider : "unguided",
        subjectModel: subjectGuidance ? subjectGuidance.model : null,
        subjectInferenceMs: subjectGuidance ? subjectGuidance.inferenceMs : 0,
        subjectSessionMs: subjectGuidance ? subjectGuidance.sessionMs : 0,
        subjectProcessingMs: subjectGuidance ? subjectGuidance.processingMs : 0,
        subjectDecodeMethod: subjectGuidance ? subjectGuidance.decodeMethod : null,
        subjectResizeMethod: subjectGuidance ? subjectGuidance.resizeMethod : null,
        subjectGuidanceError,
        subjectGuided: Boolean(subjectGuidance),
        l0JacobiIterations: analysis.metrics.structuralPreprocess === "l0-lite-jacobi" ? config.l0JacobiIterations : 0,
        l0BetaMax: analysis.metrics.structuralPreprocess === "l0-lite-jacobi" ? config.l0BetaMax : config.spectralL0BetaMax,
      },
    };
  }

  const api = Object.freeze({
    VERSION,
    DEFAULTS,
    minimalizeFile,
    _core: Object.freeze({
      fitSize,
      shouldUseLargeSourceSampling,
      nativeCompositeRgba,
      compositeImageToRgba,
      resizeAnalysisRgba,
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
      approximateL0StructuralRgba,
      canonicalLabEdgeMap,
      targetSuperpixelCount,
      regionSizeForTarget,
      runSlicoLite,
      oversegmentSpatial,
      splitDisconnectedLabelsJs,
      structuralEdgeCoverageJs,
      buildSpatialGroups,
      mergeSpatialGroupsToBudget,
      buildCanonicalRegionGraph,
      canonicalColorCost,
      canonicalBoundaryCost,
      canonicalTopologyCost,
      canonicalGeometryCost,
      evaluateCanonicalMerge,
      canonicalSafeCandidate,
      runCanonicalRegionHierarchy,
      cutCanonicalHierarchyToCount,
      cutCanonicalHierarchyMinimal,
      consolidateLegacyShapePalette,
      ciede2000Scalar,
      sampleCanonicalPaletteRegions,
      buildCanonicalPaletteRelationships,
      buildCanonicalPaletteSubjectClasses,
      canonicalPaletteSubjectConflict,
      buildCanonicalPaletteHierarchy,
      cutCanonicalPaletteHierarchy,
      repairCanonicalPaletteRelationships,
      consolidateCanonicalPalette,
      mergeAcceptedPaletteRegions,
      compareRegionRenderFidelity,
      analyzeRgba,
      renderAnalysis,
    }),
  });

  root.MinimalizerBrowserFallback = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof window !== "undefined" ? window : globalThis));
