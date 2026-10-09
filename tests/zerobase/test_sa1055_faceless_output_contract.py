"""SA10.55 signed two-case no-face-parts default target and safety regression."""
from pathlib import Path
import copy,hashlib,os,shutil,sys
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1055_faceless_output_contract as s

@pytest.fixture
def authorities():
    keys=('SA1055_RADEN_ROOT','SA1055_GC001_ROOT','SA1055_RADEN_BASE','SA1055_GC001_BASE')
    values=[os.getenv(x) for x in keys]
    if not all(values):pytest.skip('Signed two-case original images and research SVGs are private')
    return [Path(x) for x in values]


def test_signed_original_and_research_baselines_are_immutable(authorities):
    for name,root,svg in zip(s.CASES,authorities[:2],authorities[2:]):
        data,case,tree=s.check_auth(name,root,svg)
        assert data['photo'].shape==(340,340,3)
        assert s.sha(svg)==s.RESEARCH_SHA[name]
        assert s.face_feature_inventory(tree)['face_children']>0
        assert len(case['source_input_sha256']) in (7,8)


def test_forged_svg_rejected(authorities,tmp_path):
    bad=tmp_path/'forged.svg'
    bad.write_bytes(authorities[2].read_bytes()+b'forgery')
    with pytest.raises(ValueError,match='SA1054_RESEARCH_BASELINE_SHA_MISMATCH'):
        s.check_auth('Raden',authorities[0],bad)


def test_forged_original_rejected(authorities,tmp_path):
    required=s.previous.prev.last.prior.prior.dual.CASES['GC001']['root_required']
    for name in required:shutil.copy2(authorities[1]/name,tmp_path/name)
    img=tmp_path/'GC001_source.png';img.write_bytes(img.read_bytes()+b'forgery')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):
        s.check_auth('GC001',tmp_path,authorities[3])


def test_default_removes_only_rendered_face_details(authorities):
    for name,root,ref in zip(s.CASES,authorities[:2],authorities[2:]):
        data,case,svg=s.check_auth(name,root,ref)
        before=s.direct_paint_inventory(svg)
        original=s.face_feature_inventory(svg)
        result,ledger=s.enforce_face_off(svg)
        assert s.audit_default_faceless(result)
        assert len(s.face_guard(result))==1
        assert s.direct_paint_inventory(result)==before
        assert ledger['removed_face_paint_paths']==original['face_children']
        assert ledger['freed_true_path_vertices']==original['path_vertices']
        assert result.get('data-minimalizer-face-features')=='off'
        assert result.get('data-minimalizer-target-style')=='faceless_subject'
        assert len(s.face_guard(svg))>1  # original research stays intact


def test_fail_closed_on_new_eye_path(authorities):
    _,_,svg=s.check_auth('Raden',authorities[0],authorities[2])
    default,_=s.enforce_face_off(svg)
    ET.SubElement(s.face_guard(default),s.NS+'path',{'d':'M 10 10 L 12 12 Z','fill':'#111111'})
    with pytest.raises(ValueError,match='FACIAL_FEATURE_PAINT_FORBIDDEN'):
        s.audit_default_faceless(default)


def test_fail_closed_on_undeclared_mode_and_hidden_raster(authorities):
    _,_,svg=s.check_auth('Raden',authorities[0],authorities[2]);result,_=s.enforce_face_off(svg)
    result.set('data-minimalizer-face-features','enabled')
    with pytest.raises(ValueError,match='FACE_OFF_TARGET_POLICY_UNDECLARED'):
        s.audit_default_faceless(result)
    result.set('data-minimalizer-face-features','off')
    result.insert(len(result)-1,ET.Element(s.NS+'image',{'href':'data:image/png;base64,AAAA'}))
    with pytest.raises(ValueError,match='NONCANONICAL_RENDERER_OBJECT_FORBIDDEN'):
        s.audit_default_faceless(result)


def test_fail_closed_on_extra_face_guard_or_unknown_child(authorities):
    _,_,svg=s.check_auth('GC001',authorities[1],authorities[3]);result,_=s.enforce_face_off(svg)
    ET.SubElement(result,s.NS+'g',{'mask':s.FACE_MASK})
    with pytest.raises(ValueError,match='Signed final face painter'):
        s.audit_default_faceless(result)
    result,_=s.enforce_face_off(svg)
    ET.SubElement(s.face_guard(result),s.NS+'circle',{'cx':'150','cy':'100','r':'2'})
    with pytest.raises(ValueError,match='FACIAL_FEATURE_PAINT_FORBIDDEN'):
        s.audit_default_faceless(result)


def test_strict_unsigned_output_protection(authorities):
    with pytest.raises(ValueError,match='separate'):
        s.evaluate(*authorities,authorities[0])
    with pytest.raises(ValueError,match='overwrite'):
        s.evaluate(*authorities,authorities[2].parent)


def test_real_chromium_signed_faceless_two_case_output(authorities,tmp_path):
    result=s.evaluate(*authorities,tmp_path)
    assert result['target_style']=='faceless_subject'
    assert result['facial_microfeatures_default']=='OFF'
    assert result['production_integration']=='NOT_YET_WIRED'
    assert result['full_character_golden']=='HOLD'
    assert result['production_deployment']=='UNCHANGED'
    for name,expected,freed in (('Raden',1309,103),('GC001',1710,172)):
        case=result['cases'][name]
        assert case['expanded_vertex_count_after']==expected<=case['hard_budget']
        assert case['reclaimed_face_vertices']==freed
        assert case['changed_outside_signed_face']==0
        assert case['changed_signed_arms']==0
        assert case['nonuniform_eroded_face_pixels']==0
        assert case['changed_signed_face_pixels_to_remove_details']>20
        assert case['standard_output_svg_has_zero_facials']
        assert case['canonical_face_photo_mae']>=case['prior_face_photo_mae'] # intentional style, not photo RGB target
        parsed=ET.parse(tmp_path/f'{name.lower()}_faceless.svg').getroot()
        assert s.audit_default_faceless(parsed)
    assert (tmp_path/'sa1055_two_case_faceless_comparison.png').is_file()
    assert not list(tmp_path.glob('*original_private*'))
    assert '"path"' not in (tmp_path/'sa1055_metrics.json').read_text()
