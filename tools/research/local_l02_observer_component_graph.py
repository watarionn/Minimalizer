"""Build a source-only, role-aware observer component graph.

This is the next development unit after whole-image observation.  It groups
independent observer evidence into coherent 8-connected components and marks
role conflicts at component granularity.  It deliberately does not accept
human labels, frozen owner arrays, thresholds fitted to reviewed examples, or
an owner number.  Missing evidence becomes ``unknown`` and is never a
negative observation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import cv2
import numpy as np


class ObserverComponentGraphHold(ValueError):
    """Raised when source-only observer evidence cannot be authenticated."""


@dataclass(frozen=True)
class ObserverMask:
    name: str
    role: str
    mask: np.ndarray
    expected_sha256: str
    model_id: str


@dataclass(frozen=True)
class ObserverComponent:
    component_id: int
    area: int
    bbox_xywh: tuple[int, int, int, int]
    observer_positive_pixels: tuple[tuple[str, int], ...]
    role_positive_pixels: tuple[tuple[str, int], ...]
    roles: tuple[str, ...]
    decision: str


@dataclass(frozen=True)
class RoleRegion:
    region_id: int
    role: str
    area: int
    bbox_xywh: tuple[int, int, int, int]
    observer_positive_pixels: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RoleContact:
    first_region_id: int
    second_region_id: int
    first_role: str
    second_role: str
    overlap_pixels: int
    adjacent_pixels: int


@dataclass(frozen=True)
class ObserverComponentGraph:
    source_only: bool
    human_labels_used: bool
    owner_arrays_used: bool
    unknown_not_treated_as_negative: bool
    observed_pixels: int
    unknown_pixels: int
    observed_union: np.ndarray
    unknown: np.ndarray
    components: tuple[ObserverComponent, ...]


@dataclass(frozen=True)
class ContactAwareRoleGraph:
    source_only: bool
    human_labels_used: bool
    owner_arrays_used: bool
    unknown_not_treated_as_negative: bool
    observed_pixels: int
    unknown_pixels: int
    observed_union: np.ndarray
    unknown: np.ndarray
    regions: tuple[RoleRegion, ...]
    contacts: tuple[RoleContact, ...]


def _sha256(array: np.ndarray) -> str:
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _validate_observer(observer: ObserverMask, shape: tuple[int, int], names: set[str]) -> None:
    if not isinstance(observer, ObserverMask):
        raise ObserverComponentGraphHold("INVALID_OBSERVER_ENTRY")
    if (
        type(observer.name) is not str
        or not observer.name
        or observer.name in names
        or type(observer.role) is not str
        or not observer.role
        or type(observer.model_id) is not str
        or not observer.model_id
        or type(observer.expected_sha256) is not str
        or len(observer.expected_sha256) != 64
        or type(observer.mask) is not np.ndarray
        or observer.mask.dtype != np.uint8
        or observer.mask.ndim != 2
        or observer.mask.shape != shape
        or np.any(observer.mask > 1)
        or _sha256(observer.mask) != observer.expected_sha256
    ):
        raise ObserverComponentGraphHold("INVALID_OBSERVER_ENTRY")


def build_observer_component_graph(
    *, source_alpha: np.ndarray, observers: tuple[ObserverMask, ...]
) -> ObserverComponentGraph:
    """Return component-level evidence without producing an owner candidate.

    Each observer contributes only positive evidence.  The union is partitioned
    into 8-connected components.  A component with evidence for multiple roles
    is held as a whole; no pixel-level arbitration is attempted.  ``unknown``
    is the opaque source area without any observer evidence and is not a
    negative mask.
    """
    if (
        type(source_alpha) is not np.ndarray
        or source_alpha.dtype != np.bool_
        or source_alpha.ndim != 2
        or not source_alpha.size
    ):
        raise ObserverComponentGraphHold("INVALID_SOURCE_ALPHA")
    if not isinstance(observers, tuple) or not observers:
        raise ObserverComponentGraphHold("INDEPENDENT_OBSERVERS_REQUIRED")

    names: set[str] = set()
    validated: list[ObserverMask] = []
    for observer in observers:
        _validate_observer(observer, source_alpha.shape, names)
        names.add(observer.name)
        validated.append(observer)

    masks = tuple(observer.mask.astype(bool) & source_alpha for observer in validated)
    observed_union = np.logical_or.reduce(masks)
    unknown = source_alpha & ~observed_union
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        observed_union.astype(np.uint8), connectivity=8
    )
    components: list[ObserverComponent] = []
    for component_id in range(1, count):
        component = labels == component_id
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        x = int(stats[component_id, cv2.CC_STAT_LEFT])
        y = int(stats[component_id, cv2.CC_STAT_TOP])
        width = int(stats[component_id, cv2.CC_STAT_WIDTH])
        height = int(stats[component_id, cv2.CC_STAT_HEIGHT])
        observer_counts = tuple(
            (observer.name, int(np.count_nonzero(mask & component)))
            for observer, mask in zip(validated, masks)
        )
        role_totals: dict[str, int] = {}
        for observer, mask in zip(validated, masks):
            role_totals[observer.role] = role_totals.get(observer.role, 0) + int(
                np.count_nonzero(mask & component)
            )
        roles = tuple(sorted(role for role, pixels in role_totals.items() if pixels > 0))
        decision = "ROLE_CONFLICT" if len(roles) > 1 else "ROLE_EVIDENCE"
        components.append(
            ObserverComponent(
                component_id=component_id,
                area=area,
                bbox_xywh=(x, y, width, height),
                observer_positive_pixels=observer_counts,
                role_positive_pixels=tuple(sorted(role_totals.items())),
                roles=roles,
                decision=decision,
            )
        )

    return ObserverComponentGraph(
        source_only=True,
        human_labels_used=False,
        owner_arrays_used=False,
        unknown_not_treated_as_negative=True,
        observed_pixels=int(observed_union.sum()),
        unknown_pixels=int(unknown.sum()),
        observed_union=observed_union,
        unknown=unknown,
        components=tuple(components),
    )


def build_contact_aware_role_graph(
    *, source_alpha: np.ndarray, observers: tuple[ObserverMask, ...]
) -> ContactAwareRoleGraph:
    """Keep role regions separate and record their contact relationships.

    Unlike the all-role union graph, this function never collapses touching
    garment and arm regions into one component.  A role union is used only to
    find regions for that role; observer provenance is retained on each region,
    and overlap/8-neighbour contact is represented as an edge.  This is still
    observation, not owner assignment.
    """
    if (
        type(source_alpha) is not np.ndarray
        or source_alpha.dtype != np.bool_
        or source_alpha.ndim != 2
        or not source_alpha.size
    ):
        raise ObserverComponentGraphHold("INVALID_SOURCE_ALPHA")
    if not isinstance(observers, tuple) or not observers:
        raise ObserverComponentGraphHold("INDEPENDENT_OBSERVERS_REQUIRED")

    names: set[str] = set()
    validated: list[ObserverMask] = []
    for observer in observers:
        _validate_observer(observer, source_alpha.shape, names)
        names.add(observer.name)
        validated.append(observer)

    masks = tuple(observer.mask.astype(bool) & source_alpha for observer in validated)
    observed_union = np.logical_or.reduce(masks)
    unknown = source_alpha & ~observed_union
    role_names = tuple(sorted({observer.role for observer in validated}))
    role_masks: dict[str, np.ndarray] = {
        role: np.logical_or.reduce(
            [mask for observer, mask in zip(validated, masks) if observer.role == role]
        )
        for role in role_names
    }

    regions: list[RoleRegion] = []
    role_label_maps: dict[str, np.ndarray] = {}
    next_region_id = 1
    for role in role_names:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            role_masks[role].astype(np.uint8), connectivity=8
        )
        role_label_maps[role] = labels
        for local_id in range(1, count):
            component = labels == local_id
            area = int(stats[local_id, cv2.CC_STAT_AREA])
            x = int(stats[local_id, cv2.CC_STAT_LEFT])
            y = int(stats[local_id, cv2.CC_STAT_TOP])
            width = int(stats[local_id, cv2.CC_STAT_WIDTH])
            height = int(stats[local_id, cv2.CC_STAT_HEIGHT])
            region_id = next_region_id
            next_region_id += 1
            regions.append(
                RoleRegion(
                    region_id=region_id,
                    role=role,
                    area=area,
                    bbox_xywh=(x, y, width, height),
                    observer_positive_pixels=tuple(
                        (observer.name, int(np.count_nonzero(mask & component)))
                        for observer, mask in zip(validated, masks)
                        if observer.role == role
                    ),
                )
            )

    # Scan role-label maps once per role pair.  This avoids a full-image
    # dilation for every region pair on 2k x 2k inputs.
    contacts: list[RoleContact] = []
    role_region_ids = {
        role: [region.region_id for region in regions if region.role == role]
        for role in role_names
    }
    shifts = tuple(
        (dy, dx)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if (dy, dx) != (0, 0)
    )
    for first_index, first_role in enumerate(role_names):
        first_labels = role_label_maps[first_role]
        for second_role in role_names[first_index + 1 :]:
            second_labels = role_label_maps[second_role]
            overlap_mask = (first_labels > 0) & (second_labels > 0)
            overlap_keys = (
                first_labels[overlap_mask].astype(np.uint64) << np.uint64(32)
            ) | second_labels[overlap_mask].astype(np.uint64)
            overlap_counts = {
                int(key): int(count)
                for key, count in zip(*np.unique(overlap_keys, return_counts=True))
            }
            adjacent_counts: dict[int, int] = {}
            height, width = first_labels.shape
            for dy, dx in shifts:
                first_y0 = max(0, -dy)
                first_y1 = min(height, height - dy)
                first_x0 = max(0, -dx)
                first_x1 = min(width, width - dx)
                second_y0 = max(0, dy)
                second_y1 = min(height, height + dy)
                second_x0 = max(0, dx)
                second_x1 = min(width, width + dx)
                first_slice = first_labels[first_y0:first_y1, first_x0:first_x1]
                second_slice = second_labels[second_y0:second_y1, second_x0:second_x1]
                adjacent_mask = (first_slice > 0) & (second_slice > 0)
                keys = (
                    first_slice[adjacent_mask].astype(np.uint64) << np.uint64(32)
                ) | second_slice[adjacent_mask].astype(np.uint64)
                for key, count in zip(*np.unique(keys, return_counts=True)):
                    key_int = int(key)
                    adjacent_counts[key_int] = adjacent_counts.get(key_int, 0) + int(count)
            # Labels are 1-based and region records were appended in exactly
            # that order for each role.
            for key in sorted(set(overlap_counts) | set(adjacent_counts)):
                first_local = key >> 32
                second_local = key & 0xFFFFFFFF
                first_id = role_region_ids[first_role][first_local - 1]
                second_id = role_region_ids[second_role][second_local - 1]
                contacts.append(
                    RoleContact(
                        first_region_id=first_id,
                        second_region_id=second_id,
                        first_role=first_role,
                        second_role=second_role,
                        overlap_pixels=overlap_counts.get(key, 0),
                        adjacent_pixels=adjacent_counts.get(key, 0),
                    )
                )

    return ContactAwareRoleGraph(
        source_only=True,
        human_labels_used=False,
        owner_arrays_used=False,
        unknown_not_treated_as_negative=True,
        observed_pixels=int(observed_union.sum()),
        unknown_pixels=int(unknown.sum()),
        observed_union=observed_union,
        unknown=unknown,
        regions=tuple(regions),
        contacts=tuple(contacts),
    )
