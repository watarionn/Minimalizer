from minimalizer_zerobase.refine.ab import ABCase, evaluate_ab
from minimalizer_zerobase.refine.objective import objective

def row(case_id, before_total_good=True, *, guard=True, deterministic=True):
    before=objective(silhouette_iou=.95,palette=.1,semantic=.1,primitive_count=2,tiny_shape_ratio=.1,complexity=.2)
    after=objective(silhouette_iou=.96 if before_total_good else .94,palette=.08,semantic=.08,primitive_count=2,tiny_shape_ratio=.08,complexity=.18)
    return ABCase(case_id,before,after,1.0,1.0,guard,deterministic)

def test_corpus_adopts_only_when_every_case_is_safe_and_improved():
    result=evaluate_ab((row("a"),row("b")))
    assert result.decision == "ADOPT"
    assert result.accepted == 2

def test_one_regression_holds_whole_corpus():
    result=evaluate_ab((row("a"),row("b",False)))
    assert result.decision == "HOLD"
    assert result.regressed == 1

def test_regional_or_determinism_failure_holds():
    assert evaluate_ab((row("a",guard=False),)).decision == "HOLD"
    assert evaluate_ab((row("a",deterministic=False),)).decision == "HOLD"
