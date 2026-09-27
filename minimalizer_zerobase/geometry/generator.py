from __future__ import annotations
from dataclasses import dataclass, field
from math import pi
from minimalizer_zerobase.geometry.models import PrimitiveCandidate
from minimalizer_zerobase.scene.models import Region, Scene

DEFAULT_FAMILIES = ("rectangle","trapezoid","triangle","ellipse","capsule","convex_polygon")

@dataclass(frozen=True)
class PrimitiveFamilyPolicy:
    default_families: tuple[str,...] = DEFAULT_FAMILIES
    semantic_families: dict[str,tuple[str,...]] = field(default_factory=lambda:{
        "background":("rectangle",), "face":("ellipse","convex_polygon","rectangle"),
        "head":("ellipse","convex_polygon","rectangle"), "hair":("convex_polygon","trapezoid","ellipse"),
        "arm":("capsule","rectangle","trapezoid"), "leg":("capsule","rectangle","trapezoid"),
        "hand":("ellipse","capsule","rectangle"), "coat":("rectangle","trapezoid","convex_polygon"),
        "shirt":("rectangle","trapezoid","convex_polygon"), "identity_accent":("rectangle","triangle","ellipse"),
    })
    min_area: float = 1.0
    def families_for(self, role:str)->tuple[str,...]:
        return self.semantic_families.get(role,self.default_families)

class PrimitiveGenerator:
    producer="PrimitiveGenerator"; producer_version="1.0"
    def __init__(self, policy:PrimitiveFamilyPolicy|None=None):
        self.policy=policy or PrimitiveFamilyPolicy()
    def generate(self, scene:Scene)->tuple[PrimitiveCandidate,...]:
        out=[]
        for region in sorted(scene.regions,key=lambda r:r.region_id):
            box=self._bbox(region)
            if box[2]*box[3] < self.policy.min_area:
                continue
            for family in self.policy.families_for(region.semantic_role):
                out.append(self._candidate(region,family,box))
        return tuple(sorted(out,key=lambda c:(c.source_region_id,c.primitive_type,c.candidate_id)))

    def _candidate(self, region:Region, family:str, box:list[float])->PrimitiveCandidate:
        x,y,w,h=box
        params={"bbox":[x,y,w,h]}
        vertices=4; area_ratio=1.0; angularity=1.0
        if family=="ellipse":
            params.update({"cx":x+w/2,"cy":y+h/2,"rx":w/2,"ry":h/2})
            vertices=0; area_ratio=pi/4; angularity=0.0
        elif family=="capsule":
            params.update({"axis":"vertical" if h>=w else "horizontal","radius":min(w,h)/2})
            vertices=0; area_ratio=min(1.0,pi/4+abs(w-h)*min(w,h)/(w*h)); angularity=0.0
        elif family=="triangle":
            params["points"]=[[x+w/2,y],[x+w,y+h],[x,y+h]]
            vertices=3; area_ratio=.5
        elif family=="trapezoid":
            inset=.12*w
            params["points"]=[[x+inset,y],[x+w-inset,y],[x+w,y+h],[x,y+h]]
            vertices=4; area_ratio=.88
        elif family=="convex_polygon":
            params["points"]=[[x+w*.2,y],[x+w*.8,y],[x+w,y+h*.35],
                              [x+w*.82,y+h],[x+w*.18,y+h],[x,y+h*.35]]
            vertices=6; area_ratio=.86; angularity=.85
        elif family!="rectangle":
            raise ValueError(f"unsupported primitive family: {family}")
        metrics={"coverage":round(area_ratio,6),
                 "silhouette":round(1-abs(1-area_ratio),6),
                 "complexity":float(vertices),
                 "vertex_count":float(vertices),
                 "angularity":round(angularity,6)}
        constraints=(f"semantic:{region.semantic_role}",f"family:{family}")
        return PrimitiveCandidate(f"{region.region_id}:{family}",family,region.region_id,
                                  params,metrics,constraints)

    @staticmethod
    def _bbox(region:Region)->list[float]:
        box=region.geometry.get("bbox")
        if not isinstance(box,(list,tuple)) or len(box)!=4:
            raise ValueError("primitive generation requires geometry.bbox")
        x,y,w,h=(float(v) for v in box)
        if w<0 or h<0:
            raise ValueError("bbox width and height must be non-negative")
        return [x,y,w,h]
