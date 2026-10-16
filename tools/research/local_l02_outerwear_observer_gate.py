"""L02 source-bound, taxonomy-exact outerwear observer admission, research only.

The observer sees only an independently-produced class-map and signed source alpha.
Human labels are for evaluation in a separate function, not prediction or ownership.
A general 'clothes' class MUST NOT masquerade as outerwear. No production hook.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re
from typing import Mapping
import numpy as np

OUTERWEAR = frozenset({
    'jacket', 'coat', 'short_sleeve_outwear', 'long_sleeve_outwear',
    'short_sleeved_outwear', 'long_sleeved_outwear',
})
GENERIC = frozenset({
    'clothes', 'clothing', 'upper_clothes', 'upper_clothing', 'upper',
    'sleeve', 'collar', 'lapel', 'shirt', 'top', 'cardigan', 'dress',
})

class AuthorityHold(ValueError):
    pass

def _canonical(label: str) -> str:
    if not isinstance(label, str):
        raise AuthorityHold('invalid class label')
    return re.sub(r'[^a-z0-9]+', '_', label.strip().lower()).strip('_')

@dataclass(frozen=True)
class ObserverSpec:
    model_id: str
    model_sha256: str
    source_sha256: str
    class_map_sha256: str
    label_map: Mapping[int, str]
    source_kind: str = 'INDEPENDENT_PRETRAINED_MODEL'

def source_only_candidate(alpha: np.ndarray, classids: np.ndarray, spec: ObserverSpec):
    """Inference-side contract. No manual labels/vertices/ROI input whatsoever."""
    if (alpha.ndim != 2 or classids.shape != alpha.shape or
        alpha.dtype != np.dtype(bool) or classids.dtype != np.dtype('uint8')):
        raise AuthorityHold('INVALID_SOURCE_OR_CLASS_GEOMETRY')
    if not spec.model_id or spec.source_kind != 'INDEPENDENT_PRETRAINED_MODEL':
        raise AuthorityHold('INVALID_OBSERVER_PROVENANCE')
    if any(not isinstance(d, str) or not re.fullmatch('[0-9a-f]{64}', d) for d in
           (spec.model_sha256, spec.source_sha256, spec.class_map_sha256)):
        raise AuthorityHold('UNSIGNED_OBSERVER_OR_SOURCE')
    if hashlib.sha256(classids.tobytes()).hexdigest() != spec.class_map_sha256:
        raise AuthorityHold('CLASS_MAP_SHA_MISMATCH')
    if len(spec.label_map) < 2 or any(not isinstance(k,int) or k < 0 or k > 255
                                      for k in spec.label_map):
        raise AuthorityHold('INVALID_CLASS_REGISTRY')
    classes = {_canonical(label):code for code,label in spec.label_map.items()}
    if len(classes) != len(spec.label_map):
        raise AuthorityHold('DUPLICATE_CLASS_NAMES')
    if not set(np.unique(classids)).issubset(set(spec.label_map)):
        raise AuthorityHold('UNKNOWN_PREDICTED_CLASS')
    specific = sorted(code for label,code in classes.items() if label in OUTERWEAR)
    all_clothes = sorted(code for label,code in classes.items() if label in GENERIC)
    if not specific:
        return np.zeros(alpha.shape, dtype=bool), {
            'status': 'ABSTAIN_NO_OUTERWEAR_CLASS',
            'reason': 'generic clothes/upper clothes do not distinguish an outer layer',
            'specialized_classes': [],
            'generic_class_codes': all_clothes,
            'candidate_source_px': 0,
            'source_pixels_generated': 0,
            'owner_promotion_authorized': False,
        }
    candidate = alpha & np.isin(classids, specific)
    return candidate, {
        'status': 'RESEARCH_CANDIDATE_NOT_AUTHORIZED',
        'specialized_classes': specific,
        'generic_class_codes': all_clothes,
        'candidate_source_px': int(candidate.sum()),
        'source_pixels_generated': 0,
        'owner_promotion_authorized': False,
    }

def known_only_evaluation(alpha, positive, negative, candidate):
    """Evaluation-only function: explicit negatives; unknown stays unscored."""
    masks = (alpha, positive, negative, candidate)
    if any(m.ndim != 2 or m.dtype != bool or m.shape != alpha.shape for m in masks):
        raise AuthorityHold('INVALID_EVALUATION_MASKS')
    if np.any((positive | negative | candidate) & ~alpha):
        raise AuthorityHold('OUTSIDE_SIGNED_ALPHA')
    if np.any(positive & negative):
        raise AuthorityHold('OVERLAPPING_HUMAN_CLASSES')
    tp=int((candidate&positive).sum());fp=int((candidate&negative).sum());fn=int((~candidate&positive).sum())
    unknown=alpha&~(positive|negative)
    return {
        'known_only_iou':round(tp/max(1,tp+fp+fn),6),
        'positive_recall':round(tp/max(1,tp+fn),6),
        'known_negative_fp_rate':round(fp/max(1,int(negative.sum())),6),
        'unknown_predicted_px':int((candidate&unknown).sum()),
        'unknown_source_px':int(unknown.sum()),
        'known_positive_px':int(positive.sum()),
        'known_negative_px':int(negative.sum()),
        'candidate_source_px':int(candidate.sum()),
        'tp':tp,'fp_known':fp,'fn':fn,
        'unknown_are_negative':False,
    }
