from __future__ import annotations

from dataclasses import dataclass, field
import copy
from typing import Literal
import math

import cv2
import numpy as np

from ..models import Region, Shape
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType, PART_DEFAULT_ABSTRACTION
from .heuristics import mask_bbox, mask_centroid


PropType = Literal[
    "staff_like",
    "sword_like",
    "microphone_like",
    "headphone_like",
    "hat_like",
    "bag_like",
    "unknown",
]


@dataclass
class PropDescriptor:
    id: int
    prop_type: PropType
    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    confidence: float
    orientation_deg: float = 0.0
    axis_start: tuple[float, float] | None = None
    axis_end: tuple[float, float] | None = None
    source_region_ids: list[int] = field(default_factory=list)
    side: str = "unknown"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prop_type": self.prop_type,
            "bbox": list(self.bbox),
            "centroid": list(self.centroid),
            "confidence": self.confidence,
            "orientation_deg": self.orientation_deg,
            "axis_start": list(self.axis_start) if self.axis_start else None,
            "axis_end": list(self.axis_end) if self.axis_end else None,
            "source_region_ids": list(self.source_region_ids),
            "side": self.side,
            "metadata": self.metadata,
        }


def _bbox_from_points(a, b, pad=2):
    x0=min(a[0],b[0])-pad
    y0=min(a[1],b[1])-pad
    x1=max(a[0],b[0])+pad
    y1=max(a[1],b[1])+pad
    return (int(round(x0)),int(round(y0)),max(1,int(round(x1-x0))),max(1,int(round(y1-y0))))


def _line_angle(a,b)->float:
    return float(math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])))


def _line_length(a,b)->float:
    return float(math.hypot(b[0]-a[0],b[1]-a[1]))


def _side(cx:float,axis:float,tol:float)->str:
    if cx<axis-tol:return "left"
    if cx>axis+tol:return "right"
    return "center"


def _mask_from_line(shape,a,b,thickness):
    mask=np.zeros(shape[:2],dtype=np.uint8)
    cv2.line(
        mask,
        (int(round(a[0])),int(round(a[1]))),
        (int(round(b[0])),int(round(b[1]))),
        255,
        max(1,int(round(thickness))),
        cv2.LINE_AA,
    )
    return mask


def _region_ids_for_mask(regions:list[Region],mask:np.ndarray,min_overlap:float=.16)->list[int]:
    target=mask>0
    out=[]
    for r in regions:
        rm=r.mask>0
        denom=max(1,int(np.count_nonzero(rm)))
        overlap=np.count_nonzero(rm & target)/denom
        if overlap>=min_overlap:
            out.append(r.id)
    return out


def _is_skin_rgb(rgb:tuple[int,int,int])->bool:
    r,g,b=rgb
    if r<135 or g<70 or b<55:return False
    return r>=g-10 and r>=b+7 and (r-min(g,b))<=135


def _non_skin_dark_mask(image_rgb,zone_mask):
    gray=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2GRAY)
    hsv=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2HSV)
    sat=hsv[:,:,1]
    value=hsv[:,:,2]
    # Dark or moderately saturated non-skin visual masses.
    skin=np.zeros(zone_mask.shape,dtype=np.uint8)
    # vectorized broad skin rule
    r=image_rgb[:,:,0].astype(np.int16)
    g=image_rgb[:,:,1].astype(np.int16)
    b=image_rgb[:,:,2].astype(np.int16)
    skin_bool=(r>=140)&(g>=75)&(b>=60)&(r>=g-10)&(r>=b+7)
    candidate=((gray<=95)|((sat>=70)&(value<=185))) & (zone_mask>0) & (~skin_bool)
    return candidate.astype(np.uint8)*255


def _known_body_mask(structure:CharacterStructure,exclude_props=True)->np.ndarray:
    out=np.zeros_like(structure.subject_mask,dtype=np.uint8)
    include={
        CharacterPartType.FACE,
        CharacterPartType.HAIR,
        CharacterPartType.TORSO,
        CharacterPartType.OUTFIT,
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    }
    for p in structure.parts:
        if p.part_type in include:
            out=cv2.bitwise_or(out,p.mask)
    return out


