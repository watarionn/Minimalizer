"""SA10.45 signed-source visibility, hard budget and protected-raster research gates."""
from pathlib import Path
import sys
import os
import copy
import json
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
import sa1045_visible_geometry as s

@pytest.fixture
def source_root():
    root=os.environ.get('SA1045_SIGNED_ROOT')
    if not root:pytest.skip('Private SHA-locked Raden inputs are not mounted')
    return Path(root)


def test_source_visibility_preserves_true_occlusion(source_root):
    masks,signed,records=s.source_authorities(source_root)
    visible,evidence=s.source_visible_owner_masks(masks,signed,records)
    assert set(visible)==set(s.PAINTED_INDICES)
    assert not visible[5].any()
    assert evidence['8']['painted'] is False
    assert evidence['1']['proven_hidden_pixels']>0
    assert not np.any(visible[2]&signed['face'])


def test_pruner_hard_fails_if_stage9_source_owner_intersects_protected(source_root):
    masks,signed,records=s.source_authorities(source_root)
    visible,_=s.source_visible_owner_masks(masks,signed,records)
    svg=ET.parse(source_root/'full_character_vector.svg').getroot()
    fake={k:v.copy() for k,v in masks.items()}
    fake['sa1041-owner-1']|=signed['left_arm']
    with pytest.raises(ValueError,match='intersects protected'):
        s.verify_render_structure(svg,fake,signed,visible)


def test_dead_svg_masks_removed_only_on_authorized_negative_control(source_root):
    masks,signed,records=s.source_authorities(source_root)
    svg=ET.parse(source_root/'full_character_vector.svg').getroot()
    vis,_=s.source_visible_owner_masks(masks,signed,records)
    assert s.verify_render_structure(svg,masks,signed,vis)['stage37_apparel_is_empty']
    pruned=s.simplify_proven_dead_overlays(svg)
    assert len([n for n in pruned if n.get('data-owner-index') is not None])==9
    assert all('sa1041-protected-clear' not in n.get('mask','') for n in pruned.iter())
    bad=copy.deepcopy(svg)
    target=next(x for x in bad if x.get('data-owner-index')=='7')
    nested=next(x for x in target if x.get('mask')=='url(#sa1041-protected-clear)')
    ET.SubElement(nested,s.NS+'polygon',{'points':'1,1 2,1 2,2'})
    with pytest.raises(ValueError,match='nonempty'):
        s.verify_render_structure(bad,masks,signed,vis)


def test_original_provenance_and_unsupported_inputs_fail_closed(source_root,tmp_path):
    s.source_authorities(source_root)
    with pytest.raises(ValueError):s.source_authorities(tmp_path)


def test_rect_witness_merging_replays_every_black_guard_pixel():
    mask=np.zeros((340,340),bool)
    mask[1:8,3:6]=True
    mask[10:12,3:6]=True
    mask[300,300]=True
    found=s.pixel_rectangles(mask)
    recreated=np.zeros_like(mask)
    for x,y,w,h in found:recreated[y:y+h,x:x+w]=True
    assert np.array_equal(recreated,mask)
    assert len(found)==3
    with pytest.raises(ValueError):s.pixel_rectangles(mask.astype(np.uint8))


def test_protected_candidate_choice_never_forgives_over_budget():
    proposals={'a':[{'epsilon':0.5,'expanded_vertices':900,'unprotected_source_error':0},
                    {'epsilon':1.0,'expanded_vertices':200,'unprotected_source_error':15}],
               'b':[{'epsilon':0.5,'expanded_vertices':100,'unprotected_source_error':0}]}
    result=s.choose_guarded_options(proposals,500)
    assert result['nonprotected_mask_vertices']==300
    assert result['epsilons']['a']==1.0
    with pytest.raises(ValueError,match='No safe'):
        s.choose_guarded_options(proposals,90)


def test_all_trim_vertices_counted_and_unaccounted_primitives_rejected(source_root):
    masks,signed,records=s.source_authorities(source_root)
    svg=ET.parse(source_root/'full_character_vector.svg').getroot()
    baseline,report=s.replace_visible_masks(svg,masks,signed,records,1.0)
    assert report['expanded_deployed_vertices']==1310
    n=s.expanded_vertex_count_with_corrections(baseline)
    assert n==1310
    target=next(x for x in baseline.find(s.NS+'defs') if x.get('id')=='sa1041-owner-1')
    ET.SubElement(target,s.NS+'rect',{'x':'3','y':'4','width':'2','height':'1',
      'fill':'#000000','data-sa1045-protected-trim':'1'})
    assert s.expanded_vertex_count_with_corrections(baseline)==1314
    ET.SubElement(target,s.NS+'circle',{'cx':'2','cy':'3','r':'1'})
    with pytest.raises(ValueError,match='Uncounted'):
        s.expanded_vertex_count_with_corrections(baseline)


def test_right_arm_authority_mismatch_kept_distinct(source_root):
    masks,signed,records=s.source_authorities(source_root)
    assert np.count_nonzero(masks['sa1041-owner-2']!=signed['right_arm'])==2
    vis,_=s.source_visible_owner_masks(masks,signed,records)
    assert np.array_equal(vis[2],masks['sa1041-owner-2'])


def test_no_product_gate_waiver_source_archival_budget():
    assert s.BUDGET==1412
    assert s.STAGE9_VERTICES==12
    assert s.PAINTED_INDICES==(0,1,2,3,4,5,6,7,9,10)
    code=Path(s.__file__).read_text('utf-8')
    assert "'source_geometry_archival_budget_pass':False" in code
    assert "'production_promoted':False" in code
    assert "'full_character_golden_pass':False" in code


def test_signed_real_chromium_research_gate(source_root,tmp_path):
    result=s.evaluate(source_root,tmp_path)
    e=result['candidates']['visible_e0p5']
    best=result['candidates']['visible_guarded_budget']
    assert e['real_chrome_composite_equals_sa1044_exact']
    assert e['expanded_deployed_vertices']==2994
    assert e['real_chrome_metrics']['full_rgb_mismatched_pixels']==148
    assert best['expanded_deployed_vertices']<=1412
    assert best['expanded_deployed_vertices']==1409
    assert best['real_chrome_metrics']['signed_protected_mismatch_pixels']=={
        'face':0,'left_arm':0,'right_arm':0}
    assert best['real_chrome_metrics']['full_rgb_mismatched_pixels']==882
    assert result['production_promoted'] is False
    assert result['full_character_golden_pass'] is False
    assert result['source_geometry_archival_budget_pass'] is False
