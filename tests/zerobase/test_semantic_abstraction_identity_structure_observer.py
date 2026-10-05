import numpy as np
import cv2

from minimalizer_zerobase.semantic_abstraction.identity_structure_observer import observe_identity_structures
from minimalizer_zerobase.semantic_abstraction.identity_binding import bind_observed_identity_structures
from minimalizer_zerobase.semantic_abstraction.ir import AbstractionPlan, AbstractionPolicy, SemanticPart, VisualRole


def _plan(policy=AbstractionPolicy.SIMPLIFY, role=VisualRole.SILHOUETTE):
    return AbstractionPlan(parts=(SemanticPart(id="head",category="head",confidence=.9,visual_role=role,abstraction_policy=policy),))


def test_observer_finds_coherent_internal_structure_without_semantic_authority():
    rgb=np.full((80,80,3),180,np.uint8); mask=np.zeros((80,80),bool);mask[10:70,10:70]=1
    cv2.rectangle(rgb,(20,25),(60,38),(20,20,20),2)
    evidence=observe_identity_structures(rgb,mask)
    assert evidence
    assert evidence[0].confidence >= .55


def test_semantic_parent_must_authorize_observer_evidence():
    rgb=np.full((80,80,3),180,np.uint8); mask=np.zeros((80,80),bool);mask[10:70,10:70]=1
    cv2.rectangle(rgb,(20,25),(60,38),(20,20,20),2)
    evidence=observe_identity_structures(rgb,mask)
    assert bind_observed_identity_structures(_plan(), "head", evidence)
    assert bind_observed_identity_structures(_plan(AbstractionPolicy.SUPPRESS), "head", evidence) == ()


def test_internal_detail_parent_cannot_promote_identity_structure():
    rgb=np.full((80,80,3),180,np.uint8); mask=np.ones((80,80),bool)
    cv2.line(rgb,(10,30),(70,30),(0,0,0),3)
    evidence=observe_identity_structures(rgb,mask)
    assert bind_observed_identity_structures(_plan(role=VisualRole.INTERNAL_DETAIL), "head", evidence) == ()
