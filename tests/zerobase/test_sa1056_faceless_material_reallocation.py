"""SA10.56 private signed material expansion tests; research must remain faceless."""
from __future__ import annotations
import os, sys, hashlib, shutil, copy
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1056_faceless_material_reallocation as s

@pytest.fixture
def signed():
    names=('SA1056_RADEN_ROOT','SA1056_GC001_ROOT','SA1056_RADEN_BASE','SA1056_GC001_BASE')
    vals=[os.environ.get(k) for k in names]
    if not all(vals):pytest.skip('Signed private 7+8 original files, two private faceless SVGs not public')
    return [Path(x) for x in vals]

def test_signed_source_and_baselines(signed):
    for name,root,path in zip(s.CASES,signed[:2],signed[2:]):
        data,case,svg=s.signed_case(name,root,path)
        assert s.sign(path)==s.BASE_SHA[name]
        assert data['photo'].shape==(340,340,3)
        assert s.previous.audit_default_faceless(svg)
        assert s.actual_svg_vertices(svg,case)==s.BASE_COUNT[name]

def test_signed_svg_tamper_denied(signed,tmp_path):
    bad=tmp_path/'altered.svg';bad.write_bytes(signed[2].read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='SA1055_SIGNED_BASELINE_SHA_MISMATCH'):
        s.signed_case('Raden',signed[0],bad)

def test_signed_source_tamper_denied(signed,tmp_path):
    required=s.previous.previous.prev.last.prior.prior.dual.CASES['GC001']['root_required']
    for name in required:shutil.copy2(signed[1]/name,tmp_path/name)
    (tmp_path/'GC001_source.png').write_bytes((tmp_path/'GC001_source.png').read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.signed_case('GC001',tmp_path,signed[3])

def test_material_color_truly_in_signed_original(signed):
    for name,root,path in zip(s.CASES,signed[:2],signed[2:]):
        data,case,svg=s.signed_case(name,root,path)
        visible,_=s.foreground_masks(case,data['masks']['face'])
        for role in s.ROLES:
            idx=next(i for i,r in enumerate(case['records']) if r['source_mask_owner']==role)
            mask=visible[f'sa1041-owner-{idx}']
            results=s.role_color_proposals(role,data['photo'],mask)
            assert results and all(r['vertices']>=3 for r in results)
            assert all(np.any(np.all(data['photo'][mask]==r['rgb'],axis=1)) for r in results)

def test_new_paths_accounted_by_true_svg_vertices(signed):
    data,case,svg=s.signed_case('Raden',signed[0],signed[2])
    visible,_=s.foreground_masks(case,data['masks']['face'])
    p=s.role_color_proposals('hair',data['photo'],visible['sa1041-owner-1'])[0]
    out=s.add_layer(svg,case,'hair',p)
    assert s.actual_svg_vertices(out,case)==s.BASE_COUNT['Raden']+p['vertices']
    assert s.previous.audit_default_faceless(out)
    assert s.protected_inventory(out)[0]==s.protected_inventory(svg)[0]
    assert s.protected_inventory(out)[1:]==s.protected_inventory(svg)[1:]
    assert s.previous.face_guard(out) is not s.previous.face_guard(svg)

def test_reject_extra_eyes_and_wrong_owner(signed):
    _,case,svg=s.signed_case('Raden',signed[0],signed[2])
    bad=copy.deepcopy(svg)
    ET.SubElement(s.previous.face_guard(bad),s.NS+'path',{'d':'M 1 1 L 2 2 L 3 2 Z'})
    with pytest.raises(ValueError,match='FACIAL_FEATURE_PAINT_FORBIDDEN'):
        s.previous.audit_default_faceless(bad)
    with pytest.raises(StopIteration):
        s.add_layer(svg,case,'nonexistent',{'path':'M 1 1 L 2 2 L 3 2 Z','rgb':(0,0,0)})

def test_refuse_source_output_overwrites(signed):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*signed,signed[0])
    with pytest.raises(ValueError,match='overwrite'):
        s.evaluate(*signed,signed[2].parent)

def test_real_chromium_dual_source_material_quality(signed,tmp_path):
    rep=s.evaluate(*signed,tmp_path)
    assert rep['two_case_faceless_preserved'] is True
    assert rep['two_case_source_fidelity_improved'] is True
    assert rep['full_character_golden']=='HOLD'
    assert rep['production_deployment']=='UNCHANGED'
    for name,baseline,limit in [('Raden',1309,1412),('GC001',1710,1887)]:
        c=rep['cases'][name]
        assert baseline<c['expanded_vertices_final']<=limit
        assert c['actual_added_vertices']==sum(a['vertices'] for a in c['material_layers_accepted'])
        assert c['rendered_original_source_foreground_mae_after']<c['rendered_original_source_foreground_mae_before']
        assert c['face_changed_pixels']==c['both_arms_changed_pixels']==c['outside_source_visible_changed_pixels']==0
        assert c['tested_chromium_proposals']>0
        assert {q['role'] for q in c['material_layers_accepted']}==set(s.ROLES)
        svg=ET.parse(tmp_path/f'{name.lower()}_faceless_material.svg').getroot()
        assert s.previous.audit_default_faceless(svg)
        assert not [n for n in svg.iter() if n.tag in (s.NS+'image',s.NS+'foreignObject',s.NS+'feImage')]
    assert (tmp_path/'sa1056_two_case_material_board.png').is_file()
    assert '"path"' not in (tmp_path/'sa1056_metrics.json').read_text()

def test_only_research_stage_remains_not_deployed():
    assert s.CASES==('Raden','GC001')
    assert s.BASE_COUNT['Raden']<s.CAP['Raden']
    assert s.BASE_COUNT['GC001']<s.CAP['GC001']
