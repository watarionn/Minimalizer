import importlib.util
import json
import os
from pathlib import Path
import pytest

SRC = Path(__file__).resolve().parents[2] / 'tools/research/c03_stage8_budget_bounds.py'
if not SRC.exists(): SRC = Path(__file__).with_name('c03_stage8_budget_bounds.py')
spec = importlib.util.spec_from_file_location('c03_bounds', SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = Path(os.environ.get('SA1060_C03_SIGNED_DIR', '/__signed_stage8_inputs_not_provided__'))
FILES = {
    'GC001': (BASE / 'phase8_adaptive_source_contour_research.json', BASE / 'phase8_adaptive_metrics.json'),
    'Raden': (BASE / 'phase8_adaptive_source_contour_research_2.json', BASE / 'phase8_adaptive_metrics_2.json'),
}

@pytest.mark.parametrize('case', ['GC001', 'Raden'])
def test_real_signed_cases(case):
    if not FILES[case][0].exists(): pytest.skip('signed source inputs not provided')
    x = mod.inspect_case(case, *FILES[case])
    assert x['ring_vertices'] == mod.SIGNED[case]['ring_vertices']
    assert x['immutable_ring_cap'] == mod.SIGNED[case]['cap']
    assert x['over_cap'] == x['ring_vertices'] - x['immutable_ring_cap']
    assert sum(x['owner_vertices'].values()) == x['ring_vertices']
    assert x['fill_vertices'] + x['hole_vertices'] == x['ring_vertices']
    assert not x['release_authorized'] and not x['production_changed']
    assert not x['original_budget_redefined']
    assert all(not v['legally_removable'] for v in x['scenarios'].values())

@pytest.mark.parametrize('case', ['GC001', 'Raden'])
def test_repeat_deterministic(case):
    if not FILES[case][0].exists(): pytest.skip('signed source inputs not provided')
    a = mod.inspect_case(case, *FILES[case]); b = mod.inspect_case(case, *FILES[case])
    assert a == b

@pytest.mark.parametrize('case', ['GC001', 'Raden'])
def test_signed_scene_tamper_rejected(case, tmp_path):
    if not FILES[case][0].exists(): pytest.skip('signed source inputs not provided')
    scene, metrics = FILES[case]
    bad = tmp_path / 'bad.json'
    bad.write_bytes(scene.read_bytes() + b' ')
    with pytest.raises(ValueError, match='SCENE_PIN_FAIL'):
        mod.inspect_case(case, bad, metrics)

@pytest.mark.parametrize('case', ['GC001', 'Raden'])
def test_metrics_tamper_rejected(case, tmp_path):
    if not FILES[case][0].exists(): pytest.skip('signed source inputs not provided')
    scene, metrics = FILES[case]
    j = json.loads(metrics.read_text())
    j['candidate_vertices']['ring_vertices'] += 1
    bad = tmp_path / 'bad_metrics.json'
    bad.write_text(json.dumps(j))
    with pytest.raises(ValueError, match='METRICS_PIN_FAIL'):
        mod.inspect_case(case, scene, bad)

def test_unknown_case_rejected():
    with pytest.raises(ValueError, match='UNKNOWN_CASE'):
        mod.inspect_case('UNKNOWN', *FILES['GC001'])

def test_no_source_geometry_written():
    t = SRC.read_text()
    assert 'scene_mutated\': False' in t
    assert 'release_authorized\': False' in t


def test_synthetic_budget_counterfactuals():
    x = mod.counterfactual_bounds([1, 2, 3, 17], 8, 3)
    assert x['all_rings_le_2']['remaining_vertices'] == 20
    assert x['all_rings_le_16']['remaining_vertices'] == 17
    assert x['all_holes']['still_over_cap'] == 12
    assert all(not v['legally_removable'] for v in x.values())

@pytest.mark.parametrize('rings,cap,holes', [([], 10, 0), ([0, 3], 2, 0), ([3], 0, 0), ([3], 1, 4)])
def test_synthetic_invalid_input_rejected(rings, cap, holes):
    with pytest.raises(ValueError): mod.counterfactual_bounds(rings, cap, holes)
