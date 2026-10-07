"""Deterministic source-derived vector and contour-shape evidence for SA10.19.

This module produces evidence only.  It never selects or repairs visible
geometry, and its result cannot override SA10.18 structural hard gates.
"""
from __future__ import annotations

from typing import Any
import hashlib

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
    """Report the isolated backend without importing its native extension."""
    from minimalizer_zerobase.refine.vtracer_subprocess import LICENSE_BOUNDARY
    return {"name": "vtracer", "available": True, "optional": True,
            "isolated": True, "license_boundary": LICENSE_BOUNDARY,
            "authority": False}


def generate_vtracer_candidate(
    source_mask: np.ndarray,
    authorized_semantic_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    """Return a source-bound VTracer tranche-1 candidate record.

    Tranche 1 is deliberately an adapter boundary, not a renderer.  The
    source mask is immutable evidence and the optional backend may only see a
    semantic mask that was already authorized upstream.  Missing backend,
    missing authorization, shape mismatch, or pixels outside the source all
    fail closed with an explicit no-op; no visible pixels are generated.
    """
    source = np.asarray(source_mask, dtype=bool)
    status = vtracer_backend_status()
    base = {
        "schema_version": "sa10.26-vtracer-candidate-v1",
        "backend": status,
        "candidate_authority": False,
        "visible_output_changed": False,
        "rollback": False,
        "source_mask_sha256": hashlib.sha256(source.tobytes()).hexdigest(),
    }
    if source.ndim != 2:
        return {**base, "status": "no-op", "reason": "invalid_source_mask"}
    if authorized_semantic_mask is None:
        return {**base, "status": "no-op", "reason": "semantic_authorization_required"}
    authorized = np.asarray(authorized_semantic_mask, dtype=bool)
    if authorized.shape != source.shape:
        return {**base, "status": "no-op", "reason": "mask_shape_mismatch"}
    if np.any(authorized & ~source):
        return {**base, "status": "no-op", "reason": "authorized_mask_outside_immutable_source"}
    base["authorized_semantic_mask_sha256"] = hashlib.sha256(
        authorized.tobytes()
    ).hexdigest()
    from minimalizer_zerobase.refine.vtracer_subprocess import run_vtracer_isolated
    result = run_vtracer_isolated(authorized)
    return {**base, **result, "authorized_semantic_mask_sha256": base["authorized_semantic_mask_sha256"]}
