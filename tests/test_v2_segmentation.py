import hashlib
import cv2
import numpy as np
import pytest

import minimalize_engine.v2.region_merge.segmentation as segmentation
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.region_merge.segmentation import (
    oversegment,
    region_size_for_target,
    split_disconnected_labels,
    structural_edge_coverage,
    target_superpixel_count,
)


def _two_mass_image(height=64, width=96):
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, : width // 2] = (225, 45, 45)
    image[:, width // 2 :] = (35, 65, 220)
    return image


def test_superpixel_target_obeys_general_range_and_small_image_area_floor():
    assert target_superpixel_count(768, 768) == pytest.approx(655, abs=1)
    assert target_superpixel_count(64, 64) == 64
    assert region_size_for_target(64, 64, 64) == 8


def test_connectivity_split_preserves_fragments_instead_of_absorbing_them():
    labels = np.array(
        [[5, 1, 5], [1, 1, 1], [5, 1, 5]],
        dtype=np.int32,
    )
    split = split_disconnected_labels(labels)
    assert split.dtype == np.int32
    assert np.unique(split).tolist() == [0, 1, 2, 3, 4]
    for region_id in np.unique(split):
        count, _ = cv2.connectedComponents(
            (split == region_id).astype(np.uint8),
            connectivity=4,
        )
        assert count == 2


def test_numpy_slico_exact_fixture_digest_is_stable():
    bundle = build_image_bundle(_two_mass_image())
    labels = segmentation._run_numpy_slico(
        bundle.structural_lab,
        bundle.edge_structural,
        region_size=8,
        iterations=4,
    )
    digest = hashlib.sha256(labels.tobytes()).hexdigest()
    assert digest == "3a2965da334ce898e5619577dbd8a3bcf5233ae3478724f3970b7fc6dd56028f"


def test_numpy_slico_is_deterministic_sequential_and_four_connected():
    bundle = build_image_bundle(_two_mass_image())
    first = oversegment(bundle, iterations=4)
    second = oversegment(bundle, iterations=4)
    assert np.array_equal(first.labels, second.labels)
    assert np.unique(first.labels).tolist() == list(range(first.region_count))
    assert first.labels.dtype == np.int32
    for region_id in np.unique(first.labels):
        count, _ = cv2.connectedComponents(
            (first.labels == region_id).astype(np.uint8),
            connectivity=4,
        )
        assert count == 2


def test_structural_edge_coverage_rewards_label_boundaries_near_edge_energy():
    edge = np.zeros((16, 16), dtype=np.float32)
    edge[:, 7:9] = 1.0
    aligned = np.zeros((16, 16), dtype=np.int32)
    aligned[:, 8:] = 1
    flat = np.zeros((16, 16), dtype=np.int32)
    assert structural_edge_coverage(aligned, edge) > 0.95
    assert structural_edge_coverage(flat, edge) == pytest.approx(0.0)


def test_adaptive_retry_keeps_finer_result_only_when_coverage_improves(monkeypatch):
    bundle = build_image_bundle(_two_mass_image(32, 32))

    def fake_segment(bundle, *, region_size, iterations, provider):
        labels = np.zeros((32, 32), dtype=np.int32)
        if region_size >= 8:
            labels[:, 16:] = 1
        else:
            labels[:16, 16:] = 1
            labels[16:, :16] = 2
            labels[16:, 16:] = 3
        return labels

    def fake_coverage(labels, edge):
        return 0.50 if int(labels.max()) + 1 == 2 else 0.90

    monkeypatch.setattr(segmentation, "_segment_once", fake_segment)
    monkeypatch.setattr(segmentation, "structural_edge_coverage", fake_coverage)
    result = oversegment(bundle, iterations=2)
    assert result.retried is True
    assert result.region_count == 4
    assert result.edge_coverage == pytest.approx(0.90)
    assert result.initial_edge_coverage == pytest.approx(0.50)


def test_slico_provider_is_explicit_and_never_silently_falls_back():
    bundle = build_image_bundle(_two_mass_image(24, 32))
    with pytest.raises(ValueError, match="provider"):
        oversegment(bundle, iterations=1, provider="opencv_slico")


def test_adaptive_retry_rejects_pathological_region_explosion(monkeypatch):
    bundle = build_image_bundle(_two_mass_image(32, 32))

    def fake_segment(bundle, *, region_size, iterations, provider):
        if region_size >= 8:
            labels = np.zeros((32, 32), dtype=np.int32)
            labels[:, 16:] = 1
            return labels
        labels = np.arange(32 * 32, dtype=np.int32).reshape(32, 32) % 64
        return labels

    def fake_coverage(labels, edge):
        return 0.50 if int(labels.max()) + 1 == 2 else 0.95

    monkeypatch.setattr(segmentation, "_segment_once", fake_segment)
    monkeypatch.setattr(segmentation, "structural_edge_coverage", fake_coverage)
    result = oversegment(bundle, iterations=2)
    assert result.retried is False
    assert result.region_count == 2
    assert result.edge_coverage == pytest.approx(0.50)
