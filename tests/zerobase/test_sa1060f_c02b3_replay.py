"""C02b3 replay: no-private-input smoke and signed source verification."""
import importlib.util, os, hashlib
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from io import BytesIO
P=Path(__file__).resolve().parents[2]/'tools/research/sa1060f_c02b3_replay.py'
if not P.exists(): P=Path(__file__).with_name('sa1060f_c02b3_replay.py')
spec=importlib.util.spec_from_file_location('sa1060f_c02b3_replay',P)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

@pytest.fixture
def signed():
    vals=[os.getenv(k) for k in ('SA1060F_GC_SOURCE','SA1060F_STAGE_SNAPSHOT')]
    if not all(vals): pytest.skip('Signed GC001 inputs not provided')
    return tuple(map(Path,vals))

def test_binary_mask_rejects_nonbinary():
    a=np.zeros((340,340),np.uint8);a[20,20]=128
    f=BytesIO();Image.fromarray(a).save(f,format='PNG')
    with pytest.raises(ValueError,match='MASK_SHAPE_OR_VALUES'):s.binary(f.getvalue())

def test_binary_mask_rejects_wrong_shape():
    f=BytesIO();Image.fromarray(np.zeros((341,340),np.uint8)).save(f,format='PNG')
    with pytest.raises(ValueError,match='MASK_SHAPE_OR_VALUES'):s.binary(f.getvalue())

def test_digest_deterministic():
    assert s.digest(b'abc')==hashlib.sha256(b'abc').hexdigest()

def test_fail_closed_wrong_source_before_snapshot(tmp_path):
    p=tmp_path/'source.png';p.write_bytes(b'wrong')
    with pytest.raises(ValueError,match='SOURCE_PIN_FAIL'):s.probe(p,tmp_path/'missing.zip')

def test_nonpromoting_policy_in_code():
    t=P.read_text('utf-8')
    assert "'release_authorized':False" in t
    assert "'production_changed':False" in t
    assert "'human_golden':'PENDING'" in t

def test_real_source_metrics_and_determinism(signed):
    a=s.probe(*signed);b=s.probe(*signed)
    assert a==b
    assert a['original_arm_pixels']==6486
    assert a['original_arm_edges']==1353
    assert a['disputed_pixels']==16
    assert [a['variants'][str(k)]['retained'] for k in (2,4,6)]==[2542,2543,2527]
    assert [a['variants'][str(k)]['removed_source_edges'] for k in (2,4,6)]==[788,787,790]
    assert all(v['added_pixels']==0 for v in a['variants'].values())
    assert not a['release_authorized'] and not a['production_changed']

def test_snapshot_tamper_rejected(signed,tmp_path):
    src,snap=signed;p=tmp_path/'bad.zip';b=bytearray(snap.read_bytes());b[-1]^=1;p.write_bytes(b)
    with pytest.raises(ValueError,match='SNAPSHOT_PIN_FAIL'):s.probe(src,p)

def test_source_tamper_rejected(signed,tmp_path):
    src,snap=signed;p=tmp_path/'bad.png';b=bytearray(src.read_bytes());b[-1]^=1;p.write_bytes(b)
    with pytest.raises(ValueError,match='SOURCE_PIN_FAIL'):s.probe(p,snap)
