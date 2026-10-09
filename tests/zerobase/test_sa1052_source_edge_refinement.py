"""SA10.52 fail-closed tests for signed source 1px contour budget experiments."""
from pathlib import Path
from xml.etree import ElementTree as ET
import copy,hashlib,os,sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1052_source_edge_refinement as s

@pytest.fixture
def signed():
    values=[os.environ.get(x) for x in ('SA1052_RADEN_ROOT','SA1052_GC001_ROOT',
                                         'SA1052_RADEN_BASELINE','SA1052_GC001_BASELINE')]
    if not all(values):pytest.skip('Private SHA-signed character materials not included in public GitHub')
    return [Path(p) for p in values]

def test_source_and_baseline_authority_and_budget(signed):
    for name,root,ref,budget in zip(('Raden','GC001'),signed[:2],signed[2:],(1412,1882)):
        data,case,svg=s.load_case(name,root,ref)
        assert data['photo'].shape==(340,340,3)
        assert s.prior.strict_vertices(svg,case)['expanded_deployed_vertices']==budget
        assert len(case['source_input_sha256']) in (7,8)

def test_signed_svg_hash_tampering_rejected(signed,tmp_path):
    altered=tmp_path/'bad.svg';altered.write_bytes(signed[2].read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='SA1051_BASELINE_SHA_MISMATCH'):
        s.load_case('Raden',signed[0],altered)

def test_source_tampering_rejected(signed,tmp_path):
    from shutil import copy2
    for file in s.prior.prior.dual.CASES['GC001']['root_required']:
        copy2(signed[1]/file,tmp_path/file)
    target=tmp_path/'GC001_source.png';target.write_bytes(target.read_bytes()+b'forgery')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.load_case('GC001',tmp_path,signed[3])

def test_source_only_one_px_moves():
    path='M 10 20 L 12 23 L 11 27 Z'
    assert s.shift_source_segment(path,1,0)=='M 11 20 L 13 23 L 12 27 Z'
    assert s.shift_source_segment(path,0,-1)=='M 10 19 L 12 22 L 11 26 Z'
    for shift in ((0,0),(3,0),(1,1)):
        with pytest.raises(ValueError,match='cardinal'):
            s.shift_source_segment(path,*shift)
    with pytest.raises(ValueError,match='Unrecognized'):
        s.shift_source_segment('C 2 3',1,0)

def test_paint_inventory_geometry_is_fixed(signed):
    for ref in signed[2:]:
        image=ET.parse(ref).getroot()
        changed=copy.deepcopy(image)
        feature=next(n for n in changed.iter(s.NS+'path') if n.get('data-sa1051-observed')=='face')
        before=s.source_paint_inventory(image)
        feature.set('d',s.shift_source_segment(s.SEGMENT.findall(feature.get('d'))[0],1,0)+' '+' '.join(s.SEGMENT.findall(feature.get('d'))[1:]))
        assert s.source_paint_inventory(changed)==before
        feature.set('fill','#123456')
        assert s.source_paint_inventory(changed)!=before

def test_signed_gradient_evidence(signed):
    for name,root in zip(('Raden','GC001'),signed[:2]):
        data=s.prior.prior.dual.load_case(name,root)
        mask=s.source_gradient_roi(data['photo'],data['masks']['face'])
        assert mask.sum()>1000
        assert not np.any(mask&~data['masks']['face'])

def test_reject_source_output_overlap(signed):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*signed,signed[0])
    with pytest.raises(ValueError,match='overwrite'):
        s.evaluate(*signed,signed[2].parent)

def test_full_two_character_signed_chrome_replay(signed,tmp_path):
    report=s.evaluate(*signed,tmp_path)
    assert report['both_budget_pass'] and report['both_original_face_source_fidelity_improved']
    assert report['eye_nose_mouth_semantic_certification'] is False
    assert report['full_character_golden']=='HOLD' and report['production_deployment']=='UNCHANGED'
    for name,count,limit in (('Raden',1412,1412),('GC001',1882,1887)):
        stats=report['cases'][name]
        assert stats['strict_expanded_vertices']==count<=limit
        assert stats['source_metric_after']['face']<stats['source_metric_before']['face']
        assert stats['source_metric_after']['foreground']<stats['source_metric_before']['foreground']
        assert stats['source_metric_after']['face_high_gradient']<stats['source_metric_before']['face_high_gradient']
        assert stats['owner_masks_and_source_palette_unchanged']
        assert stats['arms_rgb_unchanged']
        assert stats['face_refinement']['accepted_1px_translations']>0
        tree=ET.parse(tmp_path/f'{name.lower()}_edge_refined.svg').getroot()
        assert not any(n.tag in (s.NS+'image',s.NS+'foreignObject',s.NS+'feImage') for n in tree.iter())
        assert stats['sa1051_input_svg_sha256']==s.BASELINE_SHA[name]
    assert (tmp_path/'sa1052_two_case_edge_comparison.png').is_file()
    assert not list(tmp_path.glob('*original_private*'))
