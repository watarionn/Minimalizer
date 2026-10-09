"""C02a: non-promoting validated archive and signed-owner drift audit."""
from __future__ import annotations
from pathlib import Path
import hashlib, importlib.util, json, os, sys, zipfile
import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'tools/research/sa1060c_phase03_phase04_provenance.py'
if not SCRIPT.is_file(): SCRIPT=Path(__file__).with_name('sa1060c_phase03_phase04_provenance.py')
sys.path.insert(0,str(SCRIPT.parent))
spec=importlib.util.spec_from_file_location('sa1060c_phase03_phase04_provenance',SCRIPT)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def test_signed_stage4_unmodified_common_roles():
    a=np.zeros((340,340),bool);a[20:30,30:50]=1
    b=a.copy();b[40:46,70:80]=1
    data=s.assert_role_history({'right_arm':a,'left_arm':a,'face':a},
                               {'right_arm':a,'left_arm':b,'face':a})
    assert data['left_arm']['historical_extra_pixels']==60
    assert data['left_arm']['raster_xor']==60
    assert data['right_arm']['raster_xor']==0


def test_signed_face_owner_changes_fail_closed():
    a=np.zeros((340,340),bool);b=a.copy();b[20,20]=1
    with pytest.raises(ValueError,match='EXPECTED_SHARED_RIGHT_ARM_OR_FACE_CHANGED'):
        s.assert_role_history({'right_arm':a,'left_arm':a,'face':a},
                              {'right_arm':a,'left_arm':a,'face':b})


def test_wrong_canvas_in_role_history_rejected():
    a=np.zeros((340,340),bool);b=np.zeros((340,341),bool)
    with pytest.raises(ValueError,match='HISTORICAL_MASK_SHAPE_MISMATCH'):
        s.assert_role_history({'right_arm':a,'left_arm':a,'face':a},
                              {'right_arm':a,'left_arm':b,'face':a})


def test_nonbinary_image_rejected():
    from PIL import Image
    from io import BytesIO
    a=np.zeros((340,340),np.uint8);a[0,0]=120
    f=BytesIO();Image.fromarray(a).save(f,format='PNG')
    with pytest.raises(ValueError,match='PHASE3_4_MASK_NOT_PINNED_BINARY'):
        s.read_mask(f.getvalue())


def test_zip_absence_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        s.validate_archive(tmp_path/'not_a_zip.zip')


def test_zip_digest_tamper_rejected(tmp_path):
    f=tmp_path/'tamper.zip';f.write_bytes(b'something unverified')
    with pytest.raises(ValueError,match='PHASE03_04_PRIVATE_ZIP_SHA_MISMATCH'):
        s.validate_archive(f)


def test_archive_manifest_path_and_member_sha(tmp_path):
    # Snapshot digest bypass tests exercise member validation explicitly.
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('PRIVATE_SHA_MANIFEST.json',json.dumps({'source_sha256':s.SOURCE_SHA,
            'promotion_authorized':False,'files':{'../escape.txt':'wrong'}}))
        z.writestr('../escape.txt','content')
    with pytest.raises(ValueError,match='SNAPSHOT_MANIFEST_INCOMPLETE'):
        s.validate_archive(bad,require_pin=False)


def test_forged_release_flag_rejected(tmp_path):
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('PRIVATE_SHA_MANIFEST.json',json.dumps({'source_sha256':s.SOURCE_SHA,
            'promotion_authorized':True,'files':{}}))
    with pytest.raises(ValueError,match='SOURCE_BINDING_OR_RELEASE_STATUS_INVALID'):
        s.validate_archive(bad,require_pin=False)


def test_authority_parent_never_writable(tmp_path):
    with pytest.raises(ValueError,match='OUTPUT_INSIDE_SIGNED_AUTHORITY'):
        s.analyze(tmp_path/'x',tmp_path,tmp_path/'y',tmp_path/'unapproved')


def test_private_report_public_allowlist_exists():
    code=SCRIPT.read_text('utf-8')
    assert 'source_connected_rgb_is_not_anatomy_truth' in code
    assert 'release_authorized\':False' in code
    assert 'original_stage8_budget\':\'HOLD' in code
    assert 'private_board_filename' in code and 'c02a_public_numeric.json' in code


@pytest.fixture
def real_inputs():
    keys=('SA1060C_GC_SOURCE','SA1060C_SIGNED_DIR','SA1060C_STAGE_SNAPSHOT')
    files=[os.getenv(x) for x in keys]
    if not all(files):pytest.skip('Private signed GC001 source and phase03/04 snapshot absent')
    return [Path(x) for x in files]


def test_real_immutable_phase03_phase04_owner_lineage(real_inputs,tmp_path):
    src,signed,snapshot=real_inputs
    data=s.analyze(src,signed,snapshot,tmp_path/'audit')
    assert data['metrics']['phase03_subject']['exact_border_connected_rgb_overlap']==648
    assert data['metrics']['phase04_roles']['right_arm']['exact_border_connected_rgb_overlap']==533
    assert data['metrics']['phase04_roles']['hair']['exact_border_connected_rgb_overlap']==31
    assert data['metrics']['historical_sa1041_vs_current']['left_arm']['raster_xor']==385
    assert data['metrics']['historical_sa1041_vs_current']['right_arm']['raster_xor']==0
    assert data['source_connected_rgb_is_not_anatomy_truth']
    assert not data['release_authorized'] and not data['production_changed']
    public=json.loads((tmp_path/'audit/c02a_public_numeric.json').read_text('utf-8'))
    assert 'metrics' not in public and 'private_board_filename' not in public
    assert not public['release_authorized']


def test_two_fresh_replay_artifact_shas_match(real_inputs,tmp_path):
    src,signed,snapshot=real_inputs
    s.analyze(src,signed,snapshot,tmp_path/'run1')
    s.analyze(src,signed,snapshot,tmp_path/'run2')
    for name in ('gc001_p03_p04_history_private_board.png','c02a_private_replay.json','c02a_public_numeric.json'):
        def digest(dir):return hashlib.sha256((dir/name).read_bytes()).hexdigest()
        assert digest(tmp_path/'run1')==digest(tmp_path/'run2'),name
