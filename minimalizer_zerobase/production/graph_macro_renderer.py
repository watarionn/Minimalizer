from __future__ import annotations
from typing import Mapping
import numpy as np
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph
from minimalizer_zerobase.production.semantic_contour import semantic_contour
from minimalizer_zerobase.production.part_color_regions import extract_part_color_regions
from minimalizer_zerobase.production.cross_part_region_graph import build_cross_part_region_graph, composed_regions
from minimalizer_zerobase.production.semantic_edge_regions import propose_edge_regions, propose_contrast_subregions
from minimalizer_zerobase.production.perceptual_region_budget import select_perceptual_regions
from minimalizer_zerobase.production.structural_motifs import arm_axis_band, clothing_major_regions, two_segment_arm_masks, clothing_authority, collar_motif, sleeve_boundary_motifs, sleeve_forearm_masses, collar_shape_segments, major_color_masses, garment_panels, global_mass_regions, reserve_identity_accents, silhouette_mass

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
