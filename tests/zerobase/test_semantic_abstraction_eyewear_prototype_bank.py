import numpy as np,pytest
from minimalizer_zerobase.semantic_abstraction.eyewear_prototype_bank import *
H1="1"*64;H2="2"*64
def test_bank_is_hash_frozen_and_order_invariant():
 a=PrototypeEntry(H1,np.array([1,2,0],np.float32));b=PrototypeEntry(H2,np.array([2,1,0],np.float32),"negative")
 x=build_prototype_bank((a,b));y=build_prototype_bank((b,a));assert x["bank_sha256"]==y["bank_sha256"] and len(x["bank_sha256"])==64
def test_requires_source_hash():
 with pytest.raises(ValueError):build_prototype_bank((PrototypeEntry("x",np.array([1,0],np.float32)),))
def test_rejects_zero_vector():
 with pytest.raises(ValueError):build_prototype_bank((PrototypeEntry(H1,np.zeros(2,np.float32)),))
def test_centroid_uses_positive_only():
 b=build_prototype_bank((PrototypeEntry(H1,np.array([1,0],np.float32)),PrototypeEntry(H2,np.array([0,1],np.float32),"negative")))
 assert np.allclose(positive_centroid(b),[1,0])
