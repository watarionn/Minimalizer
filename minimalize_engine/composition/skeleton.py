from __future__ import annotations

from dataclasses import dataclass, asdict
import cv2
import numpy as np

from ..models import Region


@dataclass(frozen=True)
class CompositionSkeleton:
    active: bool
    center_x: float
    corridor_x0: float
    corridor_x1: float
    horizon_y: float
    corridor_score: float
    left_mass_score: float
    right_mass_score: float
    mode: str = "none"
    confidence: float = 0.0
    subject_bbox: tuple[float, float, float, float] | None = None

    @property
    def corridor_width(self) -> float:
        return max(0.0, self.corridor_x1 - self.corridor_x0)

    def to_dict(self) -> dict:
        out = asdict(self)
        out["corridor_width"] = self.corridor_width
        return out


def _smooth_1d(values: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return values.astype(np.float32)
    k = radius * 2 + 1
    kernel = np.ones(k, dtype=np.float32) / k
    return np.convolve(values.astype(np.float32), kernel, mode="same")


def _structure_mask(regions: list[Region], h: int, w: int) -> np.ndarray:
    mask = np.zeros((h, w), dtype=np.uint8)
    preferred = [r for r in regions if r.role in {"structure", "vertical", "misc"}]
    if not preferred:
        preferred = [r for r in regions if r.role not in {"water", "reflection"}]
    for r in preferred:
        mask = cv2.bitwise_or(mask, (r.mask > 0).astype(np.uint8))
    return mask


def _estimate_horizon(regions: list[Region], h: int) -> float:
    candidates = []
    for r in regions:
        x, y, bw, bh = r.bbox
        if r.role in {"water", "boat"}:
            if h * 0.38 <= y <= h * 0.78:
                candidates.append(float(y))
    if candidates:
        return float(np.clip(np.median(candidates), h * 0.48, h * 0.70))

    lower_struct = []
    for r in regions:
        if r.role == "structure":
            _, y, _, bh = r.bbox
            bottom = y + bh
            if h * 0.40 <= bottom <= h * 0.78:
                lower_struct.append(float(bottom))
    if lower_struct:
        return float(np.clip(np.median(lower_struct), h * 0.48, h * 0.70))
    return float(h * 0.58)


def detect_composition_skeleton(
    regions: list[Region],
    image_shape,
    *,
    center_min_ratio: float = 0.30,
    center_max_ratio: float = 0.70,
    min_corridor_ratio: float = 0.08,
    max_corridor_ratio: float = 0.24,
    valley_ratio: float = 0.72,
) -> CompositionSkeleton:
    h, w = image_shape[:2]
    if not regions or w < 20 or h < 20:
        return CompositionSkeleton(False,w/2,w/2,w/2,h*.58,0,0,0,mode="none",confidence=0)

    mask = _structure_mask(regions, h, w)

    # Analyze the architecture-bearing band; ignore empty sky and most reflections.
    y0 = int(round(h * 0.20))
    y1 = int(round(h * 0.72))
    band = mask[y0:y1]
    occupancy = band.mean(axis=0).astype(np.float32)
    occupancy = _smooth_1d(occupancy, max(2, int(round(w * 0.012))))

    min_width = max(5, int(round(w * min_corridor_ratio)))
    max_width = max(min_width, int(round(w * max_corridor_ratio)))
    search_x0 = int(round(w * center_min_ratio))
    search_x1 = int(round(w * center_max_ratio))

    # Find the lowest-occupancy central window, considering several widths.
    best = None
    widths = sorted(set([
        min_width,
        int(round((min_width + max_width) / 2)),
        max_width,
    ]))
    for width in widths:
        half = width // 2
        for cx in range(search_x0, search_x1 + 1, max(1, width // 10)):
            a = max(0, cx - half)
            b = min(w, a + width)
            a = max(0, b - width)
            if b - a < min_width:
                continue
            score = float(occupancy[a:b].mean())
            center_penalty = abs((a + b) / 2 - w / 2) / max(w, 1) * 0.08
            rank = score + center_penalty
            if best is None or rank < best[0]:
                best = (rank, score, a, b)

    horizon = _estimate_horizon(regions, h)
    if best is None:
        return CompositionSkeleton(False,w/2,w/2,w/2,horizon,0,0,0,mode="none",confidence=0)

    _, corridor_occ, a, b = best
    margin = max(4, int(round(w * 0.035)))
    left_end = max(1, a - margin)
    right_start = min(w - 1, b + margin)

    left_slice = occupancy[max(0, int(w * 0.06)):left_end]
    right_slice = occupancy[right_start:min(w, int(w * 0.94))]
    left_score = float(left_slice.mean()) if left_slice.size else 0.0
    right_score = float(right_slice.mean()) if right_slice.size else 0.0
    side_floor = min(left_score, right_score)

    # The corridor is meaningful only when both sides carry noticeably more mass.
    active = (
        side_floor >= 0.055
        and corridor_occ <= side_floor * valley_ratio
        and (b - a) / max(w, 1) <= max_corridor_ratio + 0.02
    )

    # Expand the detected valley while columns remain substantially emptier than sides.
    if active:
        threshold = max(corridor_occ * 1.35, side_floor * 0.58)
        aa, bb = a, b
        max_expand = max_width
        while aa > search_x0 - max_expand // 2 and occupancy[aa - 1] <= threshold and bb - aa < max_width:
            aa -= 1
        while bb < search_x1 + max_expand // 2 and occupancy[bb] <= threshold and bb - aa < max_width:
            bb += 1
        a, b = max(0, aa), min(w, bb)

    center = (a + b) / 2 if active else w / 2
    contrast = 0.0 if side_floor <= 1e-6 else float(np.clip(1.0 - corridor_occ / side_floor, 0.0, 1.0))

    return CompositionSkeleton(
        active=bool(active),
        center_x=float(center),
        corridor_x0=float(a if active else w / 2),
        corridor_x1=float(b if active else w / 2),
        horizon_y=float(horizon),
        corridor_score=contrast,
        left_mass_score=float(left_score),
        right_mass_score=float(right_score),
        mode="central_corridor" if active else "none",
        confidence=float(contrast),
    )


def region_side(region: Region, skeleton: CompositionSkeleton) -> str:
    if not skeleton.active:
        return "center"
    cx = region.centroid[0]
    if cx < skeleton.corridor_x0:
        return "left"
    if cx > skeleton.corridor_x1:
        return "right"
    return "center"


def detect_subject_skeleton(alpha_mask: np.ndarray, image_shape) -> CompositionSkeleton:
    h,w=image_shape[:2]
    if alpha_mask is None:
        return CompositionSkeleton(False,w/2,w/2,w/2,h*.58,0,0,0,mode="none",confidence=0)
    m=alpha_mask>0; ys,xs=np.nonzero(m)
    if len(xs)==0:
        return CompositionSkeleton(False,w/2,w/2,w/2,h*.58,0,0,0,mode="none",confidence=0)
    x0,x1,y0,y1=float(xs.min()),float(xs.max()),float(ys.min()),float(ys.max());cx=float(xs.mean())
    occ=float(m.mean()); box=max(1,(x1-x0+1)*(y1-y0+1));fill=len(xs)/box
    conf=float(np.clip(.45+min(.35,occ*.7)+min(.20,fill*.25),0,1))
    return CompositionSkeleton(False,cx,cx,cx,float(y0+(y1-y0)*.62),0,float((xs<cx).mean()),float((xs>=cx).mean()),mode="center_subject",confidence=conf,subject_bbox=(x0,y0,x1,y1))