def _detect_long_linear_prop(
    image_rgb:np.ndarray,
    structure:CharacterStructure,
)->list[PropDescriptor]:
    """
    Detect staff/sword-like objects from long straight edge support.

    This is intentionally conservative: lines buried in the central body or
    mostly explained by hair/legs are rejected.
    """
    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    axis=float(structure.metadata.get("body_axis_x",sx+sw/2))
    gray=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,45,125)

    # Only consider the alpha subject vicinity.
    subject=cv2.dilate(
        (structure.subject_mask>0).astype(np.uint8)*255,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)),
    )
    edges=cv2.bitwise_and(edges,subject)

    min_len=max(18,int(round(sh*.22)))
    lines=cv2.HoughLinesP(
        edges,
        1,
        np.pi/180,
        threshold=max(18,int(round(min_len*.42))),
        minLineLength=min_len,
        maxLineGap=max(4,int(round(sh*.025))),
    )
    if lines is None:
        return []

    hair=structure.first_part(CharacterPartType.HAIR)
    torso=structure.first_part(CharacterPartType.TORSO)
    outfit=structure.first_part(CharacterPartType.OUTFIT)
    legs=[]
    for t in [CharacterPartType.LEFT_LEG,CharacterPartType.RIGHT_LEG]:
        p=structure.first_part(t)
        if p is not None:legs.append(p)

    exclusion=np.zeros((h,w),dtype=np.uint8)
    exclude_parts=([hair] if hair else [])+([outfit] if outfit else [])+legs
    for p in exclude_parts:
        exclusion=cv2.bitwise_or(exclusion,p.mask)

    candidates=[]
    for row in lines[:,0,:]:
        x1,y1,x2,y2=[float(v) for v in row]
        a=(x1,y1);b=(x2,y2)
        length=_line_length(a,b)
        if length<sh*.22:
            continue

        mid=((x1+x2)/2,(y1+y2)/2)
        lateral=abs(mid[0]-axis)/max(sw/2,1)
        # Central clothing seams, hair edges and leg seams should not become
        # weapons. In the AI-free detector we deliberately prefer precision:
        # long linear props must clearly leave the body's central silhouette.
        if lateral < .55:
            continue
        if mid[1] > sy + sh*.68 and length < sh*.55:
            continue

        sample_mask=_mask_from_line((h,w),a,b,max(2,sw*.009))
        support=np.count_nonzero((sample_mask>0)&(structure.subject_mask>0))/max(1,np.count_nonzero(sample_mask))
        excluded=np.count_nonzero((sample_mask>0)&(exclusion>0))/max(1,np.count_nonzero(sample_mask))
        if support<.22 or excluded>.50:
            continue

        # Torso-only lines are almost always costume structure.
        torso_overlap=0
        if torso is not None:
            torso_overlap=np.count_nonzero((sample_mask>0)&(torso.mask>0))/max(1,np.count_nonzero(sample_mask))
        if torso_overlap>.55:
            continue

        angle=_line_angle(a,b)
        score=.40+min(.32,length/max(sh,1)*.48)+min(.18,lateral*.15)+min(.10,support*.12)
        steep = abs(math.sin(math.radians(angle))) >= .58
        if (lateral >= .68 and steep) or length >= sh * .50:
            ptype:"PropType"="staff_like"
            score+=.10
        else:
            ptype="sword_like"

        candidates.append((score,length,ptype,a,b,sample_mask,lateral))

    # De-duplicate near-parallel lines from the two edges of one staff/blade.
    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
    out=[]
    for score,length,ptype,a,b,mask,lateral in candidates:
        angle=_line_angle(a,b)
        cx=(a[0]+b[0])/2
        cy=(a[1]+b[1])/2
        duplicate=False
        for d in out:
            if abs(((angle-d.orientation_deg+90)%180)-90)<10:
                dc=math.hypot(cx-d.centroid[0],cy-d.centroid[1])
                if dc<max(8,sw*.08):
                    duplicate=True
                    break
        if duplicate:
            continue

        # Thicken to approximate the actual prop body.
        thickness=max(2,sw*.012 if ptype=="staff_like" else sw*.018)
        pmask=_mask_from_line((h,w),a,b,thickness)
        bbox=mask_bbox(pmask)
        centroid=mask_centroid(pmask)
        out.append(
            PropDescriptor(
                id=len(out),
                prop_type=ptype,
                mask=pmask,
                bbox=bbox,
                centroid=centroid,
                confidence=float(np.clip(score,0,1)),
                orientation_deg=angle,
                axis_start=a,
                axis_end=b,
                side=_side(centroid[0],axis,sw*.05),
                metadata={"detector":"hough_line","length_ratio":length/max(sh,1),"lateral":lateral},
            )
        )
        if len(out)>=2:
            break
    return out



def _detect_short_hand_prop(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
) -> list[PropDescriptor]:
    """
    Conservative fallback for a short brush/wand/tool held near a raised hand.

    Unlike staff detection, this requires direct proximity to an arm and stays
    in the upper half of the subject to avoid skirt straps and shoe edges.
    """
    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    axis=float(structure.metadata.get("body_axis_x",sx+sw/2))
    arms=[
        p for p in [
            structure.first_part(CharacterPartType.LEFT_ARM),
            structure.first_part(CharacterPartType.RIGHT_ARM),
        ] if p is not None
    ]
    if not arms:
        return []

    gray=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,45,125)
    subject=cv2.dilate(
        (structure.subject_mask>0).astype(np.uint8)*255,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)),
    )
    edges=cv2.bitwise_and(edges,subject)

    min_len=max(8,int(round(sh*.09)))
    lines=cv2.HoughLinesP(
        edges,1,np.pi/180,
        threshold=max(10,int(round(min_len*.55))),
        minLineLength=min_len,
        maxLineGap=max(3,int(round(sh*.015))),
    )
    if lines is None:
        return []

    hair=structure.first_part(CharacterPartType.HAIR)
    outfit=structure.first_part(CharacterPartType.OUTFIT)
    exclusion=np.zeros((h,w),dtype=np.uint8)
    for part in [hair,outfit]:
        if part is not None:
            exclusion=cv2.bitwise_or(exclusion,part.mask)

    ranked=[]
    for row in lines[:,0,:]:
        x1,y1,x2,y2=[float(v) for v in row]
        a=(x1,y1);b=(x2,y2)
        length=_line_length(a,b)
        lr=length/max(sh,1)
        if not (.09<=lr<=.30):
            continue
        mid=((x1+x2)/2,(y1+y2)/2)
        if mid[1]>sy+sh*.48:
            continue

        lateral=abs(mid[0]-axis)/max(sw/2,1)
        if lateral<.18:
            continue

        # At least one endpoint must be close to a detected arm.
        endpoint_dist=min(
            math.hypot(px-arm.centroid[0],py-arm.centroid[1])
            for px,py in [a,b]
            for arm in arms
        )/max(sw,1)
        if endpoint_dist>.28:
            continue

        line_mask=_mask_from_line((h,w),a,b,max(2,sw*.010))
        excluded=np.count_nonzero((line_mask>0)&(exclusion>0))/max(1,np.count_nonzero(line_mask))
        if excluded>.38:
            continue

        angle=_line_angle(a,b)
        score=.50+.16*(1-min(1,endpoint_dist/.28))+.10*min(1,lateral)+.10*min(1,lr/.22)
        ranked.append((score,length,a,b,line_mask,angle,lateral,endpoint_dist))

    if not ranked:
        return []
    ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
    score,length,a,b,mask,angle,lateral,endpoint_dist=ranked[0]
    centroid=mask_centroid(mask)
    return [
        PropDescriptor(
            id=90,
            prop_type="unknown",
            mask=mask,
            bbox=mask_bbox(mask),
            centroid=centroid,
            confidence=float(np.clip(score,0,1)),
            orientation_deg=angle,
            axis_start=a,
            axis_end=b,
            side=_side(centroid[0],axis,sw*.05),
            metadata={
                "detector":"short_handheld_line",
                "length_ratio":length/max(sh,1),
                "endpoint_arm_distance":endpoint_dist,
            },
        )
    ]

def _component_records(mask:np.ndarray,min_area:int,max_area:int):
    n,labels,stats,cent=cv2.connectedComponentsWithStats((mask>0).astype(np.uint8),8)
    out=[]
    for cid in range(1,n):
        area=int(stats[cid,cv2.CC_STAT_AREA])
        if area<min_area or area>max_area:continue
        x=int(stats[cid,cv2.CC_STAT_LEFT]);y=int(stats[cid,cv2.CC_STAT_TOP])
        w=int(stats[cid,cv2.CC_STAT_WIDTH]);h=int(stats[cid,cv2.CC_STAT_HEIGHT])
        m=(labels==cid).astype(np.uint8)*255
        fill=area/max(1,w*h)
        out.append((cid,area,(x,y,w,h),(float(cent[cid][0]),float(cent[cid][1])),fill,m))
    return out


