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
from .residual_layer_reauthoring import (
    DEFAULT_RESIDUAL_GLOBAL_CAP,
    reauthor_residual_layers,
)


CANONICAL_MACRO_STAGE_VERSION = "sa7.44-v1"


def apply_semantic_macro_stage(
    scene: VectorScene,
    semantic_masks: Mapping[str, np.ndarray],
    palette: Mapping[str, str],
    *,
    global_primitive_budget: int = DEFAULT_MACRO_GLOBAL_CAP,
    residual_global_cap: int = DEFAULT_RESIDUAL_GLOBAL_CAP,
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

    role_masks = {
        "hair": np.asarray(semantic_masks["hair"]).astype(bool),
        "major_clothing": np.asarray(
            semantic_masks["major_clothing"]
        ).astype(bool),
    }
    residuals, residual_report = reauthor_residual_layers(
        role_masks,
        macros,
        global_cap=residual_global_cap,
    )

    result = replace_macro_roles(
        scene,
        tuple(macros) + tuple(residuals),
        dict(palette),
        require_roles=required,
    )
    provenance = {
        **result.scene.provenance,
        "semantic_macro_stage": CANONICAL_MACRO_STAGE_VERSION,
        "semantic_macro_budget": budget.to_dict(),
        "semantic_residual_layers": residual_report.to_dict(),
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
