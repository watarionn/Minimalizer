"""Source-only full-region reconstruction primitives for Lane A L02.

This module deliberately replaces pixel-patch guards with a whole-image
observation stage.  It does not consume frozen owner arrays, human masks, or
review receipts.  The result is semantic evidence and connected components,
not an owner-number candidate.  Assigning a component to an owner is a
separate authority-bearing stage and must abstain until that authority exists.

The implementation is research-only.  It never promotes Phase4, changes
production, or treats an unobserved pixel as a negative.
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image
from PIL import UnidentifiedImageError


class SourceOwnerReconstructionHold(ValueError):
    """Raised when source-only reconstruction cannot be authenticated."""


# Sapiens2 DOME-29 body-part IDs.  These are model taxonomy constants, not
# case-fitted labels or human review input.
SAPIENS2_DOME29_NAMES = {
    0: "Background",
    1: "Apparel",
    2: "Eyeglass",
    3: "Face_Neck",
    4: "Hair",
    5: "Left_Foot",
    6: "Left_Hand",
    7: "Left_Lower_Arm",
    8: "Left_Lower_Leg",
    9: "Left_Shoe",
    10: "Left_Sock",
    11: "Left_Upper_Arm",
    12: "Left_Upper_Leg",
    13: "Lower_Clothing",
    14: "Right_Foot",
    15: "Right_Hand",
    16: "Right_Lower_Arm",
    17: "Right_Lower_Leg",
    18: "Right_Shoe",
    19: "Right_Sock",
    20: "Right_Upper_Arm",
    21: "Right_Upper_Leg",
    22: "Torso",
    23: "Upper_Clothing",
    24: "Lower_Lip",
    25: "Upper_Lip",
    26: "Lower_Teeth",
    27: "Upper_Teeth",
    28: "Tongue",
}

GARMENT_CLASS_IDS = frozenset({1, 13, 23})
ARM_CLASS_IDS = frozenset({6, 7, 11, 15, 16, 20})
LOWER_CLOTHING_CLASS_IDS = frozenset({13})
UPPER_CLOTHING_CLASS_IDS = frozenset({1, 23})


@dataclass(frozen=True)
class ComponentEvidence:
    component_id: int
    semantic_band: str
    area: int
    bbox_xywh: tuple[int, int, int, int]
    components4: int
    components8: int
    holes4: int
    holes8: int


@dataclass(frozen=True)
class ReconstructionEvidence:
    source_sha256: str
    class_map_sha256: str
    source_only: bool
    human_labels_used: bool
    unknown_not_treated_as_negative: bool
    owner_arrays_used: bool
    source_opaque_pixels: int
    garment_pixels: int
    upper_clothing_pixels: int
    lower_clothing_pixels: int
    arm_pixels: int
    unknown_pixels: int
    garment_components: tuple[ComponentEvidence, ...]
    owner_assignment: str
    quality: str = "UNASSESSED"
    phase4: str = "FAIL"
    l02: str = "HOLD"

    def as_dict(self) -> dict:
        result = self.__dict__.copy()
        result["garment_components"] = [item.__dict__ for item in self.garment_components]
        return result


def _sha256(data: bytes | np.ndarray) -> str:
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(data.tobytes(order="C")).hexdigest()


def _decode_signed_rgba(source_bytes: bytes) -> np.ndarray:
    if type(source_bytes) is not bytes or not source_bytes:
        raise SourceOwnerReconstructionHold("SIGNED_SOURCE_BYTES_REQUIRED")
    try:
        with Image.open(io.BytesIO(source_bytes)) as image:
            return np.asarray(image.convert("RGBA"), dtype=np.uint8)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SourceOwnerReconstructionHold("INVALID_SIGNED_SOURCE_IMAGE") from exc


def _component_evidence(mask: np.ndarray, semantic_band: str) -> tuple[ComponentEvidence, ...]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    records: list[ComponentEvidence] = []
    for component_id in range(1, count):
        component = labels == component_id
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        x = int(stats[component_id, cv2.CC_STAT_LEFT])
        y = int(stats[component_id, cv2.CC_STAT_TOP])
        width = int(stats[component_id, cv2.CC_STAT_WIDTH])
        height = int(stats[component_id, cv2.CC_STAT_HEIGHT])
        records.append(
            ComponentEvidence(
                component_id=component_id,
                semantic_band=semantic_band,
                area=area,
                bbox_xywh=(x, y, width, height),
                components4=_component_count(component, 4),
                components8=_component_count(component, 8),
                holes4=_hole_count(component, 4),
                holes8=_hole_count(component, 8),
            )
        )
    return tuple(records)


def _component_count(mask: np.ndarray, connectivity: int) -> int:
    return int(cv2.connectedComponents(mask.astype(np.uint8), connectivity)[0] - 1)


def _hole_count(mask: np.ndarray, connectivity: int) -> int:
    if not np.any(mask):
        return 0
    padded = np.pad(mask.astype(np.uint8), 1, constant_values=0)
    background = (padded == 0).astype(np.uint8)
    count, labels, _, _ = cv2.connectedComponentsWithStats(background, connectivity)
    border = set(np.unique(np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1]))))
    return int(sum(1 for label in range(1, count) if label not in border))


def reconstruct_source_regions(
    *,
    source_bytes: bytes,
    expected_source_sha256: str,
    class_ids: np.ndarray,
    expected_class_map_sha256: str,
) -> tuple[dict[str, np.ndarray], ReconstructionEvidence]:
    """Build whole-image semantic evidence from an authenticated source.

    The returned arrays are mutually exclusive and source-alpha bounded:
    ``upper_clothing``, ``lower_clothing``, ``arm``, and ``unknown``.  Unknown
    means no positive observation was available; it is never used as a
    negative.  No existing owner array is accepted by this API.
    """
    if type(expected_source_sha256) is not str or len(expected_source_sha256) != 64:
        raise SourceOwnerReconstructionHold("SOURCE_SHA_REQUIRED")
    if _sha256(source_bytes) != expected_source_sha256:
        raise SourceOwnerReconstructionHold("SIGNED_SOURCE_SHA_MISMATCH")
    source = _decode_signed_rgba(source_bytes)
    if (
        type(class_ids) is not np.ndarray
        or class_ids.dtype != np.uint8
        or class_ids.ndim != 2
        or class_ids.shape != source.shape[:2]
        or not class_ids.size
    ):
        raise SourceOwnerReconstructionHold("INVALID_SOURCE_ONLY_CLASS_MAP")
    if type(expected_class_map_sha256) is not str or len(expected_class_map_sha256) != 64:
        raise SourceOwnerReconstructionHold("CLASS_MAP_SHA_REQUIRED")
    if _sha256(class_ids) != expected_class_map_sha256:
        raise SourceOwnerReconstructionHold("CLASS_MAP_SHA_MISMATCH")
    if np.any(class_ids > max(SAPIENS2_DOME29_NAMES)):
        raise SourceOwnerReconstructionHold("UNKNOWN_SAPIENS_CLASS_ID")

    opaque = source[:, :, 3] != 0
    upper = np.isin(class_ids, tuple(UPPER_CLOTHING_CLASS_IDS)) & opaque
    lower = np.isin(class_ids, tuple(LOWER_CLOTHING_CLASS_IDS)) & opaque
    arm = np.isin(class_ids, tuple(ARM_CLASS_IDS)) & opaque
    garment = upper | lower
    unknown = opaque & ~garment & ~arm
    if np.any((upper.astype(np.uint8) + lower + arm + unknown) > 1):
        raise SourceOwnerReconstructionHold("SEMANTIC_BAND_OVERLAP")

    evidence = ReconstructionEvidence(
        source_sha256=expected_source_sha256,
        class_map_sha256=expected_class_map_sha256,
        source_only=True,
        human_labels_used=False,
        unknown_not_treated_as_negative=True,
        owner_arrays_used=False,
        source_opaque_pixels=int(opaque.sum()),
        garment_pixels=int(garment.sum()),
        upper_clothing_pixels=int(upper.sum()),
        lower_clothing_pixels=int(lower.sum()),
        arm_pixels=int(arm.sum()),
        unknown_pixels=int(unknown.sum()),
        garment_components=_component_evidence(garment, "garment"),
        owner_assignment="ABSTAIN_UNTIL_INDEPENDENT_OWNER_AUTHORITY",
    )
    return {
        "upper_clothing": upper,
        "lower_clothing": lower,
        "garment": garment,
        "arm": arm,
        "unknown": unknown,
    }, evidence


def assert_owner_assignment_is_separate(evidence: ReconstructionEvidence) -> None:
    """Fail closed if a caller tries to treat observation as an owner result."""
    if evidence.owner_assignment != "ABSTAIN_UNTIL_INDEPENDENT_OWNER_AUTHORITY":
        raise SourceOwnerReconstructionHold("OWNER_AUTHORITY_NOT_SEPARATE")
