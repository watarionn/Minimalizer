"""SA10.50 signed source-only RGB geometry, identity and strict-budget regressions."""
from pathlib import Path
import hashlib,os,sys,shutil,json
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1050_source_color_vectorization as s

@pytest.fixture
def signed():
    paths=[os.getenv('SA1050_RADEN_ROOT'),os.getenv('SA1050_GC001_ROOT'),
           os.getenv('SA1050_RADEN_CHAMPION'),os.getenv('SA1050_GC001_CHAMPION')]
    if not all(paths):pytest.skip('Private signed source/champions not distributed in repo')
    return [Path(p) for p in paths]


def test_original_source_and_champion_authorities(signed):
    for name,root,champion in zip(('Raden','GC001'),signed[:2],signed[2:]):
        data,case,svg=s.load_signed(name,root,champion)
        assert case['budget']==(1412 if name=='Raden' else 1887)
        assert s.CHAMPION_VERTEX[name] in (1409,1883)
        assert data['photo'].shape==(340,340,3)
        assert not [x for x in svg.iter() if x.tag in (s.NS+'image',s.NS+'foreignObject')]


def test_hash_modified_private_source_refused(signed,tmp_path):
    for fn in s.dual.CASES['GC001']['root_required']:
        shutil.copy2(signed[1]/fn,tmp_path/fn)
    with (tmp_path/'GC001_source.png').open('ab') as f:f.write(b'altered')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.load_signed('GC001',tmp_path,signed[3])


def test_champion_hash_alteration_refused(signed,tmp_path):
    modified=tmp_path/'tampered.svg'
    modified.write_bytes(signed[2].read_bytes()+b'altered')
    with pytest.raises(ValueError,match='CHAMPION_SHA_MISMATCH'):
        s.load_signed('Raden',signed[0],modified)


def test_source_palette_all_rgb_colors_are_real_source_pixels(signed):
    for name,root in zip(('Raden','GC001'),signed[:2]):
        source=s.dual.load_case(name,root)
        rgb=source['photo'];mask=source['masks']['face']
        info=s.observe_palette(rgb,mask,s.PALETTE_POLICY['face'])
        real={tuple(x) for x in rgb[mask]}
        assert len(info['source_colors'])==4
        assert all(tuple(x) in real for x in info['source_colors'].values())
        assert len(info['details'])>=2
        assert sum(item['vertices'] for item in info['details'])>0


def test_source_kmeans_is_deterministic(signed):
    case=s.dual.load_case('GC001',signed[1]);source=case['photo'];mask=case['masks']['face']
    a=s.observe_palette(source,mask,s.PALETTE_POLICY['face'])
    b=s.observe_palette(source,mask,s.PALETTE_POLICY['face'])
    assert a==b


def test_face_uses_existing_signed_mask_and_explicit_extra_reference_cost(signed):
    for name,root,champion in zip(('Raden','GC001'),signed[:2],signed[2:]):
        data,case,svg=s.load_signed(name,root,champion)
        produced,details=s.make_face(svg,data['photo'],data['masks']['face'])
        assert details['new_expanded_vertices']==details['new_extra_path_vertices']+details['new_mask_reference_vertex_occurrences']
        assert details['new_expanded_vertices']>details['new_extra_path_vertices']
        assert len([n for n in produced if n.get('data-sa1050-evidence')])==1
        colors={f'#{tuple(rgb)}' for rgb in details['source_colors'].values()}
        assert len(colors)==4
        assert all(n.get('fill-rule')=='evenodd' for n in produced.iter(s.NS+'path') if n.get('data-sa1050-source-cluster'))


def test_no_original_authority_folder_overwrite(signed):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*signed[:2],*signed[2:],signed[0])


def test_safe_metrics_never_exposes_source_contour_paths():
    o={'path':'M 1 2 L 3 4','x':[{'path':'M 0 0','vertices':3}]}
    cleaned=s.safe_metrics(o)
    assert cleaned=={'x':[{'vertices':3}]}


def test_invalid_policy_refused(signed):
    c=s.dual.load_case('Raden',signed[0])
    with pytest.raises(ValueError,match='Unsafe'):
        s.observe_palette(c['photo'],c['masks']['face'],{'k':50,'epsilon':1,'min_area':10})


def test_real_chromium_dual_source_color_boundaries(signed,tmp_path):
    r=s.evaluate(*signed[:2],*signed[2:],tmp_path)
    assert r['both_signed_arms_stable'] is True
    assert r['two_case_deployed_svg_budget'] is False
    assert r['full_character_golden']=='HOLD'
    for name,face,fg,vertices in (
        ('Raden',31.191346,22.415575,2308),('GC001',30.804942,37.506238,2746)):
        case=r['cases'][name]
        assert case['signed_source_original_vs_svg_face']['face_mae_source_color_prototype']==face
        assert case['original_source_foreground_mae_prototype']==fg
        assert case['expanded_vertex_count_prototype']==vertices
        assert not case['budget_pass']
        assert case['protected_arm_champion_rgb_unchanged']
        assert all(k['accepted'] for k in case['material_details'].values())
        assert not any('path' in detail for detail in case['face_detail']['details'])
        if name=='Raden':limit=1412
        else:limit=1887
        assert case['expanded_vertex_count_prototype']>limit
        doc=ET.parse(tmp_path/f'{name.lower()}_face_hair_clothes_detail.svg').getroot()
        assert not any(n.tag in (s.NS+'image',s.NS+'feImage',s.NS+'foreignObject') for n in doc.iter())
    assert (tmp_path/'sa1050_two_case_source_detail_board.png').exists()
    assert not list(tmp_path.glob('*original_private.png'))
    metrics=json.loads((tmp_path/'sa1050_metrics.json').read_text())
    assert '"path"' not in json.dumps(metrics)
