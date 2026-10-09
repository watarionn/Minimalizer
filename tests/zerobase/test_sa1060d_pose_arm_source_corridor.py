"""Non-promoting structural source corridor verification, synthetic + pinned real."""
from __future__ import annotations
import hashlib,importlib.util,json,os,sys
from pathlib import Path
import numpy as np,pytest
P=Path(__file__).resolve().parents[2]/'tools/research/sa1060d_pose_arm_source_corridor.py'
if not P.is_file():P=Path(__file__).with_name('sa1060d_pose_arm_source_corridor.py')
sys.path.insert(0,str(P.parent))
spec=importlib.util.spec_from_file_location('sa1060d_pose_arm_source_corridor',P)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

def synthetic():
    mask=np.ones((340,340),bool)
    points=np.ones((17,2),np.float32)*50
    points[5]=[150,120];points[6]=[100,120];points[8]=[80,210];points[10]=[75,300]
    scores=np.ones(17,np.float32)
    return mask,points,scores,50.0

def test_factor_authority_locked():
    mask,points,scores,span=synthetic()
    with pytest.raises(ValueError,match='UNAPPROVED_CORRIDOR_FACTOR'):
        s.signed_corridor(mask,points,scores,span,0.90)

def test_restrict_only_never_add_pixels_and_no_source_image_copy():
    mask,points,scores,span=synthetic()
    mask[:50]=False
    candidate,support,d=s.signed_corridor(mask,points,scores,span,.20)
    assert np.all(candidate<=mask)
    assert d['added_pixels']==0
    assert d['candidate_pixels']+d['removed_pixels']==int(mask.sum())

def test_pose_confidence_guard():
    mask,points,scores,span=synthetic()
    scores[10]=.462
    candidate,support,d=s.signed_corridor(mask,points,scores,span,.20)
    assert not d['pose_confidence_pass'] and d['min_right_pose_score']<.6

def test_pose_score_pass_does_not_approve_artwork():
    mask,points,scores,span=synthetic()
    scores[10]=.9
    _,_,d=s.signed_corridor(mask,points,scores,span,.27)
    assert d['pose_confidence_pass']
    # The script itself still keeps full Chromium/Golden gates HOLD.
    code=P.read_text('utf-8')
    assert "stats['release_candidate_valid']=False" in code
    assert "'release_authorized':False" in code

def test_reject_invalid_shape_and_nan():
    mask,points,scores,span=synthetic()
    with pytest.raises(ValueError,match='UNVERIFIED_POSE_CANVAS'):
        s.signed_corridor(mask[:-1],points,scores,span,.20)
    points[6,0]=np.nan
    with pytest.raises(ValueError,match='INVALID_POSE_EVIDENCE'):
        s.signed_corridor(mask,points,scores,span,.20)

def test_reject_output_writing_over_authority(tmp_path):
    with pytest.raises(ValueError,match='OUTPUT_INSIDE_SIGNED_AUTHORITY'):
        s.run(tmp_path/'source.png',tmp_path,tmp_path/'stages.zip',tmp_path/'oops')

def test_no_generated_or_raster_embedding_code_paths():
    txt=P.read_text('utf-8')
    assert "generated_pixels':False" in txt
    assert "'chromium_full_character':'NOT_RUN'" in txt
    assert "'independent_raden_control':'NOT_RUN'" in txt

@pytest.fixture
def signed():
    vals=[os.getenv(x) for x in ('SA1060D_GC_SOURCE','SA1060D_SIGNED_DIR','SA1060D_STAGE_SNAPSHOT')]
    if not all(vals):pytest.skip('Signed source+historical masks+private snapshot not provided')
    return tuple(Path(x) for x in vals)

def test_actual_signed_model_confidence_and_source_risk(signed,tmp_path):
    r=s.run(*signed,tmp_path/'one')
    assert r['pose_confidence_gate']=='HOLD'
    assert not r['release_authorized']
    a=r['candidates']['0.2']
    assert a['candidate_pixels']==3096
    assert a['removed_pixels']==3390
    assert a['source_rgb_border_connected_removed']==533
    assert a['source_rgb_border_connected_remaining']==0
    assert a['candidate_connected_components']==1
    assert a['right_shoulder_elbow_wrist_scores'][-1]<.6
    assert r['independent_raden_control']=='NOT_RUN'

def test_signed_real_deterministic_two_run(signed,tmp_path):
    s.run(*signed,tmp_path/'first');s.run(*signed,tmp_path/'second')
    for n in ('c02b1_PRIVATE_metrics.json','c02b1_coordinate_free_public.json','gc001_pose_corridor_three_variants_PRIVATE.png'):
        a=hashlib.sha256((tmp_path/'first'/n).read_bytes()).digest()
        b=hashlib.sha256((tmp_path/'second'/n).read_bytes()).digest()
        assert a==b
