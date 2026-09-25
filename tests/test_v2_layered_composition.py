import numpy as np

from minimalize_engine.v2.layered_composition import (
    LayeredCompositionConfig,
    render_layered_preview,
)
from minimalize_engine.v2.person_parts import PersonPartPartition


def test_layered_preview_changes_background_but_preserves_subject_pixels():
    image = np.zeros((12, 12, 3), dtype=np.uint8)
    for y in range(12):
        for x in range(12):
            image[y, x] = (20 + x * 8, 40 + y * 7, 80 + (x + y) * 3)
    subject = np.zeros((12, 12), dtype=np.bool_)
    subject[3:10, 4:9] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={"head": subject & (np.indices(subject.shape)[0] < 6)},
    )

    rendered = render_layered_preview(
        image,
        partition,
        config=LayeredCompositionConfig(background_color_count=2, background_blur_sigma=1.0),
    )

    assert np.array_equal(rendered[subject], image[subject])
    assert not np.array_equal(rendered[~subject], image[~subject])
    assert len(np.unique(rendered[~subject].reshape(-1, 3), axis=0)) <= 2


def test_layered_preview_rejects_mismatched_partition_size():
    subject = np.zeros((4, 4), dtype=np.bool_)
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={},
    )
    import pytest
    with pytest.raises(ValueError, match="matching dimensions"):
        render_layered_preview(np.zeros((5, 5, 3), dtype=np.uint8), partition)


def test_compositor_respects_person_part_layer_order_and_fallback():
    from minimalize_engine.v2.layered_composition import compose_layered_rgb

    subject = np.zeros((5, 5), dtype=np.bool_)
    subject[1:5, 1:4] = True
    head = np.zeros_like(subject)
    head[1:3, 1:4] = True
    torso = np.zeros_like(subject)
    torso[2:4, 1:4] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={"head": head, "torso": torso},
    )
    background = np.full((5, 5, 3), 10, dtype=np.uint8)
    fallback = np.full((5, 5, 3), 40, dtype=np.uint8)
    head_rgb = np.full((5, 5, 3), 200, dtype=np.uint8)
    torso_rgb = np.full((5, 5, 3), 100, dtype=np.uint8)
    result = compose_layered_rgb(
        background,
        partition,
        part_renders={"head": head_rgb, "torso": torso_rgb},
        subject_fallback_rgb=fallback,
    )
    assert tuple(result[1, 2]) == (200, 200, 200)
    assert tuple(result[3, 2]) == (100, 100, 100)
    assert tuple(result[4, 2]) == (40, 40, 40)
    assert tuple(result[0, 0]) == (10, 10, 10)


def test_partitioned_scene_blocks_scene_background_from_overpainting_subject():
    from minimalize_engine.v2.layered_composition import render_partitioned_scene

    source = np.full((6, 6, 3), 240, dtype=np.uint8)
    subject = np.zeros((6, 6), dtype=np.bool_)
    subject[1:5, 2:4] = True
    source[subject] = (180, 120, 60)
    scene = np.full_like(source, 20)
    scene[subject] = (90, 70, 50)
    head = np.zeros_like(subject)
    head[1:3, 2:4] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={"head": head},
    )
    result = render_partitioned_scene(
        scene,
        source,
        partition,
        config=LayeredCompositionConfig(background_color_count=1, background_blur_sigma=0.0),
    )
    assert tuple(result[1, 2]) == (90, 70, 50)
    assert tuple(result[4, 2]) == (90, 70, 50)
    assert tuple(result[0, 0]) == (240, 240, 240)


