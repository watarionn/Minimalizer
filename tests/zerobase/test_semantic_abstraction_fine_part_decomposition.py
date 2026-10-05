import cv2
import numpy as np

from minimalizer_zerobase.semantic_abstraction.fine_part_decomposition import (
    FINE_IDENTITY_CATEGORIES, FinePartProposal, observe_fine_identity_parts, promote_fine_identity_parts, validate_fine_part_proposal,
)
from minimalizer_zerobase.semantic_abstraction.ir import AbstractionPlan,AbstractionPolicy,SemanticPart,VisualRole


def _fixture():
    rgb=np.full((120,100,3),220,np.uint8)
    masks={n:np.zeros((120,100),bool) for n in ("head","hair","face","major_clothing","accessory_or_held_object")}
    masks["head"][5:65,20:80]=1; masks["hair"][3:70,15:85]=1; masks["face"][30:62,32:68]=1
    masks["major_clothing"][65:115,18:82]=1; masks["accessory_or_held_object"][72:88,75:92]=1
    rgb[24:34,24:76]=(35,45,55)
    rgb[68:83,44:56]=(80,210,45)
    return rgb,masks


def _plan(policy=AbstractionPolicy.PRESERVE):
    return AbstractionPlan(parts=tuple(SemanticPart(id=n,category=n,confidence=.9,visual_role=VisualRole.IDENTITY_ACCENT,abstraction_policy=policy) for n in ("head","hair","face","major_clothing","accessory_or_held_object")))


def test_fine_categories_are_explicit_contract():
    assert set(("eyewear","headwear","hair_front","hair_side","collar","tie_or_neckwear","major_accessory")) <= set(FINE_IDENTITY_CATEGORIES)


def test_observer_proposes_identity_parts_without_authority():
    rgb,masks=_fixture(); rows=observe_fine_identity_parts(rgb,masks)
    cats={r.category for r in rows}
    assert "eyewear" in cats
    assert "hair_front" in cats
    assert "major_accessory" in cats


def test_promotion_creates_required_identity_semantic_parts():
    rgb,masks=_fixture(); promoted=promote_fine_identity_parts(_plan(),observe_fine_identity_parts(rgb,masks))
    parts={p.category:p for p in promoted.parts}
    assert parts["eyewear"].parent=="head"
    assert parts["eyewear"].visual_role is VisualRole.IDENTITY_ACCENT
    assert parts["eyewear"].abstraction_policy is AbstractionPolicy.PRESERVE
    assert parts["eyewear"].geometry_constraints.min_primitives==1


def test_suppressed_parent_blocks_observer_promotion():
    mask=np.ones((20,20),bool)
    proposal=FinePartProposal("eyewear","head",mask,.99,"observer:test")
    plan=AbstractionPlan(parts=(SemanticPart(id="head",category="head",abstraction_policy=AbstractionPolicy.SUPPRESS),))
    assert len(promote_fine_identity_parts(plan,(proposal,)).parts)==1


def test_unknown_category_is_not_silently_promoted():
    mask=np.ones((20,20),bool)
    proposal=FinePartProposal("mystery","head",mask,.99,"observer:test")
    plan=AbstractionPlan(parts=(SemanticPart(id="head",category="head",abstraction_policy=AbstractionPolicy.PRESERVE),))
    assert len(promote_fine_identity_parts(plan,(proposal,)).parts)==1


def test_validation_rejects_proposal_outside_parent_authority():
    parent=np.zeros((30,30),bool);parent[10:20,10:20]=1
    mask=np.zeros((30,30),bool);mask[0:8,0:8]=1
    ok,reason=validate_fine_part_proposal(FinePartProposal("eyewear","head",mask,.9,"e"),parent)
    assert not ok and reason=="outside_parent"


def test_eyewear_must_be_structurally_near_face():
    parent=np.ones((60,60),bool);face=np.zeros((60,60),bool);face[35:50,20:40]=1
    mask=np.zeros((60,60),bool);mask[2:10,2:18]=1
    ok,reason=validate_fine_part_proposal(FinePartProposal("eyewear","head",mask,.9,"e"),parent,face_mask=face)
    assert not ok and reason=="not_near_face"
