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


def test_mask_descriptor_biases_geometry_but_stays_inside_authority():
    plan={"primitives":[{"feature_id":"hair","primitive_kind":"polygon","ordinal":i} for i in range(2)]}
    left={"hair":{"authorized":True,"bbox":[10,10,80,80],"mask_descriptor":{"grid":[4,4],"occupancy":[[1,0,0,0]]*4}}}
    right={"hair":{"authorized":True,"bbox":[10,10,80,80],"mask_descriptor":{"grid":[4,4],"occupancy":[[0,0,0,1]]*4}}}
    a=fit_authorized_geometry(geometry_plan=plan,semantic_masks=left,width=100,height=100,palette={"hair":"#fff"})
    b=fit_authorized_geometry(geometry_plan=plan,semantic_masks=right,width=100,height=100,palette={"hair":"#fff"})
    assert a.primitives[0].parameters != b.primitives[0].parameters
    for scene in (a,b):
        for p in scene.primitives:
            x,y,w,h=p.parameters["bbox"]
            assert x>=10 and y>=10 and x+w<=90 and y+h<=90
