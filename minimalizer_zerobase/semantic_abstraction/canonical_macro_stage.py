from __future__ import annotations

from typing import Mapping

import numpy as np

from minimalizer_zerobase.compose.composer import VectorScene
from minimalizer_zerobase.render import SvgRenderer

from .macro_geometry_reauthoring import (
    DEFAULT_MACRO_GLOBAL_CAP,
    reauthor_macro_geometry_with_budget,
)
from .macro_renderer_integration import MacroRenderResult, replace_macro_roles


CANONICAL_MACRO_STAGE_VERSION = "sa7.43-v1"


def apply_semantic_macro_stage(
    scene: VectorScene,
    semantic_masks: Mapping[str, np.ndarray],
    palette: Mapping[str, str],
    *,
    global_primitive_budget: int = DEFAULT_MACRO_GLOBAL_CAP,
) -> MacroRenderResult:
    required = ("hair", "major_clothing")
    missing = [role for role in required if role not in semantic_masks]
    if missing:
        raise ValueError("missing semantic masks: " + ",".join(missing))

    if not any(
        primitive.source_region_id == "hair"
        for primitive in scene.primitives
    ):
        raise ValueError("scene lacks hair semantic authority")
    if not any(
        primitive.source_region_id == "major_clothing"
        for primitive in scene.primitives
    ):
        raise ValueError("scene lacks major_clothing semantic authority")

    macros, budget = reauthor_macro_geometry_with_budget(
        hair_mask=semantic_masks["hair"],
        clothing_mask=semantic_masks["major_clothing"],
        global_primitive_budget=global_primitive_budget,
    )
    result = replace_macro_roles(
        scene,
        macros,
        dict(palette),
        require_roles=required,
    )
    provenance = {
        **result.scene.provenance,
        "semantic_macro_stage": CANONICAL_MACRO_STAGE_VERSION,
        "semantic_macro_budget": budget.to_dict(),
    }
    output = VectorScene(
        result.scene.width,
        result.scene.height,
        result.scene.primitives,
        provenance,
    )
    return MacroRenderResult(
        output,
        SvgRenderer().render(output),
        result.replaced_roles,
    )
