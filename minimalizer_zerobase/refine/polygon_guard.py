from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import math

Point=tuple[float,float]

@dataclass(frozen=True)
class PolygonGuardResult:
    valid: bool
    reason: str | None = None

def signed_area(points: Sequence[Point]) -> float:
    if len(points)<3: return 0.0
    return .5*sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]))

def _orient(a:Point,b:Point,c:Point)->float:
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def _intersects(a:Point,b:Point,c:Point,d:Point)->bool:
    return _orient(a,b,c)*_orient(a,b,d)<0 and _orient(c,d,a)*_orient(c,d,b)<0

def validate_polygon_candidate(reference: Sequence[Point], candidate: Sequence[Point], *, width:int,height:int,
                               max_vertex_shift:float=4.0,min_area_ratio:float=.90) -> PolygonGuardResult:
    ref=tuple((float(x),float(y)) for x,y in reference); cand=tuple((float(x),float(y)) for x,y in candidate)
    if len(ref)!=len(cand) or len(ref)<3: return PolygonGuardResult(False,"vertex count changed or polygon degenerate")
    if any(not(math.isfinite(x) and math.isfinite(y)) for x,y in cand): return PolygonGuardResult(False,"non-finite vertex")
    if any(x<0 or y<0 or x>width or y>height for x,y in cand): return PolygonGuardResult(False,"vertex left canvas")
    ar=signed_area(ref); ac=signed_area(cand)
    if ar==0 or ac==0 or ar*ac<=0: return PolygonGuardResult(False,"winding changed or area collapsed")
    if abs(ac)/abs(ar)<min_area_ratio: return PolygonGuardResult(False,"polygon area collapsed")
    if any(math.hypot(x-x0,y-y0)>max_vertex_shift for (x0,y0),(x,y) in zip(ref,cand)):
        return PolygonGuardResult(False,"vertex shift exceeded trust region")
    n=len(cand)
    for i in range(n):
        a,b=cand[i],cand[(i+1)%n]
        for j in range(i+1,n):
            if j in (i,(i+1)%n) or (j+1)%n in (i,(i+1)%n): continue
            if _intersects(a,b,cand[j],cand[(j+1)%n]):
                return PolygonGuardResult(False,"polygon self-intersection")
    return PolygonGuardResult(True)
