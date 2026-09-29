from copy import deepcopy
import numpy as np
import pytest
from minimalizer_zerobase.compose import SemanticComposer
from minimalizer_zerobase.composition import (
    compose_semantic_scene,
    rasterize_primitive_candidate,
    render_composed_minimal,
)
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.geometry import PrimitiveGenerator
from minimalizer_zerobase.palette import MaterialAssignment
from minimalizer_zerobase.scene.models import Region, Relation, Scene

SPACE = CoordinateSpace(100, 100)

def source_scene(relations=()):
    return Scene(SPACE, "test", "1", regions=(
        Region("body", "coat", geometry={"bbox": [20, 20, 50, 70]}),
        Region("face", "face", geometry={"bbox": [35, 5, 20, 20]}),
        Region("bg", "background", geometry={"bbox": [0, 0, 100, 100]}),
    ), relations=relations)

def materials():
    return (
        MaterialAssignment("bg", "#ffffff", "#ffffff", (), True, 1.0, "disposable"),
        MaterialAssignment("body", "#112233", "#112233", (), True, 1.0, "preserve"),
        MaterialAssignment("face", "#f0c0a0", "#f0c0a0", (), True, 1.0, "protect"),
    )

def selections(candidates):
    first = {}
    for candidate in candidates:
        first.setdefault(candidate.source_region_id, candidate.candidate_id)
    return first

def test_composes_explicit_selections_without_choosing_winners():
    scene = source_scene()
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    out = SemanticComposer().compose(scene, candidates, chosen, materials())
    assert {p.source_region_id: p.selected_candidate_id for p in out.primitives} == chosen
    assert out.provenance["selection_authority"] == "external"
    assert out.primitives[0].source_region_id == "bg"
    assert [p.z_order for p in out.primitives] == list(range(3))

def test_in_front_of_and_behind_normalize_to_occlusion_order():
    scene = source_scene((
        Relation("face", "body", "in_front_of"),
        Relation("bg", "body", "behind"),
    ))
    candidates = PrimitiveGenerator().generate(scene)
    out = SemanticComposer().compose(scene, candidates, selections(candidates), materials())
    z = {p.source_region_id: p.z_order for p in out.primitives}
    assert z["bg"] < z["body"] < z["face"]
    body = next(p for p in out.primitives if p.source_region_id == "body")
    assert body.occluded_by == ("face",)

def test_missing_and_mismatched_references_fail_closed():
    scene = source_scene()
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    with pytest.raises(ValueError, match="missing candidate"):
        SemanticComposer().compose(scene, candidates, {**chosen, "face": "missing"}, materials())
    body_candidate = next(c for c in candidates if c.source_region_id == "body")
    with pytest.raises(ValueError, match="wrong region"):
        SemanticComposer().compose(scene, candidates, {**chosen, "face": body_candidate.candidate_id}, materials())
    with pytest.raises(ValueError, match="missing material"):
        SemanticComposer().compose(scene, candidates, chosen, materials()[:-1])

def test_occlusion_cycle_fails_closed():
    scene = source_scene((
        Relation("face", "body", "in_front_of"),
        Relation("body", "face", "in_front_of"),
    ))
    candidates = PrimitiveGenerator().generate(scene)
    with pytest.raises(ValueError, match="cycle"):
        SemanticComposer().compose(scene, candidates, selections(candidates), materials())

def test_replay_input_order_and_source_are_stable():
    scene = source_scene((Relation("face", "body", "in_front_of"),))
    before = deepcopy(scene.to_dict())
    candidates = PrimitiveGenerator().generate(scene)
    chosen = selections(candidates)
    a = SemanticComposer().compose(scene, candidates, chosen, materials())
    reversed_scene = Scene(scene.coordinate_space, scene.producer, scene.producer_version,
        regions=tuple(reversed(scene.regions)), relations=tuple(reversed(scene.relations)))
    b = SemanticComposer().compose(reversed_scene, tuple(reversed(candidates)), chosen,
                                   tuple(reversed(materials())))
    assert a == b
    assert scene.to_dict() == before


