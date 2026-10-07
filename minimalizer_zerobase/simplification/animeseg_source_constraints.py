"""Deterministic, source-clipped AnimeSeg evidence for Phase 12.

AnimeSeg is an observer here.  Its RGB class mask can constrain where a
candidate may be considered salient, but it never creates pixels, changes a
semantic owner, or grants rendering authority.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import cv2
from PIL import Image

CLASS_NAMES = ("background", "skin", "face", "hair_main", "left_eye",
               "right_eye", "left_eyebrow", "right_eyebrow", "nose", "mouth",
               "clothes", "accessory")
CLASS_RGB = ((0, 0, 0), (255, 220, 180), (100, 150, 255), (255, 0, 0),
             (0, 255, 255), (255, 255, 0), (150, 255, 0), (0, 255, 100),
             (255, 140, 0), (255, 0, 150), (180, 0, 255), (128, 128, 0))
DETAIL_CLASSES = {"hair_main": "hair", "face": "face", "left_eye": "face",
                  "right_eye": "face", "left_eyebrow": "face",
                  "right_eyebrow": "face", "nose": "face", "mouth": "face"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_source_constraints(source_rgba: np.ndarray, animeseg_rgb: np.ndarray,
                             *, alpha_threshold: int = 1) -> dict[str, Any]:
    """Return masks clipped strictly to source alpha, plus audit metadata.

    Inputs are HxWx4 uint8 source RGBA and HxWx3 uint8 AnimeSeg RGB mask.
    Unknown AnimeSeg colors are excluded, never guessed.  The returned
    ``masks`` mapping is intentionally numpy-only and is not a render plan.
    """
    source = np.asarray(source_rgba)
    observed = np.asarray(animeseg_rgb)
    if source.ndim != 3 or source.shape[2] != 4 or source.dtype != np.uint8:
        raise ValueError("source_rgba must be uint8 HxWx4")
    if observed.ndim != 3 or observed.shape[2] != 3 or observed.dtype != np.uint8:
        raise ValueError("animeseg_rgb must be uint8 HxWx3")
    if source.shape[:2] != observed.shape[:2]:
        raise ValueError("source and AnimeSeg masks must have equal dimensions")
    if not 0 <= alpha_threshold <= 255:
        raise ValueError("alpha_threshold must be between 0 and 255")

    source_visible = source[..., 3] >= alpha_threshold
    masks: dict[str, np.ndarray] = {}
    rows: dict[str, dict[str, Any]] = {}
    known = np.zeros(source.shape[:2], dtype=bool)
    for name, rgb in zip(CLASS_NAMES, CLASS_RGB):
        raw = np.all(observed == np.asarray(rgb, dtype=np.uint8), axis=2)
        clipped = raw & source_visible
        masks[name] = clipped
        known |= raw
        rows[name] = {"raw_pixels": int(raw.sum()),
                      "source_clipped_pixels": int(clipped.sum()),
                      "alpha_removed_pixels": int((raw & ~source_visible).sum()),
                      "provenance": "animeseg-observer+source-alpha",
                      "authority": False}
    return {"schema_version": "sa10.28-animeseg-source-constraints-v1",
            "class_names": CLASS_NAMES, "source_shape": list(source.shape[:2]),
            "alpha_threshold": alpha_threshold,
            "source_visible_pixels": int(source_visible.sum()),
            "unknown_rgb_pixels": int((~known).sum()), "classes": rows,
            "masks": masks, "authority": False,
            "production_authority": False,
            "note": "observer evidence only; no generated pixels or semantic reassignment"}


def build_source_constraints_from_files(source: Path, animeseg_mask: Path,
                                        *, alpha_threshold: int = 1) -> dict[str, Any]:
    """File adapter used by diagnostics; source/mask hashes are recorded."""
    source = Path(source); animeseg_mask = Path(animeseg_mask)
    src = np.asarray(Image.open(source).convert("RGBA"), dtype=np.uint8)
    mask = np.asarray(Image.open(animeseg_mask).convert("RGB"), dtype=np.uint8)
    result = build_source_constraints(src, mask, alpha_threshold=alpha_threshold)
    result["source_sha256"] = _sha256(source)
    result["animeseg_mask_sha256"] = _sha256(animeseg_mask)
    return result


def source_bound_detail_groups(constraints: dict[str, Any], source_rgba: np.ndarray,
                               *, minimum_pixels: int = 3,
                               epsilon_px: float = 0.0) -> list[dict[str, Any]]:
    """Create optional polygon groups from source-clipped observed masks."""
    source = np.asarray(source_rgba)
    if source.ndim != 3 or source.shape[2] != 4 or source.dtype != np.uint8:
        raise ValueError("source_rgba must be uint8 HxWx4")
    masks = constraints.get("masks")
    if not isinstance(masks, dict):
        raise ValueError("source constraints must contain masks")
    groups = []
    for class_name, owner in DETAIL_CLASSES.items():
        mask = np.asarray(masks.get(class_name), dtype=bool)
        if mask.shape != source.shape[:2]:
            raise ValueError(f"AnimeSeg detail mask shape mismatch: {class_name}")
        if int(mask.sum()) < minimum_pixels:
            continue
        color = tuple(int(v) for v in np.median(source[mask, :3], axis=0).astype(np.uint8))
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        components = []
        for contour in sorted(contours, key=lambda c: (-cv2.contourArea(c), tuple(c[0, 0]))):
            if cv2.contourArea(contour) <= 0:
                continue
            approx = cv2.approxPolyDP(contour, float(epsilon_px), True)
            if len(approx) >= 3:
                components.append([[float(x), float(y)] for x, y in approx[:, 0, :]])
        if components:
            groups.append({"part": owner, "color": color, "mask": mask.copy(),
                           "source_ids": [], "source_actions": {"protect"},
                           "source_evidence_refs": [f"animeseg:{class_name}"],
                           "source_guided_kind": f"animeseg-{class_name}-detail",
                           "first_order": 100000 + CLASS_NAMES.index(class_name)})
    return groups


derive_source_constraints = build_source_constraints
