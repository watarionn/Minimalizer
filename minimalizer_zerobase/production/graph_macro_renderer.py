from __future__ import annotations
from typing import Mapping
import numpy as np
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph
from minimalizer_zerobase.production.semantic_contour import semantic_contour
from minimalizer_zerobase.production.part_color_regions import extract_part_color_regions
from minimalizer_zerobase.production.cross_part_region_graph import build_cross_part_region_graph, composed_regions
from minimalizer_zerobase.production.semantic_edge_regions import propose_edge_regions, propose_contrast_subregions
from minimalizer_zerobase.production.perceptual_region_budget import select_perceptual_regions
from minimalizer_zerobase.production.structural_motifs import arm_axis_band, clothing_major_regions, two_segment_arm_masks, clothing_authority, collar_motif, sleeve_boundary_motifs, sleeve_forearm_masses, collar_shape_segments, major_color_masses

def _median(rgb,mask):
 p=np.asarray(rgb)[np.asarray(mask).astype(bool)]
 if not len(p): return "#808080"
 v=np.median(p,axis=0).astype(int);return "#%02x%02x%02x"%tuple(v[:3])
def _bbox(m):
 y,x=np.where(np.asarray(m).astype(bool))
 return None if not len(x) else (x.min(),y.min(),x.max()+1,y.max()+1)
def _anchor(graph,part,kind_prefix):
 a=[x for x in graph.anchors if x.part_id==part and x.kind.startswith(kind_prefix)]
 return a[0].xy_pixel if a else None

def _contour_polygon(mask, max_vertices=18):
 pts=semantic_contour(mask,max_vertices)
 return None if len(pts)<3 else " ".join(f"{x:.1f},{y:.1f}" for x,y in pts)

def _strengthened_accent_mask(mask, authority, *, target_ratio=1.35):
 """Give a selected compact accent modest visual strength without leaving semantic authority."""
 m=np.asarray(mask,bool);a=np.asarray(authority,bool)
 target=max(int(m.sum()),int(np.ceil(m.sum()*target_ratio)))
 out=m.copy()
 while int(out.sum())<target:
  p=np.pad(out,1);grown=np.zeros_like(out)
  for dy,dx in ((0,1),(1,0),(1,2),(2,1)):
   grown|=p[dy:dy+out.shape[0],dx:dx+out.shape[1]]
  nxt=(out|grown)&a
  if np.array_equal(nxt,out):break
  out=nxt
 return out

def render_graph_macro_svg(rgb:np.ndarray, masks:Mapping[str,np.ndarray], graph:StructuralLayoutGraph, allocations:Mapping[str,int])->str:
 h,w=np.asarray(rgb).shape[:2]; chunks=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="#fff"/>']
 # Central chain uses semantic silhouettes; graph still owns ordering/attachment policy.
 for role in ("lower_body","torso"):
  if allocations.get(role,0)<1 or role not in masks: continue
  pts=_contour_polygon(masks[role],18)
  if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,masks[role])}"/>')
 # Arms retain their real Phase4 silhouette instead of synthetic bbox ribbons.
 for role in ("left_arm","right_arm"):
  if allocations.get(role,0)<1 or role not in masks: continue
  near,far=sleeve_forearm_masses(rgb,masks[role],masks.get("torso",masks[role]))
  for segment in (near,far):
   if not np.any(segment):continue
   pts=_contour_polygon(segment,12)
   if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,segment)}"/>')
 # Head and hair also retain semantic contours; graph determines paint order. Hair is capped around the head neighborhood instead of using full hair bbox depth.
 if allocations.get("head",0)>0 and "head" in masks:
  pts=_contour_polygon(masks["head"],16)
  if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,masks["head"])}"/>')
 if allocations.get("hair",0)>0 and "hair" in masks:
  pts=_contour_polygon(masks["hair"],20)
  if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,masks["hair"])}"/>')
 # Accessory remains graph-authorized, but its actual semantic contour is preserved.
 if allocations.get("accessory",0)>0 and "accessory" in masks:
  rel=[r for r in graph.relations if r.source_part=="accessory_or_held_object" and r.relation_kind=="attached_to"]
  pts=_contour_polygon(masks["accessory"],12)
  if rel and pts:
   chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,masks["accessory"])}"/>')
 # Large garment masses establish collar/body/sleeve-like construction before small evidence.
 garment_mask=clothing_authority(masks["torso"],masks.get("major_clothing")) if "torso" in masks else masks.get("major_clothing")
 if garment_mask is not None:
  for cmask,crgb in clothing_major_regions(rgb,garment_mask,max_regions=5):
   pts=_contour_polygon(cmask,14)
   if pts:
    col="#%02x%02x%02x"%crgb;chunks.append(f'<polygon points="{pts}" fill="{col}"/>')
 # Reserve dominant source-derived color masses before sparse detail motifs.
 for role in ("hair","head","torso","major_clothing","left_arm","right_arm","lower_body"):
  if role not in masks:continue
  cap=3 if role in ("hair","torso","major_clothing","lower_body") else 2
  for mass,mrgb in major_color_masses(rgb,masks[role],max_masses=cap,min_ratio=.085):
   pts=_contour_polygon(mass,12)
   if pts: chunks.append(f'<polygon points="{pts}" fill="{f"rgb({mrgb[0]},{mrgb[1]},{mrgb[2]})"}"/>')
 # Sparse garment construction motifs: collar and sleeve attachments.
 if "torso" in masks:
  collar_authority=garment_mask if garment_mask is not None else masks["torso"]
  for collar in collar_shape_segments(rgb,collar_authority,masks.get("head",np.zeros_like(masks["torso"]))):
   pts=_contour_polygon(collar,10)
   if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,collar)}"/>')
  for sleeve in sleeve_boundary_motifs(masks["torso"],masks.get("left_arm"),masks.get("right_arm")):
   pts=_contour_polygon(sleeve,10)
   if pts: chunks.append(f'<polygon points="{pts}" fill="{_median(rgb,sleeve)}"/>')
 # Compose region evidence across semantic-part boundaries. Semantic masks remain authority.
 active={r:masks[r] for r in ("lower_body","torso","left_arm","right_arm","head","hair","accessory","major_clothing") if allocations.get(r,0)>0 and r in masks}
 # Edge-aware candidates compete under one perceptual budget; semantic masks remain authority.
 candidates={}
 for role in active:
  structural=list(propose_edge_regions(rgb,active[role],cell_size=8,max_regions=6))
  contrast=list(propose_contrast_subregions(rgb,active[role],max_regions=4))
  candidates[role]=tuple(structural+contrast)
 base={role:tuple(int(v) for v in np.median(np.asarray(rgb)[active[role]],axis=0)) for role in active if np.any(active[role])}
 selected=select_perceptual_regions(candidates,active,base,budget=12)
 for item in selected:
  draw_mask=_strengthened_accent_mask(item.region.mask,active[item.part]) if item.accent else item.region.mask
  pts=_contour_polygon(draw_mask,14)
  if not pts: continue
  col="#%02x%02x%02x"%item.region.rgb
  chunks.append(f'<polygon points="{pts}" fill="{col}"/>')
 chunks.append("</svg>");return "".join(chunks)
