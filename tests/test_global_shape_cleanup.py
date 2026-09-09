from minimalize_engine.analysis.shape_cleanup import cleanup_minimal_shapes
from minimalize_engine.models import Shape


def rect(i, x, y, w, h, **kw):
    return Shape(
        id=i,
        shape_type="rectangle",
        fill_color=kw.pop("fill_color", (100, 100, 100)),
        x=x,
        y=y,
        width=w,
        height=h,
        importance=kw.pop("importance", 0.4),
        semantic_type=kw.pop("semantic_type", "generic"),
        character_part=kw.pop("character_part", "unknown"),
        source_role=kw.pop("source_role", "misc"),
        layer_name=kw.pop("layer_name", "midground"),
        **kw,
    )


def test_thin_generic_rectangle_is_removed():
    shapes = [rect(1, 10, 20, 1.5, 30.0, importance=0.3)]
    out, report = cleanup_minimal_shapes(shapes, 220, 220)
    assert out == []
    assert report.removed_thin == 1
    assert report.decisions[0].reason == "thin_sliver"


def test_semantic_limb_is_protected_even_if_thin():
    shapes = [rect(
        1, 10, 20, 1.5, 30.0,
        semantic_type="character_left_arm",
        character_part="left_arm",
        source_role="character_limb",
    )]
    out, report = cleanup_minimal_shapes(shapes, 220, 220)
    assert len(out) == 1
    assert report.removed_count == 0
    assert report.protected_count == 1


def test_tiny_low_importance_fragment_is_removed_but_salient_accent_survives():
    shapes = [
        rect(1, 1, 1, 2, 2, importance=0.2),
        rect(2, 10, 10, 2, 2, importance=0.95),
    ]
    out, report = cleanup_minimal_shapes(shapes, 220, 220)
    assert [s.id for s in out] == [2]
    assert report.removed_micro == 1


def test_near_duplicate_same_color_shape_is_removed():
    shapes = [
        rect(1, 10, 10, 30, 30, importance=0.8, fill_color=(80, 90, 100)),
        rect(2, 11, 11, 28, 28, importance=0.3, fill_color=(82, 91, 101)),
    ]
    out, report = cleanup_minimal_shapes(shapes, 220, 220, remove_duplicates=True)
    assert len(out) == 1
    assert out[0].id == 1
    assert report.removed_duplicate == 1


def test_cleanup_can_be_disabled():
    shapes = [rect(1, 10, 20, 1.0, 40.0)]
    out, report = cleanup_minimal_shapes(shapes, 220, 220, enable=False)
    assert len(out) == 1
    assert report.enabled is False


def test_adjacent_same_color_small_rectangles_merge_to_one_polygon():
    shapes = [
        rect(1, 10, 10, 12, 10, importance=0.5, fill_color=(80, 90, 100)),
        rect(2, 22.4, 10, 12, 10, importance=0.4, fill_color=(82, 91, 101)),
    ]
    out, report = cleanup_minimal_shapes(
        shapes, 220, 220,
        remove_isolated=False,
        merge_gap_ratio=0.01,
        promote_primitives=False,
    )
    assert len(out) == 1
    assert out[0].shape_type == "polygon"
    assert report.merged_count == 1
    assert any(d.reason == "adjacent_same_color" for d in report.decisions)


def test_jagged_generic_polygon_is_simplified_without_shape_loss():
    points = [
        (10, 10), (20, 10), (30, 10.2), (40, 10),
        (40, 20), (40.2, 30), (40, 40), (30, 40),
        (20, 39.8), (10, 40), (10, 30), (9.8, 20),
    ]
    s = Shape(
        id=1, shape_type="polygon", fill_color=(100, 100, 100),
        points=points, importance=0.6, semantic_type="generic",
        source_role="misc", layer_name="midground",
    )
    out, report = cleanup_minimal_shapes(
        [s], 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
    )
    assert len(out) == 1
    assert len(out[0].points) < len(points)
    assert report.simplified_count == 1
    assert report.vertices_after < report.vertices_before


def test_isolated_low_value_fragment_is_removed():
    shapes = [
        rect(1, 10, 10, 40, 40, importance=0.8),
        rect(2, 190, 190, 4, 4, importance=0.2),
    ]
    out, report = cleanup_minimal_shapes(
        shapes, 220, 220,
        micro_area_ratio=0.00001,
        merge_adjacent=False,
        simplify_polygons=False,
    )
    assert [s.id for s in out] == [1]
    assert report.removed_isolated == 1
    assert any(d.reason == "isolated_fragment" for d in report.decisions)


def test_protected_hair_fragment_is_not_removed_as_isolated():
    shapes = [
        rect(1, 10, 10, 40, 40, importance=0.8),
        rect(
            2, 190, 190, 4, 4, importance=0.2,
            semantic_type="character_hair_tip",
            character_part="hair",
            source_role="character_hair",
        ),
    ]
    out, report = cleanup_minimal_shapes(
        shapes, 220, 220,
        micro_area_ratio=0.00001,
        merge_adjacent=False,
        simplify_polygons=False,
    )
    assert len(out) == 2
    assert report.removed_isolated == 0


def test_moderately_long_ultrathin_generic_rectangle_is_removed():
    # This is too short to trip the old 8:1 sliver rule, but visually it is
    # still a needle-like segmentation artifact at a 220px working canvas.
    shapes = [rect(1, 10, 20, 2.0, 11.0, importance=0.75)]
    out, report = cleanup_minimal_shapes(shapes, 220, 220)
    assert out == []
    assert report.removed_thin == 1
    assert report.decisions[0].reason == "thin_rectangle"