def _detect_headphone_prop(image_rgb,structure)->list[PropDescriptor]:
    head=structure.first_part(CharacterPartType.HEAD)
    torso=structure.first_part(CharacterPartType.TORSO)
    if head is None or torso is None:
        return []

    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    hx,hy,hw,hh=head.bbox
    head_center=float(head.centroid[0])

    x0=max(0,int(round(head_center-hw*.72)))
    x1=min(w,int(round(head_center+hw*.72)))
    y0=max(0,int(round(hy+hh*.35)))
    y1=min(h,int(round(hy+hh*.90)))
    if x1-x0<12 or y1-y0<8:
        return []

    roi=image_rgb[y0:y1,x0:x1]
    gray=cv2.cvtColor(roi,cv2.COLOR_RGB2GRAY)
    gray=cv2.GaussianBlur(gray,(5,5),1.0)

    min_r=max(3,int(round(hw*.075)))
    max_r=max(min_r+1,int(round(hw*.22)))
    circles=cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.15,
        minDist=max(6,int(round(hw*.18))),
        param1=90,
        param2=max(8,int(round(hw*.08))),
        minRadius=min_r,
        maxRadius=max_r,
    )
    if circles is None:
        return []

    edge=cv2.Canny(gray,45,120)
    candidates=[]
    for cx,cy,r in circles[0]:
        gx=float(cx+x0);gy=float(cy+y0);r=float(r)
        yy,xx=np.ogrid[:gray.shape[0],:gray.shape[1]]
        d2=(xx-cx)**2+(yy-cy)**2
        ring=(d2>=(r*.72)**2)&(d2<=(r*1.15)**2)
        disk=d2<=r*r
        if not np.any(ring) or not np.any(disk):
            continue
        ring_edge=float(edge[ring].mean()/255.0)
        darkness=float(1.0-gray[disk].mean()/255.0)
        hsv_roi=cv2.cvtColor(roi,cv2.COLOR_RGB2HSV)
        sat_med=float(np.median(hsv_roi[:,:,1][disk]))
        val_med=float(np.median(hsv_roi[:,:,2][disk]))
        score=.68*ring_edge+.32*darkness
        candidates.append((score,gx,gy,r,sat_med,val_med))

    left=[c for c in candidates if c[1]<head_center]
    right=[c for c in candidates if c[1]>head_center]
    if not left or not right:
        return []

    face=structure.first_part(CharacterPartType.FACE)
    best=None;best_score=-1.0
    for l in left:
        for r in right:
            ls,lx,ly,lr,lsat,lval=l;rs,rx,ry,rr,rsat,rval=r
            sep=rx-lx
            if sep<hw*.25 or sep>hw*.82:
                continue
            if abs(ly-ry)>hh*.14:
                continue
            size_ratio=min(lr,rr)/max(lr,rr)
            if size_ratio<.50:
                continue
            if face is not None:
                fx,fy,fw,fh=face.bbox
                mean_y=(ly+ry)/2.0
                # Neck headphones sit around the lower face / jaw line. Pairs
                # much lower than this are usually symmetric jacket/chest arcs.
                if mean_y<fy+fh*.60 or mean_y>fy+fh*.69 or sep>fw*.82:
                    continue
            # Current non-AI headphone rule targets dark/neutral ear cups.
            # Bright hair curls and pale clothing arcs are frequent false pairs.
            if max(lsat,rsat)>38 or max(lval,rval)>150:
                continue
            pair_score=min(ls,rs)*.62+size_ratio*.20+(1-min(1,abs(ly-ry)/max(hh*.22,1)))*.18
            if pair_score>best_score:
                best_score=pair_score;best=(l,r)

    if best is None or best_score<.28:
        return []

    l,r=best
    _,lx,ly,lr,lsat,lval=l;_,rx,ry,rr,rsat,rval=r
    mask=np.zeros((h,w),dtype=np.uint8)
    cv2.circle(mask,(int(round(lx)),int(round(ly))),max(2,int(round(lr))),255,-1)
    cv2.circle(mask,(int(round(rx)),int(round(ry))),max(2,int(round(rr))),255,-1)
    confidence=float(np.clip(.48+best_score*.55,0,1))
    return [
        PropDescriptor(
            id=100,
            prop_type='headphone_like',
            mask=mask,
            bbox=mask_bbox(mask),
            centroid=mask_centroid(mask),
            confidence=confidence,
            orientation_deg=0.0,
            axis_start=(lx,ly),
            axis_end=(rx,ry),
            side='center',
            metadata={
                'detector':'paired_neck_circles',
                'left_center':[lx,ly],
                'right_center':[rx,ry],
                'left_bbox':[lx-lr,ly-lr,lr*2,lr*2],
                'right_bbox':[rx-rr,ry-rr,rr*2,rr*2],
                'pair_score':best_score,
                'left_sat_median':lsat,
                'right_sat_median':rsat,
                'left_value_median':lval,
                'right_value_median':rval,
            },
        )
    ]


