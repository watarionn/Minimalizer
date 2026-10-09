"""SA10.57 immutable source-body structure and real Chromium boundary regression."""
from pathlib import Path
from xml.etree import ElementTree as ET
import copy,hashlib,os,shutil,sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1057_structure_boundary_guard as s

@pytest.fixture
def signed():
    env=('SA1057_RADEN_ROOT','SA1057_GC001_ROOT','SA1057_RADEN_BASE','SA1057_GC001_BASE')
    vals=[os.getenv(v) for v in env]
    if not all(vals):pytest.skip('Private signed originals and SVGs required')
    return [Path(v) for v in vals]

def test_authenticated_two_sources_and_svg_counts(signed):
    for name,root,ref in zip(s.CASES,signed[:2],signed[2:]):
        data,case,svg=s.signed_case(name,root,ref)
        assert data['photo'].shape==(340,340,3)
        assert s.prior.sign(ref)==s.BASE_SHA[name]
        assert s.prior.actual_svg_vertices(svg,case)==s.BASE_VERT[name]
        assert s.prior.previous.audit_default_faceless(svg)

def test_reject_modified_source(signed,tmp_path):
    needed=s.prior.previous.previous.prev.last.prior.prior.dual.CASES['GC001']['root_required']
    for n in needed:shutil.copy2(signed[1]/n,tmp_path/n)
    f=tmp_path/'GC001_source.png';f.write_bytes(f.read_bytes()+b'bad')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.signed_case('GC001',tmp_path,signed[3])

def test_reject_modified_svg(signed,tmp_path):
    f=tmp_path/'wrong.svg';f.write_bytes(signed[2].read_bytes()+b'bad')
    with pytest.raises(ValueError,match='SA1056_SIGNED_SVG_SHA_MISMATCH'):
        s.signed_case('Raden',signed[0],f)

def test_owner_adjacency_has_exact_nonoverlap(signed):
    for name,root,ref in zip(s.CASES,signed[:2],signed[2:]):
        data,case,svg=s.signed_case(name,root,ref)
        v,fg,guard,meta=s.guard_masks(data,case)
        t=s.owner_topology(case,v)
        assert t['owner_count']==9
        assert t['source_visible_owner_overlap_pixels']==0
        assert len(t['adjacency_pairs'])>8
        assert all(isinstance(k,list) and len(k)==2 for k in t['adjacency_pairs'])
        assert np.all(guard[data['masks']['face']])
        assert np.all(guard[data['masks']['left_arm']])
        assert np.all(guard[data['masks']['right_arm']])
        assert np.all(guard[~fg])
        assert meta['perimeter_pixel_count']>1000

def test_source_gradient_candidates_only_on_existing_material_paths(signed):
    for name,root,ref in zip(s.CASES,signed[:2],signed[2:]):
        data,case,svg=s.signed_case(name,root,ref)
        vis,fg,forbidden,meta=s.guard_masks(data,case)
        for role in s.ROLE_ORDER:
            index=next(i for i,c in enumerate(case['records']) if c['source_mask_owner']==role)
            owner=vis[f'sa1041-owner-{index}']
            node,points=s.select_vertices(svg,role,owner&~forbidden,data['photo'],limit=5)
            assert node.get('data-sa1056-material')==role
            assert len(points)<=5
            assert all(p[0]<=0 and p[1]>=0 for p in points)

def test_unchanged_signed_geometry_inventory_exposes_tampering(signed):
    _,_,svg=s.signed_case('Raden',signed[0],signed[2])
    a=s.inventory(svg);changed=copy.deepcopy(svg)
    node=next(n for n in changed.iter(s.NS+'path') if n.get('data-sa1056-material'))
    old=node.get('d');match=s.RE_CORD.search(old)
    node.set('d',old[:match.start()]+f'{int(match[1])+1} {match[2]}'+old[match.end():])
    assert s.inventory(changed)==a # geometry coordinates alone authorized
    node.set('fill','#112233')
    assert s.inventory(changed)!=a
    changed=copy.deepcopy(svg)
    mask=next(changed.iter(s.NS+'mask'))
    mask.set('data-forged','yes')
    assert s.inventory(changed)!=a

def test_output_never_overwrites_source(signed):
    with pytest.raises(ValueError,match='SIGNED_INPUT_OUTPUT_NOT_SEPARATE'):
        s.evaluate(*signed,signed[0])
    with pytest.raises(ValueError,match='SIGNED_SVG_MUST_NOT_BE_OVERWRITTEN'):
        s.evaluate(*signed,signed[2].parent)

def test_chromium_dual_case_protected_edges_budget_and_source_improve(signed,tmp_path):
    result=s.evaluate(*signed,tmp_path)
    assert result['two_case_signed_masks_source_owner_adjacency_preserved']
    assert result['two_case_outer_silhouette_and_arm_pixel_exact']
    assert result['two_case_faceless_default_and_vertex_budget_pass']
    assert result['any_source_edge_improvement']
    assert result['full_character_golden']=='HOLD'
    assert result['production_deployment']=='UNCHANGED'
    for name,actual,budget in [('Raden',1409,1412),('GC001',1873,1887)]:
        c=result['cases'][name]
        assert c['expanded_vertices']==actual<=budget
        assert c['fully_protected_pixel_changes']==0
        assert c['outer_silhouette_edge_pixel_changes']==0
        assert c['owner_interface_pixel_changes']==0
        assert c['standard_face_microfeatures_off']
        assert c['source_visible_foreground_rgb_mae_after']<c['source_visible_foreground_rgb_mae_before']
        assert len(c['accepted_existing_vertex_moves'])>0
        assert c['candidate_chromium_renders']>0
        img=ET.parse(tmp_path/f'{name.lower()}_structure_guarded.svg').getroot()
        assert s.prior.previous.audit_default_faceless(img)
        assert not any(n.tag in (s.NS+'image',s.NS+'feImage',s.NS+'foreignObject') for n in img.iter())
    assert (tmp_path/'sa1057_two_case_structure_board.png').exists()
    assert '"path"' not in (tmp_path/'sa1057_metrics.json').read_text()

def test_fail_closed_unknown_case(signed):
    with pytest.raises(ValueError,match='Unknown signed'):
        s.signed_case('not-an-input',signed[0],signed[2])