def test_ultrathin_rectangle_still_respects_semantic_protection():
    shapes = [rect(
        1, 10, 20, 2.0, 11.0, importance=0.75,
        semantic_type="character_hair_strand",
        character_part="hair",
        source_role="character_hair",
    )]
    out, report = cleanup_minimal_shapes(shapes, 220, 220)
    assert len(out) == 1
    assert report.removed_count == 0
    assert report.protected_count == 1


def test_role_touching_fragment_absorbs_small_fragment_into_larger_same_role_shape():
    shapes = [
        rect(1, 10, 10, 52, 36, importance=0.8, fill_color=(90, 100, 110),
             semantic_type="generic_panel", source_role="structure"),
        rect(2, 62.0, 20, 8, 8, importance=0.3, fill_color=(92, 101, 109),
             semantic_type="generic_panel", source_role="structure"),
    ]
    out, report = cleanup_minimal_shapes(
        shapes, 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
        role_fragment_merge=True,
        simplify_polygons=False,
    )
    assert len(out) == 1
    assert out[0].id == 1
    assert out[0].shape_type == "polygon"
    assert report.role_fragment_merged_count == 1
    assert any(d.reason == "role_touching_fragment" for d in report.decisions)


def test_role_touching_fragment_does_not_merge_different_roles():
    shapes = [
        rect(1, 10, 10, 52, 36, importance=0.8, fill_color=(90, 100, 110),
             semantic_type="generic_panel", source_role="structure"),
        rect(2, 62.0, 20, 8, 8, importance=0.3, fill_color=(92, 101, 109),
             semantic_type="generic_panel", source_role="accent"),
    ]
    out, report = cleanup_minimal_shapes(
        shapes, 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
        role_fragment_merge=True,
        simplify_polygons=False,
    )
    assert len(out) == 2
    assert report.role_fragment_merged_count == 0


def test_near_rectangle_polygon_is_promoted_to_rectangle():
    s = Shape(
        id=31, shape_type="polygon", fill_color=(120, 130, 140),
        points=[(10, 10), (40, 10.2), (40.1, 30), (25, 30.1), (10, 30)],
        importance=0.6, semantic_type="generic", source_role="misc", layer_name="midground",
    )
    out, report = cleanup_minimal_shapes(
        [s], 220, 220, remove_isolated=False, merge_adjacent=False,
        simplify_polygons=False, promote_rectangle_iou=0.94,
    )
    assert len(out) == 1
    assert out[0].shape_type == "rectangle"
    assert any(d.reason == "polygon_to_rectangle" and d.action == "promote" for d in report.decisions)


def test_near_ellipse_polygon_is_promoted_to_ellipse():
    pts = [(50, 20), (62, 24), (70, 35), (70, 45), (62, 56), (50, 60),
           (38, 56), (30, 45), (30, 35), (38, 24)]
    s = Shape(
        id=32, shape_type="polygon", fill_color=(120, 130, 140), points=pts,
        importance=0.6, semantic_type="generic", source_role="misc", layer_name="midground",
    )
    out, report = cleanup_minimal_shapes(
        [s], 220, 220, remove_isolated=False, merge_adjacent=False,
        simplify_polygons=False, promote_rectangle_iou=0.99, promote_ellipse_iou=0.90,
    )
    assert len(out) == 1
    assert out[0].shape_type == "ellipse"
    assert any(d.reason == "polygon_to_ellipse" and d.action == "promote" for d in report.decisions)


def test_primitive_promotion_respects_character_protection():
    s = Shape(
        id=33, shape_type="polygon", fill_color=(120, 130, 140),
        points=[(10, 10), (40, 10), (40, 30), (10, 30)], importance=0.6,
        semantic_type="character_hair_lock", character_part="hair",
        source_role="character_hair", layer_name="foreground",
    )
    out, report = cleanup_minimal_shapes(
        [s], 220, 220, remove_isolated=False, merge_adjacent=False,
        simplify_polygons=False,
    )
    assert out[0].shape_type == "polygon"
    assert not any(d.action == "promote" for d in report.decisions)


def test_global_score_removes_moderate_low_value_sliver_that_legacy_rules_keep():
    sliver = Shape(
        id=80,
        shape_type="polygon",
        fill_color=(96, 100, 104),
        points=[(10, 10), (28, 10), (28, 15), (10, 15)],
        importance=0.85,
        semantic_type="generic",
        source_role="misc",
        layer_name="background",
    )

    legacy, _ = cleanup_minimal_shapes(
        [sliver], 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
        simplify_polygons=False,
        promote_primitives=False,
    )
    assert [s.id for s in legacy] == [80]

    out, report = cleanup_minimal_shapes(
        [sliver], 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
        simplify_polygons=False,
        promote_primitives=False,
        global_scores={80: 0.20},
        global_thin_enable=True,
    )
    assert out == []
    assert report.removed_thin == 1
    assert any(d.reason == "global_low_value_sliver" for d in report.decisions)


def test_global_score_preserves_same_geometry_when_global_value_is_high():
    sliver = Shape(
        id=81,
        shape_type="polygon",
        fill_color=(96, 100, 104),
        points=[(10, 10), (28, 10), (28, 15), (10, 15)],
        importance=0.85,
        semantic_type="generic",
        source_role="misc",
        layer_name="foreground",
    )

    out, report = cleanup_minimal_shapes(
        [sliver], 220, 220,
        remove_isolated=False,
        merge_adjacent=False,
        simplify_polygons=False,
        promote_primitives=False,
        global_scores={81: 0.80},
        global_thin_enable=True,
    )

    assert [s.id for s in out] == [81]
    assert report.removed_count == 0
