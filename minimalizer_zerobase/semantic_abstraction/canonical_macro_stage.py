from __future__ import annotations
from typing import Mapping
import numpy as np
from minimalizer_zerobase.compose.composer import VectorScene
from .macro_geometry_reauthoring import reauthor_macro_geometry
from .macro_renderer_integration import MacroRenderResult,replace_macro_roles
CANONICAL_MACRO_STAGE_VERSION="sa7.27-v1"
def apply_semantic_macro_stage(scene:VectorScene,semantic_masks:Mapping[str,np.ndarray],palette:Mapping[str,str])->MacroRenderResult:
 required=("hair","major_clothing");missing=[r for r in required if r not in semantic_masks]
 if missing:raise ValueError("missing semantic masks: "+",".join(missing))
 if not any(p.source_region_id=="hair" for p in scene.primitives):raise ValueError("scene lacks hair semantic authority")
 if not any(p.source_region_id=="major_clothing" for p in scene.primitives):raise ValueError("scene lacks major_clothing semantic authority")
 macros=reauthor_macro_geometry(hair_mask=semantic_masks["hair"],clothing_mask=semantic_masks["major_clothing"])
 result=replace_macro_roles(scene,macros,dict(palette),require_roles=required)
 prov={**result.scene.provenance,"semantic_macro_stage":CANONICAL_MACRO_STAGE_VERSION}
 out=VectorScene(result.scene.width,result.scene.height,result.scene.primitives,prov)
 from minimalizer_zerobase.render import SvgRenderer
 return MacroRenderResult(out,SvgRenderer().render(out),result.replaced_roles)
