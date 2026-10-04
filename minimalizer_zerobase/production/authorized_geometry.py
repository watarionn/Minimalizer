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

        x, y, w, h = _bbox(semantic_masks[feature_id])
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
        },
    )


def render_authorized_geometry(scene: VectorScene) -> str:
    return SvgRenderer().render(scene)
