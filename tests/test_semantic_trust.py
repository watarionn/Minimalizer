from minimalizer_zerobase.refine.semantic_trust import SemanticTrustPolicy
def test_face_is_tightest_identity_region():
    p=SemanticTrustPolicy()
    assert p.face < p.limb < p.hair < p.major_clothing
def test_unknown_part_fails_to_conservative_default():
    p=SemanticTrustPolicy()
    assert p.radius_for("unknown")==p.default
def test_face_radius_is_subpixel():
    assert SemanticTrustPolicy().radius_for("face") < 1.0
