(function (root) {
  "use strict";

  const VERSION = "canonical-contour-v1";

  const DEFAULTS = Object.freeze({
    epsilonRatio: 0.022,
    epsilonMinPx: 0.75,
    epsilonMaxPx: 18.0,
    candidateFactors: Object.freeze([1.0, 0.75, 0.50, 0.25, 0.0]),
    maxAreaChange: 0.08,
    minIoU: 0.90,
    maxCentroidShiftRatio: 0.04,
    maxDirectionalLoss: 0.14,
    majorMassDirectionalFactor: 0.80,
    majorMassRatio: 0.03,
    planarLineFitMinPoints: 4,
    planarLineFitMinSpanDiagonalRatio: 0.03,
    planarLineFitMaxDeviationDiagonalRatio: 0.004,
    planarLineFitMinEfficiency: 0.94,
    cornerPruneMaxDeviationPx: 1.65,
    cornerPruneFactors: Object.freeze([1.0, 0.75, 0.50]),
    cornerProtectArmMinPx: 3.5,
    cornerProtectTurnDegrees: 55,
    cornerPruneMinIoUDelta: 0.004,
  });

  function pointKey(point) {
    return point[0] + "," + point[1];
  }

  function comparePoint(a, b) {
    return a[0] - b[0] || a[1] - b[1];
  }

  function samePoint(a, b) {
    return a[0] === b[0] && a[1] === b[1];
  }

  function canonicalPair(a, b) {
    return a <= b ? [a, b] : [b, a];
  }

  function pairKey(pair) {
    return pair[0] + "," + pair[1];
  }

  function canonicalEdge(a, b) {
    return comparePoint(a, b) <= 0 ? [a, b] : [b, a];
  }

  function edgeKey(a, b) {
    const edge = canonicalEdge(a, b);
    return pointKey(edge[0]) + "|" + pointKey(edge[1]);
  }

  function directionKey(pair, a, b, regionId) {
    return pairKey(pair) + "|" + edgeKey(a, b) + "|" + regionId;
  }

  function addMapSet(map, key, value) {
    let set = map.get(key);
    if (!set) {
      set = new Set();
      map.set(key, set);
    }
    set.add(value);
  }

  function extractRawSegments(labels, width, height) {
    const pairEdges = new Map();
    const halfedgeDirs = new Map();
    const incidentRegions = new Map();
    const points = new Map();

    function remember(point) {
      const key = pointKey(point);
      if (!points.has(key)) points.set(key, point);
      return key;
    }

    function addSegment(a, b, sideA, sideB, orientations) {
      if (sideA === sideB) return;
      const pair = canonicalPair(sideA, sideB);
      const pk = pairKey(pair);
      let record = pairEdges.get(pk);
      if (!record) {
        record = { pair, edges: new Map() };
        pairEdges.set(pk, record);
      }
      const ek = edgeKey(a, b);
      if (!record.edges.has(ek)) {
        const edge = canonicalEdge(a, b);
        record.edges.set(ek, edge);
      }
      const ak = remember(a);
      const bk = remember(b);
      for (const regionId of [sideA, sideB]) {
        if (regionId >= 0) {
          addMapSet(incidentRegions, ak, regionId);
          addMapSet(incidentRegions, bk, regionId);
        }
      }
      for (const item of orientations) {
        if (item.regionId < 0) continue;
        halfedgeDirs.set(
          directionKey(pair, a, b, item.regionId),
          { start: item.start, end: item.end },
        );
      }
    }

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x <= width; x += 1) {
        const left = x === 0 ? -1 : labels[y * width + x - 1];
        const right = x === width ? -1 : labels[y * width + x];
        const top = [x, y];
        const bottom = [x, y + 1];
        addSegment(top, bottom, left, right, [
          { regionId: left, start: top, end: bottom },
          { regionId: right, start: bottom, end: top },
        ]);
      }
    }
    for (let y = 0; y <= height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const topRegion = y === 0 ? -1 : labels[(y - 1) * width + x];
        const bottomRegion = y === height ? -1 : labels[y * width + x];
        const leftPoint = [x, y];
        const rightPoint = [x + 1, y];
        addSegment(leftPoint, rightPoint, topRegion, bottomRegion, [
          { regionId: bottomRegion, start: leftPoint, end: rightPoint },
          { regionId: topRegion, start: rightPoint, end: leftPoint },
        ]);
      }
    }
    return { pairEdges, halfedgeDirs, incidentRegions, points };
  }

  function pairAdjacency(record, points) {
    const adjacency = new Map();
    function ensure(key) {
      if (!adjacency.has(key)) adjacency.set(key, new Set());
    }
    for (const [a, b] of record.edges.values()) {
      const ak = pointKey(a);
      const bk = pointKey(b);
      ensure(ak);
      ensure(bk);
      adjacency.get(ak).add(bk);
      adjacency.get(bk).add(ak);
      if (!points.has(ak)) points.set(ak, a);
      if (!points.has(bk)) points.set(bk, b);
    }
    return adjacency;
  }

  function connectedVertexComponents(adjacency) {
    const remaining = new Set(adjacency.keys());
    const components = [];
    while (remaining.size) {
      const seed = Array.from(remaining)
        .map((key) => [key, key.split(",").map(Number)])
        .sort((a, b) => comparePoint(a[1], b[1]))[0][0];
      const queue = [seed];
      const component = new Set();
      while (queue.length) {
        const key = queue.shift();
        if (component.has(key)) continue;
        component.add(key);
        const neighbors = Array.from(adjacency.get(key) || [])
          .sort((a, b) => comparePoint(a.split(",").map(Number), b.split(",").map(Number)));
        for (const next of neighbors) if (!component.has(next)) queue.push(next);
      }
      for (const key of component) remaining.delete(key);
      components.push(component);
    }
    return components;
  }

  function farthestPointKey(originKey, keys, points) {
    const origin = points.get(originKey);
    let winner = null;
    let winnerDistance = -1;
    for (const key of keys) {
      const point = points.get(key);
      const dx = point[0] - origin[0];
      const dy = point[1] - origin[1];
      const distance = dx * dx + dy * dy;
      if (
        distance > winnerDistance
        || (
          distance === winnerDistance
          && winner !== null
          && comparePoint(point, points.get(winner)) > 0
        )
      ) {
        winner = key;
        winnerDistance = distance;
      }
    }
    return winner;
  }

  function splitVerticesForPair(
    record,
    adjacency,
    incidentRegions,
    points,
    width,
    height,
  ) {
    const split = new Set();
    for (const [key, neighbors] of adjacency.entries()) {
      const point = points.get(key);
      const incident = incidentRegions.get(key) || new Set();
      const imageCorner = (
        (point[0] === 0 || point[0] === width)
        && (point[1] === 0 || point[1] === height)
      );
      const boundaryJunction = neighbors.size !== 2;
      const onBorder = (
        point[0] === 0 || point[0] === width
        || point[1] === 0 || point[1] === height
      );
      const imageBorderAnchor = (
        onBorder && record.pair[0] >= 0 && record.pair[1] >= 0
      );
      if (
        incident.size >= 3
        || imageCorner
        || boundaryJunction
        || imageBorderAnchor
      ) {
        split.add(key);
      }
    }

    for (const component of connectedVertexComponents(adjacency)) {
      const localSplit = Array.from(component).filter((key) => split.has(key));
      if (localSplit.length >= 2) continue;
      const ordered = Array.from(component)
        .sort((a, b) => comparePoint(points.get(a), points.get(b)));
      let first;
      if (localSplit.length) {
        first = localSplit.sort((a, b) => comparePoint(points.get(a), points.get(b)))[0];
      } else {
        first = ordered[0];
        split.add(first);
      }
      if (component.size > 1) {
        const candidates = Array.from(component).filter((key) => key !== first);
        const second = farthestPointKey(first, candidates, points);
        if (second !== null) split.add(second);
      }
    }
    return split;
  }

  function tracePairChains(record, adjacency, split, points) {
    const visited = new Set();
    const chains = [];
    const splitOrdered = Array.from(split)
      .sort((a, b) => comparePoint(points.get(a), points.get(b)));
    for (const start of splitOrdered) {
      const neighbors = Array.from(adjacency.get(start) || [])
        .sort((a, b) => comparePoint(points.get(a), points.get(b)));
      for (const neighbor of neighbors) {
        const firstEdge = edgeKey(points.get(start), points.get(neighbor));
        if (visited.has(firstEdge)) continue;
        const chain = [points.get(start)];
        let previous = start;
        let current = neighbor;
        visited.add(firstEdge);
        chain.push(points.get(current));
        while (!split.has(current)) {
          const candidates = Array.from(adjacency.get(current) || [])
            .filter((item) => (
              item !== previous
              && !visited.has(edgeKey(points.get(current), points.get(item)))
            ))
            .sort((a, b) => comparePoint(points.get(a), points.get(b)));
          if (!candidates.length) break;
          if (candidates.length > 1) {
            throw new Error("canonical contour chain branches between protected vertices");
          }
          const next = candidates[0];
          visited.add(edgeKey(points.get(current), points.get(next)));
          previous = current;
          current = next;
          chain.push(points.get(current));
        }
        chains.push(chain);
      }
    }
    if (visited.size !== record.edges.size) {
      throw new Error(
        "canonical contour failed to trace "
        + (record.edges.size - visited.size)
        + " boundary segments"
      );
    }
    return chains;
  }

  function buildBoundaryGraph(labels, width, height, regionCount) {
    const raw = extractRawSegments(labels, width, height);
    const pending = [];
    const pairRecords = Array.from(raw.pairEdges.values())
      .sort((a, b) => a.pair[0] - b.pair[0] || a.pair[1] - b.pair[1]);
    for (const record of pairRecords) {
      const adjacency = pairAdjacency(record, raw.points);
      const split = splitVerticesForPair(
        record,
        adjacency,
        raw.incidentRegions,
        raw.points,
        width,
        height,
      );
      const chains = tracePairChains(record, adjacency, split, raw.points);
      for (const points of chains) pending.push({ pair: record.pair, points });
    }

    const endpointKeys = new Map();
    for (const item of pending) {
      endpointKeys.set(pointKey(item.points[0]), item.points[0]);
      endpointKeys.set(pointKey(item.points[item.points.length - 1]), item.points[item.points.length - 1]);
    }
    const endpointCoords = Array.from(endpointKeys.values()).sort(comparePoint);
    const coordToVertex = new Map(
      endpointCoords.map((point, index) => [pointKey(point), index])
    );
    const vertices = endpointCoords.map((point, id) => ({ id, point }));
    const chains = [];
    const regionChains = Array.from({ length: regionCount }, () => []);

    for (let chainId = 0; chainId < pending.length; chainId += 1) {
      const item = pending[chainId];
      const regions = item.pair.filter((value) => value >= 0);
      const chain = {
        id: chainId,
        startVertex: coordToVertex.get(pointKey(item.points[0])),
        endVertex: coordToVertex.get(pointKey(item.points[item.points.length - 1])),
        points: item.points.map((point) => point.slice()),
        regions,
        originalPointCount: item.points.length,
      };
      chains.push(chain);
      for (const regionId of regions) {
        const first = item.points[0];
        const second = item.points[1];
        const direction = raw.halfedgeDirs.get(
          directionKey(item.pair, first, second, regionId)
        );
        if (!direction) throw new Error("missing canonical contour half-edge direction");
        let reversed;
        if (samePoint(direction.start, first) && samePoint(direction.end, second)) {
          reversed = false;
        } else if (
          samePoint(direction.start, second) && samePoint(direction.end, first)
        ) {
          reversed = true;
        } else {
          throw new Error("inconsistent canonical contour half-edge direction");
        }
        regionChains[regionId].push({ chainId, reversed });
      }
    }
    for (const refs of regionChains) {
      refs.sort((a, b) => a.chainId - b.chainId || Number(a.reversed) - Number(b.reversed));
    }
    if (regionChains.some((refs) => refs.length === 0)) {
      throw new Error("canonical contour graph is missing a region");
    }
    return { vertices, chains, regionChains, width, height };
  }

  function directedEndpoints(graph, ref) {
    const chain = graph.chains[ref.chainId];
    return ref.reversed
      ? [chain.endVertex, chain.startVertex]
      : [chain.startVertex, chain.endVertex];
  }

  function orientedChainPoints(graph, ref, pointsByChain) {
    const source = pointsByChain
      ? pointsByChain[ref.chainId]
      : graph.chains[ref.chainId].points;
    if (!ref.reversed) return source.map((point) => point.slice());
    return source.slice().reverse().map((point) => point.slice());
  }

  function turnPriority(incoming, outgoing) {
    const angleIn = Math.atan2(incoming[1], incoming[0]);
    const angleOut = Math.atan2(outgoing[1], outgoing[0]);
    let delta = (angleOut - angleIn) % (2 * Math.PI);
    if (delta < 0) delta += 2 * Math.PI;
    const eps = 1e-9;
    if (eps < delta && delta < Math.PI - eps) return [0, delta];
    if (delta <= eps || Math.abs(delta - 2 * Math.PI) <= eps) return [1, 0];
    if (Math.PI + eps < delta && delta < 2 * Math.PI - eps) {
      return [2, 2 * Math.PI - delta];
    }
    return [3, 0];
  }

  function compareTuple(a, b) {
    for (let i = 0; i < Math.min(a.length, b.length); i += 1) {
      if (a[i] < b[i]) return -1;
      if (a[i] > b[i]) return 1;
    }
    return a.length - b.length;
  }

  function assembleRegionLoops(graph, regionId, pointsByChain) {
    const refs = graph.regionChains[regionId].slice();
    const unused = new Set(refs.map((_, index) => index));
    const starts = new Map();
    for (let index = 0; index < refs.length; index += 1) {
      const start = directedEndpoints(graph, refs[index])[0];
      if (!starts.has(start)) starts.set(start, []);
      starts.get(start).push(index);
    }
    const loops = [];
    while (unused.size) {
      const index = Array.from(unused).sort((a, b) => (
        refs[a].chainId - refs[b].chainId
        || Number(refs[a].reversed) - Number(refs[b].reversed)
      ))[0];
      const firstRef = refs[index];
      const endpoints = directedEndpoints(graph, firstRef);
      const startVertex = endpoints[0];
      let currentVertex = endpoints[1];
      let points = orientedChainPoints(graph, firstRef, pointsByChain);
      unused.delete(index);
      let incoming = [
        points[points.length - 1][0] - points[points.length - 2][0],
        points[points.length - 1][1] - points[points.length - 2][1],
      ];

      while (currentVertex !== startVertex) {
        const candidates = (starts.get(currentVertex) || [])
          .filter((item) => unused.has(item));
        if (!candidates.length) {
          throw new Error("canonical contour region boundary does not close");
        }
        let nextIndex;
        if (candidates.length > 1) {
          nextIndex = candidates
            .map((item) => {
              const candidatePoints = orientedChainPoints(graph, refs[item], pointsByChain);
              const outgoing = [
                candidatePoints[1][0] - candidatePoints[0][0],
                candidatePoints[1][1] - candidatePoints[0][1],
              ];
              return {
                item,
                key: turnPriority(incoming, outgoing).concat([refs[item].chainId]),
              };
            })
            .sort((a, b) => compareTuple(a.key, b.key))[0].item;
        } else {
          nextIndex = candidates[0];
        }
        const nextRef = refs[nextIndex];
        currentVertex = directedEndpoints(graph, nextRef)[1];
        const nextPoints = orientedChainPoints(graph, nextRef, pointsByChain);
        incoming = [
          nextPoints[nextPoints.length - 1][0] - nextPoints[nextPoints.length - 2][0],
          nextPoints[nextPoints.length - 1][1] - nextPoints[nextPoints.length - 2][1],
        ];
        points = points.concat(nextPoints.slice(1));
        unused.delete(nextIndex);
      }
      if (samePoint(points[0], points[points.length - 1])) points.pop();
      if (points.length < 3) throw new Error("canonical contour loop has fewer than 3 points");
      loops.push(points);
    }
    return loops;
  }

  function microCleanup(points) {
    if (points.length <= 2) return points.map((point) => point.slice());
    const kept = [points[0].slice()];
    for (let index = 1; index < points.length - 1; index += 1) {
      const a = kept[kept.length - 1];
      const b = points[index];
      const c = points[index + 1];
      const ab = [b[0] - a[0], b[1] - a[1]];
      const bc = [c[0] - b[0], c[1] - b[1]];
      const cross = ab[0] * bc[1] - ab[1] * bc[0];
      const dot = ab[0] * bc[0] + ab[1] * bc[1];
      if (Math.abs(cross) <= 1e-6 && dot >= 0) continue;
      kept.push(b.slice());
    }
    kept.push(points[points.length - 1].slice());
    return kept;
  }

  function pointSegmentDistance(point, start, end) {
    const vx = end[0] - start[0];
    const vy = end[1] - start[1];
    const wx = point[0] - start[0];
    const wy = point[1] - start[1];
    const denominator = vx * vx + vy * vy;
    if (denominator <= 1e-20) return Math.hypot(wx, wy);
    let t = (wx * vx + wy * vy) / denominator;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(
      point[0] - (start[0] + t * vx),
      point[1] - (start[1] + t * vy),
    );
  }

  function simplifyOpenCvOpen(points, epsilon) {
    const count = points.length;
    if (count <= 2) return points.map((point) => point.slice());
    const epsSquared = epsilon * epsilon;
    const stack = [{ start: 0, end: count - 1 }];
    const approximated = [];

    while (stack.length > 0) {
      const slice = stack.pop();
      const startPoint = points[slice.start];
      const endPoint = points[slice.end];
      if (slice.start + 1 >= slice.end) {
        approximated.push(startPoint.slice());
        continue;
      }

      const dx = endPoint[0] - startPoint[0];
      const dy = endPoint[1] - startPoint[1];
      const segmentLengthSquared = dx * dx + dy * dy;
      if (segmentLengthSquared <= 0) {
        approximated.push(startPoint.slice());
        continue;
      }

      let maximumDistanceScaled = 0;
      let splitIndex = slice.start;
      for (let index = slice.start + 1; index < slice.end; index += 1) {
        const point = points[index];
        const rx = point[0] - startPoint[0];
        const ry = point[1] - startPoint[1];
        const projection = rx * dx + ry * dy;
        let distanceScaled;
        if (projection < 0) {
          distanceScaled = (rx * rx + ry * ry) * segmentLengthSquared;
        } else if (projection > segmentLengthSquared) {
          const ex = point[0] - endPoint[0];
          const ey = point[1] - endPoint[1];
          distanceScaled = (ex * ex + ey * ey) * segmentLengthSquared;
        } else {
          const cross = ry * dx - rx * dy;
          distanceScaled = cross * cross;
        }
        if (distanceScaled > maximumDistanceScaled) {
          maximumDistanceScaled = distanceScaled;
          splitIndex = index;
        }
      }

      if (maximumDistanceScaled <= epsSquared * segmentLengthSquared) {
        approximated.push(startPoint.slice());
      } else {
        // OpenCV pushes right first and left second onto a LIFO stack.
        stack.push({ start: splitIndex, end: slice.end });
        stack.push({ start: slice.start, end: splitIndex });
      }
    }
    approximated.push(points[count - 1].slice());

    if (approximated.length <= 2) return approximated;

    // Match approxPolyDP_'s final open-curve cleanup pass. The OpenCV
    // implementation mutates the destination array in place; this equivalent
    // list form preserves the same scan order and skip-after-removal rule.
    const cleaned = approximated.map((point) => point.slice());
    let newCount = cleaned.length;
    let startPoint = cleaned[0];
    let point = cleaned[1];
    let writePosition = 1;
    let position = 2;
    let iteration = 1;

    while (iteration < cleaned.length - 1 && newCount > 2) {
      const endPoint = cleaned[position];
      position += 1;
      const dx = endPoint[0] - startPoint[0];
      const dy = endPoint[1] - startPoint[1];
      const dist = Math.abs(
        (point[0] - startPoint[0]) * dy
        - (point[1] - startPoint[1]) * dx
      );
      const successiveInnerProduct = (
        (point[0] - startPoint[0]) * (endPoint[0] - point[0])
        + (point[1] - startPoint[1]) * (endPoint[1] - point[1])
      );

      if (
        dist * dist <= 0.5 * epsSquared * (dx * dx + dy * dy)
        && dx !== 0
        && dy !== 0
        && successiveInnerProduct >= 0
      ) {
        newCount -= 1;
        cleaned[writePosition] = endPoint.slice();
        startPoint = endPoint;
        writePosition += 1;
        if (position < cleaned.length) {
          point = cleaned[position].slice();
          position += 1;
        }
        iteration += 2;
        continue;
      }

      cleaned[writePosition] = point.slice();
      startPoint = point;
      writePosition += 1;
      point = endPoint;
      iteration += 1;
    }

    cleaned[writePosition] = point.slice();
    return cleaned.slice(0, newCount);
  }

  function simplifyOpenChain(points, epsilon) {
    const cleaned = microCleanup(points);
    if (epsilon <= 0 || cleaned.length <= 2) return cleaned;
    const candidate = simplifyOpenCvOpen(cleaned, epsilon);
    if (candidate.length < 2) return cleaned;
    candidate[0] = cleaned[0].slice();
    candidate[candidate.length - 1] = cleaned[cleaned.length - 1].slice();
    return candidate;
  }

  function chainLength(points) {
    let total = 0;
    for (let i = 1; i < points.length; i += 1) {
      total += Math.hypot(
        points[i][0] - points[i - 1][0],
        points[i][1] - points[i - 1][1],
      );
    }
    return total;
  }

  function epsilonForChain(chain, factor, config) {
    if (factor <= 0) return 0;
    const raw = chainLength(chain.points) * config.epsilonRatio * factor;
    return Math.max(config.epsilonMinPx, Math.min(config.epsilonMaxPx, raw));
  }

  function pointInRing(x, y, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
      const xi = ring[i][0], yi = ring[i][1];
      const xj = ring[j][0], yj = ring[j][1];
      const intersects = (
        ((yi > y) !== (yj > y))
        && x < ((xj - xi) * (y - yi)) / ((yj - yi) || Number.EPSILON) + xi
      );
      if (intersects) inside = !inside;
    }
    return inside;
  }

  function pointInRings(x, y, rings) {
    let inside = false;
    for (const ring of rings) if (pointInRing(x, y, ring)) inside = !inside;
    return inside;
  }

  function topologySignatureFromPixels(pixels, width, bounds) {
    const localWidth = bounds.maxX - bounds.minX + 1;
    const localHeight = bounds.maxY - bounds.minY + 1;
    const binary = new Uint8Array(localWidth * localHeight);
    for (const index of pixels) {
      const x = index % width;
      const y = Math.floor(index / width);
      const local = (y - bounds.minY) * localWidth + (x - bounds.minX);
      binary[local] = 1;
    }

    function componentCount(target, countHoles) {
      const visited = new Uint8Array(binary.length);
      let count = 0;
      for (let start = 0; start < binary.length; start += 1) {
        if (visited[start] || binary[start] !== target) continue;
        const queue = [start];
        visited[start] = 1;
        let touchesBorder = false;
        while (queue.length) {
          const index = queue.pop();
          const x = index % localWidth;
          const y = Math.floor(index / localWidth);
          if (x === 0 || y === 0 || x === localWidth - 1 || y === localHeight - 1) {
            touchesBorder = true;
          }
          const neighbors = [];
          if (x > 0) neighbors.push(index - 1);
          if (x + 1 < localWidth) neighbors.push(index + 1);
          if (y > 0) neighbors.push(index - localWidth);
          if (y + 1 < localHeight) neighbors.push(index + localWidth);
          for (const next of neighbors) {
            if (!visited[next] && binary[next] === target) {
              visited[next] = 1;
              queue.push(next);
            }
          }
        }
        if (!countHoles || !touchesBorder) count += 1;
      }
      return count;
    }

    return {
      components: componentCount(1, false),
      holes: componentCount(0, true),
    };
  }

  function regionStats(labels, width, height, regionCount) {
    const stats = Array.from({ length: regionCount }, () => ({
      area: 0,
      minX: width,
      minY: height,
      maxX: -1,
      maxY: -1,
      sumX: 0,
      sumY: 0,
      pixels: [],
    }));
    for (let index = 0; index < labels.length; index += 1) {
      const id = labels[index];
      const x = index % width;
      const y = Math.floor(index / width);
      const item = stats[id];
      item.area += 1;
      item.minX = Math.min(item.minX, x);
      item.minY = Math.min(item.minY, y);
      item.maxX = Math.max(item.maxX, x);
      item.maxY = Math.max(item.maxY, y);
      item.sumX += x + 0.5;
      item.sumY += y + 0.5;
      item.pixels.push(index);
    }
    for (const item of stats) {
      item.centroid = [item.sumX / item.area, item.sumY / item.area];
      item.diagonal = Math.max(
        1,
        Math.hypot(item.maxX - item.minX + 1, item.maxY - item.minY + 1),
      );
      item.extents = directionalExtentsForPixels(item.pixels, width, item.centroid);
      item.topology = topologySignatureFromPixels(item.pixels, width, item);
    }
    return stats;
  }

  function directionalExtentsForPixels(pixels, width, centroid) {
    const extents = new Float64Array(8);
    for (let direction = 0; direction < 8; direction += 1) {
      const angle = direction * Math.PI / 4;
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      let maximum = 0;
      for (const index of pixels) {
        const x = index % width;
        const y = Math.floor(index / width);
        const projection = (
          (x + 0.5 - centroid[0]) * cos
          + (y + 0.5 - centroid[1]) * sin
        );
        if (projection > maximum) maximum = projection;
      }
      extents[direction] = maximum;
    }
    return extents;
  }

  function rasterizeRegionLoops(loops, stats, width, height) {
    const mask = new Uint8Array(width * height);
    let area = 0;
    let sumX = 0;
    let sumY = 0;
    const pixels = [];
    const exactRaster = (
      typeof globalThis !== "undefined"
      && globalThis.MinimalizerOpenCvRaster
      && typeof globalThis.MinimalizerOpenCvRaster.rasterizeLoops === "function"
    );

    if (exactRaster) {
      const localWidth = stats.maxX - stats.minX + 1;
      const localHeight = stats.maxY - stats.minY + 1;
      const shiftedLoops = (loops || []).map((loop) => loop.map((point) => [
        point[0] - stats.minX,
        point[1] - stats.minY,
      ]));
      const localMask = globalThis.MinimalizerOpenCvRaster.rasterizeLoops(
        shiftedLoops,
        localWidth,
        localHeight,
        2,
      );
      for (let localY = 0; localY < localHeight; localY += 1) {
        const y = stats.minY + localY;
        for (let localX = 0; localX < localWidth; localX += 1) {
          if (!localMask[localY * localWidth + localX]) continue;
          const x = stats.minX + localX;
          const index = y * width + x;
          mask[index] = 1;
          area += 1;
          sumX += x + 0.5;
          sumY += y + 0.5;
          pixels.push(index);
        }
      }
    } else {
      for (let y = stats.minY; y <= stats.maxY; y += 1) {
        for (let x = stats.minX; x <= stats.maxX; x += 1) {
          if (!pointInRings(x + 0.5, y + 0.5, loops)) continue;
          const index = y * width + x;
          mask[index] = 1;
          area += 1;
          sumX += x + 0.5;
          sumY += y + 0.5;
          pixels.push(index);
        }
      }
    }
    return {
      mask,
      area,
      pixels,
      centroid: area > 0 ? [sumX / area, sumY / area] : [0, 0],
      rasterMethod: exactRaster ? "opencv-fillpoly-2x" : "pixel-center-evenodd",
    };
  }

  function regionMetrics(original, candidate, width, totalPixels, config) {
    if (candidate.area <= 0) {
      return {
        iou: 0,
        areaChange: 1,
        centroidShiftRatio: 1,
        directionalLoss: 1,
        valid: false,
      };
    }
    let intersection = 0;
    for (const index of original.pixels) {
      if (candidate.mask[index]) intersection += 1;
    }
    const union = original.area + candidate.area - intersection;
    const iou = intersection / Math.max(union, 1);
    const areaChange = Math.abs(candidate.area - original.area) / original.area;
    const centroidShiftRatio = Math.hypot(
      candidate.centroid[0] - original.centroid[0],
      candidate.centroid[1] - original.centroid[1],
    ) / original.diagonal;
    const candidateExtents = directionalExtentsForPixels(
      candidate.pixels,
      width,
      original.centroid,
    );
    let directionalLoss = 0;
    for (let i = 0; i < 8; i += 1) {
      const denominator = Math.max(original.extents[i], 1);
      directionalLoss = Math.max(
        directionalLoss,
        Math.max(original.extents[i] - candidateExtents[i], 0) / denominator,
      );
    }
    const directionalLimit = config.maxDirectionalLoss * (
      original.area / totalPixels >= config.majorMassRatio
        ? config.majorMassDirectionalFactor
        : 1
    );
    const candidateTopology = topologySignatureFromPixels(
      candidate.pixels,
      width,
      original,
    );
    const topologyOk = (
      candidateTopology.components === original.topology.components
      && candidateTopology.holes === original.topology.holes
    );
    return {
      iou,
      areaChange,
      centroidShiftRatio,
      directionalLoss,
      directionalLimit,
      topologyOk,
      valid: (
        topologyOk
        && areaChange <= config.maxAreaChange
        && iou >= config.minIoU
        && centroidShiftRatio <= config.maxCentroidShiftRatio
        && directionalLoss <= directionalLimit
      ),
    };
  }

  function orientation(a, b, c) {
    return (
      (b[0] - a[0]) * (c[1] - a[1])
      - (b[1] - a[1]) * (c[0] - a[0])
    );
  }

  function onSegment(a, b, p) {
    const eps = 1e-6;
    return (
      Math.min(a[0], b[0]) - eps <= p[0]
      && p[0] <= Math.max(a[0], b[0]) + eps
      && Math.min(a[1], b[1]) - eps <= p[1]
      && p[1] <= Math.max(a[1], b[1]) + eps
      && Math.abs(orientation(a, b, p)) <= eps
    );
  }

  function segmentsIntersect(a, b, c, d) {
    const eps = 1e-6;
    const o1 = orientation(a, b, c);
    const o2 = orientation(a, b, d);
    const o3 = orientation(c, d, a);
    const o4 = orientation(c, d, b);
    if (
      ((o1 > eps && o2 < -eps) || (o1 < -eps && o2 > eps))
      && ((o3 > eps && o4 < -eps) || (o3 < -eps && o4 > eps))
    ) return true;
    return (
      (Math.abs(o1) <= eps && onSegment(a, b, c))
      || (Math.abs(o2) <= eps && onSegment(a, b, d))
      || (Math.abs(o3) <= eps && onSegment(c, d, a))
      || (Math.abs(o4) <= eps && onSegment(c, d, b))
    );
  }

  function candidateChainIntersectionFree(graph, regionId, chainId, pointsByChain) {
    const candidate = pointsByChain[chainId];
    const segments = [];
    for (let i = 0; i + 1 < candidate.length; i += 1) {
      segments.push([candidate[i], candidate[i + 1]]);
    }
    for (let i = 0; i < segments.length; i += 1) {
      for (let j = i + 2; j < segments.length; j += 1) {
        if (segmentsIntersect(
          segments[i][0], segments[i][1], segments[j][0], segments[j][1]
        )) return false;
      }
    }

    const otherSegments = [];
    for (const ref of graph.regionChains[regionId]) {
      if (ref.chainId === chainId) continue;
      const other = orientedChainPoints(graph, ref, pointsByChain);
      for (let i = 0; i + 1 < other.length; i += 1) {
        otherSegments.push([other[i], other[i + 1]]);
      }
    }
    const eps = 1e-6;
    for (const [a, b] of segments) {
      for (const [c, d] of otherSegments) {
        const shared = [];
        for (const first of [a, b]) {
          for (const second of [c, d]) {
            if (samePoint(first, second)) shared.push(first);
          }
        }
        if (shared.length) {
          if (shared.length > 1) return false;
          const point = shared[0];
          const otherA = samePoint(a, point) ? b : a;
          const otherB = samePoint(c, point) ? d : c;
          if (Math.abs(orientation(point, otherA, otherB)) <= eps) {
            const dot = (
              (otherA[0] - point[0]) * (otherB[0] - point[0])
              + (otherA[1] - point[1]) * (otherB[1] - point[1])
            );
            if (dot > eps) return false;
          }
          continue;
        }
        if (segmentsIntersect(a, b, c, d)) return false;
      }
    }
    return true;
  }

  function candidateValidForRegions(
    graph,
    labels,
    stats,
    pointsByChain,
    chainId,
    regionIds,
    width,
    height,
    config,
  ) {
    const totalPixels = labels.length;
    for (const regionId of regionIds) {
      if (!candidateChainIntersectionFree(graph, regionId, chainId, pointsByChain)) {
        return false;
      }
      const loops = assembleRegionLoops(graph, regionId, pointsByChain);
      const candidate = rasterizeRegionLoops(loops, stats[regionId], width, height);
      const metrics = regionMetrics(
        stats[regionId],
        candidate,
        width,
        totalPixels,
        config,
      );
      if (!metrics.valid) return false;
    }
    return true;
  }

  function planarLineCandidate(points, width, height, config) {
    if (points.length < config.planarLineFitMinPoints) return points;
    const diagonal = Math.max(1, Math.hypot(width, height));
    const minSpan = diagonal * config.planarLineFitMinSpanDiagonalRatio;
    const maxDeviation = diagonal * config.planarLineFitMaxDeviationDiagonalRatio;
    const output = [points[0].slice()];
    let start = 0;
    while (start < points.length - 1) {
      let best = start + 1;
      const minimumEnd = start + config.planarLineFitMinPoints - 1;
      for (let end = points.length - 1; end >= minimumEnd; end -= 1) {
        const first = points[start];
        const last = points[end];
        const dx = last[0] - first[0];
        const dy = last[1] - first[1];
        const chord = Math.hypot(dx, dy);
        if (chord < minSpan) continue;
        let arc = 0;
        for (let i = start + 1; i <= end; i += 1) {
          arc += Math.hypot(
            points[i][0] - points[i - 1][0],
            points[i][1] - points[i - 1][1],
          );
        }
        if (arc <= 0 || chord / arc < config.planarLineFitMinEfficiency) continue;
        const ux = dx / chord;
        const uy = dy / chord;
        const nx = -uy;
        const ny = ux;
        let valid = true;
        let maximumDeviation = 0;
        for (let i = start; i <= end; i += 1) {
          const rx = points[i][0] - first[0];
          const ry = points[i][1] - first[1];
          const projection = rx * ux + ry * uy;
          if (projection < -1e-6 || projection > chord + 1e-6) {
            valid = false;
            break;
          }
          maximumDeviation = Math.max(
            maximumDeviation,
            Math.abs(rx * nx + ry * ny),
          );
        }
        if (valid && maximumDeviation <= maxDeviation) {
          best = end;
          break;
        }
      }
      output.push(points[best].slice());
      start = best;
    }
    return output;
  }

  // Local geometric cleanup after the conservative OpenCV-compatible DP pass.
  // Only existing vertices are removed; shared arcs, color ownership and endpoints
  // remain unchanged. Evaluate skipped *raw* contour points against the new chord,
  // rather than relying on the already simplified intermediate vertices.
  function cornerAwareLineCandidate(points, rawPoints, tolerance, config) {
    if (points.length < 3 || !(tolerance > 0)) {
      return points.map((point) => point.slice());
    }
    const rawIndices = [];
    let cursor = 0;
    for (const point of points) {
      while (cursor < rawPoints.length && !samePoint(rawPoints[cursor], point)) {
        cursor += 1;
      }
      if (cursor >= rawPoints.length) {
        return points.map((p) => p.slice());
      }
      rawIndices.push(cursor);
      cursor += 1;
    }

    const survivor = points.map((_, i) => i);
    const protectedAngle = config.cornerProtectTurnDegrees * Math.PI / 180;
    const rawMaxDev = tolerance;
    // The hard work bound is deterministic. It prevents unexpectedly large
    // inputs from turning this optional simplifier into an unbounded search.
    const workBudget = Math.min(points.length * points.length, 150000);
    let inspected = 0;

    while (survivor.length > 2 && inspected < workBudget) {
      let bestIndex = -1;
      let bestScore = Infinity;
      for (let j = 1; j + 1 < survivor.length && inspected < workBudget; j += 1) {
        inspected += 1;
        const ia = survivor[j - 1];
        const ib = survivor[j];
        const ic = survivor[j + 1];
        const a = points[ia], b = points[ib], c = points[ic];
        const ux = b[0] - a[0], uy = b[1] - a[1];
        const vx = c[0] - b[0], vy = c[1] - b[1];
        const la = Math.hypot(ux, uy), lb = Math.hypot(vx, vy);
        if (!(la > 0 && lb > 0)) continue;
        const bend = Math.atan2(Math.abs(ux * vy - uy * vx), ux * vx + uy * vy);
        if (
          bend >= protectedAngle
          && Math.min(la, lb) >= config.cornerProtectArmMinPx
        ) continue;
        let highest = 0;
        let valid = true;
        const firstRaw = rawIndices[ia];
        const lastRaw = rawIndices[ic];
        for (let k = firstRaw + 1; k < lastRaw; k += 1) {
          const dev = pointSegmentDistance(rawPoints[k], a, c);
          if (dev > rawMaxDev) { valid = false; break; }
          highest = Math.max(highest, dev);
        }
        if (!valid) continue;
        // Favor small stair notches before longer, meaningful corners.
        const score = highest + 0.004 * (la + lb) + 0.00001 * ib;
        if (score < bestScore) {
          bestScore = score;
          bestIndex = j;
        }
      }
      if (bestIndex < 0) break;
      survivor.splice(bestIndex, 1);
    }
    return survivor.map((i) => points[i].slice());
  }

  function simplifyLabels(labels, width, height, regionCount, options) {
    const config = Object.assign({}, DEFAULTS, options || {});
    const geometryMode = config.geometryMode || "baseline";
    if (geometryMode !== "baseline" && geometryMode !== "corner-aware") {
      throw new Error("Unsupported geometry mode: " + geometryMode);
    }
    const graph = buildBoundaryGraph(labels, width, height, regionCount);
    const stats = regionStats(labels, width, height, regionCount);
    const pointsByChain = graph.chains.map((chain) => (
      chain.points.map((point) => point.slice())
    ));
    let fallbackChainCount = 0;
    let rejectedCandidateCount = 0;
    let cornerPrunedChains = 0;
    let cornerPrunedVertices = 0;
    let cornerRejectedCandidates = 0;

    for (const chain of graph.chains) {
      if (chain.points.length <= 2) continue;
      let accepted = chain.points.map((point) => point.slice());
      let simplified = false;
      for (const factor of config.candidateFactors) {
        const epsilon = epsilonForChain(chain, factor, config);
        const candidate = simplifyOpenChain(chain.points, epsilon);
        if (factor > 0 && candidate.length >= chain.points.length) continue;
        pointsByChain[chain.id] = candidate;
        if (
          factor === 0
          || candidateValidForRegions(
            graph,
            labels,
            stats,
            pointsByChain,
            chain.id,
            chain.regions,
            width,
            height,
            config,
          )
        ) {
          accepted = candidate;
          simplified = factor > 0 && candidate.length < chain.points.length;
          break;
        }
        rejectedCandidateCount += 1;
      }

      if (accepted.length >= config.planarLineFitMinPoints) {
        const planar = planarLineCandidate(accepted, width, height, config);
        if (planar.length < accepted.length) {
          pointsByChain[chain.id] = planar;
          if (candidateValidForRegions(
            graph,
            labels,
            stats,
            pointsByChain,
            chain.id,
            chain.regions,
            width,
            height,
            config,
          )) {
            accepted = planar;
            simplified = true;
          }
        }
      }
      pointsByChain[chain.id] = accepted;
      if (geometryMode === "corner-aware" && accepted.length > 2) {
        const baselineRegionIoU = new Map();
        for (const regionId of chain.regions) {
          const loops = assembleRegionLoops(graph, regionId, pointsByChain);
          const raster = rasterizeRegionLoops(loops, stats[regionId], width, height);
          baselineRegionIoU.set(
            regionId, regionMetrics(stats[regionId], raster, width, labels.length, config).iou
          );
        }
        for (const factor of config.cornerPruneFactors) {
          const candidate = cornerAwareLineCandidate(
            accepted, chain.points, config.cornerPruneMaxDeviationPx * factor, config
          );
          if (candidate.length >= accepted.length) continue;
          pointsByChain[chain.id] = candidate;
          let safe = candidateValidForRegions(
            graph, labels, stats, pointsByChain, chain.id, chain.regions,
            width, height, config
          );
          if (safe) {
            for (const regionId of chain.regions) {
              const loops = assembleRegionLoops(graph, regionId, pointsByChain);
              const raster = rasterizeRegionLoops(loops, stats[regionId], width, height);
              const metrics = regionMetrics(stats[regionId], raster, width, labels.length, config);
              if (
                metrics.iou + config.cornerPruneMinIoUDelta
                < baselineRegionIoU.get(regionId)
              ) {
                safe = false;
                break;
              }
            }
          }
          if (safe) {
            cornerPrunedChains += 1;
            cornerPrunedVertices += accepted.length - candidate.length;
            accepted = candidate;
            simplified = true;
            break;
          }
          cornerRejectedCandidates += 1;
          pointsByChain[chain.id] = accepted;
        }
      }
      pointsByChain[chain.id] = accepted;
      if (!simplified && chain.points.length > 2) fallbackChainCount += 1;
    }

    const loopsByRegion = [];
    const regionIoU = [];
    let minimumIoU = 1;
    let meanIoU = 0;
    for (let regionId = 0; regionId < regionCount; regionId += 1) {
      const loops = assembleRegionLoops(graph, regionId, pointsByChain);
      loopsByRegion.push(loops);
      const candidate = rasterizeRegionLoops(loops, stats[regionId], width, height);
      const metrics = regionMetrics(
        stats[regionId],
        candidate,
        width,
        labels.length,
        config,
      );
      regionIoU.push(metrics.iou);
      minimumIoU = Math.min(minimumIoU, metrics.iou);
      meanIoU += metrics.iou;
    }
    meanIoU /= Math.max(regionCount, 1);

    const originalVertexCount = graph.chains.reduce(
      (sum, chain) => sum + chain.originalPointCount, 0
    );
    const simplifiedVertexCount = pointsByChain.reduce(
      (sum, points) => sum + points.length, 0
    );

    return {
      version: VERSION,
      method: "canonical-shared-chain",
      graph,
      loopsByRegion,
      regionIoU,
      metrics: {
        originalVertexCount,
        simplifiedVertexCount,
        fallbackChainCount,
        rejectedCandidateCount,
        cornerPrunedChains,
        cornerPrunedVertices,
        cornerRejectedCandidates,
        geometryMode,
        minRegionIoU: minimumIoU,
        meanRegionIoU: meanIoU,
      },
    };
  }

  const api = Object.freeze({
    VERSION,
    DEFAULTS,
    simplifyLabels,
    _core: Object.freeze({
      buildBoundaryGraph,
      assembleRegionLoops,
      microCleanup,
      simplifyOpenCvOpen,
      simplifyOpenChain,
      planarLineCandidate,
      cornerAwareLineCandidate,
      candidateChainIntersectionFree,
      regionStats,
      regionMetrics,
      topologySignatureFromPixels,
    }),
  });

  root.MinimalizerCanonicalContour = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof window !== "undefined" ? window : globalThis));
