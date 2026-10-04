from minimalizer_zerobase.refine import AcceptancePolicy, accept_candidate, cosine_loss, objective

def test_semantic_cosine_loss_is_zero_for_same_direction():
    assert cosine_loss([1,2,3],[2,4,6]) == 0.0

def test_complexity_reduction_can_win_without_identity_regression():
    before=objective(silhouette_iou=.94,palette=.08,semantic=.08,primitive_count=12,tiny_shape_ratio=.20,complexity=20)
    after=objective(silhouette_iou=.945,palette=.08,semantic=.06,primitive_count=9,tiny_shape_ratio=.08,complexity=14)
    assert after.total < before.total
    assert accept_candidate(before=before,after=after,identity_ratio=.99,silhouette_ratio=.995)

def test_better_total_is_rejected_when_identity_guard_fails():
    before=objective(silhouette_iou=.94,palette=.1,semantic=.1,primitive_count=12,tiny_shape_ratio=.2,complexity=20)
    after=objective(silhouette_iou=.95,palette=.05,semantic=.05,primitive_count=5,tiny_shape_ratio=.01,complexity=8)
    assert not accept_candidate(before=before,after=after,identity_ratio=.96,silhouette_ratio=.995,
                                policy=AcceptancePolicy(min_identity_ratio=.985))
