import numpy as np

from minimalizer_zerobase.semantic_abstraction.identity_binding import (
    bind_required_identity_features,
    required_identity_budget,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan, AbstractionPolicy, GeometryConstraints, SemanticPart, VisualRole,
)


def part(pid, role=VisualRole.IDENTITY_ACCENT, policy=AbstractionPolicy.PRESERVE, minimum=0):
    return SemanticPart(
        id=pid, category=pid, confidence=.9, visual_role=role,
        abstraction_policy=policy,
        geometry_constraints=GeometryConstraints(min_primitives=minimum),
    )


def test_required_roles_reserve_minimum_before_optional_geometry():
    mask=np.zeros((40,40),bool); mask[5:20,5:20]=1
    plan=AbstractionPlan(parts=(part("hair", minimum=2),part("major_clothing"),part("accessory_or_held_object")))
    bindings=bind_required_identity_features(plan,{"hair":mask,"major_clothing":mask,"accessory_or_held_object":mask})
    assert [b.semantic_role for b in bindings] == ["major_accessory","major_hair_front","major_clothing_identity"]
    assert required_identity_budget(bindings) >= 4


def test_suppressed_semantic_part_cannot_reserve_geometry():
    mask=np.ones((20,20),bool)
    plan=AbstractionPlan(parts=(part("accessory_or_held_object",policy=AbstractionPolicy.SUPPRESS),))
    assert bind_required_identity_features(plan,{"accessory_or_held_object":mask}) == ()


def test_color_change_does_not_change_identity_binding():
    mask=np.zeros((32,32),bool);mask[4:20,7:24]=1
    plan=AbstractionPlan(parts=(part("hair"),))
    a=bind_required_identity_features(plan,{"hair":mask})
    b=bind_required_identity_features(plan,{"hair":mask.copy()})
    assert [(x.semantic_role,x.min_primitives,x.max_primitives,x.mask.tolist()) for x in a] == [(x.semantic_role,x.min_primitives,x.max_primitives,x.mask.tolist()) for x in b]


def test_unknown_unbound_part_does_not_invent_identity():
    mask=np.ones((16,16),bool)
    plan=AbstractionPlan(parts=(part("unknown"),))
    assert bind_required_identity_features(plan,{"unknown":mask}) == ()
