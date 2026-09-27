from minimalizer_zerobase.evaluation import MigrationGate

def capture():
    return {
        "case_count": 78,
        "all_source_sha256_verified": True,
        "all_replay_deterministic": True,
    }

def comparison(z_iou=0.50, l_iou=0.49, z_fg=0.20, l_fg=0.21):
    return {"all_reference_sha256_verified": True, "aggregate": {
        "zerobase_mean_silhouette_iou": z_iou,
        "legacy2_mean_silhouette_iou": l_iou,
        "zerobase_mean_foreground_ratio_error": z_fg,
        "legacy2_mean_foreground_ratio_error": l_fg,
    }}

def test_migration_gate_authorizes_only_non_regressing_complete_evidence():
    result = MigrationGate().evaluate(capture(), comparison())
    assert result.switch_authorized
    assert result.reasons == ()
def test_migration_gate_holds_on_visual_regression():
    result = MigrationGate().evaluate(
        capture(), comparison(z_iou=0.39, l_iou=0.41, z_fg=0.54, l_fg=0.46)
    )
    assert not result.switch_authorized
    assert len(result.reasons) == 2

def test_migration_gate_holds_on_incomplete_replay_evidence():
    bad = capture()
    bad["case_count"] = 77
    bad["all_replay_deterministic"] = False
    result = MigrationGate().evaluate(bad, comparison())
    assert not result.switch_authorized
    assert any("77/78" in reason for reason in result.reasons)
    assert any("non-deterministic" in reason for reason in result.reasons)
