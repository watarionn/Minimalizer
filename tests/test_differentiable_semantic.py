from minimalizer_zerobase.refine.semantic import SemanticObservation, semantic_feature_loss, identity_ratio_from_loss
from minimalizer_zerobase.refine.dinov3_observer import DinoV3Observer, DinoV3Unavailable

def test_identical_features_have_zero_loss():
    obs = SemanticObservation((1.0, 0.0), ((1.0, 0.0), (0.0, 1.0)))
    assert semantic_feature_loss(obs, obs) == 0.0
    assert identity_ratio_from_loss(0.0) == 1.0

def test_semantic_loss_prefers_closer_candidate():
    ref = SemanticObservation((1.0, 0.0))
    close = SemanticObservation((0.9, 0.1))
    far = SemanticObservation((0.0, 1.0))
    assert semantic_feature_loss(ref, close) < semantic_feature_loss(ref, far)

def test_observer_is_read_only_from_callers_perspective():
    image = {"pixels": [1, 2, 3]}
    before = list(image["pixels"])
    observer = DinoV3Observer(lambda _: SemanticObservation((1.0, 0.0)))
    observer.observe(image)
    assert image["pixels"] == before

def test_dinov3_is_optional_and_fails_closed():
    try:
        DinoV3Observer()
    except DinoV3Unavailable as exc:
        assert "optional" in str(exc)
    else:
        raise AssertionError("expected DinoV3Unavailable")


def test_patch_damage_can_fail_existing_identity_gate():
    from minimalizer_zerobase.refine.objective import LossBreakdown
    from minimalizer_zerobase.refine.semantic import accept_with_semantic_observation
    before=LossBreakdown(0,0,0,0,0,0,2.0)
    after=LossBreakdown(0,0,0,0,0,0,1.0)
    ref=SemanticObservation((1.,0.),((1.,0.),(0.,1.)))
    damaged=SemanticObservation((1.,0.),((0.,1.),(0.,1.)))
    assert not accept_with_semantic_observation(before=before,after=after,reference=ref,candidate=damaged,silhouette_ratio=1.0)

def test_semantically_preserved_improvement_can_pass_gate():
    from minimalizer_zerobase.refine.objective import LossBreakdown
    from minimalizer_zerobase.refine.semantic import accept_with_semantic_observation
    before=LossBreakdown(0,0,0,0,0,0,2.0)
    after=LossBreakdown(0,0,0,0,0,0,1.0)
    ref=SemanticObservation((1.,0.),((1.,0.),(0.,1.)))
    same=SemanticObservation((1.,0.),((1.,0.),(0.,1.)))
    assert accept_with_semantic_observation(before=before,after=after,reference=ref,candidate=same,silhouette_ratio=1.0)
