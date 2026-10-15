"""Manual-supervised Phase4 *research shadow*. No inference-time copied trace coordinates.

Train with source+label pixels in private research, infer from source RGBA colors,
local image gradients and source-relative position. Never deploy from one training
image. The manual mask is a TRAINING/EVALUATION input ONLY, never accepted as a
rendered output; all decisions are constrained to opaque original source pixels.

The human H04 jacket labels are grounded by independent overlap against the
previous 3-polygon user jacket trace; other generic 17 shapes remain unlabelled.
"""
from __future__ import annotations
import dataclasses
import hashlib
import math
from typing import Mapping
import cv2
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

PARTS=("head","hair","face","neck","torso","left_arm","right_arm","lower_body","major_clothing","accessory_or_held_object","unknown")
PROTECTED=("face","neck","left_arm","right_arm","lower_body","accessory_or_held_object")
MODEL_PARAMETERS={"max_iter":65,"max_leaf_nodes":24,"max_depth":7,"min_samples_leaf":70,"learning_rate":.08,"l2_regularization":3,"random_state":741}
THRESHOLD=.50 # exploratory H04-tuned, NOT a Golden threshold
NECK_GUARD_RATIO=.0143 # 20px for H04; exploratory single-reference tuning
SEED=20261015

class AuthorityHold(ValueError): pass

def sha256(buf:bytes)->str: return hashlib.sha256(buf).hexdigest()

def validate_masks(src:np.ndarray,masks:Mapping[str,np.ndarray]):
    if src.ndim!=3 or src.shape[-1]!=4 or src.dtype!=np.uint8: raise AuthorityHold("source must be RGBA uint8")
    h,w=src.shape[:2]
    if set(masks)!=set(PARTS): raise AuthorityHold("part mask key set mismatch")
    for key in PARTS:
        v=masks[key]
        if v.shape!=(h,w) or v.dtype not in (bool,np.dtype('bool')):raise AuthorityHold('nonbinary or wrong shape '+key)
    alpha=src[:,:,3]>0
    if any(np.any(masks[k]&~alpha) for k in PARTS):raise AuthorityHold('signed source owner outside foreground')
    return alpha

def eligible_region(src:np.ndarray,masks:Mapping[str,np.ndarray]):
    alpha=validate_masks(src,masks)
    protected=np.logical_or.reduce([masks[k] for k in PROTECTED])
    return alpha&~protected

def source_features(src:np.ndarray)->np.ndarray:
    """Unsupervised image features: no hand trace, masks or H04 coordinates used."""
    if src.dtype!=np.uint8 or src.ndim!=3 or src.shape[2]!=4:raise AuthorityHold('invalid RGBA input')
    alpha=src[:,:,3]>0
    if alpha.sum()<30:raise AuthorityHold('too few source pixels')
    lab=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2LAB).astype(np.float32)
    smooth=cv2.GaussianBlur(lab,(5,5),.9)
    big=cv2.GaussianBlur(lab,(15,15),2.8)
    gray=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2GRAY)
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)
    gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    ys,xs=np.indices(alpha.shape)
    ya,xa=np.where(alpha)
    xnorm=((xs-xa.min())/max(1,int(xa.max()-xa.min()))).astype(np.float32)
    ynorm=((ys-ya.min())/max(1,int(ya.max()-ya.min()))).astype(np.float32)
    return np.concatenate([lab,smooth,big,lab-smooth,lab-big,
        np.hypot(gx,gy)[...,None],ynorm[...,None],xnorm[...,None]],axis=2)

def auto_guard(src:np.ndarray,masks:Mapping[str,np.ndarray]):
    """Original neck location, not a ground-truth jacket polygon or hand ROI."""
    allow=eligible_region(src,masks)
    yy=np.where(masks['neck'])[0]
    if not len(yy):raise AuthorityHold('missing neck: abstain, do not invent jacket ROI')
    ys=np.arange(src.shape[0])[:,None]
    return allow & (ys >= (int(yy.min())+max(4,int(round(src.shape[0]*NECK_GUARD_RATIO)))))

def train(src:np.ndarray,masks:Mapping[str,np.ndarray],human_jacket:np.ndarray,train_pixels:np.ndarray):
    eligible=eligible_region(src,masks)
    if human_jacket.shape!=eligible.shape or human_jacket.dtype!=np.dtype('bool'):
        raise AuthorityHold('wrong or nonbinary training label')
    if train_pixels.shape!=eligible.shape or train_pixels.dtype!=np.dtype('bool'):
        raise AuthorityHold('wrong training split')
    y=human_jacket&eligible
    train_mask=train_pixels&eligible
    ix=np.flatnonzero(train_mask.ravel());yi=y.ravel()
    pos=ix[yi[ix]];neg=ix[~yi[ix]]
    if min(len(pos),len(neg))<300:raise AuthorityHold('insufficient diverse human reference labels')
    rng=np.random.default_rng(SEED)
    selection=np.sort(np.concatenate([rng.choice(pos,min(18000,len(pos)),replace=False),
                                     rng.choice(neg,min(28000,len(neg)),replace=False)]))
    features=source_features(src).reshape((-1,18))
    clf=HistGradientBoostingClassifier(**MODEL_PARAMETERS)
    clf.fit(features[selection],yi[selection])
    return clf

