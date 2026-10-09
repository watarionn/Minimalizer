"""GC001 signed arm source/visible experiment; baseline frozen, no promotion."""
from pathlib import Path
import copy,json,os,sys,hashlib
import numpy as np
import pytest
from PIL import Image
research = Path(__file__).resolve().parents[2] / "tools" / "research"
sys.path.insert(0, str(research if research.is_dir() else Path(__file__).resolve().parent))
import sa1060_gc_arm_color_experiment as s


def test_synthetic_exact_polygon_mask():
    poly=np.array([[2,2],[8,2],[2,8]],dtype=np.int32)
    m=s.polygon_mask(poly,(12,12))
    assert m[3,3] and not m[0,0] and m.sum()>10


def test_synthetic_source_color_proposals_do_not_synthesize_palette():
    rgb=np.full((80,80,3),[100,100,100],dtype=np.uint8)
    rgb[10:35,10:35]=[215,10,10];rgb[45:70,45:70]=[20,140,245]
    mask=np.ones((80,80),dtype=bool)
    opts=s.candidates(rgb,mask,(100,100,100),'left')
    assert opts
    for a in opts:
        assert len(a['points'])==a['vertices']
        assert 3<=a['vertices']<=7
        assert list(a['rgb']) in ([215,10,10],[20,140,245],[100,100,100])


def test_frozen_metadata_never_allows_promotion():
    assert s.BASE_COST==1873 and s.BUDGET==1887
    assert s.OWNER=={'left':7,'right':2}
    assert s.BASELINE_PNG_SHA=='c51c8bac13f68802b1a7d0022eccd1eff66ae2e4b2f601a7e9b881b936eb4445'


def test_readonly_input_output_overlap_guard(tmp_path):
    with pytest.raises(ValueError,match='PRIVATE_INPUT_OUTPUT_OVERLAP'):
        s.evaluate(tmp_path,tmp_path/'not_allowed')


def test_missing_signed_authority_fails_closed(tmp_path):
    with pytest.raises(ValueError,match='SIGNED_PIN_MISMATCH'):
        s.pin_load(tmp_path)


def test_bad_background_source_edge_fails_closed():
    rgb=np.zeros((340,340,3),dtype=np.uint8)
    with pytest.raises(ValueError,match='SIGNED_BORDER_ANCHOR_AMBIGUOUS'):
        s.border_background_overlap(rgb,np.zeros((340,340),bool))


@pytest.fixture
def source_root():
    p=os.getenv('SA1060_GC_SOURCE_ROOT')
    if not p:pytest.skip('Private signed GC001 input not mounted')
    return Path(p)


def test_pinned_real_owner_and_arm_masks(source_root):
    root,rgb,masks,groups=s.pin_load(source_root)
    assert root.get('data-minimalizer-face-features')=='off'
    assert masks['face'].sum()>4000 and masks['left'].sum()>2000 and masks['right'].sum()>5000
    assert (masks['left']&masks['right']).sum()==0
    background=s.border_background_overlap(rgb,masks['right'])
    assert background['overlap_with_signed_arm_pixels']==533
    assert s.border_background_overlap(rgb,masks['left'])['overlap_with_signed_arm_pixels']==0


def test_actual_chromium_candidate_holds_no_promotion(source_root,tmp_path):
    result=s.evaluate(source_root,tmp_path/'unapproved')
    assert result['trial_candidate_visual_gate']=='HOLD'
    assert not result['trial_candidate_promotion_allowed']
    assert result['production']=='UNCHANGED'
    assert result['expanded_svg_vertices']<=1887
    assert result['signed_face_pixel_changes']==result['pixels_outside_signed_arms_changed']==0
    assert result['signed_arm_mae_after']['left']<result['signed_arm_mae_before']['left']
    assert result['signed_arm_mae_after']['right']<result['signed_arm_mae_before']['right']
    assert result['background_owner_contamination_diagnostic']['right']['overlap_with_signed_arm_pixels']==533
    trial=(tmp_path/'unapproved/gc001_sa1060_arm_candidate.svg').read_text()
    assert 'data-minimalizer-face-features="off"' in trial
    assert '<image' not in trial and 'data:image' not in trial
    assert result['artifact_sha256']['gc001_sa1057_frozen_baseline.png']==s.BASELINE_PNG_SHA
