from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_style import (
    _abstract_hand_symbols,
    _abstract_hair_planes,
    _consolidate_outfit_color_blocks,
    _prune_target_microdetails,
    _suppress_face_fragments,
    apply_rinka_reference_style,
)


def _poly(i, points, *, part="unknown", semantic="generic", role="misc", importance=0.5, color=(220, 190, 175), side="unknown"):
    return Shape(
        id=i,
        shape_type="polygon",
        fill_color=color,
        points=points,
        character_part=part,
        semantic_type=semantic,
        source_role=role,
        layer_name="foreground",
        importance=importance,
        side_hint=side,
    )


def test_phase11_collapses_open_hand_and_finger_fragments_to_one_fingerless_symbol():
    palm = _poly(
        1,
        [(20, 20), (34, 19), (39, 26), (34, 35), (20, 34), (16, 27)],
        part="left_hand",
        semantic="character_hand_open",
        role="character_hand_base",
        importance=0.985,
        side="left",
    )
    finger = _poly(
        2,
        [(35, 20), (49, 15), (51, 18), (39, 27)],
        part="left_hand",
        semantic="character_hand_finger",
        role="character_hand_detail",
        importance=0.65,
        side="left",
    )

    out, stats = _abstract_hand_symbols([palm, finger], 220.0)

    assert len(out) == 1
    assert out[0].semantic_type == "target_hand_symbol"
    assert out[0].source_role == "target_hand_symbol"
    assert len(out[0].points) == 6
    assert stats["input_shapes"] == 2
    assert stats["symbol_count"] == 1
    assert stats["merged_shapes"] == 1


def test_phase11_faceless_cleanup_removes_high_importance_face_features():
    carrier = _poly(
        1,
        [(40, 32), (74, 32), (76, 68), (39, 68)],
        semantic="skin_mass",
        importance=0.84,
        color=(236, 205, 188),
    )
    eye = _poly(
        2,
        [(47, 44), (54, 43), (55, 48), (47, 49)],
        semantic="character_eye_detail",
        role="character_eye",
        importance=0.995,
        color=(40, 70, 90),
    )
    mouth = _poly(
        3,
        [(55, 57), (64, 56), (63, 60), (55, 60)],
        semantic="character_mouth_detail",
        role="character_mouth",
        importance=0.96,
        color=(180, 80, 90),
    )
    hair = _poly(
        4,
        [(38, 30), (77, 29), (71, 44), (43, 43)],
        part="hair",
        semantic="character_hair",
        role="character_hair_base",
        importance=1.0,
        color=(30, 30, 35),
    )
    metadata = {"subject_mode": True, "character": {"structure": {"parts": [{"part_type": "face", "bbox": [40, 32, 36, 38]}]}}}
    scene = Scene(120, 120, (245, 245, 240), [carrier, eye, mouth, hair], metadata)

    out, removed = _suppress_face_fragments(scene, scene.shapes)

    assert {shape.id for shape in out} == {1, 4}
    assert removed == 2


def test_phase11_microdetail_prune_removes_lace_but_keeps_prop():
    lace = _poly(
        1,
        [(20, 20), (26, 20), (26, 23), (20, 23)],
        part="outfit",
        semantic="character_lace_detail",
        role="character_outfit_detail",
        importance=0.98,
        color=(245, 245, 240),
    )
    prop = _poly(
        2,
        [(60, 20), (64, 20), (64, 45), (60, 45)],
        part="prop",
        semantic="character_prop",
        role="character_prop",
        importance=1.0,
        color=(40, 40, 45),
    )
    scene = Scene(120, 120, (20, 20, 20), [lace, prop])

    out, removed = _prune_target_microdetails(scene, scene.shapes)

    assert [shape.id for shape in out] == [2]
    assert removed == 1


def test_phase11_pipeline_reports_faceless_and_hand_symbol_abstraction():
    carrier = _poly(
        1,
        [(40, 32), (74, 32), (76, 68), (39, 68)],
        semantic="skin_mass",
        importance=0.84,
        color=(236, 205, 188),
    )
    eye = _poly(
        2,
        [(47, 44), (54, 43), (55, 48), (47, 49)],
        semantic="character_eye_detail",
        role="character_eye",
        importance=0.995,
        color=(40, 70, 90),
    )
    hand = _poly(
        3,
        [(82, 46), (91, 39), (99, 42), (102, 50), (95, 58), (84, 56), (79, 51)],
        part="left_hand",
        semantic="character_hand_open",
        role="character_hand_base",
        importance=0.985,
        side="left",
    )
    metadata = {"subject_mode": True, "character": {"structure": {"parts": [{"part_type": "face", "bbox": [40, 32, 36, 38]}]}}}
    scene = Scene(120, 120, (245, 245, 240), [carrier, eye, hand], metadata)

    out = apply_rinka_reference_style(scene)
    target = out.metadata["target_style"]

    assert target["version"] == "phase13"
    assert target["face_fragments_removed"] >= 1
    assert target["hand_abstraction"]["symbol_count"] == 1
    symbols = [shape for shape in out.shapes if shape.semantic_type == "target_hand_symbol"]
    assert len(symbols) == 1
    assert len(symbols[0].points) == 6



