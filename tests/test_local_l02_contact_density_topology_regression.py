"""Prevent large class32 additions from joining unrelated frozen components."""
import numpy as np
from scipy import ndimage
from local_l02_contact_density_palette_shadow import propose_contact_density_palette_shadow
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts


def _run(right_owner):
    rgba=np.zeros((160,160,4),dtype=np.uint8)
    rgba[:]=[210,105,130,255]
    cls=np.zeros((160,160),dtype=np.uint8)
    anime=np.zeros((160,160),dtype=np.uint8)
    owner=np.zeros((160,160),dtype=np.uint8)
    owner[15:145,15:31]=1
    owner[15:145,51:67]=right_owner
    cls[15:145,15:67]=32
    anime[15:145,15:67]=10
    out,meta=propose_contact_density_palette_shadow(
        source_rgba=rgba,class_ids=cls,anime_classes=anime,
        baseline_owner=owner)
    assert np.array_equal(out[owner>0],owner[owner>0])
    for oid in (1,2):
        for conn in (1,2):
            st=ndimage.generate_binary_structure(2,conn)
            assert ndimage.label(owner==oid,structure=st)[1] == ndimage.label(out==oid,structure=st)[1]
    verify_no_new_cross_owner_contacts(before=owner,after=out)
    assert meta['Phase4']=='FAIL'
    return out


def test_cross_owner_sleeve_bridge_cannot_join_jacket_and_coat():
    _run(2)


def test_same_owner_sleeve_bridge_cannot_merge_frozen_islands():
    _run(1)