def _detect_microphone_prop(image_rgb,structure)->list[PropDescriptor]:
    face=structure.first_part(CharacterPartType.FACE)
    torso=structure.first_part(CharacterPartType.TORSO)
    if face is None or torso is None:
        return []
    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    axis=float(structure.metadata.get("body_axis_x",sx+sw/2))
    fx,fy,fw,fh=face.bbox
    tx,ty,tw,th=torso.bbox

    y0=max(0,int(round(fy-fh*.12)))
    y1=min(h,int(round(fy+fh*.72)))
    x0=max(0,int(round(axis-sw*.42)))
    x1=min(w,int(round(axis+sw*.42)))
    zone=np.zeros((h,w),dtype=np.uint8);zone[y0:y1,x0:x1]=255

    hsv=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2HSV)
    sat=hsv[:,:,1];val=hsv[:,:,2]
    # Colorful microphone heads or metallic/dark compact heads.
    candidate=((sat>=95)&(val>=65)&(val<=250)&(zone>0)&(structure.subject_mask>0)).astype(np.uint8)*255
    candidate=cv2.morphologyEx(candidate,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))

    comps=_component_records(
        candidate,
        min_area=max(4,int(fw*fh*.003)),
        max_area=max(18,int(fw*fh*.12)),
    )

    arms=[
        p for p in [
            structure.first_part(CharacterPartType.LEFT_ARM),
            structure.first_part(CharacterPartType.RIGHT_ARM),
        ] if p is not None
    ]

    best=None;best_score=-1
    for _,area,bbox,cent,fill,m in comps:
        x,y,bw,bh=bbox
        aspect=bw/max(bh,1)
        if not (.45<=aspect<=2.2):continue
        if fill<.20:continue
        if min(bw,bh) < fw*.17 or max(bw,bh) > fw*.46:
            continue

        hpix = hsv[:, :, 0][m > 0]
        spix = hsv[:, :, 1][m > 0]
        vpix = hsv[:, :, 2][m > 0]
        if len(hpix) < 4:
            continue
        mean_hue=float(np.mean(hpix))
        mean_sat=float(np.mean(spix))
        mean_val=float(np.mean(vpix))
        # Phase-6 microphone detection is deliberately conservative. The
        # corpus microphone has a vivid magenta/red head; common hair ribbons,
        # sunglasses and shirt graphics otherwise produce too many false hits.
        color_ok = (
            (145 <= mean_hue <= 179)
            or (mean_hue <= 8 and mean_val >= 150)
        )
        if not color_ok or mean_sat < 108:
            continue

        # The head of a handheld microphone usually sits beside the face.
        # Lower torso accents are a common false positive and are excluded.
        if cent[1] < fy - fh*.08 or cent[1] > fy + fh*.70:
            continue

        arm_dist=1.0
        if arms:
            arm_dist=min(
                math.hypot(cent[0]-a.centroid[0],cent[1]-a.centroid[1])
                for a in arms
            )/max(sw,1)
        face_dist=math.hypot(cent[0]-(fx+fw/2),cent[1]-(fy+fh/2))/max(sw,1)
        if arm_dist>.42 and face_dist>.34:
            continue
        expected_y=fy+fh*.24
        y_prior=1-min(1,abs(cent[1]-expected_y)/max(fh*.46,1))
        score=.42+.20*min(1,fill)+.14*(1-min(1,arm_dist/.42))+.10*(1-min(1,face_dist/.34))+.22*y_prior
        if score>best_score:
            best_score=score;best=(bbox,cent,m,arm_dist,face_dist)

    if best is None:return []
    bbox,cent,head_mask,arm_dist,face_dist=best

    # Infer a short stem extending down toward the nearest arm / torso.
    if arms:
        target=min(arms,key=lambda a:math.hypot(cent[0]-a.centroid[0],cent[1]-a.centroid[1])).centroid
    else:
        target=torso.centroid
    vx=target[0]-cent[0];vy=target[1]-cent[1]
    norm=max(1e-6,math.hypot(vx,vy))
    stem_len=max(fw*.22,min(fw*.62,norm*.55))
    end=(cent[0]+vx/norm*stem_len,cent[1]+vy/norm*stem_len)
    stem=_mask_from_line((h,w),cent,end,max(2,fw*.045))
    mask=cv2.bitwise_or(head_mask,stem)
    return [
        PropDescriptor(
            id=110,
            prop_type="microphone_like",
            mask=mask,
            bbox=mask_bbox(mask),
            centroid=mask_centroid(mask),
            confidence=float(np.clip(best_score,0,1)),
            orientation_deg=_line_angle(cent,end),
            axis_start=cent,
            axis_end=end,
            side=_side(cent[0],axis,sw*.05),
            metadata={"detector":"saturated_head_near_face","head_center":list(cent),"head_bbox":list(bbox)},
        )
    ]


def _detect_hat_prop(image_rgb,structure)->list[PropDescriptor]:
    head=structure.first_part(CharacterPartType.HEAD)
    if head is None:return []
    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    hx,hy,hw,hh=head.bbox
    axis=float(structure.metadata.get("body_axis_x",sx+sw/2))

    y0=max(0,int(round(hy-hh*.60)))
    y1=min(h,int(round(hy+hh*.25)))
    x0=max(0,int(round(hx-hw*.55)))
    x1=min(w,int(round(hx+hw*1.55)))
    zone=np.zeros((h,w),dtype=np.uint8);zone[y0:y1,x0:x1]=255
    m=cv2.bitwise_and(zone,structure.subject_mask)
    # Exclude central head so only protruding headwear remains.
    core=np.zeros_like(m)
    core[max(0,hy):min(h,hy+int(hh*.45)),max(0,hx):min(w,hx+hw)]=255
    protr=cv2.bitwise_and(m,cv2.bitwise_not(core))
    protr=cv2.morphologyEx(protr,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))

    comps=_component_records(
        protr,
        min_area=max(8,int(hw*hh*.018)),
        max_area=max(25,int(hw*hh*.55)),
    )
    if not comps:return []
    comps.sort(key=lambda r:r[1],reverse=True)
    _,area,bbox,cent,fill,mask=comps[0]
    x,y,bw,bh=bbox
    aspect=bw/max(bh,1)
    if bw<hw*.72 or bh>hh*.58 or aspect<1.35:
        return []
    if cent[1] > hy + hh*.18:
        return []

    crop=image_rgb[y:y+bh,x:x+bw]
    gray=cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY)
    edge=cv2.Canny(gray,45,120)
    lines=cv2.HoughLinesP(
        edge,1,np.pi/180,
        threshold=max(8,int(round(bw*.22))),
        minLineLength=max(6,int(round(bw*.28))),
        maxLineGap=3,
    )
    brim_support=0.0
    if lines is not None:
        for row in lines[:,0,:]:
            x1,y1,x2,y2=[float(v) for v in row]
            angle=abs(math.degrees(math.atan2(y2-y1,x2-x1)))
            angle=min(angle,180-angle)
            length=math.hypot(x2-x1,y2-y1)
            if angle<=18:
                brim_support=max(brim_support,length/max(bw,1))
    if brim_support < .34:
        return []

    confidence=.50+.18*min(1,bw/max(hw,1))+.10*fill+.08*min(1,brim_support)
    return [
        PropDescriptor(
            id=120,
            prop_type="hat_like",
            mask=mask,
            bbox=bbox,
            centroid=cent,
            confidence=float(np.clip(confidence,0,1)),
            orientation_deg=0.0,
            side=_side(cent[0],axis,sw*.05),
            metadata={"detector":"head_protrusion"},
        )
    ]


