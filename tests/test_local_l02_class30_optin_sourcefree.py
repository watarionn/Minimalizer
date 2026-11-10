"""Source-free opt-in class30 extension; default class32 policy must be identical."""
import numpy as np
import pytest
from local_l02_contact_density_partition_shadow import (
    propose_contact_density_partition_shadow, ContactDensityHold,
)

def synthetic():
    shape=(256,64)
    rgba=np.zeros((*shape,4),dtype=np.uint8)
    rgba[:,:,:3]=[165,92,115]
    rgba[:,:,3]=255
    classes=np.zeros(shape,dtype=np.uint8)
    owner=np.zeros(shape,dtype=np.uint8)
    anime=np.zeros(shape,dtype=np.uint8)
    owner[10:210,0:10]=1
    classes[10:210,0]=5
    classes[10:210,1:10]=32
    classes[10:210,10:16]=30
    anime[10:210,0:16]=10
    return rgba,classes,anime,owner

def test_default_abstains_class30_and_optin_adds_without_relabel():
    rgba,cls,anime,owner=synthetic()
    kw=dict(source_rgba=rgba,class_ids=cls,anime_classes=anime,baseline_owner=owner)
    default,_=propose_contact_density_partition_shadow(**kw)
    assert np.array_equal(default,owner)
    out,meta=propose_contact_density_partition_shadow(**kw,eligible_classes=(30,32))
    assert meta['new_source_supported_px']>0
    assert np.array_equal(out[owner>0],owner[owner>0])
    assert not np.any((out>0)&(rgba[:,:,3]==0))
    assert not np.any((out>0)&~np.isin(cls,[5,30,32]))

def test_optin_requires_exact_whitelist():
    rgba,cls,anime,owner=synthetic()
    with pytest.raises(ContactDensityHold,match='UNAPPROVED_ELIGIBLE_CLASS_POLICY'):
        propose_contact_density_partition_shadow(source_rgba=rgba,class_ids=cls,
            anime_classes=anime,baseline_owner=owner,eligible_classes=(25,30,32))
    with pytest.raises(ContactDensityHold,match='UNAPPROVED_ELIGIBLE_CLASS_POLICY'):
        propose_contact_density_partition_shadow(source_rgba=rgba,class_ids=cls,
            anime_classes=anime,baseline_owner=owner,eligible_classes=np.array([30,32]))

def test_alpha_and_unknown_preserved():
    rgba,cls,anime,owner=synthetic()
    rgba[10:210,14:16,3]=0
    out,_=propose_contact_density_partition_shadow(source_rgba=rgba,class_ids=cls,
        anime_classes=anime,baseline_owner=owner,eligible_classes=(30,32))
    assert not np.any(out[rgba[:,:,3]==0])
    assert np.array_equal(out[owner>0],owner[owner>0])
