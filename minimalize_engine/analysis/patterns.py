from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from ..models import Region,Shape

@dataclass
class PatternGroup:
    id:int; region_ids:list[int]; orientation:str; spacing:float; palette_id:int

def detect_patterns(regions,image_shape,min_count=3,alignment_tolerance=.10):
    h,w=image_shape[:2]; candidates=[r for r in regions if r.area_ratio<=.006 and (r.is_accent or r.semantic_type in {"accent","elongated"})]
    by={}
    for r in candidates: by.setdefault(r.palette_id,[]).append(r)
    groups=[]; gid=1
    for pid,items in by.items():
        if len(items)<min_count: continue
        med=float(np.median([r.area for r in items])); items=[r for r in items if .35*med<=r.area<=2.8*med]
        if len(items)<min_count: continue
        xs=np.array([r.centroid[0] for r in items]); ys=np.array([r.centroid[1] for r in items])
        if np.ptp(xs)/max(w,1)<=alignment_tolerance and np.ptp(ys)/max(h,1)>alignment_tolerance:
            ori="vertical"; ordered=sorted(items,key=lambda r:r.centroid[1]); vals=[r.centroid[1] for r in ordered]
        elif np.ptp(ys)/max(h,1)<=alignment_tolerance and np.ptp(xs)/max(w,1)>alignment_tolerance:
            ori="horizontal"; ordered=sorted(items,key=lambda r:r.centroid[0]); vals=[r.centroid[0] for r in ordered]
        else: continue
        spacing=float(np.median(np.diff(vals))) if len(vals)>1 else 0
        g=PatternGroup(gid,[r.id for r in ordered],ori,spacing,pid)
        for r in ordered:r.pattern_group=gid
        groups.append(g); gid+=1
    return groups

def regularize_pattern_shapes(shapes,patterns):
    by={s.source_region_id:s for s in shapes if s.source_region_id is not None}
    for g in patterns:
        members=[by[i] for i in g.region_ids if i in by]
        if len(members)<3:continue
        def center(s):
            if s.shape_type in {"circle","ellipse"}:return s.cx,s.cy
            if s.shape_type=="rectangle":return s.x+s.width/2,s.y+s.height/2
            return sum(x for x,_ in s.points)/len(s.points),sum(y for _,y in s.points)/len(s.points)
        if g.orientation=="vertical":
            members.sort(key=lambda s:center(s)[1]); x=float(np.median([center(s)[0] for s in members])); vals=[center(s)[1] for s in members]
            sp=float(np.median(np.diff(vals))); targets=[(x,min(vals)+i*sp) for i in range(len(members))]
        else:
            members.sort(key=lambda s:center(s)[0]); y=float(np.median([center(s)[1] for s in members])); vals=[center(s)[0] for s in members]
            sp=float(np.median(np.diff(vals))); targets=[(min(vals)+i*sp,y) for i in range(len(members))]
        for s,(tx,ty) in zip(members,targets):
            cx,cy=center(s); dx,dy=tx-cx,ty-cy
            if s.shape_type in {"circle","ellipse"}: s.cx,s.cy=float(tx),float(ty)
            elif s.shape_type=="rectangle": s.x+=dx;s.y+=dy
            else:s.points=[(x+dx,y+dy) for x,y in s.points]
            s.pattern_group=g.id
    return shapes
