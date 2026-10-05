from __future__ import annotations

from typing import Any, Mapping

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.render import SvgRenderer


class AuthorizedGeometryError(RuntimeError):
    pass


KIND_MAP = {
    "polygon": "convex_polygon",
    "ellipse": "ellipse",
    "ring": "ellipse",
    "ribbon": "rectangle",
    "trapezoid": "trapezoid",
    "bezier_silhouette": "convex_polygon",
}


def _bbox(mask: Mapping[str, Any]) -> tuple[float, float, float, float]:
    box = mask.get("bbox")
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        raise AuthorizedGeometryError("authorized semantic mask requires bbox")
    x, y, w, h = (float(v) for v in box)
    if w <= 0 or h <= 0:
        raise AuthorizedGeometryError("authorized semantic mask bbox must have positive size")
    return x, y, w, h


def _feature_bbox(
    bbox: tuple[float, float, float, float], ordinal: int, count: int
) -> tuple[float, float, float, float]:
    """Make repeated primitive budget geometrically effective without leaving authority."""
    x, y, w, h = bbox
    if count <= 1:
        return bbox
    phase = ordinal % 4
    ring = ordinal // 4
    ix = min(w * (0.06 + 0.035 * ring), w * 0.28)
    iy = min(h * (0.06 + 0.035 * ring), h * 0.28)
    left = ix if phase in (0, 2) else ix * 0.45
    right = ix if phase in (1, 2) else ix * 0.45
    top = iy if phase in (0, 1) else iy * 0.45
    bottom = iy if phase in (2, 3) else iy * 0.45
    return x + left, y + top, w - left - right, h - top - bottom


def _descriptor_bias(mask: Mapping[str, Any]) -> tuple[float, float]:
    descriptor = mask.get("mask_descriptor")
    if not isinstance(descriptor, Mapping) or descriptor.get("grid") != [4, 4]:
        return 0.0, 0.0
    occ = descriptor.get("occupancy")
    if not isinstance(occ, list) or len(occ) != 4 or any(not isinstance(r, list) or len(r) != 4 for r in occ):
        return 0.0, 0.0
    total = sum(float(v) for row in occ for v in row)
    if total <= 0:
        return 0.0, 0.0
    cx = sum((x + .5) * float(occ[y][x]) for y in range(4) for x in range(4)) / total / 4
    cy = sum((y + .5) * float(occ[y][x]) for y in range(4) for x in range(4)) / total / 4
    return max(-.18, min(.18, cx - .5)), max(-.18, min(.18, cy - .5))


def fit_authorized_geometry(
    *,
    geometry_plan: Mapping[str, Any],
    semantic_masks: Mapping[str, Mapping[str, Any]],
    width: int,
    height: int,
    palette: Mapping[str, str],
    fitter: str = "native",
) -> VectorScene:
    if fitter not in {"native", "vtracer"}:
        raise AuthorizedGeometryError("unsupported fitter")
    if width <= 0 or height <= 0:
        raise AuthorizedGeometryError("canvas dimensions must be positive")

    rows = geometry_plan.get("primitives")
    if not isinstance(rows, list) or not rows:
        raise AuthorizedGeometryError("authorized geometry plan requires primitives")

    planned_features = {row.get("feature_id") for row in rows}
    missing_palette_features = planned_features - set(palette)
    extra_palette_features = set(palette) - planned_features
    if missing_palette_features:
        raise AuthorizedGeometryError("missing palette assignment: " + ", ".join(sorted(missing_palette_features)))
    if extra_palette_features:
        raise AuthorizedGeometryError("palette supplied for unauthorized feature: " + ", ".join(sorted(extra_palette_features)))
    unknown_masks = set(semantic_masks) - planned_features
    if unknown_masks:
        raise AuthorizedGeometryError("semantic mask supplied for unauthorized feature: " + ", ".join(sorted(unknown_masks)))

    feature_counts: dict[str, int] = {}
    for row in rows:
        fid = row.get("feature_id")
        feature_counts[fid] = feature_counts.get(fid, 0) + 1

    primitives = []
    identities = set()
    for z_order, row in enumerate(rows):
        feature_id = row.get("feature_id")
        kind = row.get("primitive_kind")
        ordinal = row.get("ordinal")
        identity = (feature_id, kind, ordinal)
        if None in identity or identity in identities:
            raise AuthorizedGeometryError("geometry plan contains invalid or duplicate primitive identity")
        identities.add(identity)
        if feature_id not in semantic_masks:
            raise AuthorizedGeometryError(f"missing authorized semantic mask: {feature_id}")
        if semantic_masks[feature_id].get("authorized") is not True:
            raise AuthorizedGeometryError(f"semantic mask is not authorized: {feature_id}")
        if kind not in KIND_MAP:
            raise AuthorizedGeometryError(f"unsupported planned primitive kind: {kind}")
        if feature_id not in palette:
            raise AuthorizedGeometryError(f"missing palette assignment: {feature_id}")

        authority_box = _bbox(semantic_masks[feature_id])
        x, y, w, h = _feature_bbox(authority_box, int(ordinal), feature_counts[feature_id])
        bx, by = _descriptor_bias(semantic_masks[feature_id])
        ax, ay, aw, ah = authority_box
        dx, dy = bx * aw * .35, by * ah * .35
        x = min(max(x + dx, ax), ax + aw - w)
        y = min(max(y + dy, ay), ay + ah - h)
        rendered_kind = KIND_MAP[kind]
        params: dict[str, Any] = {"bbox": [x, y, w, h]}
        if rendered_kind == "ellipse":
            params.update({"cx": x + w / 2, "cy": y + h / 2, "rx": w / 2, "ry": h / 2})
        elif rendered_kind == "trapezoid":
            inset = .12 * w
            params["points"] = [[x + inset, y], [x + w - inset, y], [x + w, y + h], [x, y + h]]
        elif rendered_kind == "convex_polygon":
            params["points"] = [[x+w*.2,y],[x+w*.8,y],[x+w,y+h*.35],[x+w*.82,y+h],[x+w*.18,y+h],[x,y+h*.35]]

        primitives.append(ComposedPrimitive(
            primitive_id=f"golden:{feature_id}:{kind}:{ordinal}",
            source_region_id=feature_id,
            selected_candidate_id=f"authorized:{fitter}:{feature_id}:{kind}:{ordinal}",
            primitive_type=rendered_kind,
            parameters=params,
            fill_ref=palette[feature_id],
            z_order=z_order,
        ))

    return VectorScene(
        width=width,
        height=height,
        primitives=tuple(primitives),
        provenance={
            "producer": "AuthorizedGeometryFitter",
            "fitter": fitter,
            "semantic_authority": "manifest_and_authorized_masks",
            "fitter_may_decide_semantics": False,
            "golden_raster_used": False,
            "repeated_budget_geometry": "deterministic_in_bbox_decomposition",
            "mask_descriptor_used": True,
        },
    )


def render_authorized_geometry(scene: VectorScene) -> str:
    return SvgRenderer().render(scene)
