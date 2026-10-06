from __future__ import annotations
import numpy as np
from minimalizer_zerobase.production.palette_role_candidates import propose_palette_role_candidates
from minimalizer_zerobase.production.semantic_edge_regions import EdgeRegion

SA83_VERSION="sa8.3-v1"

def propose_palette_budget_regions(
    rgb:np.ndarray, part_mask:np.ndarray, semantic_part:str,
    *, palette_role_budget:int=3, primitive_budget:int=3,
    min_component_ratio:float=.025,
)->tuple[EdgeRegion,...]:
    """Expose SA8 source components as ordinary perceptual-budget candidates.

    No dedicated draw pass is granted. Existing global budget/scoring decides
    whether any SA8 evidence survives.
    """
    out=[]
    for c in propose_palette_role_candidates(
        rgb,part_mask,semantic_part,palette_role_budget=palette_role_budget,
        primitive_budget=primitive_budget,min_role_ratio=.085,
        min_component_ratio=min_component_ratio,
    ):
        out.append(EdgeRegion(mask=c.mask,rgb=c.rgb,area=c.pixel_count,edge_boundary=0.0))
    return tuple(out)
