"""SA10.59 release-blocking, source-locked visual review regressions."""
from __future__ import annotations
import copy, json, os, sys, shutil, hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1059_golden_review_harness as s

@pytest.fixture
def signed():
    keys=('SA1059_RADEN_ROOT','SA1059_GC001_ROOT','SA1059_R55','SA1059_R56','SA1059_R57','SA1059_G55','SA1059_G56','SA1059_G57')
    values=[os.getenv(k) for k in keys]
    if not all(values):pytest.skip('Signed private source images and all six SHA-pinned SVGs required')
    paths=[Path(x) for x in values]
    if not all(p.exists() for p in paths):pytest.skip('Private signed file unavailable')
    return paths

def cases(signed):
    return [(s.CASES[0],signed[0],signed[2:5]),(s.CASES[1],signed[1],signed[5:8])]

def test_signed_authenticity_and_stage_counts(signed):
    for name,root,inputs in cases(signed):
        data,case=s.require_pins(name,root,inputs)
        assert data['photo'].shape==(340,340,3)
        assert case['historical_stage8_vertices']>case['budget']
        for stage,path in zip(s.STAGES,inputs):
            assert s.sha(path)==s.VECTORS[name][stage][0]

def test_reject_tampered_prior_svg(signed,tmp_path):
    name,root,paths=cases(signed)[0];alter=tmp_path/'tampered.svg'
    alter.write_bytes(paths[0].read_bytes()+b'forged')
    with pytest.raises(ValueError,match='SHA_PINNED_SVG_CHANGED'):
        s.require_pins(name,root,[alter,*paths[1:]])

def test_reject_tampered_signed_source(signed,tmp_path):
    name,root,paths=cases(signed)[1]
    required=s.old.previous.prior.previous.previous.prev.last.prior.prior.dual.CASES[name]['root_required']
    for filename in required:shutil.copy2(root/filename,tmp_path/filename)
    (tmp_path/'GC001_source.png').write_bytes((tmp_path/'GC001_source.png').read_bytes()+b'bad')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.require_pins(name,tmp_path,paths)

def test_human_review_cannot_auto_pass():
    assert 'PENDING' in ('PENDING','HOLD')
    assert len(s.CHECKLIST)==6 and len(set(s.CHECKLIST))==6
    assert s.STAGES==('SA10.55','SA10.56','SA10.57')

def test_matte_iou_and_boundary_known_cases():
    x=np.zeros((340,340),dtype=bool);x[20:80,30:70]=1
    same=s.silhouette_stats(x,x)
    assert same['iou']==1.0 and same['symmetric_difference_pixels']==0
    y=x.copy();y[35,41]=False
    altered=s.silhouette_stats(x,y)
    assert altered['iou']<1 and altered['symmetric_difference_pixels']==1

def test_mask_roles_do_not_fake_source_face(signed):
    name,root,paths=cases(signed)[0];data,case=s.require_pins(name,root,paths)
    labels,roles=s.source_owners(case,data['masks']['face'])
    assert all(np.count_nonzero(mask)>100 for mask in roles.values())
    assert not np.any(roles['hair']&roles['left_arm'])
    assert np.any(labels>=0)

def test_no_mutation_or_source_output_overlap(signed,tmp_path):
    with pytest.raises(ValueError,match='SIGNED_INPUT_OUTPUT_MUST_NOT_OVERLAP'):
        s.output_safety([signed[2:5],signed[5:8]],signed[:2],signed[0])
    with pytest.raises(ValueError,match='SIGNED_INPUT_OUTPUT_MUST_NOT_OVERLAP'):
        s.output_safety([signed[2:5],signed[5:8]],signed[:2],signed[4].parent)
    with pytest.raises(ValueError,match='SOURCES_MUST_BE_SEPARATE'):
        s.output_safety([signed[2:5],signed[5:8]],[signed[0],signed[0]],tmp_path)

def test_real_chromium_multiimage_full_golden_hold(signed,tmp_path):
    inputs=[signed[2:5],signed[5:8]]
    result=s.evaluate(signed[:2],inputs,tmp_path)
    assert result['stage']=='SA10.59'
    assert result['total_independent_signed_input_images']==2
    assert result['total_chromium_stage_replays']==6
    assert result['golden_coverage_limited_to_two_signed_images']
    assert result['human_visual_judgments_are_not_auto_certified']
    assert result['source_stage8_release']==result['full_character_golden']=='HOLD'
    assert result['production_phase15_gate']=='NOT_RUN'
    assert result['production_deployment']=='UNCHANGED'
    for n,row in result['cases'].items():
        assert row['default_faceless_pass']
        assert row['signed_face_pixels_identical_across_stages']
        assert row['signed_arms_pixels_identical_across_stages']
        assert row['source_original_stage8_ring_vertices']>row['historic_stage8_source_ring_budget']
        assert row['stages']['SA10.57']['expanded_vertices']<=row['historic_stage8_source_ring_budget']
        assert row['stages']['SA10.57']['source_nonface_rgb_mae'] < row['stages']['SA10.55']['source_nonface_rgb_mae']
        assert row['silhouette_matte_vs_original_source']['iou']<1
        assert row['human_identity_verdict']=='PENDING'
        assert set(row['human_checklist'])==set(s.CHECKLIST)
        assert all(v=='PENDING' for v in row['human_checklist'].values())
        assert (tmp_path/f'{n.lower()}_review_strip.png').exists()
        assert (tmp_path/f'{n.lower()}_detail_strip.png').exists()
    human=json.loads((tmp_path/'sa1059_human_review_blank.json').read_text())
    assert all(human['cases'][n]['artistic_identity']=='PENDING' for n in s.CASES)
    assert 'HOLD' in (tmp_path/'sa1059_human_review_sheet.md').read_text()
    assert '"path"' not in (tmp_path/'sa1059_metrics.json').read_text()
