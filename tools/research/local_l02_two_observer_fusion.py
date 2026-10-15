"""Conservative source-bound L02 jacket-shadow fusion.

Primary observer: H04 hand-trace-trained pixel learner. Secondary observer:
independently trained AnimeSeg Mask2Former v3 'clothes' semantic class.

Agreement is NOT an independently signed jacket label and cannot become Phase4
ownership without per-character external evaluation. Never draw human facial
features or replace the signed source, and never silently merge overlapping
owner masks into production.
"""
from __future__ import annotations
import dataclasses
import hashlib
from typing import Mapping
import numpy as np
import cv2

CLOTHES_CLASS_ID=10
DEFAULT_DILATION=3
PROTECTED=("face","neck","left_arm","right_arm","lower_body","accessory_or_held_object")

class AuthorityHold(ValueError):
    pass


def validate_digest(x:str):
    if not isinstance(x,str) or len(x)!=64 or any(c not in '0123456789abcdef' for c in x):
        raise AuthorityHold('immutable SHA-256 required')
    return x


@dataclasses.dataclass(frozen=True)
class FusionObservation:
    agreement_pixels:int
    primary_pixels:int
    secondary_pixels:int
    disagreement_pixels:int
    foreground_xor_pixels:int
    protected_overlap_pixels:int
    semantic_quality_verified:bool=False
    production_authorized:bool=False
    def to_dict(self):return dataclasses.asdict(self)


def fuse_observers(primary:np.ndarray,secondary_classes:np.ndarray,source_alpha:np.ndarray,
                   signed_owner_union:np.ndarray,protected:Mapping[str,np.ndarray],*,primary_source_sha256:str,
                   secondary_source_sha256:str,secondary_weights_sha256:str,
                   clothes_id:int=CLOTHES_CLASS_ID,dilation:int=DEFAULT_DILATION):
    """Produces *diagnostic evidence* only, not semantic part masks.

    Dilate 3px only to account for independent observer boundary co-registration.
    The class-10 mask denotes generic CLOTHES, not an authenticated jacket mask.
    """
    validate_digest(primary_source_sha256);validate_digest(secondary_source_sha256)
    validate_digest(secondary_weights_sha256)
    if primary_source_sha256!=secondary_source_sha256:
        raise AuthorityHold('two observers evaluated different signed source bytes')
    if not isinstance(primary,np.ndarray) or primary.dtype!=np.dtype('bool'):
        raise AuthorityHold('primary not boolean')
    if secondary_classes.dtype!=np.uint8 or secondary_classes.shape!=primary.shape:
        raise AuthorityHold('secondary class image must be exact source extent uint8')
    if not isinstance(source_alpha,np.ndarray) or source_alpha.dtype!=np.dtype('bool') or source_alpha.shape!=primary.shape:
        raise AuthorityHold('authentic source alpha extent mismatch')
    if not isinstance(signed_owner_union,np.ndarray) or signed_owner_union.dtype!=np.dtype('bool') or signed_owner_union.shape!=primary.shape:
        raise AuthorityHold('signed Phase4 source foreground union required')
    if np.any(signed_owner_union & ~source_alpha):
        raise AuthorityHold('signed ownership outside source alpha')
    if not set(PROTECTED).issubset(protected):
        raise AuthorityHold('missing protected original owners')
    for k in PROTECTED:
        v=protected[k]
        if v.dtype!=np.dtype('bool') or v.shape!=primary.shape:
            raise AuthorityHold('protected owner mask not exact binary original extent: '+k)
    if not isinstance(dilation,int) or dilation not in (1,3):
        raise AuthorityHold('unreviewed edge dilation')
    if clothes_id != CLOTHES_CLASS_ID:
        raise AuthorityHold('unsanctioned observer class')
    if np.any(primary&~source_alpha):
        raise AuthorityHold('primary proposed new transparent-background pixel')
    if np.any(secondary_classes>11):
        raise AuthorityHold('unrecognized secondary model class id')
    excluded=np.logical_or.reduce([protected[k] for k in PROTECTED])
    if np.any(primary&excluded):
        raise AuthorityHold('primary invades signed protected area')
    base=secondary_classes==clothes_id
    if dilation==3:
        base=cv2.dilate(base.astype(np.uint8),np.ones((3,3),np.uint8))>0
    secondary=(base&source_alpha&signed_owner_union&~excluded)
    agreement=primary&secondary&signed_owner_union
    uncertain=(primary^secondary)&source_alpha&signed_owner_union&~excluded
    metrics=FusionObservation(agreement_pixels=int(agreement.sum()),primary_pixels=int(primary.sum()),
        secondary_pixels=int(secondary.sum()),disagreement_pixels=int(uncertain.sum()),
        foreground_xor_pixels=0,protected_overlap_pixels=int((agreement&excluded).sum()))
    return agreement,uncertain,metrics


def quality_gate(observed:dict,*,unseen_jacket_truth:bool=False)->dict:
    """A structural/within-H04 benchmark is not a release authority."""
    if unseen_jacket_truth:
        raise AuthorityHold('requires independent verified source-bound human review')
    return {'status':'HOLD','production_release':'NO_GO','semantic_iou_unseen':None,
            'reason':'ONLY_H04_GROUND_TRUTH_AND_CLOTHES_IS_NOT_JACKET_CLASS'}
