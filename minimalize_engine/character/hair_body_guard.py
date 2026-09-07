from __future__ import annotations

from dataclasses import dataclass, asdict, replace
import cv2
import numpy as np

from .models import CharacterPartCandidate


@dataclass(slots=True)
class HairBodyGuardReport:
    applied: bool
    overlap_before: int
    overlap_after: int
    removed_pixels: int
    hair_pixels_before: int
    hair_pixels_after: int
    diagnostics: dict

    def to_dict(self) -> dict:
        return asdict(self)


def guard_hair_from_body_core(
    hair: CharacterPartCandidate,
    torso: CharacterPartCandidate | None,
    face: CharacterPartCandidate | None,
    *,
    trigger_overlap_ratio: float = 0.44,
    max_remove_ratio: float = 0.12,
) -> tuple[CharacterPartCandidate, HairBodyGuardReport]:
    """Remove only suspicious central torso conflict from a hair candidate.

    Long side/back hair remains untouched.  The guard activates only when the
    detected hair occupies an unusually large fraction of the torso mask, a
    common failure mode when dark hair and dark clothing collapse together.
    """
    hm = (hair.mask > 0).astype(np.uint8) * 255
    if torso is None:
        return hair, HairBodyGuardReport(False, 0, 0, 0, int(np.count_nonzero(hm)), int(np.count_nonzero(hm)), {"reason": "no torso"})
    tm = torso.mask > 0
    hair_pixels = max(1, int(np.count_nonzero(hm)))
    torso_pixels = max(1, int(np.count_nonzero(tm)))
    overlap = int(np.count_nonzero((hm > 0) & tm))
    overlap_ratio = overlap / torso_pixels
    if overlap_ratio < trigger_overlap_ratio:
        return hair, HairBodyGuardReport(False, overlap, overlap, 0, hair_pixels, hair_pixels, {"overlap_ratio": overlap_ratio, "reason": "below trigger"})

    x, y, w, h = torso.bbox
    core = np.zeros_like(hm)
    xa = int(round(x + w * 0.24)); xb = int(round(x + w * 0.76))
    ya = int(round(y + h * 0.16)); yb = int(round(y + h * 0.92))
    if face is not None:
        _, fy, _, fh = face.bbox
        ya = max(ya, int(round(fy + fh * 0.72)))
    core[max(0, ya):min(core.shape[0], yb), max(0, xa):min(core.shape[1], xb)] = 255
    conflict = ((hm > 0) & tm & (core > 0)).astype(np.uint8) * 255
    max_remove = int(round(hair_pixels * max_remove_ratio))
    conflict_pixels = int(np.count_nonzero(conflict))
    if conflict_pixels == 0 or conflict_pixels > max_remove:
        return hair, HairBodyGuardReport(False, overlap, overlap, 0, hair_pixels, hair_pixels, {
            "overlap_ratio": overlap_ratio,
            "conflict_pixels": conflict_pixels,
            "max_remove_pixels": max_remove,
            "reason": "conflict unsafe to remove",
        })

    # Feather only the local conflict band.  Do not globally erode hair.
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    local = cv2.morphologyEx(conflict, cv2.MORPH_OPEN, k)
    guarded = hm.copy()
    guarded[local > 0] = 0
    after_overlap = int(np.count_nonzero((guarded > 0) & tm))
    after_pixels = int(np.count_nonzero(guarded))
    if after_pixels == hair_pixels:
        return hair, HairBodyGuardReport(False, overlap, overlap, 0, hair_pixels, hair_pixels, {
            "overlap_ratio": overlap_ratio,
            "reason": "local conflict vanished during safety cleanup",
        })
    if after_pixels < hair_pixels * 0.88:
        return hair, HairBodyGuardReport(False, overlap, overlap, 0, hair_pixels, hair_pixels, {"reason": "safety rollback"})

    ys, xs = np.nonzero(guarded > 0)
    if len(xs) < 3:
        return hair, HairBodyGuardReport(False, overlap, overlap, 0, hair_pixels, hair_pixels, {"reason": "empty result"})
    bbox = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
    candidate = replace(
        hair,
        mask=guarded,
        bbox=bbox,
        centroid=(float(xs.mean()), float(ys.mean())),
        area=after_pixels,
        area_ratio=after_pixels / guarded.size,
        metadata={**hair.metadata, "hair_body_guard": True},
    )
    return candidate, HairBodyGuardReport(
        True, overlap, after_overlap, hair_pixels - after_pixels,
        hair_pixels, after_pixels,
        {
            "phase": "13.1",
            "overlap_ratio": overlap_ratio,
            "trigger_overlap_ratio": trigger_overlap_ratio,
            "max_remove_ratio": max_remove_ratio,
            "principle": "protect torso readability while preserving side/back hair",
        },
    )