def _detect_bag_prop(image_rgb,structure)->list[PropDescriptor]:
    torso=structure.first_part(CharacterPartType.TORSO)
    if torso is None:return []
    h,w=image_rgb.shape[:2]
    sx,sy,sw,sh=structure.subject_bbox
    axis=float(structure.metadata.get("body_axis_x",sx+sw/2))
    tx,ty,tw,th=torso.bbox

    y0=max(0,int(round(ty+th*.45)))
    y1=min(h,int(round(sy+sh*.72)))
    x0=max(0,int(round(axis-sw*.36)))
    x1=min(w,int(round(axis+sw*.36)))
    zone=np.zeros((h,w),dtype=np.uint8);zone[y0:y1,x0:x1]=255
    valid=(zone>0)&(structure.subject_mask>0)
    gray=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2GRAY)
    vals=gray[valid]
    if len(vals)<20:
        return []
    dark_threshold=int(np.clip(np.percentile(vals,28),35,78))
    candidate=((gray<=dark_threshold)&valid).astype(np.uint8)*255
    candidate=cv2.morphologyEx(candidate,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    candidate=cv2.morphologyEx(candidate,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))

    comps=_component_records(
        candidate,
        min_area=max(10,int(sw*sh*.002)),
        max_area=max(80,int(sw*sh*.065)),
    )
    best=None;best_score=-1
    for _,area,bbox,cent,fill,m in comps:
        x,y,bw,bh=bbox
        wr=bw/max(sw,1);hr=bh/max(sh,1)
        aspect=bw/max(bh,1)
        if not (.26<=wr<=.46 and .06<=hr<=.28):continue
        if not (.65<=aspect<=1.8):continue
        if fill<.30:continue
        if cent[1] > sy + sh*.62:
            continue
        # Bags usually sit below torso center and away from the head.
        score=.45+.20*fill+.18*min(1,wr/.30)+.10*min(1,hr/.18)
        if abs(cent[0]-axis)<sw*.25:
            score+=.05
        if score>best_score:
            best_score=score;best=(bbox,cent,m)
    if best is None:return []
    bbox,cent,mask=best
    return [
        PropDescriptor(
            id=130,
            prop_type="bag_like",
            mask=mask,
            bbox=bbox,
            centroid=cent,
            confidence=float(np.clip(best_score,0,1)),
            orientation_deg=0.0,
            side=_side(cent[0],axis,sw*.05),
            metadata={"detector":"lower_torso_compact_dark_mass"},
        )
    ]


def _overlap_ratio(a:np.ndarray,b:np.ndarray)->float:
    aa=a>0;bb=b>0
    denom=max(1,int(np.count_nonzero(aa)))
    return float(np.count_nonzero(aa&bb)/denom)


def _dedupe_props(props:list[PropDescriptor])->list[PropDescriptor]:
    props=sorted(props,key=lambda p:p.confidence,reverse=True)
    out=[]
    for p in props:
        dup=False
        for q in out:
            overlap=max(_overlap_ratio(p.mask,q.mask),_overlap_ratio(q.mask,p.mask))
            dc=math.hypot(p.centroid[0]-q.centroid[0],p.centroid[1]-q.centroid[1])
            scale=max(p.bbox[2],p.bbox[3],q.bbox[2],q.bbox[3],1)
            if overlap>.45 or (dc<scale*.20 and p.prop_type==q.prop_type):
                dup=True
                break
        if not dup:
            out.append(p)
    return out


def _detect_props_native(
    image_rgb:np.ndarray,
    structure:CharacterStructure,
    regions:list[Region],
)->list[PropDescriptor]:
    props=[]
    props.extend(_detect_long_linear_prop(image_rgb,structure))
    props.extend(_detect_headphone_prop(image_rgb,structure))
    props.extend(_detect_microphone_prop(image_rgb,structure))
    props.extend(_detect_hat_prop(image_rgb,structure))
    props.extend(_detect_bag_prop(image_rgb,structure))

    props=_dedupe_props(props)

    # Source-region provenance for debugging and Shape suppression.
    for i,p in enumerate(props):
        p.id=i
        p.source_region_ids=_region_ids_for_mask(regions,p.mask,min_overlap=.12)

    # Keep a small, high-confidence set. Character identity is improved by
    # one or two distinctive props, not by labeling every accessory as a prop.
    props=[p for p in props if p.confidence>=.56]
    props.sort(key=lambda p:(p.confidence,p.prop_type in {"staff_like","microphone_like","headphone_like","bag_like"}),reverse=True)
    return props[:3]



def _scale_bbox(bbox: tuple[int, int, int, int], scale: float) -> tuple[int, int, int, int]:
    x,y,w,h=bbox
    return (
        int(round(x*scale)),
        int(round(y*scale)),
        max(1,int(round(w*scale))),
        max(1,int(round(h*scale))),
    )


def _scale_point(point: tuple[float,float] | list[float], scale: float) -> tuple[float,float]:
    return (float(point[0])*scale,float(point[1])*scale)


def _scaled_structure_for_prop_detection(
    structure: CharacterStructure,
    size: tuple[int,int],
    scale: float,
) -> CharacterStructure:
    sw,sh=size
    scaled=copy.deepcopy(structure)
    scaled.subject_mask=cv2.resize(
        structure.subject_mask,(sw,sh),interpolation=cv2.INTER_NEAREST
    )
    scaled.subject_bbox=_scale_bbox(structure.subject_bbox,scale)
    scaled.metadata=dict(structure.metadata)
    if 'body_axis_x' in scaled.metadata:
        scaled.metadata['body_axis_x']=float(scaled.metadata['body_axis_x'])*scale

    for src,dst in zip(structure.parts,scaled.parts):
        dst.mask=cv2.resize(src.mask,(sw,sh),interpolation=cv2.INTER_NEAREST)
        dst.bbox=_scale_bbox(src.bbox,scale)
        dst.centroid=_scale_point(src.centroid,scale)
        dst.area=int(np.count_nonzero(dst.mask))
    return scaled


