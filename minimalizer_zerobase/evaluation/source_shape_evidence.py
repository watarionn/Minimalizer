"""Deterministic source-derived vector and contour-shape evidence for SA10.19.

This module produces evidence only.  It never selects or repairs visible
geometry, and its result cannot override SA10.18 structural hard gates.
"""
from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def _largest_contour(mask: np.ndarray) -> np.ndarray | None:
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(contours, key=cv2.contourArea, default=None)


def _contour_record(mask: np.ndarray) -> dict[str, Any]:
    contour = _largest_contour(mask)
    if contour is None or cv2.contourArea(contour) <= 0:
        return {"available": False, "area": 0.0, "points": 0}
    perimeter = float(cv2.arcLength(contour, True))
    hu = cv2.HuMoments(cv2.moments(contour)).ravel()
    hu_log = [float(-np.sign(v) * np.log10(abs(v))) if v else 0.0 for v in hu]
    return {
        "available": True,
        "area": float(cv2.contourArea(contour)),
        "perimeter": perimeter,
        "points": int(len(contour)),
        "hu_moments_log10": hu_log,
        "contour": contour,
    }


def evaluate_source_shape_evidence(source_mask: np.ndarray, candidate_mask: np.ndarray) -> dict[str, Any]:
    """Compare source/candidate outer contours without granting authority."""
    if source_mask.shape != candidate_mask.shape or source_mask.ndim != 2:
        raise ValueError("source and candidate masks must be same-size 2D arrays")
    source = _contour_record(source_mask)
    candidate = _contour_record(candidate_mask)
    if not source["available"] or not candidate["available"]:
        return {"schema_version": "sa10.19-source-shape-evidence-v1", "available": False,
                "match_shapes_i1": None, "hu_moments_available": False,
                "vectorization": {"backend": "opencv-contour", "available": True}}
    score = float(cv2.matchShapes(source["contour"], candidate["contour"], cv2.CONTOURS_MATCH_I1, 0.0))
    source.pop("contour"); candidate.pop("contour")
    return {
        "schema_version": "sa10.19-source-shape-evidence-v1",
        "available": True,
        "match_shapes_i1": score,
        "hu_moments_available": True,
        "source": source,
        "candidate": candidate,
        "vectorization": {"backend": "opencv-contour", "available": True, "authority": False},
        "authority": {"source_anatomy": True, "source_silhouette": True, "topology": True,
                       "shape_matching": False, "vectorization": False},
    }


def vtracer_backend_status() -> dict[str, Any]:
    """Report optional VTracer availability; importing it is never required."""
    try:
        import vtracer  # type: ignore
    except ImportError:
        return {"name": "vtracer", "available": False, "optional": True,
                "license_boundary": "MIT OR Apache-2.0", "reason": "not installed"}
    return {"name": "vtracer", "available": True, "optional": True,
            "version": getattr(vtracer, "__version__", "unknown"),
            "license_boundary": "MIT OR Apache-2.0", "authority": False}
