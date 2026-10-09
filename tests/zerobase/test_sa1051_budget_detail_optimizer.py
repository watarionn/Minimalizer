"""SA10.51 strict 2-case face/detail geometry replay and source-only regression tests."""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib,os,sys,shutil,json
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1051_budget_detail_optimizer as s

@pytest.fixture
def authority():
    names=('SA1051_RADEN_ROOT','SA1051_GC001_ROOT','SA1051_RADEN_CHAMPION','SA1051_GC001_CHAMPION')
    paths=[os.getenv(name) for name in names]
    if not all(paths):pytest.skip('Two private signed originals and champion SVG paths are intentionally not public')
    return [Path(p) for p in paths]


def test_immutable_two_case_source_authorities_and_champions(authority):
    for name,root,champion in zip(s.CASES,authority[:2],authority[2:]):
        data,case,svg=s.prior.load_signed(name,root,champion)
        assert data['photo'].shape==(340,340,3)
        assert case['budget']==(1412 if name=='Raden' else 1887)
        assert s.strict_vertices(svg,case)['expanded_deployed_vertices']==s.prior.CHAMPION_VERTEX[name]
        assert s.strict_vertices(svg,case)['signed_face_mask_references']==1


def test_original_source_tampering_rejected(authority,tmp_path):
    from sa1049_source_detail_dual_gate import CASES
    for name in CASES['GC001']['root_required']:shutil.copy2(authority[1]/name,tmp_path/name)
    image=tmp_path/'GC001_source.png'
    image.write_bytes(image.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.prior.load_signed('GC001',tmp_path,authority[3])


def test_champion_tampering_rejected(authority,tmp_path):
    f=tmp_path/'altered.svg';f.write_bytes(authority[2].read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='CHAMPION_SHA_MISMATCH'):
        s.prior.load_signed('Raden',authority[0],f)


def test_face_inserts_into_single_existing_guard_without_second_reference(authority):
    for name,root,svg_path in zip(s.CASES,authority[:2],authority[2:]):
        data,case,root_svg=s.prior.load_signed(name,root,svg_path)
        svg,detail=s.embed_face(root_svg,data['photo'],data['masks']['face'],
            {'k':4,'epsilon':4.0,'min_area':15})
        base=s.strict_vertices(root_svg,case); after=s.strict_vertices(svg,case)
        assert after['signed_face_mask_references']==1
        assert after['expanded_deployed_vertices']-base['expanded_deployed_vertices']==detail['true_new_path_vertices']
        assert detail['duplicate_mask_reference_vertices']==0
        assert any(n.get('data-sa1051-observed')=='face' for n in svg.iter())
        original=set(map(tuple,data['photo'][data['masks']['face']]))
        assert all(tuple(k) in original for k in detail['source_colors'].values())


def test_unknown_svg_mask_geometry_is_rejected(authority):
    name='Raden';root,champ=authority[0],authority[2]
    _,case,source=s.prior.load_signed(name,root,champ)
    node=next(n for n in source.iter(s.NS+'mask'))
    ET.SubElement(node,s.NS+'circle',{'r':'1'})
    with pytest.raises(ValueError,match='Unaccounted SVG geometry'):
        s.strict_vertices(source,case)


def test_nonsource_context_cannot_overwrite_original(authority):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*authority,authority[0])
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(authority[0],authority[0],authority[2],authority[3],Path('/mnt/data/should_not_run'))


def test_signed_original_color_only_policy_rejects_invalid(authority):
    data=s.prior.dual.load_case('Raden',authority[0])
    with pytest.raises(ValueError,match='Unsafe'):
        s.prior.observe_palette(data['photo'],data['masks']['face'],{'k':80,'min_area':1,'epsilon':1.0})


def test_real_chromium_dual_budget_face_arm_and_trim_gate(authority,tmp_path):
    report=s.evaluate(*authority,tmp_path)
    assert report['two_case_expanded_vertex_budget_pass'] is True
    assert report['two_case_proven_dead_trim_pass'] is True
    assert report['human_visual_review']=='PENDING'
    assert report['full_character_golden']=='HOLD'
    assert report['production_deployment']=='UNCHANGED'
    for case,limit,removed in (('Raden',1412,28),('GC001',1887,49)):
        metrics=report['cases'][case]
        assert metrics['strict_account']['expanded_deployed_vertices']<=limit
        assert metrics['strict_account']['signed_face_mask_references']==1
        assert metrics['dead_trim_composite_proof']['removed_count']==removed
        assert metrics['dead_trim_composite_proof']['all_old_chromium_pixels_unchanged']
        assert metrics['budget_source_fidelity']['face_rgb_mae']<metrics['prior_source_fidelity']['face_rgb_mae']
        assert metrics['budget_source_fidelity']['foreground_rgb_mae']<metrics['prior_source_fidelity']['foreground_rgb_mae']
        assert metrics['budget_source_fidelity']['left_arm_changed_vs_champion']==0
        assert metrics['budget_source_fidelity']['right_arm_changed_vs_champion']==0
        assert metrics['extra_face_mask_reference_vertex_occurrences']==0
        svg=ET.parse(tmp_path/f'{case.lower()}_budget_detail.svg').getroot()
        assert not any(n.tag in (s.NS+'image',s.NS+'feImage',s.NS+'foreignObject') for n in svg.iter())
        assert any(n.get('data-sa1051-observed')=='face' for n in svg.iter())
    assert (tmp_path/'sa1051_two_case_budget_comparison.png').is_file()
    assert not (tmp_path/'raden_original_private.png').exists()
    assert '\"path\"' not in (tmp_path/'sa1051_metrics.json').read_text()


def test_signed_manifest_sha256_matches_outputs(authority,tmp_path):
    # Check the reproducible record exists, without committing signed photos.
    assert len(s.CASES)==2
    assert s.CASES==('Raden','GC001')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==s.prior.CHAMPION_HASH[name]
               for name,p in zip(s.CASES,authority[2:]))