def _scaled_regions_for_prop_detection(
    regions: list[Region],
    size: tuple[int,int],
    scale: float,
) -> list[Region]:
    sw,sh=size
    out=[]
    for region in regions:
        r=copy.deepcopy(region)
        r.mask=cv2.resize(region.mask,(sw,sh),interpolation=cv2.INTER_NEAREST)
        r.bbox=_scale_bbox(region.bbox,scale)
        r.centroid=_scale_point(region.centroid,scale)
        r.area=int(np.count_nonzero(r.mask))
        out.append(r)
    return out


def _scale_descriptor_back(
    descriptor: PropDescriptor,
    original_size: tuple[int,int],
    inv_scale: float,
) -> PropDescriptor:
    ow,oh=original_size
    descriptor.mask=cv2.resize(
        descriptor.mask,(ow,oh),interpolation=cv2.INTER_NEAREST
    )
    descriptor.bbox=_scale_bbox(descriptor.bbox,inv_scale)
    descriptor.centroid=_scale_point(descriptor.centroid,inv_scale)
    if descriptor.axis_start is not None:
        descriptor.axis_start=_scale_point(descriptor.axis_start,inv_scale)
    if descriptor.axis_end is not None:
        descriptor.axis_end=_scale_point(descriptor.axis_end,inv_scale)

    md=dict(descriptor.metadata)
    for key in ['left_center','right_center','head_center']:
        if md.get(key) is not None:
            md[key]=list(_scale_point(md[key],inv_scale))
    for key in ['left_bbox','right_bbox','head_bbox']:
        if md.get(key) is not None:
            b=md[key]
            md[key]=list(_scale_bbox((int(round(b[0])),int(round(b[1])),int(round(b[2])),int(round(b[3]))),inv_scale))
    descriptor.metadata=md
    return descriptor


def _map_descriptor_to_size(
    descriptor: PropDescriptor,
    output_size: tuple[int,int],
) -> PropDescriptor:
    ow,oh=output_size
    ih,iw=descriptor.mask.shape[:2]
    sx=ow/max(iw,1)
    sy=oh/max(ih,1)
    descriptor.mask=cv2.resize(descriptor.mask,(ow,oh),interpolation=cv2.INTER_NEAREST)
    descriptor.bbox=mask_bbox(descriptor.mask)
    descriptor.centroid=mask_centroid(descriptor.mask)
    if descriptor.axis_start is not None:
        descriptor.axis_start=(descriptor.axis_start[0]*sx,descriptor.axis_start[1]*sy)
    if descriptor.axis_end is not None:
        descriptor.axis_end=(descriptor.axis_end[0]*sx,descriptor.axis_end[1]*sy)
    md=dict(descriptor.metadata)
    for key in ['left_center','right_center','head_center']:
        if md.get(key) is not None:
            md[key]=[float(md[key][0])*sx,float(md[key][1])*sy]
    for key in ['left_bbox','right_bbox','head_bbox']:
        if md.get(key) is not None:
            b=md[key]
            md[key]=[
                float(b[0])*sx,float(b[1])*sy,
                float(b[2])*sx,float(b[3])*sy,
            ]
    descriptor.metadata=md
    return descriptor


def _detect_props_from_source(
    source_rgb: np.ndarray,
    source_alpha: np.ndarray,
    preset: str,
    output_size: tuple[int,int],
    regions: list[Region],
) -> list[PropDescriptor]:
    sh,sw=source_rgb.shape[:2]
    target=300.0
    scale=target/max(sh,sw,1)
    cw=max(8,int(round(sw*scale)))
    ch=max(8,int(round(sh*scale)))
    canonical=cv2.resize(
        source_rgb,(cw,ch),
        interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC,
    )
    alpha=cv2.resize(source_alpha,(cw,ch),interpolation=cv2.INTER_AREA)
    valid=(alpha>=16).astype(np.uint8)*255

    from .detect import detect_character_structure
    from .refine import refine_character_structure
    cstructure=detect_character_structure(
        [],valid,canonical.shape,image_rgb=canonical,preset=preset,
    )
    cstructure=refine_character_structure(cstructure,[],canonical.shape)
    props=_detect_props_native(canonical,cstructure,[])

    for descriptor in props:
        _map_descriptor_to_size(descriptor,output_size)
        descriptor.source_region_ids=_region_ids_for_mask(
            regions,descriptor.mask,min_overlap=.12
        )
    return props


def detect_props(
    image_rgb:np.ndarray,
    structure:CharacterStructure,
    regions:list[Region],
    *,
    source_rgb:np.ndarray | None=None,
    source_alpha:np.ndarray | None=None,
)->list[PropDescriptor]:
    """Scale-invariant Phase-6 prop detection.

    When the original source and alpha are available, detection is performed
    from a single direct resize to the canonical 300 px scale. This avoids
    two-step alpha resampling changing the inferred head/face at Level 4.
    """
    h,w=image_rgb.shape[:2]
    if source_rgb is not None and source_alpha is not None:
        return _detect_props_from_source(
            source_rgb,source_alpha,structure.preset,(w,h),regions
        )

    max_side=max(h,w)
    target=300.0
    scale=target/max(max_side,1)
    if 0.92 <= scale <= 1.08:
        return _detect_props_native(image_rgb,structure,regions)

    nw=max(8,int(round(w*scale)))
    nh=max(8,int(round(h*scale)))
    scaled_image=cv2.resize(
        image_rgb,(nw,nh),
        interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC,
    )
    scaled_subject=cv2.resize(
        structure.subject_mask,(nw,nh),interpolation=cv2.INTER_NEAREST
    )
    from .detect import detect_character_structure
    from .refine import refine_character_structure
    scaled_structure=detect_character_structure(
        [],scaled_subject,scaled_image.shape,
        image_rgb=scaled_image,preset=structure.preset,
    )
    scaled_structure=refine_character_structure(
        scaled_structure,[],scaled_image.shape
    )
    props=_detect_props_native(scaled_image,scaled_structure,[])
    for descriptor in props:
        _map_descriptor_to_size(descriptor,(w,h))
        descriptor.source_region_ids=_region_ids_for_mask(
            regions,descriptor.mask,min_overlap=.12
        )
    return props


