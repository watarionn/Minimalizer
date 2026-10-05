from __future__ import annotations
from typing import Mapping
import numpy as np
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph

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

def render_graph_macro_svg(rgb:np.ndarray, masks:Mapping[str,np.ndarray], graph:StructuralLayoutGraph, allocations:Mapping[str,int])->str:
 h,w=np.asarray(rgb).shape[:2]; chunks=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="#fff"/>']
 # Central chain first. Geometry uses mask extents but graph anchors constrain joins.
 for role in ("lower_body","torso"):
  if allocations.get(role,0)<1 or role not in masks: continue
  b=_bbox(masks[role])
  if not b: continue
  x0,y0,x1,y1=b;cx=(x0+x1)/2;fill=_median(rgb,masks[role])
  top=_anchor(graph,role,"attachment-to-torso") if role=="lower_body" else None
  ty=top[1] if top else y0; half=(x1-x0)/2
  chunks.append(f'<polygon points="{cx-half*.72:.1f},{ty:.1f} {cx+half*.72:.1f},{ty:.1f} {x1:.1f},{y1:.1f} {x0:.1f},{y1:.1f}" fill="{fill}"/>')
 # Arms become attachment-to-extremity ribbons, not bbox rectangles.
 for role in ("left_arm","right_arm"):
  if allocations.get(role,0)<1 or role not in masks: continue
  b=_bbox(masks[role])
  if not b: continue
  x0,y0,x1,y1=b; c=((x0+x1)/2,(y0+y1)/2); attach=_anchor(graph,role,"attachment-to-torso") or c
  dx=c[0]-attach[0];dy=c[1]-attach[1];L=max((dx*dx+dy*dy)**.5,1); nx=-dy/L;ny=dx/L;th=max(3,min(x1-x0,y1-y0)*.35); ex=(c[0]+dx*.35,c[1]+dy*.35)
  pts=[(attach[0]+nx*th,attach[1]+ny*th),(attach[0]-nx*th,attach[1]-ny*th),(ex[0]-nx*th,ex[1]-ny*th),(ex[0]+nx*th,ex[1]+ny*th)]
  chunks.append('<polygon points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+f'" fill="{_median(rgb,masks[role])}"/>')
 # Head before hair. Hair is capped around the head neighborhood instead of using full hair bbox depth.
 if allocations.get("head",0)>0 and "head" in masks:
  b=_bbox(masks["head"])
  if b:
   x0,y0,x1,y1=b;chunks.append(f'<ellipse cx="{(x0+x1)/2:.1f}" cy="{(y0+y1)/2:.1f}" rx="{(x1-x0)/2:.1f}" ry="{(y1-y0)/2:.1f}" fill="{_median(rgb,masks["head"])}"/>')
 if allocations.get("hair",0)>0 and "hair" in masks and "head" in masks:
  hb=_bbox(masks["head"]); xb=_bbox(masks["hair"])
  if hb and xb:
   hx0,hy0,hx1,hy1=hb; x0=max(xb[0],hx0-(hx1-hx0)*.45);x1=min(xb[2],hx1+(hx1-hx0)*.45);y0=min(xb[1],hy0);y1=min(xb[3],hy1+(hy1-hy0)*.65);fill=_median(rgb,masks["hair"])
   chunks.append(f'<ellipse cx="{(x0+x1)/2:.1f}" cy="{(y0+y1)/2:.1f}" rx="{(x1-x0)/2:.1f}" ry="{(y1-y0)/2:.1f}" fill="{fill}"/>')
 # Accessory only when graph has an attachment relation; use its local bbox.
 if allocations.get("accessory",0)>0 and "accessory" in masks:
  rel=[r for r in graph.relations if r.source_part=="accessory_or_held_object" and r.relation_kind=="attached_to"]
  b=_bbox(masks["accessory"])
  if rel and b:
   x0,y0,x1,y1=b;chunks.append(f'<ellipse cx="{(x0+x1)/2:.1f}" cy="{(y0+y1)/2:.1f}" rx="{max(2,(x1-x0)/2):.1f}" ry="{max(2,(y1-y0)/2):.1f}" fill="{_median(rgb,masks["accessory"])}"/>')
 chunks.append("</svg>");return "".join(chunks)
