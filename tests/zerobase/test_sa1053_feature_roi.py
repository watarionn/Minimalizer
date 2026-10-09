"""Private-authority regression for original-2D annotated face ROIs and zero-vertex moves."""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib,os,shutil,sys,json
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1053_feature_roi as s

@pytest.fixture
def auth():
    vals=[os.environ.get(k) for k in ('SA1053_RADEN_ROOT','SA1053_GC001_ROOT','SA1053_RADEN_BASE','SA1053_GC001_BASE')]
    if not all(vals):pytest.skip('Private signed originals and two SVGS required')
    return [Path(v) for v in vals]

def test_sha_signed_two_case_baselines(auth):
    for name,root,svg in zip(s.CASES,auth[:2],auth[2:]):
        data,case,node=s.signed_inputs(name,root,svg)
        assert s.last.prior.strict_vertices(node,case)['expanded_deployed_vertices'] in (1412,1882)
        assert data['photo'].shape==(340,340,3)
        assert hashlib.sha256(svg.read_bytes()).hexdigest()==s.BASE_SHA[name]

def test_visual_rois_clip_to_signed_face(auth):
    for name,root in zip(s.CASES,auth[:2]):
        data=s.last.prior.prior.dual.load_case(name,root)
        rois,b=s.get_rois(name,data['masks']['face'])
        assert set(rois)==set(s.PRIORITY)
        for key,region in rois.items():
            assert region.sum()>25
            assert not np.any(region & ~data['masks']['face'])
            assert s.gray_edge_mask(data['photo'],region).sum()>5

def test_annotated_bbox_outside_image_is_clamped():
    mask=np.zeros((340,340),dtype=bool);mask[0:42,0:38]=True
    assert s.box_from_mask(mask,(-1,-1,.5,.5))==(0,0,19,21)

def test_signed_original_modification_rejected(auth,tmp_path):
    from sa1049_source_detail_dual_gate import CASES
    for key in CASES['GC001']['root_required']:shutil.copy2(auth[1]/key,tmp_path/key)
    with (tmp_path/'GC001_source.png').open('ab') as f:f.write(b'tamper')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.signed_inputs('GC001',tmp_path,auth[3])

def test_prior_svg_modified_rejected(auth,tmp_path):
    p=tmp_path/'bad.svg';p.write_bytes(auth[2].read_bytes()+b'tamper')
    with pytest.raises(ValueError,match='SA1052_FEATURE_BASELINE_SHA_MISMATCH'):
        s.signed_inputs('Raden',auth[0],p)

def test_no_original_source_overwrite(auth):
    with pytest.raises(ValueError,match='separate'):s.evaluate(*auth,auth[0])
    with pytest.raises(ValueError,match='overwrite'):s.evaluate(*auth,auth[2].parent)

def test_complete_chromium_annotated_roi_and_vertex_gate(auth,tmp_path):
    r=s.evaluate(*auth,tmp_path)
    assert r['two_case_budget_pass'] and r['two_case_protected_regions_exact']
    assert r['semantic_landmark_detector_used'] is False
    assert r['full_character_golden']=='HOLD' and r['production_deployment']=='UNCHANGED'
    for name,limit in [('Raden',1412),('GC001',1887)]:
        t=r['cases'][name]
        assert t['accepted_vertex_micro_moves']>0 and t['candidate_trials']>0
        assert t['vertex_cost']<=limit
        assert t['arms_unchanged'] and t['outside_face_unchanged']
        assert t['original_source_face_mae_after']<t['original_source_face_mae_before']
        assert t['original_source_foreground_mae_after']<t['original_source_foreground_mae_before']
        assert all(q['after']['rgb_mae']<=q['before']['rgb_mae'] for q in t['roi_result'].values())
        root=ET.parse(tmp_path/f'{name.lower()}_sa1053.svg').getroot()
        assert not any(x.tag in (s.NS+'image',s.NS+'foreignObject',s.NS+'feImage') for x in root.iter())
    assert (tmp_path/'sa1053_face_closeup.png').exists()
    assert (tmp_path/'sa1053_two_case_comparison.png').exists()
    assert not list(tmp_path.glob('*original_private*'))
    assert '"path"' not in (tmp_path/'sa1053_metrics.json').read_text()