def refresh_prop_parts(
    image_rgb:np.ndarray,
    structure:CharacterStructure,
    regions:list[Region],
    *,
    source_rgb:np.ndarray | None=None,
    source_alpha:np.ndarray | None=None,
)->list[PropDescriptor]:
    """
    Replace alpha1's weak generic PROP proposals with dedicated Phase-6 props.
    """
    descriptors=detect_props(
        image_rgb,structure,regions,
        source_rgb=source_rgb,source_alpha=source_alpha,
    )
    structure.parts=[
        p for p in structure.parts
        if p.part_type!=CharacterPartType.PROP
    ]

    next_id=max([p.id for p in structure.parts]+[-1])+1
    image_area=max(1,structure.subject_mask.size)
    torso=structure.first_part(CharacterPartType.TORSO)
    parent_id=torso.id if torso is not None else None

    by_id={r.id:r for r in regions}
    for d in descriptors:
        colors=[by_id[rid] for rid in d.source_region_ids if rid in by_id]
        color_rgb=None;color_lab=None
        if colors:
            total=sum(max(1,r.area) for r in colors)
            color_rgb=tuple(
                int(round(sum(r.color_rgb[k]*r.area for r in colors)/total))
                for k in range(3)
            )
            color_lab=tuple(
                float(sum(r.color_lab[k]*r.area for r in colors)/total)
                for k in range(3)
            )

        part=CharacterPartCandidate(
            id=next_id,
            part_type=CharacterPartType.PROP,
            mask=d.mask.copy(),
            bbox=d.bbox,
            centroid=d.centroid,
            area=int(np.count_nonzero(d.mask)),
            area_ratio=float(np.count_nonzero(d.mask)/image_area),
            region_ids=list(d.source_region_ids),
            confidence=d.confidence,
            side=d.side,
            parent_part_id=parent_id,
            color_rgb=color_rgb,
            color_lab=color_lab,
            abstraction_level=PART_DEFAULT_ABSTRACTION.get(CharacterPartType.PROP,.85),
            metadata={
                "prop_type":d.prop_type,
                "orientation_deg":d.orientation_deg,
                "axis_start":list(d.axis_start) if d.axis_start else None,
                "axis_end":list(d.axis_end) if d.axis_end else None,
                "detector":d.metadata.get("detector"),
                "descriptor_metadata":d.metadata,
                "protected":True,
            },
        )
        structure.parts.append(part)
        next_id+=1

    structure.metadata["prop_descriptors"]=[d.to_dict() for d in descriptors]
    return descriptors


def analyze_props(structure:CharacterStructure)->list[PropDescriptor]:
    out=[]
    for i,p in enumerate(structure.get_parts(CharacterPartType.PROP)):
        md=p.metadata
        ptype=md.get("prop_type","unknown")
        if ptype not in {
            "staff_like","sword_like","microphone_like","headphone_like",
            "hat_like","bag_like","unknown",
        }:
            ptype="unknown"
        axis_start=md.get("axis_start")
        axis_end=md.get("axis_end")
        out.append(
            PropDescriptor(
                id=i,
                prop_type=ptype,
                mask=p.mask.copy(),
                bbox=p.bbox,
                centroid=p.centroid,
                confidence=p.confidence,
                orientation_deg=float(md.get("orientation_deg",0.0)),
                axis_start=tuple(axis_start) if axis_start else None,
                axis_end=tuple(axis_end) if axis_end else None,
                source_region_ids=list(p.region_ids),
                side=p.side,
                metadata=dict(md.get("descriptor_metadata") or {}),
            )
        )
    return out


def _dominant_color(image_rgb,mask,fallback=(70,70,78)):
    pix=image_rgb[mask>0]
    if len(pix)<6:return tuple(fallback)
    lum=pix.astype(np.float32)@np.array([.299,.587,.114],dtype=np.float32)
    lo,hi=np.percentile(lum,[12,88])
    core=pix[(lum>=lo)&(lum<=hi)]
    if len(core)<6:core=pix
    med=np.median(core.astype(np.float32),axis=0)
    return tuple(int(np.clip(round(v),0,255)) for v in med)


def _axis_for_descriptor(d:PropDescriptor):
    if d.axis_start is not None and d.axis_end is not None:
        return d.axis_start,d.axis_end
    x,y,w,h=d.bbox
    if h>=w:
        return (x+w/2,y),(x+w/2,y+h)
    return (x,y+h/2),(x+w,y+h/2)


def _circle_shape(sid,cx,cy,r,color,role,confidence,side="unknown"):
    return Shape(
        id=sid,
        shape_type="circle",
        fill_color=color,
        cx=float(cx),cy=float(cy),
        rx=float(max(1,r)),ry=float(max(1,r)),
        source_role=role,
        layer_name="character_prop_detail",
        semantic_type=role,
        character_part="prop",
        part_confidence=confidence,
        side_hint=side,
        importance=1.0,
    )


def _line_shape(sid,a,b,color,width,role,confidence,side="unknown"):
    return Shape(
        id=sid,
        shape_type="line",
        fill_color=None,
        stroke_color=color,
        stroke_width=float(max(.8,width)),
        points=[(float(a[0]),float(a[1])),(float(b[0]),float(b[1]))],
        source_role=role,
        layer_name="character_prop_base",
        semantic_type=role,
        character_part="prop",
        part_confidence=confidence,
        side_hint=side,
        importance=1.0,
    )