def _phase11_fixture(specs, relations=()):
    width = height = 24
    candidates = []
    selected = []
    present_parts = []
    for token, part, points, color in specs:
        mass_id = f"mass-{token}"
        candidate_id = f"candidate-{token}"
        primitive_id = f"primitive-{token}"
        parameters = {"components": [points]}
        candidate = {
            "candidate_id": candidate_id,
            "mass_id": mass_id,
            "semantic_part_id": part,
            "binding_status": "bound",
            "action": "protect",
            "primitive_type": "polygon",
            "parameters": parameters,
            "palette_id": f"palette-{token}",
            "palette_color_rgb": list(color),
            "source_pixel_count": 1,
        }
        candidate["candidate_pixel_count"] = int(
            rasterize_primitive_candidate(
                candidate, width=width, height=height
            ).sum()
        )
        candidates.append(candidate)
        selected.append(
            {
                "primitive_id": primitive_id,
                "candidate_id": candidate_id,
                "mass_id": mass_id,
                "semantic_part_id": part,
                "binding_status": "bound",
                "primitive_type": "polygon",
                "palette_id": f"palette-{token}",
                "palette_color_rgb": list(color),
                "total_cost": 0.1,
            }
        )
        if part not in present_parts:
            present_parts.append(part)
    coordinate = {
        "pixel_width": width,
        "pixel_height": height,
        "normalized_origin": "top-left",
        "normalized_range": [0.0, 1.0],
    }
    graph = {
        "coordinate_space": coordinate,
        "present_parts": present_parts,
        "relations": list(relations),
        "validation": {"pass": True},
    }
    geometry = {
        "coordinate_space": coordinate,
        "primitive_candidates": candidates,
        "selected_primitives": selected,
        "omitted_mass_ids": [],
        "validation": {"pass": True},
    }
    return graph, geometry


def _relation(source, kind, target):
    return {
        "relation_id": f"relation:{source}:{kind}:{target}",
        "source_part": source,
        "relation_kind": kind,
        "target_part": target,
    }


def test_phase11_uses_only_explicit_phase5_depth_relations():
    graph, geometry = _phase11_fixture(
        (
            ("head", "head", [[4, 3], [16, 3], [16, 15], [4, 15]], (180, 100, 40)),
            ("hair", "hair", [[3, 2], [17, 2], [17, 9], [3, 9]], (50, 35, 30)),
            ("face", "face", [[7, 6], [13, 6], [13, 13], [7, 13]], (230, 180, 150)),
            ("torso", "torso", [[5, 12], [18, 12], [18, 23], [5, 23]], (60, 90, 150)),
            ("tie", "accessory_or_held_object", [[10, 13], [12, 13], [12, 21], [10, 21]], (30, 170, 70)),
        ),
        (
            _relation("face", "inside", "head"),
            _relation("hair", "surrounds", "face"),
            _relation("accessory_or_held_object", "in_front_of", "torso"),
        ),
    )

    result = compose_semantic_scene(graph, geometry)

    assert [
        (edge["lower_part"], edge["upper_part"], edge["relation_kinds"])
        for edge in result.applied_graph_edges
    ] == [("torso", "accessory_or_held_object", ["in_front_of"])]
    assert result.part_raster_order.index("torso") < result.part_raster_order.index(
        "accessory_or_held_object"
    )
    unresolved = {tuple(item["parts"]): item for item in result.unresolved_depth_pairs}
    assert unresolved[("face", "head")]["supporting_non_depth_relations"] == ["inside"]
    assert unresolved[("face", "hair")]["supporting_non_depth_relations"] == ["surrounds"]
    assert result.validation["implicit_depth_edge_count"] == 0
    assert result.validation["containment_depth_edge_count"] == 0
    assert result.validation["non_explicit_depth_edge_count"] == 0
    assert result.validation["pass"] is True


