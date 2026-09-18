import numpy as np
import pytest

from minimalize_engine.v2.characteristic import annotate_initial_regions
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.region_merge.graph import build_region_graph, validate_graph
from minimalize_engine.v2.region_merge.segmentation import oversegment
from minimalize_engine.v2.types import (
    CharacteristicAnchor,
    CharacteristicContext,
    ImageBundle,
    RegionAnnotation,
)


def _bundle_fixture():
    labels = np.tile(np.array([[0, 0, 1, 1]], dtype=np.int32), (4, 1))
    analysis_rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    structural_rgb = analysis_rgb.copy()
    analysis_lab = np.empty((4, 4, 3), dtype=np.float32)
    analysis_lab[labels == 0] = (20.0, 5.0, 6.0)
    analysis_lab[labels == 1] = (70.0, -2.0, -3.0)
    structural_lab = np.full((4, 4, 3), 99.0, dtype=np.float32)
    raw = np.zeros((4, 4), dtype=np.float32)
    structural = np.zeros((4, 4), dtype=np.float32)
    raw[:, 1:3] = 0.8
    structural[:, 1:3] = 0.5
    subject_prob = np.where(labels == 0, 0.9, 0.1).astype(np.float32)
    subject_confidence = np.where(labels == 0, 0.8, 0.7).astype(np.float32)
    alpha = np.where(labels == 0, 1.0, 0.0).astype(np.float32)
    bundle = ImageBundle(
        source_rgb=analysis_rgb.copy(),
        analysis_rgb=analysis_rgb,
        structural_rgb=structural_rgb,
        analysis_lab=analysis_lab,
        structural_lab=structural_lab,
        edge_raw=raw,
        edge_structural=structural,
        subject_prob=subject_prob,
        subject_confidence=subject_confidence,
        alpha=alpha,
    )
    return bundle, labels


def _characteristic_fixture():
    anchors = (
        CharacteristicAnchor(0, np.array([20.0, 5.0, 6.0]), 0.8),
        CharacteristicAnchor(1, np.array([70.0, -2.0, -3.0]), 0.6),
    )
    anchor_map = np.array(
        [[0, 0, 1, 1], [0, 1, 1, 1], [-1, 1, 1, 1], [-1, -1, 1, 1]],
        dtype=np.int32,
    )
    confidence_map = np.full((4, 4), 0.5, dtype=np.float32)
    return CharacteristicContext(
        anchors=anchors,
        anchor_map=anchor_map,
        confidence_map=confidence_map,
    )


def test_initial_annotations_preserve_multiple_characteristic_supports():
    bundle, labels = _bundle_fixture()
    annotations = annotate_initial_regions(
        bundle,
        labels,
        characteristic=_characteristic_fixture(),
        semantic={0: ("subject", 0.9), 1: ("background", 0.8)},
    )
    supports0 = {item.anchor_id: item for item in annotations[0].characteristic_supports}
    assert supports0[0].support_mass == pytest.approx(3.0)
    assert supports0[0].confidence == pytest.approx(0.4)
    assert supports0[1].support_mass == pytest.approx(2.0)
    assert supports0[1].confidence == pytest.approx(0.3)
    assert annotations[0].semantic_tag == "subject"
    assert annotations[0].semantic_confidence == pytest.approx(0.9)
    supports1 = annotations[1].characteristic_supports
    assert len(supports1) == 1
    assert supports1[0].anchor_id == 1
    assert supports1[0].support_mass == pytest.approx(8.0)


def test_bundle_graph_uses_analysis_lab_and_carries_annotation_and_masks():
    bundle, labels = _bundle_fixture()
    annotations = annotate_initial_regions(
        bundle,
        labels,
        characteristic=_characteristic_fixture(),
        semantic={0: ("subject", 0.9), 1: ("background", 0.8)},
    )
    graph = build_region_graph(bundle, labels, annotations=annotations)
    validate_graph(graph)

    assert graph.nodes[0].mean_lab == pytest.approx((20.0, 5.0, 6.0))
    assert graph.nodes[0].mean_lab != pytest.approx((99.0, 99.0, 99.0))
    assert graph.nodes[0].subject_ratio == pytest.approx(0.9)
    assert graph.nodes[0].subject_confidence == pytest.approx(0.8)
    assert graph.nodes[0].semantic_tag == "subject"
    assert len(graph.nodes[0].characteristic_supports) == 2

    edge = graph.edges[(0, 1)]
    assert edge.shared_boundary_px == pytest.approx(4.0)
    assert int(edge.raw_gradient_hist.sum()) == 4
    assert int(edge.structural_gradient_hist.sum()) == 4
    assert edge.alpha_boundary_fraction == pytest.approx(1.0)
    assert graph.adjacency == {0: {1}, 1: {0}}
    assert graph.initial_labels.flags.writeable is False


def test_annotation_and_graph_reject_noncanonical_initial_labels():
    bundle, labels = _bundle_fixture()
    with pytest.raises(ValueError, match="dtype int32"):
        annotate_initial_regions(bundle, labels.astype(np.int64))

    gapped = labels.copy()
    gapped[gapped == 1] = 2
    with pytest.raises(ValueError, match="sequential from 0"):
        annotate_initial_regions(bundle, gapped)
    with pytest.raises(ValueError, match="sequential from 0"):
        build_region_graph(bundle, gapped)


def test_annotation_rejects_unknown_anchor_and_graph_rejects_unknown_region():
    bundle, labels = _bundle_fixture()
    characteristic = _characteristic_fixture()
    bad_map = characteristic.anchor_map.copy()
    bad_map[0, 0] = 7
    bad = CharacteristicContext(
        anchors=characteristic.anchors,
        anchor_map=bad_map,
        confidence_map=characteristic.confidence_map,
    )
    with pytest.raises(ValueError, match="unknown anchor ids"):
        annotate_initial_regions(bundle, labels, characteristic=bad)

    with pytest.raises(ValueError, match="unknown regions"):
        build_region_graph(bundle, labels, annotations={9: RegionAnnotation()})


def test_phase2_to_phase3_pipeline_builds_valid_initial_rag():
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    image[:, :32] = (220, 40, 40)
    image[:, 32:] = (40, 80, 220)
    bundle = build_image_bundle(image, analysis_max_side=64)
    segmentation = oversegment(bundle, edge_coverage_threshold=0.0)
    annotations = annotate_initial_regions(bundle, segmentation.labels)
    graph = build_region_graph(bundle, segmentation.labels, annotations=annotations)
    validate_graph(graph)

    region_ids = np.unique(segmentation.labels)
    assert set(graph.nodes) == set(int(value) for value in region_ids)
    assert set(graph.adjacency) == set(graph.nodes)
    assert graph.next_region_id == int(region_ids[-1]) + 1
    assert len(graph.edges) > 0
    for key, edge in graph.edges.items():
        assert key == tuple(sorted(key))
        assert int(edge.raw_gradient_hist.sum()) == int(edge.shared_boundary_px)
        assert int(edge.structural_gradient_hist.sum()) == int(edge.shared_boundary_px)