def _mask_polygon(mask,max_vertices=8):
    contours,_=cv2.findContours((mask>0).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    contours=list(contours)
    if not contours:return []
    c=max(contours,key=cv2.contourArea)
    peri=max(1.0,float(cv2.arcLength(c,True)))
    eps=peri*.018
    approx=cv2.approxPolyDP(c,eps,True)
    while len(approx)>max_vertices and eps<peri*.08:
        eps*=1.18
        approx=cv2.approxPolyDP(c,eps,True)
    return [(float(p[0][0]),float(p[0][1])) for p in approx]


def _build_single_prop(
    d:PropDescriptor,
    image_rgb:np.ndarray,
    budget:int,
    start_id:int,
)->list[Shape]:
    if budget<=0:return []
    color=_dominant_color(image_rgb,d.mask)
    dark=tuple(int(v*.60) for v in color)
    a,b=_axis_for_descriptor(d)
    x,y,w,h=d.bbox
    sid=start_id
    out=[]

    if d.prop_type=="staff_like":
        thickness=max(1.2,min(w,h,6)*.55)
        out.append(_line_shape(sid,a,b,dark,thickness,"character_staff",d.confidence,d.side));sid+=1
        if len(out)<budget:
            top=a if a[1]<=b[1] else b
            r=max(2.0,min(max(w,h)*.055,6.0))
            pts=[
                (top[0],top[1]-r*1.6),
                (top[0]+r,top[1]),
                (top[0],top[1]+r*1.4),
                (top[0]-r,top[1]),
            ]
            out.append(Shape(
                id=sid,shape_type="polygon",fill_color=color,points=pts,
                source_role="character_staff_head",layer_name="character_prop_detail",
                semantic_type="character_staff_head",character_part="prop",
                part_confidence=d.confidence,side_hint=d.side,importance=1.0,
            ))

    elif d.prop_type=="sword_like":
        thickness=max(1.6,min(w,h,7)*.65)
        out.append(_line_shape(sid,a,b,color,thickness,"character_sword_blade",d.confidence,d.side));sid+=1
        if len(out)<budget:
            # small cross-guard near lower endpoint
            grip=a if a[1]>=b[1] else b
            dx=b[0]-a[0];dy=b[1]-a[1];norm=max(1e-6,math.hypot(dx,dy))
            px=-dy/norm;py=dx/norm;half=max(3.0,min(8.0,max(w,h)*.06))
            g1=(grip[0]-px*half,grip[1]-py*half);g2=(grip[0]+px*half,grip[1]+py*half)
            out.append(_line_shape(sid,g1,g2,dark,max(1.2,thickness*.75),"character_sword_guard",d.confidence,d.side))

    elif d.prop_type=="microphone_like":
        head=d.metadata.get("head_center")
        if head is None:
            head=a
        else:
            head=tuple(head)
        other=b if math.hypot(b[0]-head[0],b[1]-head[1])>math.hypot(a[0]-head[0],a[1]-head[1]) else a
        out.append(_line_shape(sid,head,other,dark,max(1.2,min(w,h)*.32),"character_microphone_body",d.confidence,d.side));sid+=1
        if len(out)<budget:
            r=max(2.0,min(w,h)*.40)
            out.append(_circle_shape(sid,head[0],head[1],r,color,"character_microphone_head",d.confidence,d.side))

    elif d.prop_type=="headphone_like":
        lc=d.metadata.get("left_center")
        rc=d.metadata.get("right_center")
        if lc and rc:
            lb=d.metadata.get("left_bbox") or [0,0,6,6]
            rb=d.metadata.get("right_bbox") or [0,0,6,6]
            lr=max(2.0,min(lb[2],lb[3])*.42)
            rr=max(2.0,min(rb[2],rb[3])*.42)
            out.append(_circle_shape(sid,lc[0],lc[1],lr,color,"character_headphone_cup",d.confidence,"left"));sid+=1
            if len(out)<budget:
                out.append(_circle_shape(sid,rc[0],rc[1],rr,color,"character_headphone_cup",d.confidence,"right"));sid+=1
            if len(out)<budget:
                top_y=min(lc[1],rc[1])-max(lr,rr)*1.25
                out.append(_line_shape(
                    sid,(lc[0],lc[1]-lr*.55),(rc[0],rc[1]-rr*.55),
                    dark,max(1.0,min(lr,rr)*.32),"character_headphone_band",d.confidence,"center"
                ))

    elif d.prop_type=="hat_like":
        pts=_mask_polygon(d.mask,7)
        if len(pts)>=3:
            out.append(Shape(
                id=sid,shape_type="polygon",fill_color=color,points=pts,
                source_role="character_hat",layer_name="character_prop_base",
                semantic_type="character_hat",character_part="prop",
                part_confidence=d.confidence,side_hint=d.side,importance=1.0,
            ));sid+=1
        if len(out)<budget:
            out.append(_line_shape(
                sid,(x,y+h*.78),(x+w,y+h*.78),dark,max(1.0,h*.08),
                "character_hat_brim",d.confidence,d.side
            ))

    elif d.prop_type=="bag_like":
        pts=[
            (x+w*.16,y+h*.16),(x+w*.84,y+h*.16),
            (x+w,y+h*.38),(x+w*.88,y+h),
            (x+w*.12,y+h),(x,y+h*.38),
        ]
        out.append(Shape(
            id=sid,shape_type="polygon",fill_color=color,
            points=[(float(px),float(py)) for px,py in pts],
            source_role="character_bag",layer_name="character_prop_base",
            semantic_type="character_bag",character_part="prop",
            part_confidence=d.confidence,side_hint=d.side,importance=1.0,
        ));sid+=1
        if len(out)<budget:
            out.append(_line_shape(
                sid,(x+w*.30,y+h*.23),(x+w*.70,y+h*.23),
                dark,max(1.0,h*.05),"character_bag_handle",d.confidence,d.side
            ))

    else:
        if d.axis_start is not None and d.axis_end is not None:
            out.append(_line_shape(
                sid,d.axis_start,d.axis_end,color,
                max(1.2,min(w,h)*.50),
                "character_handheld_prop",d.confidence,d.side,
            ))
        else:
            pts=_mask_polygon(d.mask,8)
            if len(pts)>=3:
                out.append(Shape(
                    id=sid,shape_type="polygon",fill_color=color,points=pts,
                    source_role="character_prop",layer_name="character_prop_base",
                    semantic_type="character_prop",character_part="prop",
                    part_confidence=d.confidence,side_hint=d.side,importance=1.0,
                ))

    return out[:budget]


def build_prop_shapes(
    descriptors:list[PropDescriptor],
    image_rgb:np.ndarray,
    budget:int,
    *,
    start_id:int,
)->list[Shape]:
    if budget<=0 or not descriptors:return []

    ranked=sorted(descriptors,key=lambda d:d.confidence,reverse=True)
    allocations=[1 for _ in ranked]
    remaining=max(0,budget-len(allocations))

    # Identity-heavy props may use one secondary symbol (head / guard /
    # handle), but never turn into a miniature trace. Two Shapes per prop is
    # the finishing-stage hard cap; unused budget stays unused.
    while remaining>0:
        candidates=[i for i,a in enumerate(allocations) if a<2]
        if not candidates:
            break
        target=max(
            candidates,
            key=lambda i:(
                ranked[i].prop_type in {"microphone_like","headphone_like","staff_like","sword_like","bag_like"},
                ranked[i].confidence,
            ),
        )
        allocations[target]+=1
        remaining-=1

    out=[];sid=start_id
    for d,alloc in zip(ranked,allocations):
        built=_build_single_prop(d,image_rgb,alloc,sid)
        out.extend(built)
        sid+=len(built)
        if len(out)>=budget:break
    return out[:budget]
