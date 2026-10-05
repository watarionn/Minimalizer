from minimalizer_zerobase.production.authorized_geometry import fit_authorized_geometry

def test_contour_envelope_drives_polygon_points():
    plan={"primitives":[{"feature_id":"face","primitive_kind":"polygon","ordinal":0}]}
    mask={"face":{"authorized":True,"bbox":[0,0,80,80],"contour_envelope":{"bands":8,"x_extent":[[.25,.75]]*8}}}
    s=fit_authorized_geometry(geometry_plan=plan,semantic_masks=mask,width=100,height=100,palette={"face":"#aaa"})
    pts=s.primitives[0].parameters["points"]
    assert len(pts)==16
    assert min(x for x,y in pts)==20 and max(x for x,y in pts)==60

def test_accent_uses_existing_last_feature_primitive_not_extra_budget():
    plan={"primitives":[{"feature_id":"x","primitive_kind":"polygon","ordinal":0},{"feature_id":"x","primitive_kind":"polygon","ordinal":1}]}
    mask={"x":{"authorized":True,"bbox":[0,0,50,50]}}
    s=fit_authorized_geometry(geometry_plan=plan,semantic_masks=mask,width=50,height=50,palette={"x":"#111"},accent_palette={"x":"#0f0"})
    assert len(s.primitives)==2
    assert s.primitives[0].fill_ref=="#111"
    assert s.primitives[1].fill_ref=="#0f0"

def test_accent_cannot_create_unauthorized_feature():
    import pytest
    from minimalizer_zerobase.production.authorized_geometry import AuthorizedGeometryError
    with pytest.raises(AuthorizedGeometryError):
        fit_authorized_geometry(geometry_plan={"primitives":[{"feature_id":"x","primitive_kind":"polygon","ordinal":0}]},semantic_masks={"x":{"authorized":True,"bbox":[0,0,10,10]}},width=10,height=10,palette={"x":"#111"},accent_palette={"tie":"#0f0"})