def test_compositor_uses_whole_person_fallback_only_for_uncovered_seam_pixels():
    from minimalize_engine.v2.layered_composition import compose_layered_rgb

    subject = np.zeros((7, 7), dtype=np.bool_)
    subject[1:5, 2:5] = True
    head = np.zeros_like(subject)
    head[1:3, 2:5] = True
    torso = np.zeros_like(subject)
    torso[3:5, 2:5] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={"head": head, "torso": torso},
    )

    background = np.full((7, 7, 3), 10, dtype=np.uint8)
    fallback = np.full((7, 7, 3), 40, dtype=np.uint8)
    head_rgb = np.full((7, 7, 3), 200, dtype=np.uint8)
    torso_rgb = np.full((7, 7, 3), 100, dtype=np.uint8)

    head_coverage = np.zeros_like(subject)
    head_coverage[1, 2:5] = True
    torso_coverage = np.zeros_like(subject)
    torso_coverage[4, 2:5] = True
    fallback_coverage = np.zeros_like(subject)
    fallback_coverage[2:4, 3] = True

    result = compose_layered_rgb(
        background,
        partition,
        part_renders={"head": head_rgb, "torso": torso_rgb},
        part_coverage_masks={
            "head": head_coverage,
            "torso": torso_coverage,
        },
        subject_fallback_rgb=fallback,
        subject_fallback_coverage=fallback_coverage,
        seam_fallback_radius=1,
    )

    assert tuple(result[1, 3]) == (200, 200, 200)
    assert tuple(result[4, 3]) == (100, 100, 100)
    assert tuple(result[2, 3]) == (40, 40, 40)
    assert tuple(result[3, 3]) == (40, 40, 40)
    # Coverage-gated composition must not paste a part render's blank canvas.
    assert tuple(result[2, 2]) == (10, 10, 10)
    assert tuple(result[0, 0]) == (10, 10, 10)


def test_compositor_respects_source_alpha_when_painting_parts():
    from minimalize_engine.v2.layered_composition import compose_layered_rgb

    subject = np.zeros((5, 5), dtype=np.bool_)
    subject[1:4, 1:4] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={"head": subject.copy()},
    )
    background = np.full((5, 5, 3), 25, dtype=np.uint8)
    part = np.full((5, 5, 3), 220, dtype=np.uint8)
    coverage = subject.copy()
    alpha = np.ones((5, 5), dtype=np.float32)
    alpha[2, 2] = 0.0

    result = compose_layered_rgb(
        background,
        partition,
        part_renders={"head": part},
        part_coverage_masks={"head": coverage},
        source_alpha=alpha,
    )

    assert tuple(result[1, 1]) == (220, 220, 220)
    assert tuple(result[2, 2]) == (25, 25, 25)


def test_layered_background_quantization_is_byte_deterministic():
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    yy, xx = np.indices((32, 32))
    image[..., 0] = 20 + (xx * 5 + yy * 2) % 220
    image[..., 1] = 30 + (yy * 6 + xx) % 210
    image[..., 2] = 40 + (xx * 3 + yy * 4) % 200
    subject = np.zeros((32, 32), dtype=np.bool_)
    subject[9:24, 11:22] = True
    partition = PersonPartPartition(
        subject_mask=subject,
        background_mask=~subject,
        part_masks={},
    )
    config = LayeredCompositionConfig(
        background_color_count=3,
        background_blur_sigma=1.5,
    )

    outputs = [
        render_layered_preview(image, partition, config=config)
        for _ in range(5)
    ]
    assert all(np.array_equal(outputs[0], output) for output in outputs[1:])


def test_deterministic_kmeans_labels_cover_each_requested_cluster():
    from minimalize_engine.v2.layered_composition import _deterministic_kmeans_labels

    pixels = np.asarray(
        [
            [0, 0, 0],
            [2, 2, 2],
            [120, 100, 90],
            [125, 105, 95],
            [245, 245, 240],
            [250, 250, 250],
        ],
        dtype=np.float32,
    )
    first = _deterministic_kmeans_labels(pixels, 3)
    second = _deterministic_kmeans_labels(pixels, 3)

    assert np.array_equal(first, second)
    assert set(first[:, 0].tolist()) == {0, 1, 2}
