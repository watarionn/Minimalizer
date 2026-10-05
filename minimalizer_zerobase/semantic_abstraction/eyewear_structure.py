from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(frozen=True)
class EyewearStructuralEvidence:
    left_lens: np.ndarray
    right_lens: np.ndarray
    frame: np.ndarray
    bridge: np.ndarray
    confidence: float
    paired: bool

    @property
    def mask(self)->np.ndarray:
        return self.left_lens|self.right_lens|self.frame|self.bridge

    def to_dict(self)->dict:
        def box(mask):
            y,x=np.where(mask)
            return None if not len(x) else [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
        return {
            "paired":self.paired,"confidence":round(float(self.confidence),6),
            "left_lens_bbox":box(self.left_lens),"right_lens_bbox":box(self.right_lens),
            "frame_bbox":box(self.frame),"bridge_bbox":box(self.bridge),
            "pixel_count":int(self.mask.sum()),
        }


def _empty(shape): return np.zeros(shape,bool)


def _ring(mask:np.ndarray,radius:int)->np.ndarray:
    k=max(3,2*int(radius)+1)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))
    outer=cv2.dilate(mask.astype(np.uint8),kernel)>0
    inner=cv2.erode(mask.astype(np.uint8),kernel)>0
    return outer&~inner


def observe_eyewear_structure(
    rgb:np.ndarray,
    head_mask:np.ndarray,
    hair_mask:np.ndarray,
    face_mask:np.ndarray,
)->EyewearStructuralEvidence:
    """Observe upper-face worn structure. Evidence only; never semantic authority."""
    image=np.asarray(rgb,dtype=np.uint8)
    head=np.asarray(head_mask).astype(bool);hair=np.asarray(hair_mask).astype(bool);face=np.asarray(face_mask).astype(bool)
    if image.ndim!=3 or image.shape[:2]!=head.shape or hair.shape!=head.shape or face.shape!=head.shape:
        raise ValueError("eyewear observer shape mismatch")
    empty=_empty(head.shape)
    if not np.any(face):
        return EyewearStructuralEvidence(empty,empty,empty,empty,0.0,False)

    fx,fy,fw,fh=cv2.boundingRect(face.astype(np.uint8))
    yy,xx=np.indices(face.shape)
    authority=head|hair
    # Eyewear worn on the forehead/upper face can cross the face boundary, but not roam the full head.
    zone=(yy>=max(0,fy-int(.75*fh)))&(yy<=fy+int(.34*fh))&(xx>=max(0,fx-int(.55*fw)))&(xx<=min(head.shape[1]-1,fx+int(1.55*fw)))
    authority&=zone
    if not np.any(authority):
        return EyewearStructuralEvidence(empty,empty,empty,empty,0.0,False)

    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY).astype(np.float32)
    blur=cv2.GaussianBlur(gray,(0,0),2.2)
    contrast=np.abs(gray-blur)
    edges=cv2.Canny(image,55,145)>0

    # Candidate support is structural contrast near the upper face, excluding the central eye/mouth interior.
    central_face=face&(yy>=fy+int(.05*fh))&(yy<=fy+int(.72*fh))
    support=authority&~central_face&((contrast>=10)|(edges))
    support=cv2.morphologyEx(support.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))>0
    # A bridge may connect both lenses; split support into face-side hypotheses before pairing.
    face_mid=fx+.5*fw
    side_masks=(support&(xx<face_mid),support&(xx>=face_mid))

    labels=np.zeros(support.shape,np.int32);comps=[];next_label=1
    for side in side_masks:
        count,local_labels,stats,cent=cv2.connectedComponentsWithStats(side.astype(np.uint8),8)
        for label in range(1,count):
            area=int(stats[label,cv2.CC_STAT_AREA]);x=int(stats[label,cv2.CC_STAT_LEFT]);y=int(stats[label,cv2.CC_STAT_TOP])
            w=int(stats[label,cv2.CC_STAT_WIDTH]);h=int(stats[label,cv2.CC_STAT_HEIGHT])
            if area<max(5,int(fw*fh*.0015)) or w<max(4,int(.10*fw)) or h<3: continue
            if w>.95*fw or h>.65*fh: continue
            cx,cy=cent[label]
            labels[local_labels==label]=next_label
            comps.append((next_label,area,float(cx),float(cy),w,h));next_label+=1

    # Prefer a horizontally separated pair with similar vertical placement and scale.
    best=None
    for i,a in enumerate(comps):
        for b in comps[i+1:]:
            left,right=(a,b) if a[2]<=b[2] else (b,a)
            sep=(right[2]-left[2])/max(fw,1);dy=abs(right[3]-left[3])/max(fh,1)
            ar=min(left[1],right[1])/max(left[1],right[1])
            if not (.20<=sep<=1.05 and dy<=.30 and ar>=.18): continue
            score=1.8*ar+max(0,1-dy)+min(1,sep)
            if best is None or score>best[0]: best=(score,left,right)

    if best is None:
        return EyewearStructuralEvidence(empty,empty,support,empty,min(.45,float(support.sum())/max(1,int(authority.sum()))),False)

    _,left,right=best
    lm=labels==left[0];rm=labels==right[0]
    # Lens surfaces are bounded hulls inferred from source-supported paired structure, then clipped to authority.
    def lens(component):
        y,x=np.where(component); hull=np.zeros_like(component,np.uint8)
        pts=np.column_stack((x,y)).astype(np.int32)
        if len(pts)>=3: cv2.fillConvexPoly(hull,cv2.convexHull(pts),1)
        else: hull[component]=1
        return hull.astype(bool)&authority
    ll=lens(lm);rr=lens(rm)
    radius=max(1,int(round(min(fw,fh)*.025)))
    frame=(_ring(ll,radius)|_ring(rr,radius)|lm|rm)&authority

    lbox=cv2.boundingRect(ll.astype(np.uint8));rbox=cv2.boundingRect(rr.astype(np.uint8))
    lx1=lbox[0]+lbox[2];rx0=rbox[0]
    y0=max(lbox[1],rbox[1]);y1=min(lbox[1]+lbox[3],rbox[1]+rbox[3])
    bridge=np.zeros_like(face)
    if rx0>lx1 and y1>y0:
        cy=(y0+y1)//2;th=max(1,radius)
        bridge[max(0,cy-th):min(face.shape[0],cy+th+1),lx1:rx0+1]=True
        bridge&=authority

    source_support=float(((lm|rm)&(contrast>=10)).sum()/max(1,int((lm|rm).sum())))
    symmetry=min(left[1],right[1])/max(left[1],right[1])
    confidence=min(1.0,.52+.20*symmetry+.18*source_support+.10*min(1,(right[2]-left[2])/max(fw,1)))
    return EyewearStructuralEvidence(ll,rr,frame,bridge,confidence,True)
