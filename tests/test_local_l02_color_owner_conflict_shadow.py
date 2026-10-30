"""Source-free safety tests; these are not visual-quality acceptance."""
import sys
from pathlib import Path
import numpy as np
import pytest
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_color_owner_conflict_shadow import propose_color_owner_conflict_shadow,ColorOwnerConflictHold

def fixture():
    rgba=np.zeros((80,160,4),dtype=np.uint8);rgba[...,3]=255
    colors=([206,180,127],[43,70,137],[148,114,68],[60,42,31])
    for j,color in enumerate(colors):rgba[:,40*j:40*(j+1),:3]=color
    classes=np.full((80,160),10,dtype=np.uint8)
    owner=np.full((80,160),2,dtype=np.uint8)
    ind=np.ones((80,160),dtype=np.uint8)
    ind[:,40:80]=0
    ind[::8,40:80]=1
    return rgba,classes,ind,owner

def test_independent_positive_protected_and_topology_preserved():
    rgba,classes,ind,owner=fixture()
    out,meta=propose_color_owner_conflict_shadow(source_rgba=rgba,class_ids=classes,independent_outerwear=ind,frozen_owner=owner)
    assert meta['removed_px']>1000
    assert np.array_equal(out[ind==1],owner[ind==1])
    assert np.all((out==0)|(out==owner))
    for conn in (1,2):
        st=ndimage.generate_binary_structure(2,conn)
        assert ndimage.label(owner==2,structure=st)[1]==ndimage.label(out==2,structure=st)[1]
    assert meta['semantic_quality_pass'] is False

def test_unsupported_mode_without_support_gap_is_noop():
    rgba,classes,ind,owner=fixture()
    ind[:]=1
    out,meta=propose_color_owner_conflict_shadow(source_rgba=rgba,class_ids=classes,independent_outerwear=ind,frozen_owner=owner)
    np.testing.assert_array_equal(out,owner)
    assert meta['removed_px']==0

def test_invalid_owner_source_fails_closed():
    rgba,classes,ind,owner=fixture()
    rgba[0,0,3]=0
    with pytest.raises(ColorOwnerConflictHold,match='OUTSIDE_SIGNED_ALPHA'):
        propose_color_owner_conflict_shadow(source_rgba=rgba,class_ids=classes,independent_outerwear=ind,frozen_owner=owner)
