"""SA10.54 SHA-pinned two-source color-conservation and actual Chromium regressions."""
from pathlib import Path
import os, sys, shutil, hashlib, json
import numpy as np
import pytest
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1054_iris_component_palette as s

@pytest.fixture
def auth():
    keys=('SA1054_RADEN_ROOT','SA1054_GC001_ROOT','SA1054_RADEN_BASE','SA1054_GC001_BASE')
    p=[os.getenv(k) for k in keys]
    if not all(p):pytest.skip('Signed original imagery and SHA-pinned private SVG not included in GitHub')
    return [Path(x) for x in p]

def test_two_signed_origins_and_pinned_svg(auth):
    for name,root,base in zip(s.CASES,auth[:2],auth[2:]):
        case=s.prev.last.prior.prior.dual.load_case(name,root)
        assert case['photo'].shape==(340,340,3)
        assert s.digest(base)==s.SHA[name]

def test_genuine_source_color_medoids(auth):
    for name,root in zip(s.CASES,auth[:2]):
        data=s.prev.last.prior.prior.dual.load_case(name,root)
        rois,_=s.prev.get_rois(name,data['masks']['face'])
        for eye in s.EYES:
            mask,color=s.eye_evidence(data['photo'],rois[eye],name)
            assert mask.sum()>=12
            assert np.any(np.all(data['photo'][mask]==color,axis=1))
            assert not np.any(mask&~data['masks']['face'])

def test_no_fake_palette_or_unsafe_empty():
    with pytest.raises(ValueError,match='No source iris'):s.source_color(np.empty((0,3),dtype=np.uint8))
    assert s.hexc((79,114,152))=='#4f7298'

def test_original_svg_tamper_blocks(auth,tmp_path):
    changed=tmp_path/'changed.svg';changed.write_bytes(auth[2].read_bytes()+b'tampered')
    with pytest.raises(ValueError,match='SA1053_CHAMPION_SHA_MISMATCH'):
        s.evaluate(auth[0],auth[1],changed,auth[3],tmp_path.parent/'separate_output')

def test_signed_source_tamper_blocks(auth,tmp_path):
    from sa1049_source_detail_dual_gate import CASES
    for name in CASES['GC001']['root_required']:shutil.copy2(auth[1]/name,tmp_path/name)
    image=tmp_path/'GC001_source.png';image.write_bytes(image.read_bytes()+b'tamper')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.evaluate(auth[0],tmp_path,auth[2],auth[3],tmp_path.parent/'separate_output')

def test_input_output_never_overlap(auth):
    with pytest.raises(ValueError,match='Separate signed source'):
        s.evaluate(*auth,auth[0])
    with pytest.raises(ValueError,match='overwrite signed champion'):
        s.evaluate(*auth,auth[2].parent)

def test_actual_two_case_chromium_source_palette_and_geometry(auth,tmp_path):
    report=s.evaluate(*auth,tmp_path)
    assert report['both_hard_vertex_budgets_pass']
    assert not report['semantic_iris_eye_lid_mouth_accuracy_certified']
    assert report['full_character_golden']=='HOLD' and report['production_deployment']=='UNCHANGED'
    for name,v,accepted,splits in (('Raden',1412,1,13),('GC001',1882,1,20)):
        case=report['cases'][name]
        assert case['expanded_vertices']==v<=case['budget']
        assert case['source_face_mismatch_mae_after']<case['source_face_mismatch_mae_before']
        assert case['component_split_proof']['pixel_exact_restructures']==splits
        assert len(case['iris_chroma_roi']['accepted_contour_recolors'])==accepted
        before=case['iris_chroma_roi']['pixel_rgb_before'];after=case['iris_chroma_roi']['pixel_rgb_after']
        assert after['iris']['image_left_eye']<before['iris']['image_left_eye']
        assert after['roi']['image_left_eye']<before['roi']['image_left_eye']
        assert after['roi']['mouth']<=before['roi']['mouth']
        assert case['signed_both_arms_rgb_identical']
        root=ET.parse(tmp_path/f'{name.lower()}_source_chroma.svg').getroot()
        assert not [x for x in root.iter() if x.tag in (s.NS+'image',s.NS+'foreignObject',s.NS+'feImage')]
        old=ET.parse(auth[2] if name=='Raden' else auth[3]).getroot()
        assert s.masks_and_shape_inventory(root)==s.masks_and_shape_inventory(old)
        assert s.face_contours(root)==s.face_contours(old)
    assert report['cases']['GC001']['iris_chroma_roi']['pixel_rgb_after']['iris']['image_right_eye']<report['cases']['GC001']['iris_chroma_roi']['pixel_rgb_before']['iris']['image_right_eye']
    assert (tmp_path/'sa1054_two_case_iris_comparison.png').is_file()
    assert '"path"' not in (tmp_path/'sa1054_metrics.json').read_text()
