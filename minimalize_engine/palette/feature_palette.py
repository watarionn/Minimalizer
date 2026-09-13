#!/usr/bin/env python3
"""
AI-free feature palette extraction for Minimalizer.

Extracts 3-6 visually characteristic colors instead of merely choosing the
most frequent pixels. The scorer combines background suppression, Lab-space
clustering, area compression, chroma, spatial spread, family diversity and
special handling for white/dark/muted colors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    x = srgb_to_linear(rgb.astype(np.float64))
    X = x[..., 0] * 0.4124564 + x[..., 1] * 0.3575761 + x[..., 2] * 0.1804375
    Y = x[..., 0] * 0.2126729 + x[..., 1] * 0.7151522 + x[..., 2] * 0.0721750
    Z = x[..., 0] * 0.0193339 + x[..., 1] * 0.1191920 + x[..., 2] * 0.9503041
    X /= 0.95047
    Z /= 1.08883
    e = 216 / 24389
    k = 24389 / 27

    def f(t):
        return np.where(t > e, np.cbrt(t), (k * t + 16) / 116)

    fx, fy, fz = f(X), f(Y), f(Z)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    L, a, b = [lab[..., i] for i in range(3)]
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    e = 216 / 24389
    k = 24389 / 27

    def finv(t):
        t3 = t ** 3
        return np.where(t3 > e, t3, (116 * t - 16) / k)

    X = 0.95047 * finv(fx)
    Y = finv(fy)
    Z = 1.08883 * finv(fz)
    r = 3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z
    g = -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z
    bl = 0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z
    c = np.stack([r, g, bl], axis=-1)
    c = np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(np.uint8)


def delta_e76(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.linalg.norm(a - b, axis=-1)


def estimate_background_mask(rgb: np.ndarray, border_fraction: float = 0.045, de_threshold: float = 17.0) -> np.ndarray:
    h, w, _ = rgb.shape
    bw = max(2, int(min(h, w) * border_fraction))
    border = np.concatenate([
        rgb[:bw].reshape(-1, 3), rgb[-bw:].reshape(-1, 3),
        rgb[:, :bw].reshape(-1, 3), rgb[:, -bw:].reshape(-1, 3),
    ], axis=0)
    q = (border // 16).astype(np.int16)
    keys, counts = np.unique(q, axis=0, return_counts=True)
    top = keys[np.argsort(counts)[-5:]]
    candidates = []
    for k3 in top:
        m = np.all(q == k3, axis=1)
        candidates.append(np.median(border[m], axis=0))
    cand = np.array(candidates, dtype=np.uint8)
    lab_border = rgb_to_lab(border)
    lab_cand = rgb_to_lab(cand)
    cover = np.array([(delta_e76(lab_border, c) < de_threshold).mean() for c in lab_cand])
    bg_lab = lab_cand[int(np.argmax(cover))]
    lab = rgb_to_lab(rgb)
    mask = delta_e76(lab, bg_lab) < de_threshold
    border_mask = np.concatenate([mask[:bw].ravel(), mask[-bw:].ravel(), mask[:, :bw].ravel(), mask[:, -bw:].ravel()])
    return mask if border_mask.mean() >= 0.26 else np.zeros((h, w), dtype=bool)


def weighted_kmeans_lab(lab: np.ndarray, weights: np.ndarray, k: int, iterations: int = 24, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(lab)
    if n <= k:
        return lab.copy(), np.arange(n)
    centers = [lab[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min(np.stack([np.sum((lab - c) ** 2, axis=1) for c in centers], axis=1), axis=1)
        p = d2 * weights
        s = p.sum()
        idx = rng.integers(n) if s <= 0 else rng.choice(n, p=p / s)
        centers.append(lab[idx])
    centers = np.array(centers, dtype=np.float64)
    labels = np.zeros(n, dtype=np.int32)
    for _ in range(iterations):
        dist = np.stack([np.sum((lab - c) ** 2, axis=1) for c in centers], axis=1)
        new_labels = np.argmin(dist, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(k):
            m = labels == j
            centers[j] = lab[rng.integers(n)] if not np.any(m) else np.average(lab[m], axis=0, weights=weights[m])
    return centers, labels


@dataclass
class FeatureColor:
    rgb: tuple[int, int, int]
    hex: str
    lab: tuple[float, float, float]
    area: float
    chroma: float
    spread: float
    neutral_kind: str
    family: str
    score: float


def _hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _spatial_spread(xs, ys, w, h):
    if len(xs) < 2:
        return 0.0
    sx = min(1.0, np.std(xs) / max(1, w * 0.22))
    sy = min(1.0, np.std(ys) / max(1, h * 0.22))
    return float((sx + sy) / 2)


def lab_hue_deg(lab_triplet):
    _, a, b = lab_triplet
    return math.degrees(math.atan2(b, a)) % 360.0


_FAMILY_ANCHOR_RGB = {
    "red": (220, 45, 45), "orange": (235, 125, 35), "yellow": (238, 205, 55),
    "yellowgreen": (160, 190, 60), "green": (55, 155, 85), "cyan": (55, 190, 200),
    "blue": (70, 115, 220), "purple": (135, 85, 205), "pink": (230, 105, 170),
}
_FAMILY_ANCHOR_LAB = {name: rgb_to_lab(np.array(rgb, dtype=np.uint8)) for name, rgb in _FAMILY_ANCHOR_RGB.items()}


def color_family(lab_triplet, neutral_kind):
    L, a, b = map(float, lab_triplet)
    C = math.hypot(a, b)
    h = lab_hue_deg(lab_triplet)
    if neutral_kind == "light": return "white"
    if neutral_kind == "dark": return "black"
    if neutral_kind == "neutral": return "gray"
    if C < 28:
        if 15 <= h < 75: return "beige" if L >= 68 else "brown"
        if 75 <= h < 125: return "beige" if L >= 72 else "yellow"
        if 125 <= h < 205: return "gray" if L >= 72 else "green"
        if 205 <= h < 270: return "bluegray" if L >= 72 else "blue"
        if 270 <= h < 330: return "mauve" if L >= 72 else "purple"
        if h >= 330 or h < 15: return "pink" if L >= 70 else "red"
    labv = np.array([L, a, b], dtype=np.float64)
    best_name, best_d = None, float("inf")
    for name, anchor in _FAMILY_ANCHOR_LAB.items():
        anchor = np.array(anchor, dtype=np.float64)
        dL = (labv[0] - anchor[0]) * (0.48 if C < 38 else 0.62)
        da, db = labv[1] - anchor[1], labv[2] - anchor[2]
        d = math.sqrt(dL*dL + da*da + db*db)
        if name == "pink" and (h >= 325 or h < 350): d *= 0.90
        if name == "red" and (h >= 350 or h < 22): d *= 0.91
        if name == "yellow" and 55 <= h <= 100: d *= 0.88
        if name == "yellowgreen" and 90 <= h <= 125: d *= 0.94
        if name == "cyan" and 170 <= h <= 220: d *= 0.90
        if name == "blue" and 220 <= h <= 285: d *= 0.91
        if name == "purple" and 285 <= h <= 325: d *= 0.91
        if d < best_d:
            best_name, best_d = name, d
    return best_name


def extract_feature_palette(image: Image.Image, n_colors: int = 4, remove_background: bool = True,
                            sample_max: int = 12000, clusters: int = 18, seed: int = 42) -> list[FeatureColor]:
    rgba = image.convert("RGBA")
    arr = np.array(rgba)
    rgb, alpha = arr[..., :3], arr[..., 3]
    valid = alpha > 20
    if remove_background:
        valid &= ~estimate_background_mask(rgb)
    ys, xs = np.nonzero(valid)
    px = rgb[valid]
    if len(px) == 0:
        raise ValueError("No foreground pixels were available for palette extraction.")
    rng = np.random.default_rng(seed)
    if len(px) > sample_max:
        idx = rng.choice(len(px), size=sample_max, replace=False)
        px_s, xs_s, ys_s = px[idx], xs[idx], ys[idx]
    else:
        px_s, xs_s, ys_s = px, xs, ys
    lab_s = rgb_to_lab(px_s)
    k = min(clusters, max(6, len(px_s) // 120))
    centers, labels = weighted_kmeans_lab(lab_s, np.ones(len(px_s)), k=k, seed=seed)
    h, w = rgb.shape[:2]
    candidates = []
    for j, c in enumerate(centers):
        m = labels == j
        count = int(m.sum())
        if count < max(12, len(px_s) * 0.0025):
            continue
        area = count / len(px_s)
        L, a, b = map(float, c)
        chroma = math.hypot(a, b)
        spread = _spatial_spread(xs_s[m], ys_s[m], w, h)
        if chroma < 13 and L > 76: neutral = "light"
        elif chroma < 15 and L < 31: neutral = "dark"
        elif chroma < 12: neutral = "neutral"
        else: neutral = "color"
        area_term = area ** 0.56
        if neutral == "color":
            chroma_term = 0.70 + 0.55 * min(1.0, chroma / 52.0)
            light_term = 0.90 + 0.10 * (1.0 - abs(L - 58) / 58)
        elif neutral == "light":
            chroma_term, light_term = 0.96, (1.11 if L > 86 else 1.02)
        elif neutral == "dark":
            chroma_term, light_term = 0.80, 0.82 + 0.55 * min(1.0, area / 0.12)
        else:
            chroma_term, light_term = 0.78, 0.92
        score = area_term * chroma_term * light_term * (0.90 + 0.22 * spread)
        rgbc = tuple(map(int, lab_to_rgb(np.array(c)).tolist()))
        candidates.append({"rgb": rgbc, "hex": _hex(rgbc), "lab": (L, a, b), "area": area,
                           "chroma": chroma, "spread": spread, "neutral": neutral, "score": score})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    merged = []
    for c in candidates:
        if any(float(delta_e76(np.array(c["lab"]), np.array(m["lab"]))) < 13.0 for m in merged):
            continue
        merged.append(c)
    selected = []
    pool = merged[:]
    for slot in range(min(n_colors, len(pool))):
        best, bestscore = None, -1.0
        for c in pool:
            score = c["score"]
            fam = color_family(c["lab"], c["neutral"])
            if c["neutral"] == "color" and c["area"] >= 0.009:
                score *= 1.0 + 0.16 * min(1.0, c["chroma"] / 48.0)
            if selected:
                d = min(float(delta_e76(np.array(c["lab"]), np.array(s["lab"]))) for s in selected)
                score *= 0.12 + 0.88 * min(1.0, max(0.0, (d - 9.0) / 30.0))
                seen = [color_family(s["lab"], s["neutral"]) for s in selected]
                if fam in seen:
                    score *= 0.18 if fam in {"white","black","gray","bluegray","mauve","beige","brown"} else 0.22
                elif c["area"] >= 0.008:
                    score *= 1.10 if fam in {"bluegray","mauve","beige","brown","gray"} else 1.16
                neutrals = [s for s in selected if s["neutral"] != "color"]
                if c["neutral"] != "color" and neutrals:
                    opposite = any((c["neutral"] == "light" and s["neutral"] == "dark") or
                                   (c["neutral"] == "dark" and s["neutral"] == "light") for s in neutrals)
                    score *= 0.78 if opposite and c["area"] >= 0.065 else 0.46
            if c["neutral"] == "light" and c["area"] >= 0.050:
                score *= 1.10
            if slot >= 2 and sum(s["neutral"] == "color" for s in selected) < 2 and c["neutral"] == "color" and c["area"] >= 0.009:
                score *= 1.18
            if score > bestscore:
                best, bestscore = c, score
        if best is None:
            break
        best = dict(best)
        best["final_score"] = float(bestscore)
        selected.append(best)
        pool.remove(next(x for x in pool if x is not None and x["hex"] == best["hex"] and x["lab"] == best["lab"]))
    return [FeatureColor(
        rgb=s["rgb"], hex=s["hex"], lab=s["lab"], area=float(s["area"]), chroma=float(s["chroma"]),
        spread=float(s["spread"]), neutral_kind=s["neutral"], family=color_family(s["lab"], s["neutral"]),
        score=float(s["final_score"]),
    ) for s in selected]


# Backward-friendly alias for experimentation scripts.
extract_palette = extract_feature_palette
