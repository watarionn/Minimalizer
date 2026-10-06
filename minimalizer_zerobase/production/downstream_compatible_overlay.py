from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from minimalizer_zerobase.production.palette_role_candidates import PaletteRolePrimitiveCandidate, propose_palette_role_candidates

SA82_VERSION="sa8.2-v1"

@dataclass(frozen=True)
class DownstreamCompatibleOverlay:
    candidate: PaletteRolePrimitiveCandidate
    visible_mask: np.ndarray
    visible_gain_pixels: int
    visible_gain_ratio: float
    downstream_overlap_ratio: float

def propose_downstream_compatible_overlays(
    rgb:np.ndarray, part_mask:np.ndarray, semantic_part:str,
    established_masks:tuple[np.ndarray,...], downstream_masks:tuple[np.ndarray,...],
    *, palette_role_budget:int=3, candidate_budget:int=6, overlay_budget:int=1,
    min_visible_gain_ratio:float=.035, max_downstream_overlap_ratio:float=.25,
)->tuple[DownstreamCompatibleOverlay,...]:
    """Select SA8 components only when useful pixels remain after later layers.

    Later renderer layers are treated conservatively as overwrite authority.
    The selector never changes their masks or ordering.
    """
    authority=np.asarray(part_mask,bool)
    if overlay_budget<0: raise ValueError("overlay_budget must be >= 0")
    if overlay_budget==0 or not np.any(authority): return ()
    covered=np.zeros_like(authority)
    for m in established_masks:
        mm=np.asarray(m,bool)
        if mm.shape!=authority.shape: raise ValueError("shape mismatch")
        covered|=mm&authority
    downstream=np.zeros_like(authority)
    for m in downstream_masks:
        mm=np.asarray(m,bool)
        if mm.shape!=authority.shape: raise ValueError("shape mismatch")
        downstream|=mm&authority
    total=int(authority.sum())
    candidates=propose_palette_role_candidates(
        rgb,authority,semantic_part,palette_role_budget=palette_role_budget,
        primitive_budget=candidate_budget,min_role_ratio=.085,min_component_ratio=.025,
    )
    rows=[]
    for c in candidates:
        raw=c.mask&authority&~covered
        raw_n=int(raw.sum())
        if not raw_n: continue
        overlap=float((raw&downstream).sum()/raw_n)
        visible=raw&~downstream
        gain=int(visible.sum());ratio=float(gain/total)
        if ratio<min_visible_gain_ratio or overlap>max_downstream_overlap_ratio: continue
        rows.append(DownstreamCompatibleOverlay(c,visible,gain,ratio,overlap))
    rows.sort(key=lambda x:(-x.visible_gain_pixels,x.downstream_overlap_ratio,x.candidate.component_id))
    return tuple(rows[:overlay_budget])
