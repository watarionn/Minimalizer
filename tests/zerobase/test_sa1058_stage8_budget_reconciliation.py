"""SA10.58 signed-source historical ring budget and no-false-release regressions."""
from pathlib import Path
import hashlib,os,shutil,sys,copy
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1058_stage8_budget_reconciliation as s

@pytest.fixture
def signed():
    keys=('SA1058_RADEN_ROOT','SA1058_GC001_ROOT','SA1058_RADEN_BASE','SA1058_GC001_BASE')
    vals=[os.environ.get(k) for k in keys]
    if not all(vals):pytest.skip('Signed private original and previous SVG materials required')
    roots=[Path(x) for x in vals[:2]]
    svg=[Path(x) for x in vals[2:]]
    if not all(p.exists() for p in roots+svg):pytest.skip('Signed private source files not mounted')
    return roots+svg

def test_signed_source_lineage_and_distinct_vertex_ledgers(signed):
    for n,r,svg,historic,compact,cap in zip(s.CASES,signed[:2],signed[2:],(2370,3604),(1409,1873),(1412,1887)):
        data,case,tree=s.authorities(n,r,svg)
        assert data['photo'].shape==(340,340,3)
        assert case['historical_stage8_vertices']==historic>cap
        assert s.previous.prior.actual_svg_vertices(tree,case)==compact<=cap
        assert s.digest(svg)==s.SVG_SHA[n]

def test_original_source_tampering_fail_closed(signed,tmp_path):
    n='GC001';needed=s.previous.prior.previous.previous.prev.last.prior.prior.dual.CASES[n]['root_required']
    for f in needed:shutil.copy2(signed[1]/f,tmp_path/f)
    p=tmp_path/'GC001_source.png';p.write_bytes(p.read_bytes()+b'bad')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.authorities(n,tmp_path,signed[3])

def test_modified_sa1057_svg_fail_closed(signed,tmp_path):
    altered=tmp_path/'altered.svg';altered.write_bytes(signed[2].read_bytes()+b'forgery')
    with pytest.raises(ValueError,match='SA1057_SVG_SHA_MISMATCH'):
        s.authorities('Raden',signed[0],altered)

def test_budgeted_option_never_forges_source_coordinates(signed):
    data,case,tree=s.authorities('Raden',signed[0],signed[2])
    original=case['masks']['sa1041-owner-1'];part=case['records'][1]
    opts=s.choices_for_ring_owner(part,original,original,np.zeros_like(original))
    assert any(c['epsilon']==0 and c['ring_mask_error_pixels']==0 for c in opts)
    assert all(c['vertices']<=sum(len(r['points']) for r in part['parameters']['rings']) for c in opts)
    assert all(c['ring_mask_error_pixels']>=0 for c in opts)

def test_strict_face_arm_safe_filter_is_fail_closed(signed):
    d,case,_=s.authorities('Raden',signed[0],signed[2]);face=d['masks']['face'];arms=d['masks']['left_arm']|d['masks']['right_arm']
    for i,rec in enumerate(case['records']):
        reference=case['masks'][f'sa1041-owner-{i}']
        opts=s.choices_for_ring_owner(rec,reference,reference,face|arms)
        assert opts
        for opt in opts:assert not np.any((opt['mask']^reference)&(face|arms))

def test_ring_visibility_accounting_and_cannot_hide_source_support(signed):
    data,case,_=s.authorities('GC001',signed[1],signed[3]);
    src=[case['masks'][f'sa1041-owner-{i}'] for i in range(len(case['records']))]
    face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    meta,base,proposal=s.compare_partition(src,src,case['records'],face,arms)
    assert np.array_equal(base,proposal)
    assert meta['source_ownership_mismatched_pixels']==0
    assert meta['source_visible_silhouette_symmetric_difference_pixels']==0
    assert meta['source_visible_silhouette_iou']==1.0

def test_dominance_and_budget_search_does_not_silently_relax_cap():
    opts=[[{'vertices':7,'weighted_source_loss':0,'epsilon':0}, {'vertices':3,'weighted_source_loss':100,'epsilon':1}],
          [{'vertices':8,'weighted_source_loss':0,'epsilon':0}, {'vertices':4,'weighted_source_loss':100,'epsilon':1}]]
    used,loss,chosen=s.select_budgeted(opts,11)
    assert used==11 and loss==100
    with pytest.raises(ValueError,match='NO_BUDGET_FEASIBLE'):
        s.select_budgeted([[{'vertices':12,'weighted_source_loss':0,'epsilon':0}]],11)

def test_no_private_authority_overwrite(signed):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*signed,signed[0])
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*signed,signed[2].parent)

def test_full_two_case_actual_chromium_source_gate_and_holds(signed,tmp_path):
    j=s.evaluate(*signed,tmp_path)
    assert j['separate_source_lineage_vs_deployed_svg_counts']
    assert j['source_stage8_release_gate']=='HOLD'
    assert j['candidate_source_equivalence_release_gate']=='HOLD'
    assert j['human_visual_golden']=='HOLD' and j['production_deployment']=='UNCHANGED'
    for n,min_safe in [('Raden',1726),('GC001',2981)]:
        row=j['cases'][n]
        assert row['sa1057_expanded_budget_pass']
        assert not row['source_stage8_budget_pass']
        assert row['candidate_ring_budget_pass']
        assert row['candidate_ring_vertices']==row['original_stage8_budget']
        assert row['minimum_all_protected_face_arm_pixel_safe_vertices_in_tested_epsilon_family']==min_safe
        assert not row['all_protected_face_arm_pixels_safe_within_source_budget_in_tested_epsilon_family']
        assert row['full_source_ownership_replay']['changed_signed_arm_ownership_pixels']>0
        assert not row['candidate_source_exact_release_gate']
        assert row['signed_source_face_arm_ring_masks_unchanged']
        assert row['rendered_current_svg_vs_source_geometry']['actual_chromium_matte_render']
        assert 0<row['rendered_current_svg_vs_source_geometry']['silhouette_iou']<1
        assert (tmp_path/f'{n.lower()}_unapproved_stage8_candidate.json').exists()
        assert (tmp_path/f'{n.lower()}_stage8_source_difference.png').exists()
    assert (tmp_path/'sa1058_source_budget_review.png').exists()
    assert not any('points' in x for x in j['cases'].values() if isinstance(x,str))
