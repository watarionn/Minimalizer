from __future__ import annotations

from minimalizer_zerobase.production.authorized_geometry import fit_authorized_geometry


def test_repeated_feature_primitives_are_not_geometrically_identical():
    plan={"primitives":[
        {"feature_id":"hair","primitive_kind":"bezier_silhouette","ordinal":0},
        {"feature_id":"hair","primitive_kind":"polygon","ordinal":1},
        {"feature_id":"hair","primitive_kind":"polygon","ordinal":2},
    ]}
    masks={"hair":{"authorized":True,"bbox":[10,5,60,50]}}
    scene=fit_authorized_geometry(
        geometry_plan=plan,semantic_masks=masks,width=100,height=100,palette={"hair":"#f80"}
    )
    signatures=[p.parameters for p in scene.primitives]
    assert signatures[0] != signatures[1]
    assert signatures[1] != signatures[2]
    assert all(p.source_region_id=="hair" for p in scene.primitives)


def test_ordinal_decomposition_stays_inside_authorized_bbox():
    plan={"primitives":[
        {"feature_id":"hair","primitive_kind":"polygon","ordinal":i} for i in range(4)
    ]}
    scene=fit_authorized_geometry(
        geometry_plan=plan,
        semantic_masks={"hair":{"authorized":True,"bbox":[20,10,40,60]}},
        width=100,height=100,palette={"hair":"#fff"},
    )
    for primitive in scene.primitives:
        x,y,w,h=primitive.parameters["bbox"]
        assert 20 <= x <= 60 and 10 <= y <= 70
        assert x+w <= 60 and y+h <= 70
        assert w > 0 and h > 0
