from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

CompatibilityDisposition = Literal[
    "mapped", "legacy_retained", "versioned_deprecated", "out_of_scope"
]
PUBLIC_CONTRACT_SCHEMA_VERSION = "minimalizer-v2-public-contract-v1"


@dataclass(frozen=True, slots=True)
class PublicControlCompatibility:
    surface: Literal["web", "cli"]
    control: str
    disposition: CompatibilityDisposition
    route: Literal["v2", "legacy", "specialized_legacy"]
    v2_target: str | None
    rationale: str


@dataclass(frozen=True, slots=True)
class PublicContractCompatibilityReport:
    schema_version: str
    scope: str
    items: tuple[PublicControlCompatibility, ...]

    def to_dict(self) -> dict[str, object]:
        counts = {name: 0 for name in ("mapped", "legacy_retained", "versioned_deprecated", "out_of_scope")}
        for item in self.items:
            counts[item.disposition] += 1
        return {
            "schema_version": self.schema_version,
            "scope": self.scope,
            "disposition_counts": counts,
            "items": [asdict(item) for item in self.items],
        }

_WEB_SPECIALIZED = (
    "color_similarity",
    "color_size_mode",
    "color_order",
    "color_orientation",
    "color_selection_mode",
    "rinka_preset",
)

_WEB_LEGACY_RETAINED = (
    "level",
    "output_format",
    "mode",
    "colors",
    "max_shapes",
    "background",
)

_CLI_LEGACY_RETAINED = (
    "output", "png", "webp", "level", "colors", "max_shapes", "padding",
    "background", "no_lines", "no_layer_composition", "no_macro_underlays",
    "no_composition_skeleton", "no_multiscale", "no_semantics",
    "no_design_primitives", "no_design_palette", "no_patterns", "no_auto_retry",
    "ignore_alpha", "quality_report", "no_global_shape_value",
    "no_global_shape_cleanup", "no_character_structure", "no_body_primitives",
    "no_hand_analysis", "no_hand_primitives", "no_hand_geometry_validation",
    "no_hand_validation", "no_hand_quality", "no_limb_geometry_refine",
    "no_hair_body_guard", "no_character_layout", "no_character_quality",
    "no_character_auto_retry", "no_pose_proxy", "character_preset", "no_face_rules",
    "face_primitives", "no_face_validation", "no_face_geometry_quality",
    "no_face_contour_fit", "no_face_boundary_guard", "no_face_identity_budget",
    "no_face_identity_validation", "no_hair_rules", "no_outfit_rules", "no_prop_rules",
    "no_adaptive_character_budget", "no_outfit_structure_quality", "no_prop_symbol_quality",
    "no_character_wide_identity", "debug_dir",
)


def _item(
    surface: Literal["web", "cli"],
    control: str,
    disposition: CompatibilityDisposition,
    route: Literal["v2", "legacy", "specialized_legacy"],
    *,
    v2_target: str | None = None,
    rationale: str,
) -> PublicControlCompatibility:
    return PublicControlCompatibility(
        surface=surface,
        control=control,
        disposition=disposition,
        route=route,
        v2_target=v2_target,
        rationale=rationale,
    )

def build_public_contract_compatibility() -> PublicContractCompatibilityReport:
    items: list[PublicControlCompatibility] = [
        _item(
            "web", "file", "mapped", "v2", v2_target="input file",
            rationale="Both standard entry points accept the same source-image file boundary.",
        )
    ]
    for control in _WEB_LEGACY_RETAINED:
        items.append(_item(
            "web", control, "legacy_retained", "legacy",
            rationale="No exact V2 public-contract equivalence has been approved; retain legacy semantics until its dependent compatibility blocker is resolved.",
        ))
    for control in _WEB_SPECIALIZED:
        items.append(_item(
            "web", control, "out_of_scope", "specialized_legacy",
            rationale="This control belongs to Rinka Reference or Color Strip, which remain separately routed specialized modes.",
        ))
    items.append(_item(
        "cli", "input", "mapped", "v2", v2_target="input file",
        rationale="Legacy CLI and V2 shadow CLI consume the same source-image path.",
    ))
    for control in _CLI_LEGACY_RETAINED:
        items.append(_item(
            "cli", control, "legacy_retained", "legacy",
            rationale="The control has legacy-specific output or algorithm semantics and stays on the legacy route unless a later versioned contract maps or deprecates it.",
        ))
    return PublicContractCompatibilityReport(
        schema_version=PUBLIC_CONTRACT_SCHEMA_VERSION,
        scope="legacy_standard_public_controls_to_v2",
        items=tuple(items),
    )
