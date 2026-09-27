import pytest
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.evaluation import (
    Approved78Binding, ApprovedReference, CalibrationCase,
    Approved78CalibrationHarness, CalibrationTargets, load_approved78_binding,
)
from minimalizer_zerobase.geometry import PrimitiveCandidate
from minimalizer_zerobase.optimize import GeometryObjectivePolicy
from minimalizer_zerobase.scene.models import Region, Scene

def refs():
    return tuple(ApprovedReference(
        i, f"ref-{i:02d}", f"{i:02d}_APPROVED_GEOMETRIC_REFERENCE.png",
        f"artifacts/approved78/{i:02d}/scene.json",
        f"artifacts/approved78/{i:02d}/candidates.json",
    ) for i in range(1, 79))

def case(reference):
    scene = Scene(CoordinateSpace(100,100), "fixture", "1",
                  regions=(Region("coat","coat",geometry={"bbox":[10,10,50,70]}),))
    candidates = (
        PrimitiveCandidate("simple","rectangle","coat",{},{
            "coverage":.91,"silhouette":.90,"complexity":3,"angularity":.9}),
        PrimitiveCandidate("complex","convex_polygon","coat",{},{
            "coverage":.99,"silhouette":.98,"complexity":8,"angularity":.65}),
    )
    return CalibrationCase(reference, scene, candidates)

def test_binding_is_fixed_to_exact_78_and_saved_artifacts():
    binding = Approved78Binding(refs())
    binding.validate()
    with pytest.raises(ValueError, match="exactly 78"):
        Approved78Binding(refs()[:-1]).validate()

def test_baseline_reports_independent_dimensions():
    binding = Approved78Binding(refs())
    metrics = Approved78CalibrationHarness(binding).evaluate((case(refs()[0]),))
    assert metrics.case_count == 1
    assert metrics.region_count == 1
    assert 0 <= metrics.mean_coverage <= 1
    assert 0 <= metrics.mean_silhouette <= 1
    assert metrics.mean_complexity >= 0
    assert 0 <= metrics.mean_angularity <= 1
    assert 0 <= metrics.mean_semantic_cost <= 1
    assert set(metrics.primitive_type_rates)

def test_calibration_prefers_policy_closer_to_approved_simplicity_targets():
    binding = Approved78Binding(refs())
    harness = Approved78CalibrationHarness(binding, CalibrationTargets(max_mean_complexity=4.0))
    faithful = GeometryObjectivePolicy(complexity_weight=.01)
    simple = GeometryObjectivePolicy(complexity_weight=.5)
    result = harness.calibrate((case(refs()[0]),), (faithful, simple))
    assert result.policy == simple
    assert result.metrics.mean_complexity == 3

def test_unbound_duplicate_and_empty_cases_fail_closed():
    binding = Approved78Binding(refs())
    harness = Approved78CalibrationHarness(binding)
    foreign = ApprovedReference(1,"other","other.png","s.json","c.json")
    with pytest.raises(ValueError, match="canonical"):
        harness.evaluate((case(foreign),))
    c = case(refs()[0])
    with pytest.raises(ValueError, match="duplicate"):
        harness.evaluate((c,c))
    with pytest.raises(ValueError, match="requires candidates"):
        harness.evaluate((CalibrationCase(refs()[0], c.scene, ()),))


def test_repository_manifest_binds_all_canonical_reference_filenames():
    binding = load_approved78_binding("docs/zerobase/approved78_manifest.json")
    assert len(binding.references) == 78
    assert binding.references[0].reference_filename == "01_Kikirara-Vivi_APPROVED_GEOMETRIC_REFERENCE.png"
    assert binding.references[-1].reference_filename == "78_Murasaki-Shion_APPROVED_GEOMETRIC_REFERENCE_20260918.png"
