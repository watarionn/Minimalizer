"""Read-only signed source-ring exact pixel feasibility tests."""
import json
import os
from pathlib import Path
import pytest
import importlib.util
import sys
TOOL=Path(__file__).resolve().parents[2]/'tools/research'
if not (TOOL/'c03_exact_vertex_prune.py').exists(): TOOL=Path(__file__).parent
sys.path.insert(0,str(TOOL))
spec=importlib.util.spec_from_file_location('c03_exact_vertex_prune',TOOL/'c03_exact_vertex_prune.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

SIGNED_DIR=Path(os.getenv('SA1060_C03_SIGNED_DIR','/__private_stage8_unavailable__'))
FILES={'GC001':SIGNED_DIR/'phase8_adaptive_source_contour_research.json',
       'Raden':SIGNED_DIR/'phase8_adaptive_source_contour_research_2.json'}

def test_collinear_existing_vertex_removed():
    p=[[0,0],[2,0],[4,0],[4,4],[0,4]]
    q=s.greedy_prune(p)
    assert len(q)==4
    assert s.parity_masks(p,q)

def test_sharp_corner_retained():
    p=[[0,0],[4,0],[4,4],[0,4]]
    q=s.greedy_prune(p)
    assert len(q)==4
    assert s.parity_masks(p,q)

def test_noninteger_corner_retained_when_two_x_differs():
    p=[[0,0],[3,0],[3,3],[2,2],[0,3]]
    q=s.greedy_prune(p)
    assert s.parity_masks(p,q)
    assert len(q)>=4

def test_degenerate_ring_untouched():
    assert s.greedy_prune([[1,1]])==[[1,1]]
    assert s.greedy_prune([[1,1],[2,2]])==[[1,1],[2,2]]
    assert s.greedy_prune([[1,1],[2,2],[3,3]])==[[1,1],[2,2],[3,3]]

def test_unknown_case_rejected():
    with pytest.raises(ValueError,match='UNKNOWN_CASE'):
        s.load('unknown',Path('/missing'))

def test_wrong_scene_rejected(tmp_path):
    f=tmp_path/'fake.json';f.write_text('{}')
    with pytest.raises(ValueError,match='SCENE_PIN_FAIL'):
        s.load('GC001',f)

@pytest.mark.parametrize('case',["GC001","Raden"])
def test_real_signed_case_and_repeat(case):
    if not FILES[case].exists():pytest.skip('signed source not provided')
    a=s.audit(case,FILES[case]);b=s.audit(case,FILES[case])
    assert a==b
    assert a['original_vertices']==s.SIGNED[case]['ring_vertices']
    assert a['original_over_cap']>0
    assert sum(x['before'] for x in a['by_owner'].values())==a['original_vertices']
    assert sum(x['after'] for x in a['by_owner'].values())==a['strict_pruned_vertices']
    assert a['candidate_over_cap']>0
    assert not a['release_authorized'] and not a['production_changed']
    assert a['whole_scene_chromium']=='NOT_RUN'

@pytest.mark.parametrize('case',["GC001","Raden"])
def test_tampered_signed_case_rejected(case,tmp_path):
    if not FILES[case].exists():pytest.skip('signed source not provided')
    bad=tmp_path/'bad.json';bad.write_bytes(FILES[case].read_bytes()+b' ')
    with pytest.raises(ValueError,match='SCENE_PIN_FAIL'):
        s.audit(case,bad)
