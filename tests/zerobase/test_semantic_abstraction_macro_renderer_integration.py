import numpy as np,pytest
from minimalizer_zerobase.compose.composer import ComposedPrimitive,VectorScene
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import MacroGeometryPrimitive
from minimalizer_zerobase.semantic_abstraction.macro_renderer_integration import *
def prim(i,r,z):return ComposedPrimitive(i,r,i,"convex_polygon",{"points":[[0,0],[2,0],[1,2]]},"#111",z)
def macro(r):return MacroGeometryPrimitive(r,np.array([[1,1],[5,1],[3,5]]),10,9)
def scene():return VectorScene(10,10,(prim("h","hair",1),prim("c","major_clothing",2),prim("a","left_arm",3)),{"golden_raster_used":False})
def test_replaces_only_authorized_macro_roles():
 r=replace_macro_roles(scene(),(macro("hair"),macro("major_clothing")),{"hair":"#222","major_clothing":"#333"})
 assert len([p for p in r.scene.primitives if p.source_region_id=="hair"])==1 and any(p.source_region_id=="left_arm" for p in r.scene.primitives)
def test_missing_role_fails_closed():
 with pytest.raises(ValueError):replace_macro_roles(scene(),(macro("hair"),),{"hair":"#222","major_clothing":"#333"})
def test_unknown_role_fails_closed():
 with pytest.raises(ValueError):replace_macro_roles(scene(),(macro("hair"),macro("major_clothing"),macro("face")),{"hair":"#222","major_clothing":"#333"})
def test_no_golden_authority():
 r=replace_macro_roles(scene(),(macro("hair"),macro("major_clothing")),{"hair":"#222","major_clothing":"#333"})
 assert r.scene.provenance["golden_raster_used"] is False

def test_identity_accent_is_recomposed_last():
 s=VectorScene(10,10,(prim("h","hair",5),prim("c","major_clothing",6),prim("identity-accent-goggle","head",1)),{"golden_raster_used":False})
 r=replace_macro_roles(s,(macro("hair"),macro("major_clothing")),{"hair":"#222","major_clothing":"#333"})
 accent=next(p for p in r.scene.primitives if p.primitive_id=="identity-accent-goggle")
 assert accent.z_order==max(p.z_order for p in r.scene.primitives)


def test_residual_layers_get_explicit_ids():
    base=macro("hair")
    residual=MacroGeometryPrimitive(
        "hair",
        np.array([[6,6],[8,6],[7,8]]),
        3,
        3,
        layer_kind="residual",
        component_index=4,
    )
    r=replace_macro_roles(
        scene(),
        (base,residual,macro("major_clothing")),
        {"hair":"#222","major_clothing":"#333"},
    )
    ids={p.primitive_id for p in r.scene.primitives}
    assert "semantic-macro:hair:0" in ids
    assert "semantic-macro-residual:hair:4" in ids