def test_phase11_replay_is_stable_when_upstream_arrays_are_reversed():
    graph, geometry = _phase11_fixture(
        (
            ("body", "torso", [[3, 8], [20, 8], [20, 22], [3, 22]], (60, 90, 150)),
            ("face", "face", [[8, 2], [15, 2], [15, 10], [8, 10]], (230, 180, 150)),
            ("item", "accessory_or_held_object", [[11, 9], [13, 9], [13, 20], [11, 20]], (30, 170, 70)),
        ),
        (
            _relation("accessory_or_held_object", "in_front_of", "torso"),
            _relation("face", "inside", "torso"),
        ),
    )
    reversed_graph = deepcopy(graph)
    reversed_geometry = deepcopy(geometry)
    reversed_graph["relations"].reverse()
    reversed_graph["present_parts"].reverse()
    reversed_geometry["primitive_candidates"].reverse()
    reversed_geometry["selected_primitives"].reverse()

    first = compose_semantic_scene(graph, geometry)
    second = compose_semantic_scene(reversed_graph, reversed_geometry)

    assert first.to_dict() == second.to_dict()
    assert (render_composed_minimal(first) == render_composed_minimal(second)).all()


def test_phase11_identifier_order_cannot_change_visible_overlap():
    points = [[5, 5], [18, 5], [18, 18], [5, 18]]
    first_graph, first_geometry = _phase11_fixture(
        (
            ("a", "torso", points, (20, 30, 40)),
            ("z", "torso", points, (180, 190, 200)),
        )
    )
    second_graph, second_geometry = _phase11_fixture(
        (
            ("z", "torso", points, (20, 30, 40)),
            ("a", "torso", points, (180, 190, 200)),
        )
    )

    first = compose_semantic_scene(first_graph, first_geometry)
    second = compose_semantic_scene(second_graph, second_geometry)

    assert (render_composed_minimal(first) == render_composed_minimal(second)).all()
    assert first.validation["region_id_only_ordering"] is False
    assert first.validation["mass_id_only_ordering"] is False


def test_phase11_part_name_cannot_order_equal_union_and_color_set_rasters():
    left = [[4, 4], [11, 4], [11, 19], [4, 19]]
    right = [[11, 4], [19, 4], [19, 19], [11, 19]]
    red = (210, 30, 40)
    blue = (20, 60, 220)
    first_graph, first_geometry = _phase11_fixture(
        (
            ("a-left", "alpha_part", left, red),
            ("a-right", "alpha_part", right, blue),
            ("z-left", "zeta_part", left, blue),
            ("z-right", "zeta_part", right, red),
        )
    )
    second_graph, second_geometry = _phase11_fixture(
        (
            ("z-right", "alpha_part", right, red),
            ("z-left", "alpha_part", left, blue),
            ("a-right", "zeta_part", right, blue),
            ("a-left", "zeta_part", left, red),
        )
    )

    first = compose_semantic_scene(first_graph, first_geometry)
    second = compose_semantic_scene(second_graph, second_geometry)

    def part_raster(result, part):
        raster = np.zeros((result.height, result.width, 4), dtype=np.uint8)
        colors = set()
        for item in result.primitives:
            if item["composition_part"] != part:
                continue
            mask = result.primitive_masks[item["primitive_id"]]
            color = tuple(item["palette_color_rgb"])
            raster[mask, :3] = color
            raster[mask, 3] = 255
            colors.add(color)
        return raster, colors

    first_alpha, first_alpha_colors = part_raster(first, "alpha_part")
    first_zeta, first_zeta_colors = part_raster(first, "zeta_part")
    second_alpha, _ = part_raster(second, "alpha_part")
    second_zeta, _ = part_raster(second, "zeta_part")

    assert first.applied_graph_edges == second.applied_graph_edges == ()
    assert first.unresolved_depth_pairs[0]["overlap_pixel_count"] > 0
    assert second.unresolved_depth_pairs[0]["overlap_pixel_count"] > 0
    assert np.array_equal(first_alpha[..., 3], first_zeta[..., 3])
    assert first_alpha_colors == first_zeta_colors == {red, blue}
    assert not np.array_equal(first_alpha, first_zeta)
    assert np.array_equal(first_alpha, second_zeta)
    assert np.array_equal(first_zeta, second_alpha)
    assert (render_composed_minimal(first) == render_composed_minimal(second)).all()
    assert first.validation["semantic_identifier_visual_authority"] is False
    assert first.validation["serialization_tie_requires_identical_part_raster"] is True
