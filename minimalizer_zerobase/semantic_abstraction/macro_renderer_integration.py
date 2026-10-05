from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import numpy as np
from minimalizer_zerobase.compose.composer import ComposedPrimitive,VectorScene
from minimalizer_zerobase.render import SvgRenderer
from .macro_geometry_reauthoring import MacroGeometryPrimitive
MACRO_RENDER_VERSION="sa7.26-v1"
_ALLOWED=("hair","major_clothing")
@dataclass(frozen=True)
class MacroRenderResult:
 scene:VectorScene
 svg:str
 replaced_roles:tuple[str,...]
def _points(poly:np.ndarray)->list[list[float]]:
 a=np.asarray(poly)
 if a.ndim!=2 or a.shape[1]!=2 or len(a)<3:raise ValueError("macro polygon must be Nx2")
 return [[float(x),float(y)] for x,y in a]
def replace_macro_roles(scene:VectorScene,macros:Iterable[MacroGeometryPrimitive],palette:dict[str,str],*,require_roles:tuple[str,...]=("hair","major_clothing"))->MacroRenderResult:
 rows=tuple(macros);by_role={r:[] for r in _ALLOWED}
 for m in rows:
  if m.semantic_part not in by_role:raise ValueError("unauthorized macro role")
  by_role[m.semantic_part].append(m)
 for role in require_roles:
  if role not in by_role or not by_role[role]:raise ValueError(f"missing required macro role: {role}")
  if role not in palette:raise ValueError(f"missing macro palette: {role}")
 kept=[p for p in scene.primitives if p.source_region_id not in set(require_roles)]
 base_z={r:min((p.z_order for p in scene.primitives if p.source_region_id==r),default=len(scene.primitives)) for r in require_roles}
 added=[]
 for role in require_roles:
  for i,m in enumerate(by_role[role]):
   added.append(ComposedPrimitive(primitive_id=f"semantic-macro:{role}:{i}",source_region_id=role,selected_candidate_id=f"semantic-macro:{MACRO_RENDER_VERSION}:{role}:{i}",primitive_type="convex_polygon",parameters={"points":_points(m.polygon)},fill_ref=palette[role],z_order=base_z[role]+i))
 merged=tuple(sorted(kept+added,key=lambda p:(p.z_order,p.primitive_id)))
 out=VectorScene(width=scene.width,height=scene.height,primitives=merged,provenance={**scene.provenance,"semantic_macro_renderer":MACRO_RENDER_VERSION,"macro_semantic_authority":"upstream_authorized_masks","golden_raster_used":False})
 return MacroRenderResult(out,SvgRenderer().render(out),tuple(require_roles))
