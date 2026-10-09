"""SA10.47 fail-closed cross-character research regressions. Private input roots required."""
from pathlib import Path
from xml.etree import ElementTree as ET
import copy
import os
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1047_two_case_visible_optimizer as s

@pytest.fixture
def signed_roots():
    r=os.getenv('SA1047_RADEN_ROOT');g=os.getenv('SA1047_GC001_ROOT')
    if not r or not g:pytest.skip('Frozen private originals absent, not distributed through GitHub')
    return Path(r),Path(g)

def test_two_distinct_source_authorities(signed_roots):
    r,g=(s.load_case(name,path) for name,path in zip(('Raden','GC001'),signed_roots))
    assert r['budget']==1412 and g['budget']==1887
    assert r['overlay_vertices']==12 and g['overlay_vertices']==55
    assert r['historical_stage8_vertices']==2370
    assert g['historical_stage8_vertices']==3604
    assert r['painted']!=g['painted']
    assert len(r['source_input_sha256'])==7 and len(g['source_input_sha256'])==8

def test_declared_masks_and_original_color_group_preservation(signed_roots):
    for kind,path in zip(('Raden','GC001'),signed_roots):
        case=s.load_case(kind,path)
        visible,stat=s.visible_ownership(case)
        out=s.prune_scene(case)
        assert sum(len(x.get('points','').split()) for x in out.iter(s.NS+'polygon'))==case['overlay_vertices']
        assert len(visible)==len(case['painted'])-1
        assert stat['face']['visible_pixels']==0
        if kind=='GC001':
            protected=[n for n in out.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
            assert len(protected)==4
            assert any(len(list(n.iter(s.NS+'polygon')))==5 for n in protected)
        else:
            assert not [n for n in out.iter() if n.get('mask')=='url(#sa1041-protected-clear)']

def test_crosscase_signed_arm_mismatch_not_silently_aliased(signed_roots):
    g=s.load_case('GC001',signed_roots[1]);r=s.load_case('Raden',signed_roots[0])
    for case in (r,g):
        for label in s.PROTECTED:
            n=next(i for i,owner in enumerate(case['records']) if owner['source_mask_owner']==label)
            delta=int(np.count_nonzero(case['masks'][f'sa1041-owner-{n}']!=case['signed'][label]))
            if case['case']=='GC001':assert delta=={'face':0,'left_arm':5,'right_arm':24}[label]
            else:assert delta=={'face':0,'left_arm':0,'right_arm':2}[label]

def test_hard_budget_knapsack_rejects_no_solution():
    options={'a':[{'epsilon':1.0,'vertices':6,'outside_protected_binary_error':0}],
             'b':[{'epsilon':1.0,'vertices':7,'outside_protected_binary_error':1}]}
    assert not s.score(options,12)['feasible']
    result=s.score(options,13)
    assert result['feasible'] and result['candidate_path_and_trim_vertices']==13

def test_budgeted_svg_counts_black_guards_and_color(signed_roots):
    case=s.load_case('Raden',signed_roots[0]);svg=s.prune_scene(case)
    masks,_=s.visible_ownership(case)
    for ident,mask in masks.items():
        d,_=s.vector_path(mask,0.5);s.edge.replace_svg_mask(svg,ident,d)
    d,_=s.vector_path(case['signed']['face'],0.5)
    s.edge.replace_svg_mask(svg,'sa1041-original-face-guard',d)
    expected=s.count_svg(svg,12)['expanded_deployed_vertices']
    mask=next(n for n in svg.iter(s.NS+'mask') if n.get('id') in masks)
    ET.SubElement(mask,s.NS+'rect',{'fill':'#000000','width':'1','height':'1','data-sa1047-protected-trim':'1'})
    assert s.count_svg(svg,12)['expanded_deployed_vertices']==expected+4
    ET.SubElement(mask,s.NS+'circle',{'r':'1'})
    with pytest.raises(ValueError,match='Unaccounted SVG geometry'):s.count_svg(svg,12)

def test_changes_to_source_must_fail_closed(signed_roots,tmp_path):
    from shutil import copy2
    gc=s.gc46.EXPECTED_SHA
    for name in gc:copy2(signed_roots[1]/name,tmp_path/name)
    path=tmp_path/'signed_right_arm_stage04_mask.png'
    path.write_bytes(path.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='hash mismatch'):s.load_case('GC001',tmp_path)

def test_source_output_separation(signed_roots,tmp_path):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(signed_roots[0],signed_roots[1],signed_roots[0])
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(signed_roots[0],signed_roots[0],tmp_path)

def test_two_case_real_chromium_and_strict_no_go(signed_roots,tmp_path):
    report=s.evaluate(*signed_roots,tmp_path)
    a=report['cases']['Raden'];b=report['cases']['GC001']
    assert a['visible_exact_equals_original_exact_chromium']
    assert b['visible_exact_equals_original_exact_chromium']
    assert a['budget_probe']['expanded_deployed_vertices']==1411
    assert a['budget_probe']['dual_gate_pass']
    assert a['budget_probe']['full_chrome']['source_signed_protected']==dict.fromkeys(s.PROTECTED,0)
    assert b['visible_exact']['expanded_deployed_vertices']==5327
    assert b['budget_probe']['expanded_deployed_vertices']==2925
    assert b['budget_probe']['full_chrome']['source_signed_protected']==dict.fromkeys(s.PROTECTED,0)
    assert not b['budget_probe']['dual_gate_pass']
    assert not report['two_case_budget_and_protection_pass']
    assert not report['two_case_source_ring_budget_pass']
    assert report['full_character_golden']=='HOLD' and report['production_deployment']=='UNCHANGED'
    assert (tmp_path/'sa1047_two_case_comparison.png').is_file()
