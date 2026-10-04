from __future__ import annotations

import pytest
from minimalizer_zerobase.production.authorized_geometry import (
    AuthorizedGeometryError, fit_authorized_geometry, render_authorized_geometry,
)


def _plan():
    return {"primitives":[
        {"feature_id":"hair","primitive_kind":"bezier_silhouette","ordinal":0},
        {"feature_id":"tie","primitive_kind":"trapezoid","ordinal":0},
        {"feature_id":"tie","primitive_kind":"ribbon","ordinal":1},
    ]}


def _masks():
    return {
        "hair":{"authorized":True,"bbox":[10,5,50,40]},
        "tie":{"authorized":True,"bbox":[28,42,12,30]},
    }


def test_authorized_plan_fits_and_renders_with_existing_svg_renderer():
    scene=fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=_masks(),width=80,height=100,palette={"hair":"#f08040","tie":"#40a060"})
    svg=render_authorized_geometry(scene)
    assert len(scene.primitives)==3
    assert svg.startswith("<svg ")
    assert 'id="golden:hair:bezier_silhouette:0"' in svg
    assert scene.provenance["golden_raster_used"] is False


def test_missing_semantic_mask_fails_closed():
    masks=_masks(); del masks["tie"]
    with pytest.raises(AuthorizedGeometryError,match="missing authorized semantic mask"):
        fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=masks,width=80,height=100,palette={"hair":"#fff","tie":"#000"})


def test_unauthorized_mask_fails_closed():
    masks=_masks(); masks["tie"]["authorized"]=False
    with pytest.raises(AuthorizedGeometryError,match="not authorized"):
        fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=masks,width=80,height=100,palette={"hair":"#fff","tie":"#000"})


def test_extra_mask_cannot_create_unplanned_semantic_part():
    masks=_masks(); masks["eyes"]={"authorized":True,"bbox":[1,1,2,2]}
    with pytest.raises(AuthorizedGeometryError,match="unauthorized feature"):
        fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=masks,width=80,height=100,palette={"hair":"#fff","tie":"#000","eyes":"#111"})


def test_fitter_choice_cannot_change_semantic_identity_or_count():
    a=fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=_masks(),width=80,height=100,palette={"hair":"#fff","tie":"#000"},fitter="native")
    b=fit_authorized_geometry(geometry_plan=_plan(),semantic_masks=_masks(),width=80,height=100,palette={"hair":"#fff","tie":"#000"},fitter="vtracer")
    assert [(x.source_region_id,x.primitive_type) for x in a.primitives]==[(x.source_region_id,x.primitive_type) for x in b.primitives]
    assert len(a.primitives)==len(b.primitives)==3


def test_rendering_is_deterministic():
    kwargs=dict(geometry_plan=_plan(),semantic_masks=_masks(),width=80,height=100,palette={"hair":"#f80","tie":"#0a6"})
    assert render_authorized_geometry(fit_authorized_geometry(**kwargs))==render_authorized_geometry(fit_authorized_geometry(**kwargs))
