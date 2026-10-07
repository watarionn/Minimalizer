"""Deterministic source-derived vector and contour-shape evidence for SA10.19.

This module produces evidence only.  It never selects or repairs visible
geometry, and its result cannot override SA10.18 structural hard gates.
"""
from __future__ import annotations

from typing import Any
import hashlib
import re
import xml.etree.ElementTree as ET

import cv2
import numpy as np

_PATH_TOKEN = re.compile(r"([MLCZmlcz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)")


def rasterize_source_bound_svg(svg: str, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize the deliberately small VTracer subset, fail-closed.

    Only filled path data using M/L/C/Z and an optional translate() transform
    is accepted.  This is evidence rasterization, never a visible renderer.
    """
    root = ET.fromstring(svg)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("SVG root required")
    out = np.zeros(shape, np.uint8)
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "path":
            continue
        fill = element.attrib.get("fill", "").lower()
        if fill in {"none", ""}:
            continue
        transform = element.attrib.get("transform", "")
        match = re.fullmatch(r"translate\(\s*([-+0-9.eE]+)(?:[ ,]+([-+0-9.eE]+))?\s*\)", transform)
        if transform and not match:
            raise ValueError("unsupported transform")
        tx, ty = (float(match.group(1)), float(match.group(2) or 0)) if match else (0.0, 0.0)
        tokens = _PATH_TOKEN.findall(element.attrib.get("d", ""))
        if not tokens:
            raise ValueError("empty path")
        i = 0; command = None; points = []; start = None; current = None
        while i < len(tokens):
            if tokens[i].isalpha(): command = tokens[i]; i += 1
            if command not in {"M", "L", "C", "Z", "m", "l", "c", "z"}:
                raise ValueError("unsupported path command")
            if command.lower() == "z":
                if start and current and current != start: points.append(start)
                current = start; command = None; continue
            n = {"m": 2, "l": 2, "c": 6}[command.lower()]
            if i + n > len(tokens) or any(t.isalpha() for t in tokens[i:i+n]): raise ValueError("malformed path")
            vals = list(map(float, tokens[i:i+n])); i += n
            base = current or (0.0, 0.0); rel = command.islower()
            def p(x, y): return (x + (base[0] if rel else 0) + tx, y + (base[1] if rel else 0) + ty)
            if command.lower() == "c":
                p0 = current or (tx, ty); p1, p2, p3 = p(vals[0], vals[1]), p(vals[2], vals[3]), p(vals[4], vals[5])
                for t in np.linspace(0, 1, 17)[1:]:
                    u = 1-t; points.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0], u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
                current = p3
            else:
                current = p(vals[0], vals[1]); points.append(current)
            if command.lower() == "m": start = current; command = "l" if command == "m" else "L"
        if len(points) >= 3: cv2.fillPoly(out, [np.rint(np.asarray(points)).astype(np.int32)], 255)
    return out


def evaluate_source_bound_candidate(source_mask: np.ndarray, candidate_mask: np.ndarray) -> dict[str, Any]:
    if source_mask.shape != candidate_mask.shape or source_mask.ndim != 2: raise ValueError("same-size 2D masks required")
    source = np.asarray(source_mask) > 0
    candidate = (np.asarray(candidate_mask) > 0) & source
    inter = int(np.count_nonzero(source & candidate)); union = int(np.count_nonzero(source | candidate))
    boundary = cv2.morphologyEx(source.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    boundary_recall = float(np.count_nonzero(boundary & candidate) / max(1, np.count_nonzero(boundary)))
    n_source, _, _, _ = cv2.connectedComponentsWithStats(source.astype(np.uint8)); n_candidate, _, _, _ = cv2.connectedComponentsWithStats(candidate.astype(np.uint8))
    return {"schema_version":"sa10.26-source-bound-gate-v1", "iou": inter / max(1, union), "boundary_recall": boundary_recall, "source_components": n_source-1, "candidate_components": n_candidate-1, "material_topology_preserved": (n_source-1)==(n_candidate-1), "candidate_mask_sha256": hashlib.sha256(candidate.astype(np.uint8).tobytes()).hexdigest(), "authority": False}


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
