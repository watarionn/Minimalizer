from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance

PERSON_PART_NAMES = (
    "head",
    "torso",
    "left_arm",
    "right_arm",
    "left_leg",
    "right_leg",
)


@dataclass(frozen=True, slots=True)
class PersonPartConfig:
    subject_threshold: float = 0.50
    structural_threshold: float = 0.08
    head_height_ratio: float = 0.28
    head_width_ratio: float = 0.58
    minimum_part_pixels: int = 4
    structural_min_coverage_ratio: float = 0.80
    structural_min_part_pixels: int = 24

    def __post_init__(self) -> None:
        for name in ("subject_threshold", "structural_threshold", "head_height_ratio", "head_width_ratio"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be finite and within (0, 1]")
        if self.minimum_part_pixels < 1:
            raise ValueError("minimum_part_pixels must be positive")
        if not np.isfinite(self.structural_min_coverage_ratio) or not 0.0 < self.structural_min_coverage_ratio <= 1.0:
            raise ValueError("structural_min_coverage_ratio must be finite and within (0, 1]")
        if self.structural_min_part_pixels < 1:
            raise ValueError("structural_min_part_pixels must be positive")


@dataclass(frozen=True, slots=True)
class PersonPartPartition:
    subject_mask: NDArray[np.bool_]
    background_mask: NDArray[np.bool_]
    part_masks: dict[str, NDArray[np.bool_]]

    def __post_init__(self) -> None:
        if self.subject_mask.dtype != np.bool_ or self.subject_mask.ndim != 2:
            raise ValueError("subject_mask must be a bool 2D array")
        if self.background_mask.dtype != np.bool_ or self.background_mask.shape != self.subject_mask.shape:
            raise ValueError("background_mask must match subject_mask")
        if np.any(self.subject_mask & self.background_mask):
            raise ValueError("subject and background masks must not overlap")
        if not np.array_equal(self.background_mask, ~self.subject_mask):
            raise ValueError("background_mask must be the complement of subject_mask")
        unknown = set(self.part_masks) - set(PERSON_PART_NAMES)
        if unknown:
            raise ValueError(f"unknown person parts: {sorted(unknown)}")
        for name, mask in self.part_masks.items():
            if mask.dtype != np.bool_ or mask.shape != self.subject_mask.shape:
                raise ValueError(f"{name} mask must be bool and match subject_mask")
            if np.any(mask & ~self.subject_mask):
                raise ValueError(f"{name} mask must stay inside subject_mask")


def _union_structural_channels(guidance: AnalysisGuidance, names: tuple[str, ...]) -> NDArray[np.float32] | None:
    guide = guidance.structural
    if guide is None:
        return None
    indices = [guide.labels.index(name) for name in names if name in guide.labels]
    if not indices:
        return None
    return np.max(guide.confidence_maps[indices], axis=0).astype(np.float32)


def _head_prior(subject: NDArray[np.bool_], config: PersonPartConfig) -> NDArray[np.bool_]:
    result = np.zeros_like(subject)
    ys, xs = np.nonzero(subject)
    if len(xs) == 0:
        return result
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    width, height = x1 - x0, y1 - y0
    head_h = max(1, int(round(height * config.head_height_ratio)))
    head_w = max(1, int(round(width * config.head_width_ratio)))
    cx = (x0 + x1) // 2
    hx0 = max(x0, cx - head_w // 2)
    hx1 = min(x1, hx0 + head_w)
    result[y0:min(y1, y0 + head_h), hx0:hx1] = True
    return result & subject






def _silhouette_fallback_parts(
    subject: NDArray[np.bool_],
    head: NDArray[np.bool_],
) -> dict[str, NDArray[np.bool_]]:
    parts = {
        "head": head,
        "torso": np.zeros_like(subject),
        "left_arm": np.zeros_like(subject),
        "right_arm": np.zeros_like(subject),
        "left_leg": np.zeros_like(subject),
        "right_leg": np.zeros_like(subject),
    }
    ys, xs = np.nonzero(subject)
    if len(xs) == 0:
        return parts
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    width, height = x1 - x0, y1 - y0
    torso_y0 = y0 + max(1, int(round(height * 0.24)))
    hip_y = y0 + max(1, int(round(height * 0.62)))
    center_x = (x0 + x1) // 2
    torso_half = max(1, int(round(width * 0.22)))
    torso_x0, torso_x1 = max(x0, center_x - torso_half), min(x1, center_x + torso_half)
    yy, xx = np.indices(subject.shape)
    torso_band = (yy >= torso_y0) & (yy < hip_y)
    parts["torso"] = subject & torso_band & (xx >= torso_x0) & (xx < torso_x1)
    parts["left_arm"] = subject & torso_band & (xx < torso_x0)
    parts["right_arm"] = subject & torso_band & (xx >= torso_x1)
    lower = subject & (yy >= hip_y)
    parts["left_leg"] = lower & (xx < center_x)
    parts["right_leg"] = lower & (xx >= center_x)
    return parts

def _expand_structural_parts_to_subject(
    subject: NDArray[np.bool_],
    parts: dict[str, NDArray[np.bool_]],
) -> dict[str, NDArray[np.bool_]]:
    """Grow pose corridors into a complete semantic partition of the silhouette."""
    names = tuple(name for name in PERSON_PART_NAMES if np.any(parts.get(name, False)))
    if not names:
        return parts
    distances: list[NDArray[np.float32]] = []
    for name in names:
        seed = np.asarray(parts[name] & subject, dtype=np.bool_)
        # distanceTransform measures distance to zero pixels.
        field = cv2.distanceTransform((~seed).astype(np.uint8), cv2.DIST_L2, 3)
        distances.append(field.astype(np.float32))
    nearest = np.argmin(np.stack(distances, axis=0), axis=0)
    grown = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    for index, name in enumerate(names):
        grown[name] = subject & (nearest == index)
    return grown


def _assign_exclusive_parts(
    subject: NDArray[np.bool_],
    raw_parts: dict[str, NDArray[np.bool_]],
    *,
    minimum_part_pixels: int,
) -> dict[str, NDArray[np.bool_]]:
    assigned = np.zeros_like(subject)
    exclusive: dict[str, NDArray[np.bool_]] = {}
    # Foreground-first painter order. Head owns the top silhouette, then limbs,
    # and torso receives the remaining central support.
    order = ("head", "left_arm", "right_arm", "left_leg", "right_leg", "torso")
    for name in order:
        mask = np.asarray(raw_parts[name] & subject & ~assigned, dtype=np.bool_)
        if int(mask.sum()) < minimum_part_pixels:
            mask = np.zeros_like(subject)
        exclusive[name] = mask
        assigned |= mask
    return exclusive



def resize_person_part_partition(
    partition: PersonPartPartition,
    target_shape: tuple[int, int],
) -> PersonPartPartition:
    if target_shape == partition.subject_mask.shape:
        return partition
    height, width = target_shape
    if height <= 0 or width <= 0:
        raise ValueError("target_shape must be positive")

    def resize(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
        return cv2.resize(
            mask.astype(np.uint8),
            (width, height),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.bool_)

    subject = resize(partition.subject_mask)
    raw_parts = {name: resize(mask) & subject for name, mask in partition.part_masks.items()}
    parts = _assign_exclusive_parts(subject, raw_parts, minimum_part_pixels=1)
    return PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks=parts,
    )

def build_person_part_partition(
    guidance: AnalysisGuidance,
    *,
    config: PersonPartConfig | None = None,
) -> PersonPartPartition:
    active = config or PersonPartConfig()
    if guidance.subject_prob is None:
        raise ValueError("person-part partition requires subject_prob guidance")
    subject = np.asarray(guidance.subject_prob >= active.subject_threshold, dtype=np.bool_)
    head = _head_prior(subject, active)
    parts: dict[str, NDArray[np.bool_]] = {"head": head}
    groups = {
        "torso": ("torso",),
        "left_arm": ("left_upper_arm", "left_forearm"),
        "right_arm": ("right_upper_arm", "right_forearm"),
        "left_leg": ("left_thigh", "left_shin"),
        "right_leg": ("right_thigh", "right_shin"),
    }
    has_structural_support = False
    for name, channels in groups.items():
        support = _union_structural_channels(guidance, channels)
        if support is None:
            parts[name] = np.zeros_like(subject)
        else:
            candidate = (support >= active.structural_threshold) & subject
            parts[name] = candidate
            has_structural_support = has_structural_support or bool(candidate.any())
    fallback = _silhouette_fallback_parts(subject, head)
    if has_structural_support:
        required = ("torso", "left_arm", "right_arm", "left_leg", "right_leg")
        supported = sum(int(parts[name].sum()) >= active.structural_min_part_pixels for name in required)
        coverage = supported / float(len(required))
        if coverage < active.structural_min_coverage_ratio:
            has_structural_support = False
        else:
            # Keep good pose corridors, but repair an individual missing/tiny
            # channel from the silhouette instead of dropping the whole pose.
            for name in required:
                if int(parts[name].sum()) < active.structural_min_part_pixels:
                    parts[name] = fallback[name]
    if not has_structural_support:
        parts = fallback
    else:
        # Pose channels are thin skeleton corridors, not full body-part masks.
        # Expand them across the subject silhouette before exclusivity so hair,
        # clothing, and skin pixels inherit the nearest semantic body part.
        parts = _expand_structural_parts_to_subject(subject, parts)
    parts = _assign_exclusive_parts(
        subject,
        parts,
        minimum_part_pixels=active.minimum_part_pixels,
    )
    return PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks=parts,
    )
