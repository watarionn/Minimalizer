"""Fail-closed source-only test-time equivariance diagnostic, research only.

One model viewed on source and its horizontal mirror is NOT a second observer.
The mirrored image is an ephemeral feature-analysis view, not a new original.
This routine never creates Phase4 ownership and never authorizes a release.
"""
from __future__ import annotations
import hashlib,io
from PIL import Image
import numpy as np

class AuthorityHold(ValueError): pass

def verify_rgba(source: np.ndarray, source_bytes: bytes, expected_sha256: str) -> np.ndarray:
    if not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or hashlib.sha256(source_bytes).hexdigest()!=expected_sha256:
        raise AuthorityHold('original source SHA mismatch')
    if not isinstance(source,np.ndarray) or source.dtype!=np.uint8 or source.ndim!=3 or source.shape[2]!=4:
        raise AuthorityHold('source must be RGBA uint8')
    try:
        encoded=np.asarray(Image.open(io.BytesIO(source_bytes)).convert('RGBA'),dtype=np.uint8)
    except Exception as exc:
        raise AuthorityHold('signed bytes are not a valid image') from exc
    if encoded.shape!=source.shape or not np.array_equal(encoded,source):
        raise AuthorityHold('decoded signed source pixels differ from supplied source array')
    alpha=source[:,:,3]>0
    if int(alpha.sum())<30:raise AuthorityHold('empty source foreground')
    return alpha

def probabilities(source,model,features_fn,mask,*,batch=18000):
    if not isinstance(mask,np.ndarray) or mask.dtype!=np.dtype('bool') or mask.shape!=source.shape[:2]:
        raise AuthorityHold('source foreground shape mismatch')
    if (mask&~(source[:,:,3]>0)).any():raise AuthorityHold('unsupported predicted foreground')
    if not isinstance(batch,int) or not 100<=batch<=65536:raise AuthorityHold('untrusted chunk size')
    values=features_fn(source)
    if values.ndim!=3 or values.shape[:2]!=mask.shape or not np.isfinite(values).all():
        raise AuthorityHold('invalid source-only feature array')
    ids=np.flatnonzero(mask.ravel());flat=values.reshape((-1,values.shape[2]))
    out=np.zeros(mask.size,dtype=np.float32)
    for start in range(0,len(ids),batch):
        sel=ids[start:start+batch];v=np.asarray(model.predict_proba(flat[sel]))
        if v.shape!=(len(sel),2) or not np.isfinite(v).all() or (v<0).any() or (v>1).any():
            raise AuthorityHold('invalid probability evidence')
        out[sel]=v[:,1]
    return out.reshape(mask.shape)

def flip_agreement(source,model,features_fn,allowed,*,threshold=.5,minimum_foreground_ratio=.002,minimum_iou=.75):
    """Return only diagnostic masks and gating metrics, never exclusive owner."""
    if not (0<threshold<1 and 0<minimum_iou<=1 and 0<=minimum_foreground_ratio<1):
        raise AuthorityHold('invalid gate threshold')
    if allowed.dtype!=np.dtype('bool') or allowed.shape!=source.shape[:2] or (allowed&~(source[:,:,3]>0)).any():
        raise AuthorityHold('inconsistent allowed mask')
    if allowed.sum()<30:raise AuthorityHold('no supported foreground')
    original=probabilities(source,model,features_fn,allowed)
    # A reversible view only; no interpolation, painted pixels, generated geometry, or output file.
    flipped=np.ascontiguousarray(source[:,::-1,:]);flipped_allowed=np.ascontiguousarray(allowed[:,::-1])
    mirrored=probabilities(flipped,model,features_fn,flipped_allowed)[:,::-1].copy()
    a=(original>=threshold)&allowed;b=(mirrored>=threshold)&allowed
    union=int((a|b).sum());hit=int((a&b).sum())
    iou=hit/union if union else 1.0
    fraction=float(union)/int(allowed.sum())
    accepted=union>0 and fraction>=minimum_foreground_ratio and iou>=minimum_iou
    return {'status':'DIAGNOSTIC_CONSISTENT_NOT_SEMANTIC_PASS' if accepted else 'ABSTAIN_UNSTABLE_OR_SPARSE',
            'flipped_is_not_independent_observer':True,
            'original_response_pixels':int(a.sum()),'flipped_response_pixels':int(b.sum()),
            'consensus_pixels':hit,'union_pixels':union,'flip_iou':round(iou,6),
            'response_fraction':round(fraction,6),'source_pixels_generated':0,
            'semantic_quality_verified':False,'production_release':'NO_GO'},a&b,a^b
