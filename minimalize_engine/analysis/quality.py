from dataclasses import dataclass,asdict
import cv2,numpy as np
from ..models import Scene
from ..io.image_exporter import render_scene
@dataclass
class QualityReport:
    score:float; minimality_score:float; identity_score:float; palette_score:float; complexity_score:float; balance_score:float
    shape_count:int; vertex_count:int; tiny_shape_ratio:float; color_count:int; edge_similarity:float; silhouette_similarity:float
    def to_dict(self):return asdict(self)
def _area(s):
    if s.shape_type=="rectangle":return max(0,(s.width or 0)*(s.height or 0))
    if s.shape_type=="circle":return np.pi*(s.rx or 0)**2
    if s.shape_type=="ellipse":return np.pi*(s.rx or 0)*(s.ry or 0)
    if s.shape_type=="polygon" and len(s.points)>=3:
        return abs(sum(s.points[i][0]*s.points[(i+1)%len(s.points)][1]-s.points[(i+1)%len(s.points)][0]*s.points[i][1] for i in range(len(s.points))))/2
    return 0
def _verts(s):return len(s.points) if s.shape_type=="polygon" else 2 if s.shape_type=="line" else 4
def _edge(source,scene):
    out=np.asarray(render_scene(scene,1).convert("RGB")); h,w=source.shape[:2]
    if out.shape[:2]!=(h,w):out=cv2.resize(out,(w,h))
    a=cv2.dilate(cv2.Canny(cv2.cvtColor(source,cv2.COLOR_RGB2GRAY),70,160),np.ones((5,5),np.uint8),1)>0
    b=cv2.dilate(cv2.Canny(cv2.cvtColor(out,cv2.COLOR_RGB2GRAY),70,160),np.ones((5,5),np.uint8),1)>0
    u=np.count_nonzero(a|b);return 1.0 if u==0 else np.count_nonzero(a&b)/u
def _sil(scene,mask):
    if mask is None:return 1.0
    a=np.asarray(render_scene(scene,1).convert("RGBA"))[:,:,3]>16;b=mask>0
    if a.shape!=b.shape:b=cv2.resize(b.astype(np.uint8),(a.shape[1],a.shape[0]),interpolation=cv2.INTER_NEAREST)>0
    u=np.count_nonzero(a|b);return 1.0 if u==0 else np.count_nonzero(a&b)/u
def evaluate_scene(scene,source_rgb,target_max_shapes,target_tiny_ratio=.34,target_vertex_per_shape=9,subject_mask=None):
    area=max(1,scene.width*scene.height); draw=[s for s in scene.shapes if s.shape_type!="line"]; areas=[_area(s) for s in draw]
    tiny=sum(1 for a in areas if a/area<.0012)/max(1,len(draw)); sc=len(scene.shapes); vc=sum(_verts(s) for s in scene.shapes)
    colors=len({tuple(s.fill_color) for s in scene.shapes if s.fill_color is not None})
    minimal=float(np.clip(1.05-(sc/max(1,target_max_shapes))*.45-tiny*.35,0,1))
    complexity=float(np.clip(1-max(0,vc/max(1,sc)-target_vertex_per_shape)/12,0,1))
    palette=float(np.clip(1-max(0,colors-8)/12,0,1)); edge=_edge(source_rgb,scene); sil=_sil(scene,subject_mask)
    identity=float(np.clip(np.clip(edge/.32,0,1)*.62+sil*.38,0,1))
    sk=scene.metadata.get("composition_skeleton",{})
    if sk.get("mode")=="central_corridor" and sk.get("active"):
        l,r=float(sk.get("left_mass_score",0)),float(sk.get("right_mass_score",0)); balance=min(l,r)/max(l,r) if max(l,r)>0 else .5
    else:balance=.78
    score=float(np.clip(minimal*.24+identity*.30+palette*.12+complexity*.18+balance*.16,0,1))
    return QualityReport(score,minimal,identity,palette,complexity,balance,sc,vc,float(tiny),colors,float(edge),float(sil))
