"""SA10.48 signed GC001, source proof, mask safety and real Chromium tests."""
from pathlib import Path
import os,sys,copy,shutil
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1048_guardless_component_optimizer as s

@pytest.fixture
def signed_root():
    path=os.environ.get('SA1048_GC001_ROOT')
    if not path:pytest.skip('Private SHA-locked GC001 source not in public repository')
    return Path(path)


def test_root_and_source_authority(signed_root):
    c=s.source_case(signed_root)
    assert c['case']=='GC001' and c['budget']==1887
    assert len(c['source_input_sha256'])==8
    assert c['overlay_vertices']==55
    assert c['records'][0]['source_mask_owner']=='hair'
    assert c['records'][1]['source_mask_owner']=='lower_body'


def test_frozen_guarded_exact_and_group_preservation(signed_root):
    c=s.source_case(signed_root); svg,visible=s.build_exact(c)
    assert s.previous.count_svg(svg,55)['expanded_deployed_vertices']==5327
    without=s.remove_redundant_protector(svg)
    assert s.previous.count_svg(without,55)['expanded_deployed_vertices']==4675
    assert len([n for n in without.iter() if n.get('mask')=='url(#sa1041-protected-clear)'])==0
    assert len(list(without.iter(s.NS+'polygon')))==8
    assert len(visible)==9


def test_exact_apparel_clothing_not_discarded(signed_root):
    c=s.source_case(signed_root);svg,visible=s.build_exact(c)
    unmasked=s.remove_redundant_protector(svg)
    assert len([n for n in unmasked.iter(s.NS+'polygon') if len(n.get('points','').split())>0])==8
    assert sum(len(n.get('points','').split()) for n in unmasked.iter(s.NS+'polygon'))==55
    assert any(len(list(n.iter(s.NS+'polygon')))==5 for n in unmasked.iter())


def test_guard_prune_requires_proven_structure(signed_root):
    case=s.source_case(signed_root);scene,visible=s.build_exact(case)
    targets=[n for n in scene.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
    targets[0].set('mask','url(#unapproved)')
    with pytest.raises(ValueError,match='four signed'):s.remove_redundant_protector(scene)


def test_exact_component_filter_never_adds_pixels(signed_root):
    case=s.source_case(signed_root);vis,_=s.previous.visible_ownership(case)
    unknown=vis['sa1041-owner-6']
    clean,stats=s.component_filter(unknown,8)
    assert stats['removed_pixels']==137
    assert not np.any(clean & ~unknown)
    assert not np.array_equal(clean,unknown)
    assert stats['removed_components']>0


def test_invalid_component_threshold_refused(signed_root):
    case=s.source_case(signed_root)
    with pytest.raises(ValueError,match='Negative'):s.component_filter(next(iter(case['masks'].values())),-1)


def test_authority_modified_refused(signed_root,tmp_path):
    for key in s.previous.gc46.EXPECTED_SHA:shutil.copyfile(signed_root/key,tmp_path/key)
    filename=tmp_path/'signed_face_stage04_mask.png'
    filename.write_bytes(filename.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='hash mismatch'):s.source_case(tmp_path)


def test_source_output_isolation(signed_root):
    with pytest.raises(ValueError,match='source-authority'):s.evaluate(signed_root,signed_root)


def test_real_chrome_exact_guard_proof_and_budget(signed_root,tmp_path):
    result=s.evaluate(signed_root,tmp_path)
    assert result['guard_non_effect_proof']['tested_combinations']==16
    assert not any(result['guard_non_effect_proof']['mismatched_rgb_pixels_per_combination'])
    assert result['exact_guarded_and_guardless_rgb_identical']
    assert result['exact_full_rgb_mismatch']==683
    assert result['budget_candidate']['expanded_deployed_vertices']==1883
    assert result['budget_candidate']['full_chromium']['full_rgb_mismatch']==1871
    assert result['budget_candidate']['full_chromium']['source_signed_protected']==s.EXPECTED['protected_rgb']
    assert result['budget_candidate']['expanded_deployed_vertices']<=1887
    assert result['all_source_color_polygons_preserved']
    assert result['full_character_golden']=='HOLD' and result['production_deployment']=='UNCHANGED'
    assert not [n for n in ET.parse(tmp_path/'gc001_guardless_component_budget.svg').getroot().iter() if n.tag in
        (s.NS+'image',s.NS+'feImage',s.NS+'foreignObject')]
