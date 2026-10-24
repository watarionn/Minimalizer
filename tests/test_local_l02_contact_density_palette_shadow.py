"""Source-free negative and invariant checks for an exposed research hypothesis."""
import numpy as np
import pytest
from local_l02_contact_density_palette_shadow import (
    propose_contact_density_palette_shadow, ContactPaletteHold)
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts


def arrays(shape=(160,160)):
    rgba=np.zeros((*shape,4),dtype=np.uint8)
    rgba[:]=[210,105,130,255]
    cls=np.zeros(shape,dtype=np.uint8)
    anime=np.zeros(shape,dtype=np.uint8)
    owner=np.zeros(shape,dtype=np.uint8)
    return rgba,cls,anime,owner


def run(rgba,cls,anime,owner):
    return propose_contact_density_palette_shadow(
        source_rgba=rgba,class_ids=cls,anime_classes=anime,
        baseline_owner=owner)


def test_attached_source_only_sleeve_preserved():
    rgba,cls,anime,owner=arrays()
    owner[15:145,15:31]=1
    cls[15:145,15:41]=32
    anime[15:145,15:41]=10
    out,meta=run(rgba,cls,anime,owner)
    assert meta['new_source_supported_px']>=1024
    assert np.all(out[15:145,15:31]==1)
    assert meta['Phase4']=='FAIL' and not meta['semantic_quality_pass']


def test_weak_contact_component_abstains():
    rgba,cls,anime,owner=arrays()
    owner[15:145,15:31]=1
    cls[15:145,15:130]=32
    anime[15:145,15:130]=10
    out,meta=run(rgba,cls,anime,owner)
    assert np.array_equal(out,owner)
    assert meta['new_source_supported_px']==0


def test_original_owner_is_immutable_and_alpha_is_bounded():
    rgba,cls,anime,owner=arrays()
    owner[15:145,15:31]=1
    cls[15:145,15:41]=32
    anime[15:145,15:41]=10
    rgba[15:145,31:41,3]=0
    out,meta=run(rgba,cls,anime,owner)
    assert np.array_equal(out,owner)
    assert np.all(out[rgba[...,3]==0]==0)


def test_rejects_untrusted_source_owner():
    rgba,cls,anime,owner=arrays()
    owner[15:145,15:31]=1
    rgba[20,20,3]=0
    with pytest.raises(ContactPaletteHold,match='SOURCE_CONTACT_PARTITION_HOLD'):
        run(rgba,cls,anime,owner)


def test_deterministic_without_human_labels():
    rgba,cls,anime,owner=arrays()
    owner[15:145,15:31]=1
    cls[15:145,15:41]=32
    anime[15:145,15:41]=10
    first,a=run(rgba,cls,anime,owner)
    second,b=run(rgba,cls,anime,owner)
    assert np.array_equal(first,second)
    assert a==b
    verify_no_new_cross_owner_contacts(before=owner,after=first)


def test_bad_observer_domain_is_rejected():
    rgba,cls,anime,owner=arrays()
    anime[20,20]=255
    with pytest.raises(ContactPaletteHold,match='SOURCE_CONTACT_PARTITION_HOLD'):
        run(rgba,cls,anime,owner)
