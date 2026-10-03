import numpy as np
import pytest

from minimalizer_zerobase.refine.spatial_evidence import observations_from_confidence_npz, spatial_overlap_from_npz

def write_npz(path,confidence,labels=("hair","accessory")):
    np.savez_compressed(path,labels=np.asarray(labels),confidence=np.asarray(confidence,dtype=np.float32))

def test_threshold_matches_phase_e_active_area_rule(tmp_path):
    p=tmp_path/"e.npz"
    write_npz(p,[[[.2,.19],[.8,0]],[[0,0],[0,.21]]])
    obs=observations_from_confidence_npz(p)
    assert obs[0].coverage == .5
    assert obs[1].coverage == .25

def test_self_overlap_is_one(tmp_path):
    p=tmp_path/"e.npz"
    write_npz(p,[[[.8,0],[.3,0]],[[0,.5],[0,0]]])
    assert spatial_overlap_from_npz(p,p) == {"hair":1.0,"accessory":1.0}

def test_equal_coverage_relocation_has_zero_iou(tmp_path):
    a,b=tmp_path/"a.npz",tmp_path/"b.npz"
    write_npz(a,[[[1,0],[0,0]],[[0,0],[0,1]]])
    write_npz(b,[[[0,1],[0,0]],[[0,0],[1,0]]])
    assert spatial_overlap_from_npz(a,b) == {"hair":0.0,"accessory":0.0}

def test_nonfinite_evidence_fails_closed(tmp_path):
    p=tmp_path/"bad.npz"
    write_npz(p,[[[np.nan]],[[0]]])
    with pytest.raises(ValueError,match="non-finite"):
        observations_from_confidence_npz(p)
