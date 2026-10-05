from __future__ import annotations
from dataclasses import dataclass
import numpy as np

CLASSIFIER_WITNESS_VERSION="sa7.19-v1"
MODEL_FAMILY="mantasu/glasses-detector"
MODEL_KIND="anyglasses"
MODEL_SIZE="small"
MIN_PRESENT_PROBABILITY=.80

@dataclass(frozen=True)
class EyewearClassifierEvidence:
 probability:float
 present:bool
 observer_role:str="eyewear_classifier"

def bind_classifier_probability(value:float)->EyewearClassifierEvidence:
 p=float(value)
 if not np.isfinite(p) or not 0<=p<=1:raise ValueError("probability must be finite in [0,1]")
 return EyewearClassifierEvidence(p,p>=MIN_PRESENT_PROBABILITY)

def independent_from_region_proposal(evidence:EyewearClassifierEvidence, *, used_region_proposal:bool)->bool:
 # Only source/head-authority crops may act as an independent witness.
 return evidence.present and not used_region_proposal
