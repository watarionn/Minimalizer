"""Source-locked SA10.46 Chrome crosscase positive holdout and fail-closed regressions."""
from pathlib import Path
import copy
import json
import os
import sys
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
import sa1046_gc001_positive_holdout as s

@pytest.fixture
def private_root():
    path=os.environ.get('SA1046_GC001_ROOT')
    if not path:
        pytest.skip('Private GC001 real source is intentionally not shipped in GitHub')
    return Path(path)


def test_frozen_gc001_signed_lineage_and_owner_order(private_root):
    records,masks,signed,svg,ref,delta=s.load_signed(private_root)
    assert [p['source_mask_owner'] for p in records]==list(s.ORDER)
    assert ref.shape==(340,340,3)
    assert delta=={'face':0,'left_arm':5,'right_arm':24}
    assert len(masks)==13
    assert len(list(svg.iter(s.NS+'polygon')))==8


def test_mutated_gc001_source_hash_fails_closed(private_root,tmp_path):
    import shutil
    for f in s.EXPECTED_SHA:
        shutil.copy2(private_root/f,tmp_path/f)
    payload=tmp_path/'signed_left_arm_stage04_mask.png'
    payload.write_bytes(payload.read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='hash mismatch'):
        s.load_signed(tmp_path)


def test_no_raden_index_or_empty_apparel_transfer(private_root):
    _,masks,signed,svg,_,_=s.load_signed(private_root)
    lower=next(n for n in svg if n.get('data-owner-index')=='1')
    clothing=next(n for n in lower if n.get('mask')=='url(#sa1041-protected-clear)')
    assert len(list(clothing.iter(s.NS+'polygon')))==5
    assert s.ORDER.index('face')==3 and s.ORDER.index('left_arm')==7
    assert not np.array_equal(masks['sa1041-owner-7'],signed['left_arm'])
    assert not np.array_equal(masks['sa1041-owner-2'],signed['right_arm'])


def test_source_exact_variant_counts_all_colored_planes(private_root):
    _,masks,_,svg,_,_=s.load_signed(private_root)
    result,stats=s.compile_candidate(svg,masks,0.5)
    assert stats['expanded_deployed_vertices']==6083
    assert stats['stage9_and_clothing_polygon_vertices']==55
    assert not stats['budget_pass']
    assert len(list(result.iter(s.NS+'mask')))==13
    assert not list(result.iter(s.NS+'image'))


def test_all_budgets_fail_even_when_signed_masks_are_exact(private_root):
    _,masks,_,svg,_,_=s.load_signed(private_root)
    for eps in s.EPSILONS:
        _,stats=s.compile_candidate(svg,masks,eps)
        assert stats['expanded_deployed_vertices']>s.BUDGET
    with pytest.raises(ValueError):
        s.compile_candidate(svg,masks,0.8)


def test_partition_accounts_for_all_pixels(private_root):
    records,masks,signed,_,expected,_=s.load_signed(private_root)
    role=s.visible_partition(records,masks,signed)
    assert (role==s.ORDER.index('face'))[signed['face']].all()
    assert not np.any(role==s.ORDER.index('head'))
    rows=s.errors_by_owner(expected,expected,role)
    assert sum(v['visible_source_owned_pixels'] for v in rows.values())==340*340
    assert sum(v['rgb_mismatched_pixels'] for v in rows.values())==0


def test_source_guard_requires_clothing_panels(private_root,tmp_path):
    import shutil
    for f in s.EXPECTED_SHA:shutil.copy2(private_root/f,tmp_path/f)
    # Altering the authoritative SVG gets blocked before any unsafe pruning.
    data=(tmp_path/'full_character_vector.svg').read_text()
    (tmp_path/'full_character_vector.svg').write_text(data.replace('data-owner-index="1"','data-owner-index="77"'))
    with pytest.raises(ValueError,match='hash mismatch'):s.load_signed(tmp_path)


def test_real_gc001_chromium_positive_holdout(private_root,tmp_path):
    report=s.evaluate(private_root,tmp_path)
    assert report['baseline']['full_rgb_mismatch']==3919
    exact=report['candidates']['exact']
    assert exact['rgb']['full_rgb_mismatch']==683
    assert exact['rgb']['source_signed_protected']=={'face':0,'left_arm':0,'right_arm':0}
    assert exact['all_13_signed_masks_exact']
    assert exact['visible_owner_error_partition']['lower_body']['rgb_mismatched_pixels']==413
    assert not exact['budget_pass']
    assert not report['production_promotion_authorized']
    assert report['gc001_stage37_five_apparel_panels_preserved']