def test_phase11_priority2_removes_local_bang_lines_but_keeps_major_hair_flow_cue():
    hair = _poly(
        10,
        [(35, 25), (82, 24), (88, 80), (30, 82)],
        part="hair",
        semantic="character_hair",
        role="character_hair_base",
        importance=1.0,
        color=(50, 45, 60),
    )
    bang = Shape(
        id=11,
        shape_type="line",
        fill_color=None,
        points=[(48, 30), (55, 46)],
        stroke_color=(40, 35, 45),
        stroke_width=2.0,
        character_part="hair",
        semantic_type="character_bangs",
        source_role="character_bangs",
        layer_name="foreground",
        importance=0.95,
    )
    flow = Shape(
        id=12,
        shape_type="line",
        fill_color=None,
        points=[(82, 40), (84, 100)],
        stroke_color=(40, 35, 45),
        stroke_width=2.0,
        character_part="hair",
        semantic_type="character_back_hair",
        source_role="character_back_hair",
        layer_name="foreground",
        importance=0.95,
    )

    out, stats = _abstract_hair_planes([hair, bang, flow], 220.0)

    assert {shape.id for shape in out} == {10, 12}
    assert stats["line_cues_removed"] == 1
    assert stats["major_flow_cues_preserved"] == 1


def test_phase11_priority2_simplifies_complex_hair_mass_with_raster_guard():
    hair = _poly(
        20,
        [(20, 20), (35, 18), (50, 20), (66, 25), (72, 40), (70, 58),
         (62, 72), (48, 80), (32, 76), (22, 66), (17, 50), (18, 34)],
        part="hair",
        semantic="character_hair",
        role="character_hair_base",
        importance=1.0,
        color=(70, 55, 90),
    )

    out, stats = _abstract_hair_planes([hair], 220.0)

    assert len(out) == 1
    assert len(out[0].points) < len(hair.points)
    assert stats["simplified_planes"] == 1
    assert stats["vertices_removed"] > 0


def test_phase11_priority2_flattens_near_duplicate_upper_garment_colors():
    torso = _poly(
        30,
        [(40, 60), (85, 60), (88, 105), (38, 105)],
        part="outfit",
        semantic="character_outfit_torso",
        role="character_outfit_torso",
        importance=0.98,
        color=(210, 202, 228),
    )
    sleeve = _poly(
        31,
        [(16, 65), (26, 64), (26, 95), (14, 92)],
        part="outfit",
        semantic="character_sleeve",
        role="character_sleeve",
        importance=0.98,
        color=(215, 211, 225),
        side="left",
    )
    accent = _poly(
        32,
        [(50, 80), (60, 80), (60, 90), (50, 90)],
        part="outfit",
        semantic="character_outfit_accent",
        role="character_outfit_detail",
        importance=0.95,
        color=(120, 55, 90),
    )

    out, stats = _consolidate_outfit_color_blocks([torso, sleeve, accent], 220.0)
    by_id = {shape.id: shape for shape in out}

    assert by_id[31].fill_color == torso.fill_color
    assert by_id[32].fill_color == accent.fill_color
    assert stats["recolored_shapes"] == 1
    assert stats["color_blocks_after"] < stats["color_blocks_before"]


def test_phase11_priority2_merges_small_same_color_sleeve_when_hull_is_compact():
    torso = _poly(
        40,
        [(40, 60), (80, 60), (80, 100), (40, 100)],
        part="outfit",
        semantic="character_outfit_torso",
        role="character_outfit_torso",
        importance=0.98,
        color=(200, 195, 220),
    )
    sleeve = _poly(
        41,
        [(30, 68), (40, 68), (40, 92), (30, 92)],
        part="outfit",
        semantic="character_sleeve",
        role="character_sleeve",
        importance=0.96,
        color=(202, 198, 218),
        side="left",
    )

    out, stats = _consolidate_outfit_color_blocks([torso, sleeve], 220.0)

    assert len(out) == 1
    assert stats["merged_shapes"] == 1
    assert out[0].shape_type == "polygon"
