"""L02 research: normalize human silhouette scale *before* calculating local features.

DO NOT ship as an image-segmentation model. No signed labels for unseen cases.
Source-only RGBA, no hallucination/inpainting, no geometry copied from user traces.
A resized image is an ephemeral analysis image, NEVER a replacement for the signed
original and NEVER a raster output in a production candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import numpy as np
import cv2

TARGET_HEIGHT=900
MAX_WIDTH=900
MIN_FOREGROUND=500

class AuthorityHold(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    """Integer crop + analysis-scale transform. Original coordinate mapping is explicit."""
    left:int
    top:int
    right:int  # exclusive
    bottom:int # exclusive
    source_width:int
    source_height:int
    analysis_width:int
    analysis_height:int
    original_sha256:str
    def to_dict(self):
        return dict(left=self.left,top=self.top,right=self.right,bottom=self.bottom,
          source_width=self.source_width,source_height=self.source_height,
          analysis_width=self.analysis_width,analysis_height=self.analysis_height,
          original_sha256=self.original_sha256)


def sha256(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def foreground_frame(src:np.ndarray,original_sha256:str,*,target_height:int=TARGET_HEIGHT,padding_ratio:float=.018)->Frame:
    if src.dtype!=np.uint8 or src.ndim!=3 or src.shape[-1]!=4:
        raise AuthorityHold('source must be RGBA uint8')
    if len(original_sha256)!=64 or any(c not in '0123456789abcdef' for c in original_sha256):
        raise AuthorityHold('source identity SHA256 required')
    if not isinstance(target_height,int) or target_height<256 or target_height>1200:
        raise AuthorityHold('invalid analysis height')
    fg=src[:,:,3]>0
    if int(fg.sum())<MIN_FOREGROUND:
        raise AuthorityHold('insufficient authenticated foreground')
    border=np.concatenate([fg[0],fg[-1],fg[1:-1,0],fg[1:-1,-1]])
    if float(border.mean())>.20 or float(fg.mean())>.92:
        raise AuthorityHold('opaque or complex background, cannot normalize')
    yy,xx=np.nonzero(fg)
    h,w=fg.shape
    padx=max(1,int(np.ceil((xx.max()-xx.min()+1)*padding_ratio)))
    pady=max(1,int(np.ceil((yy.max()-yy.min()+1)*padding_ratio)))
    left=max(0,int(xx.min())-padx);right=min(w,int(xx.max())+1+padx)
    top=max(0,int(yy.min())-pady);bottom=min(h,int(yy.max())+1+pady)
    crop_h=bottom-top;crop_w=right-left
    scale=min(target_height/crop_h,MAX_WIDTH/crop_w)
    ah=max(1,int(round(crop_h*scale)));aw=max(1,int(round(crop_w*scale)))
    if aw<25 or ah<25:raise AuthorityHold('degenerate subject-scale frame')
    return Frame(left,top,right,bottom,w,h,aw,ah,original_sha256)


def normalize_source(src:np.ndarray,frame:Frame)->np.ndarray:
    if src.shape[:2]!=(frame.source_height,frame.source_width) or src.shape[-1]!=4:
        raise AuthorityHold('original size/source channels differ from frozen frame')
    roi=np.ascontiguousarray(src[frame.top:frame.bottom,frame.left:frame.right])
    if roi.size==0:raise AuthorityHold('empty authenticated source frame')
    interpolation=(cv2.INTER_AREA if frame.analysis_height<roi.shape[0] else cv2.INTER_LINEAR)
    img=cv2.resize(roi,(frame.analysis_width,frame.analysis_height),interpolation=interpolation)
    if img.ndim!=3 or img.shape[-1]!=4:raise AuthorityHold('invalid analysis output')
    return img


def normalize_mask(src_mask:np.ndarray,frame:Frame)->np.ndarray:
    if src_mask.shape!=(frame.source_height,frame.source_width) or src_mask.dtype!=np.dtype('bool'):
        raise AuthorityHold('non-binary or shape mismatch with signed original')
    crop=np.ascontiguousarray(src_mask[frame.top:frame.bottom,frame.left:frame.right]).astype(np.uint8)
    return cv2.resize(crop,(frame.analysis_width,frame.analysis_height),interpolation=cv2.INTER_NEAREST)>0


def project_mask(mask:np.ndarray,frame:Frame,original_alpha:np.ndarray)->np.ndarray:
    """Projection is evidence only; never materialize a new signed source/mask."""
    if mask.dtype!=np.dtype('bool') or mask.shape!=(frame.analysis_height,frame.analysis_width):
        raise AuthorityHold('unexpected analysis prediction extent')
    if original_alpha.dtype!=np.dtype('bool') or original_alpha.shape!=(frame.source_height,frame.source_width):
        raise AuthorityHold('original source alpha required to constrain projected evidence')
    restored=cv2.resize(mask.astype(np.uint8),(frame.right-frame.left,frame.bottom-frame.top),interpolation=cv2.INTER_NEAREST)>0
    result=np.zeros((frame.source_height,frame.source_width),dtype=bool)
    result[frame.top:frame.bottom,frame.left:frame.right]=restored
    result &= original_alpha
    return result


def predict_source_bound(src:np.ndarray,frame:Frame,model,features_fn,*,threshold:float=.5,chunk:int=18000)->tuple[np.ndarray,dict]:
    if not 0<threshold<1 or chunk<100:raise AuthorityHold('untrusted prediction parameters')
    analysis=normalize_source(src,frame)
    alpha=analysis[:,:,3]>0
    features=features_fn(analysis).reshape(-1,18)
    indices=np.flatnonzero(alpha.ravel())
    output=np.zeros(alpha.size,np.uint8)
    for start in range(0,len(indices),chunk):
        ids=indices[start:start+chunk]
        prob=np.asarray(model.predict_proba(features[ids]))
        if prob.shape!=(len(ids),2) or not np.isfinite(prob).all() or (prob<0).any() or (prob>1).any():
            raise AuthorityHold('untrusted classifier output')
        output[ids]=(prob[:,1]>=threshold)
    result=output.reshape(alpha.shape).astype(bool)
    if np.any(result&~alpha):raise AuthorityHold('predicted unsupported analysis pixel')
    return result,{'analysis_samples':int(indices.size),'analysis_positive':int(result.sum()),
                   'response_fraction':round(float(result.sum())/max(1,int(indices.size)),6)}


def normalized_overlap(a:np.ndarray,frame_a:Frame,b:np.ndarray,frame_b:Frame,original_alpha:np.ndarray)->dict:
    """Compare the SAME signed source at two resolutions, transformed to native pixel coordinates."""
    if (frame_a.source_width,frame_a.source_height)!=(frame_b.source_width,frame_b.source_height):
        raise AuthorityHold('unrelated source resolution')
    if frame_a.original_sha256!=frame_b.original_sha256:raise AuthorityHold('unrelated originals')
    pa=project_mask(a,frame_a,original_alpha);pb=project_mask(b,frame_b,original_alpha)
    union=int((pa|pb).sum());inter=int((pa&pb).sum());xor=int((pa^pb).sum())
    return {'intersection':inter,'union':union,'xor':xor,'iou':round(inter/union,6) if union else 1.0,
           'orig_positive_a':int(pa.sum()),'orig_positive_b':int(pb.sum())}


def release_guard(*,independent_character_labels:int,semantic_iou:float|None)->dict:
    if independent_character_labels==0 and semantic_iou is not None:
        raise AuthorityHold('cannot assert unseen semantic IoU without authenticated labels')
    return {'L02_status':'HOLD','production_release':'NO_GO',
            'independent_character_labels':independent_character_labels,
            'semantic_iou':semantic_iou}
