from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .semantic_manifest import validate_semantic_manifest


PRIMITIVE_KINDS = {"polygon", "ellipse", "ring", "ribbon", "trapezoid", "bezier_silhouette"}

ROLE_GRAMMAR: dict[str, tuple[str, ...]] = {
    "hair": ("bezier_silhouette", "polygon"),
    "eyewear_accessory": ("ring", "ellipse", "ribbon"),
    "necktie": ("trapezoid", "polygon", "ribbon"),
    "uniform": ("trapezoid", "polygon", "ribbon"),
    "hair_accessory": ("polygon", "ellipse"),
    "uniform_badges": ("ring", "ellipse"),
    "armband": ("ribbon", "trapezoid"),
}

FALLBACK_GRAMMAR = ("polygon", "ellipse", "trapezoid", "ribbon", "ring", "bezier_silhouette")


class GeometryGrammarError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeometryPrimitive:
    feature_id: str
    semantic_role: str
    primitive_kind: str
    ordinal: int
    source: str = "semantic_grammar"

    def __post_init__(self) -> None:
        if self.primitive_kind not in PRIMITIVE_KINDS:
            raise GeometryGrammarError(f"unsupported primitive kind: {self.primitive_kind}")
        if self.ordinal < 0:
            raise GeometryGrammarError("primitive ordinal must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "semantic_role": self.semantic_role,
            "primitive_kind": self.primitive_kind,
            "ordinal": self.ordinal,
            "source": self.source,
        }


def allowed_primitive_kinds(semantic_role: str) -> tuple[str, ...]:
    return ROLE_GRAMMAR.get(semantic_role, FALLBACK_GRAMMAR)


def build_geometry_plan(
    manifest: dict[str, Any],
    budget_report: dict[str, Any],
) -> dict[str, Any]:
    validate_semantic_manifest(manifest)
    if budget_report.get("case_id") != manifest["case_id"]:
        raise GeometryGrammarError("budget case_id does not match semantic manifest")

    features = {feature["id"]: feature for feature in manifest["features"]}
    allocations = budget_report.get("allocations")
    if not isinstance(allocations, list):
        raise GeometryGrammarError("budget report allocations are required")

    seen: set[str] = set()
    primitives: list[GeometryPrimitive] = []
    for row in sorted(allocations, key=lambda item: item.get("feature_id", "")):
        feature_id = row.get("feature_id")
        if feature_id not in features:
            raise GeometryGrammarError(f"budget references unknown feature: {feature_id}")
        if feature_id in seen:
            raise GeometryGrammarError(f"duplicate budget feature: {feature_id}")
        seen.add(feature_id)
        count = row.get("allocated_primitives")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise GeometryGrammarError(f"{feature_id}: allocated_primitives must be non-negative integer")
        feature = features[feature_id]
        if feature["disposition"] == "forbidden" and count:
            raise GeometryGrammarError(f"{feature_id}: forbidden feature cannot receive geometry")
        kinds = allowed_primitive_kinds(feature["semantic_role"])
        for ordinal in range(count):
            primitives.append(
                GeometryPrimitive(
                    feature_id=feature_id,
                    semantic_role=feature["semantic_role"],
                    primitive_kind=kinds[min(ordinal, len(kinds) - 1)],
                    ordinal=ordinal,
                )
            )

    missing = set(features) - seen
    if missing:
        raise GeometryGrammarError("budget missing feature allocation: " + ", ".join(sorted(missing)))

    return {
        "schema_version": "1.0",
        "case_id": manifest["case_id"],
        "grammar_version": "1.0",
        "primitives": [primitive.to_dict() for primitive in primitives],
    }


def validate_authorized_fit(
    plan: dict[str, Any],
    *,
    feature_id: str,
    primitive_kind: str,
    mask_authorized: bool,
    fitter: str,
) -> dict[str, Any]:
    if not mask_authorized:
        raise GeometryGrammarError("geometry fitting requires an authorized semantic mask")
    if fitter not in {"native", "vtracer"}:
        raise GeometryGrammarError("unsupported geometry fitter")
    planned = [
        row for row in plan.get("primitives", [])
        if row.get("feature_id") == feature_id
    ]
    if not planned:
        raise GeometryGrammarError(f"feature has no authorized primitive budget: {feature_id}")
    allowed = {row["primitive_kind"] for row in planned}
    if primitive_kind not in allowed:
        raise GeometryGrammarError(
            f"{feature_id}: primitive kind {primitive_kind} is outside authorized grammar"
        )
    return {
        "feature_id": feature_id,
        "primitive_kind": primitive_kind,
        "mask_authorized": True,
        "fitter": fitter,
        "semantic_authority": "manifest",
        "fitter_may_decide_semantics": False,
    }
