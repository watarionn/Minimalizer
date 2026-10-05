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
    edge_u8=cv2.Canny(image,55,145)
    contours,hierarchy=cv2.findContours(edge_u8,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    labels=np.zeros(head.shape,np.int32);comps=[];next_label=1
    if hierarchy is not None:
        for idx,contour in enumerate(contours):
            # A contour with a child encloses a bounded structure; open hair strokes do not.
            child=int(hierarchy[0][idx][2])
            if child<0: continue
            x,y,w,h=cv2.boundingRect(contour);area=abs(float(cv2.contourArea(contour)))
            if area<max(8,fw*fh*.004) or area>fw*fh*.34: continue
            if w<max(5,int(.12*fw)) or h<max(4,int(.07*fh)) or w>.85*fw or h>.55*fh: continue
            comp=np.zeros(head.shape,np.uint8);cv2.drawContours(comp,[contour],-1,1,-1);comp=comp.astype(bool)&authority
            if int(comp.sum())<8: continue
            cy=y+.5*h;cx=x+.5*w
            # The contour center must stay in the upper-face worn zone, not deep inside facial features.
            if cy>fy+.34*fh: continue
            perimeter=max(1.0,float(cv2.arcLength(contour,True)))
            closure=min(1.0,4*np.pi*max(area,1.0)/(perimeter*perimeter))
            labels[comp]=next_label
            comps.append((next_label,int(comp.sum()),float(cx),float(cy),w,h,closure));next_label+=1
    edges=(edge_u8>0)&authority

    # Prefer a horizontally separated pair with similar vertical placement and scale.
    best=None
    for i,a in enumerate(comps):
        for b in comps[i+1:]:
            left,right=(a,b) if a[2]<=b[2] else (b,a)
            sep=(right[2]-left[2])/max(fw,1);dy=abs(right[3]-left[3])/max(fh,1)
            ar=min(left[1],right[1])/max(left[1],right[1])
            if not (.20<=sep<=1.05 and dy<=.30 and ar>=.18): continue
            score=1.8*ar+max(0,1-dy)+min(1,sep)+.5*(left[6]+right[6])
            if best is None or score>best[0]: best=(score,left,right)

    if best is None:
        return EyewearStructuralEvidence(empty,empty,edges,empty,min(.45,float(edges.sum())/max(1,int(authority.sum()))),False)

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
    if y1>y0:
        cy=(y0+y1)//2;th=max(1,radius)
        xa=min(lx1,rx0);xb=max(lx1,rx0)
        bridge[max(0,cy-th):min(face.shape[0],cy+th+1),xa:xb+1]=True
        bridge&=authority

    ring_support=.5*(left[6]+right[6])
    source_support=min(1.0,ring_support*2.0)
    symmetry=min(left[1],right[1])/max(left[1],right[1])
    confidence=min(1.0,.52+.20*symmetry+.18*source_support+.10*min(1,(right[2]-left[2])/max(fw,1)))
    return EyewearStructuralEvidence(ll,rr,frame,bridge,confidence,True)