def inference(src:np.ndarray,masks:Mapping[str,np.ndarray],model,*,evaluate_only_mask:np.ndarray|None=None)->np.ndarray:
    """No human manual trace in inference API. Fail closed on protected pixels."""
    allowed=auto_guard(src,masks)
    if evaluate_only_mask is not None:
        if evaluate_only_mask.shape!=allowed.shape or evaluate_only_mask.dtype!=np.dtype('bool'):
            raise AuthorityHold('bad holdout mask')
        allowed&=evaluate_only_mask
    out=np.zeros(allowed.shape,bool)
    positions=np.flatnonzero(allowed.ravel())
    if not len(positions):return out
    X=source_features(src).reshape((-1,18))
    prob=model.predict_proba(X[positions])[:,1]
    out.ravel()[positions]=prob>=THRESHOLD
    if np.any(out & ~allowed):raise AuthorityHold('candidate out of guarded source pixels')
    return out

def score(y:np.ndarray,p:np.ndarray)->dict:
    tp=int((y&p).sum());fp=int((~y&p).sum());fn=int((y&~p).sum())
    return {'tp':tp,'fp':fp,'fn':fn,'precision':round(tp/max(1,tp+fp),6),
            'recall':round(tp/max(1,tp+fn),6), 'iou':round(tp/max(1,tp+fp+fn),6),
            'f1':round(2*tp/max(1,2*tp+fp+fn),6),'pred_pixels':int(p.sum())}

def spatial_fold_masks(h:int,w:int):
    yy,xx=np.indices((h,w))
    return {'train_viewer_left':xx<w//2,'train_viewer_right':xx>=w//2,
            'train_upper':yy<int(round(h*.392857)),'train_lower':yy>=int(round(h*.25)),
            'train_alternating_tiles':((xx//max(2,w//10)+yy//max(2,h//20))%2==0)}

def evaluate_h04(src:np.ndarray,masks:Mapping[str,np.ndarray],manual:np.ndarray,old:np.ndarray):
    eligible=eligible_region(src,masks)
    truth=manual&eligible
    if not np.any(truth):raise AuthorityHold('empty manual jacket')
    old=old&eligible
    fold_report={};oof=np.zeros(truth.shape,bool)
    for name,train_pixels in spatial_fold_masks(*truth.shape).items():
        holdout=eligible&~train_pixels
        clf=train(src,masks,manual,train_pixels)
        prediction=inference(src,masks,clf,evaluate_only_mask=holdout)
        baseline=score(truth&holdout,old&holdout)
        result=score(truth&holdout,prediction)
        fold_report[name]={'train_eligible_pixels':int((eligible&train_pixels).sum()),
            'holdout_eligible_pixels':int(holdout.sum()),'old':baseline,'new':result,
            'iou_delta':round(result['iou']-baseline['iou'],6)}
        if name=='train_viewer_left':oof |=prediction
        if name=='train_viewer_right':oof |=prediction
    # pixelwise out-of-fold across image halves; H04 remains the same source image
    oof_stats=score(truth,oof)
    full=train(src,masks,manual,np.ones(truth.shape,bool))
    fullpred=inference(src,masks,full)
    return {'folds':fold_report,'out_of_fold':oof_stats,'old_whole':score(truth,old),
            'full_model_in_sample':score(truth,fullpred),
            'all_spatial_folds_improved':all(r['iou_delta']>0 for r in fold_report.values())},oof,fullpred

def postprocess_jacket_evidence(src:np.ndarray,masks:Mapping[str,np.ndarray],jacket:np.ndarray,*,median_kernel:int=5,min_island:int=30):
    """Retain ownership of head/hair; only add soft garment evidence.

    This is NOT mutually-exclusive semantic remapping. A future graph renderer
    must resolve overlap and order, and cannot publish without human Golden.
    """
    eligible=eligible_region(src,masks)
    if jacket.shape!=eligible.shape or jacket.dtype!=np.dtype('bool') or np.any(jacket&~eligible):
        raise AuthorityHold('untrusted garment candidates')
    if median_kernel%2!=1 or median_kernel<1 or median_kernel>9 or min_island<0:
        raise AuthorityHold('invalid regularizer')
    evidence=(cv2.medianBlur(jacket.astype(np.uint8)*255,median_kernel)>0) if median_kernel>1 else jacket.copy()
    signed_union=np.logical_or.reduce([masks[k] for k in PARTS])
    evidence&=auto_guard(src,masks)&signed_union
    count,labels,stats,_=cv2.connectedComponentsWithStats(evidence.astype(np.uint8),8)
    for i in range(1,count):
        if int(stats[i,cv2.CC_STAT_AREA])<min_island:evidence[labels==i]=False
    owner={k:v.copy() for k,v in masks.items()}
    owner['major_clothing']|=evidence
    # Preserve every original owner except addition of foreground-only evidence.
    for key in PARTS:
        if key!='major_clothing' and not np.array_equal(owner[key],masks[key]):
            raise AuthorityHold('non-destructive evidence altered source owner '+key)
    old_union=np.logical_or.reduce([masks[k] for k in PARTS])
    new_union=np.logical_or.reduce([owner[k] for k in PARTS])
    if not np.array_equal(old_union,new_union):
        raise AuthorityHold('non-destructive evidence changes original union')
    return owner,evidence
