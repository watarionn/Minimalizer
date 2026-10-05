import numpy as np,pytest
from minimalizer_zerobase.compose.composer import ComposedPrimitive,VectorScene
from minimalizer_zerobase.semantic_abstraction.canonical_macro_stage import *
def p(i,r,z):return ComposedPrimitive(i,r,i,"convex_polygon",{"points":[[2,2],[8,2],[5,8]]},"#111",z)
def scene():return VectorScene(20,20,(p("h","hair",1),p("c","major_clothing",2),p("a","left_arm",3)),{"golden_raster_used":False})
def masks():
 h=np.zeros((20,20),np.uint8);c=np.zeros_like(h);h[2:9,3:14]=1;c[10:18,5:15]=1;return {"hair":h,"major_clothing":c}
def test_stage_uses_semantic_roles_not_indices():
 r=apply_semantic_macro_stage(scene(),masks(),{"hair":"#222","major_clothing":"#333"})
 assert r.replaced_roles==("hair","major_clothing") and any(x.source_region_id=="left_arm" for x in r.scene.primitives)
 assert r.scene.provenance["semantic_macro_stage"]==CANONICAL_MACRO_STAGE_VERSION
def test_missing_scene_authority_fails():
 s=VectorScene(20,20,(p("h","hair",1),),{})
 with pytest.raises(ValueError):apply_semantic_macro_stage(s,masks(),{"hair":"#222","major_clothing":"#333"})
def test_missing_mask_fails():
 with pytest.raises(ValueError):apply_semantic_macro_stage(scene(),{"hair":masks()["hair"]},{"hair":"#222","major_clothing":"#333"})
