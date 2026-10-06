from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.analyzers.structured_mask_evidence import observe_mask_components


PALETTE_ROLE_ADAPTER_VERSION = "sa8-v1"
MAX_PALETTE_ROLES_PER_PART = 3
MIN_PALETTE_ROLE_RATIO = 0.10
MIN_COMPONENT_RATIO = 0.025


@dataclass(frozen=True)
class PaletteRoleComponent:
    semantic_part: str
    palette_role_index: int
    component_index: int
    component_id: str
    mask: np.ndarray
    rgb: tuple[int, int, int]
    role_source_ratio: float
    component_source_ratio: float
    pixel_count: int


@dataclass(frozen=True)
class PaletteRole:
    semantic_part: str
    palette_role_index: int
    rgb: tuple[int, int, int]
    source_ratio: float
    components: tuple[PaletteRoleComponent, ...]


@dataclass(frozen=True)
class PaletteRoleAdapterReport:
    version: str
    roles: tuple[PaletteRole, ...]
    palette_role_count: int
    component_count: int
    palette_budget: int
    production_authority: bool
    production_output_changed: bool


def _validate(rgb: np.ndarray, part_mask: np.ndarray, max_roles: int) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(rgb)
    mask = np.asarray(part_mask).astype(bool)
    if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
        raise ValueError("rgb must be uint8 RGB")
    if mask.shape != image.shape[:2]:
        raise ValueError("shape mismatch")
    if max_roles < 1:
        raise ValueError("max_roles must be >= 1")
    return image, mask


def adapt_palette_roles(
    rgb: np.ndarray,
    part_mask: np.ndarray,
    semantic_part: str,
    *,
    max_roles: int = MAX_PALETTE_ROLES_PER_PART,
    min_role_ratio: float = MIN_PALETTE_ROLE_RATIO,
    min_component_ratio: float = MIN_COMPONENT_RATIO,
) -> PaletteRoleAdapterReport:
    """Build source-only palette roles while preserving disconnected components.

    Palette-role identity and component identity are deliberately separate.
    PB2's deterministic component observer is reused for component enumeration.
    The result is evidence/IR only and has no production rendering authority.
    """
    image, mask = _validate(rgb, part_mask, max_roles)
    total = int(mask.sum())
    if total < 16:
        return PaletteRoleAdapterReport(
            version=PALETTE_ROLE_ADAPTER_VERSION,
            roles=(),
            palette_role_count=0,
            component_count=0,
            palette_budget=max_roles,
            production_authority=False,
            production_output_changed=False,
        )

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    values = lab[mask].astype(np.float32)
    k = min(max_roles, max(1, total // 64))
    cv2.setRNGSeed(730)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(values, k, None, criteria, 1, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(-1)
    counts = np.bincount(labels, minlength=k)
    cluster_order = sorted(
        range(k),
        key=lambda index: (-int(counts[index]), tuple(float(v) for v in centers[index])),
    )

    yy, xx = np.where(mask)
    roles: list[PaletteRole] = []
    for cluster in cluster_order:
        role_ratio = float(counts[cluster] / total)
        if role_ratio < min_role_ratio:
            continue

        cluster_mask = np.zeros_like(mask, dtype=bool)
        selected = labels == cluster
        cluster_mask[yy[selected], xx[selected]] = True

        observations = observe_mask_components({semantic_part: cluster_mask})
        kept = [
            item
            for item in observations
            if float(item.pixel_count / total) >= min_component_ratio
        ]
        if not kept:
            continue

        role_index = len(roles)
        components: list[PaletteRoleComponent] = []
        for component_index, observation in enumerate(kept):
            x, y, width, height = observation.bbox
            local = cluster_mask[y : y + height, x : x + width]
            component_mask = np.zeros_like(mask, dtype=bool)
            component_mask[y : y + height, x : x + width] = local
            # Restrict to the exact observed connected component by flood-filling
            # from its deterministic centroid-nearest source pixel.
            n, component_labels, stats, _ = cv2.connectedComponentsWithStats(
                component_mask.astype(np.uint8), 8
            )
            candidates = []
            for label_index in range(1, n):
                sx, sy, sw, sh, area = [int(v) for v in stats[label_index]]
                if (sx, sy, sw, sh) == tuple(observation.bbox) and area == observation.pixel_count:
                    candidates.append(label_index)
            if len(candidates) != 1:
                raise RuntimeError("PB2 component identity could not be reconstructed")
            exact = component_labels == candidates[0]
            color = tuple(int(v) for v in np.median(image[exact], axis=0))
            components.append(
                PaletteRoleComponent(
                    semantic_part=semantic_part,
                    palette_role_index=role_index,
                    component_index=component_index,
                    component_id=f"sa8:{semantic_part}:role:{role_index}:component:{component_index}",
                    mask=exact,
                    rgb=color,
                    role_source_ratio=role_ratio,
                    component_source_ratio=float(observation.pixel_count / total),
                    pixel_count=int(observation.pixel_count),
                )
            )

        role_pixels = np.logical_or.reduce([component.mask for component in components])
        role_color = tuple(int(v) for v in np.median(image[role_pixels], axis=0))
        roles.append(
            PaletteRole(
                semantic_part=semantic_part,
                palette_role_index=role_index,
                rgb=role_color,
                source_ratio=role_ratio,
                components=tuple(components),
            )
        )
        if len(roles) >= max_roles:
            break

    role_tuple = tuple(roles)
    return PaletteRoleAdapterReport(
        version=PALETTE_ROLE_ADAPTER_VERSION,
        roles=role_tuple,
        palette_role_count=len(role_tuple),
        component_count=sum(len(role.components) for role in role_tuple),
        palette_budget=max_roles,
        production_authority=False,
        production_output_changed=False,
    )
