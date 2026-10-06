import cv2
import numpy as np

from minimalizer_zerobase.semantic_abstraction.background_field_geometry import (
    MAX_EXPANSION_RATIO,
    MAX_FIELDS,
    MIN_SOURCE_COVERAGE,
    _coarsest_safe_polygon,
    reauthor_background_fields,
)


def test_background_fields_never_overlap_subject():
    im = np.zeros((40, 40, 3), np.uint8)
    im[:] = [20, 30, 40]
    s = np.zeros((40, 40), bool)
    s[10:30, 14:26] = 1
    im[:, 20:] = [180, 90, 30]

    rows = reauthor_background_fields(im, s)

    assert len(rows) <= MAX_FIELDS
    assert all(r.subject_overlap == 0 for r in rows)
    assert all(r.source_coverage >= MIN_SOURCE_COVERAGE for r in rows)


def test_deterministic_fields():
    im = np.zeros((30, 30, 3), np.uint8)
    im[:15] = [10, 20, 30]
    im[15:] = [150, 120, 90]
    s = np.zeros((30, 30), bool)
    s[8:22, 10:20] = 1

    a = reauthor_background_fields(im, s)
    b = reauthor_background_fields(im, s)

    assert [
        (
            x.cluster_index,
            x.component_index,
            x.rgb,
            x.source_area,
            x.retained_area,
            len(x.polygon),
        )
        for x in a
    ] == [
        (
            x.cluster_index,
            x.component_index,
            x.rgb,
            x.source_area,
            x.retained_area,
            len(x.polygon),
        )
        for x in b
    ]


def test_small_background_returns_empty():
    im = np.zeros((10, 10, 3), np.uint8)
    s = np.ones((10, 10), bool)
    s[:2, :2] = 0
    assert reauthor_background_fields(im, s) == ()


def test_uniform_field_wrapping_subject_fails_closed():
    im = np.full((80, 80, 3), [180, 90, 30], np.uint8)
    s = np.zeros((80, 80), bool)
    s[20:60, 28:52] = 1
    assert reauthor_background_fields(im, s, max_fields=1) == ()


def test_adaptive_contour_preserves_open_concavity():
    comp = np.zeros((80, 80), bool)
    comp[:, 0:18] = 1
    comp[0:18, 0:62] = 1
    comp[62:80, 0:62] = 1
    subject = np.zeros((80, 80), bool)
    subject[24:56, 20:50] = 1

    cs, _ = cv2.findContours(
        comp.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    chosen = _coarsest_safe_polygon(
        max(cs, key=cv2.contourArea),
        comp,
        subject,
    )

    assert chosen is not None
    poly, _, _, coverage, expansion, overlap = chosen
    assert overlap == 0
    assert coverage >= MIN_SOURCE_COVERAGE
    assert expansion <= MAX_EXPANSION_RATIO
    assert len(poly) >= 3


def test_one_palette_cluster_can_emit_multiple_major_components():
    im = np.full((120, 120, 3), [20, 40, 160], np.uint8)
    # Two disconnected orange regions share one palette role.
    im[4:48, 4:44] = [240, 120, 30]
    im[72:116, 4:44] = [240, 120, 30]
    subject = np.zeros((120, 120), bool)
    subject[42:78, 54:82] = 1

    rows = reauthor_background_fields(
        im,
        subject,
        max_fields=6,
        max_palette_clusters=2,
    )

    orange = [row for row in rows if row.rgb == (240, 120, 30)]
    assert len(orange) == 2
    assert orange[0].cluster_index == orange[1].cluster_index
    assert orange[0].component_index != orange[1].component_index


def test_subthreshold_component_is_rejected_without_lowering_contract():
    im = np.full((120, 120, 3), [20, 40, 160], np.uint8)
    im[4:54, 4:54] = [240, 120, 30]
    im[102:110, 102:110] = [240, 120, 30]
    subject = np.zeros((120, 120), bool)
    subject[48:72, 58:82] = 1

    rows = reauthor_background_fields(
        im,
        subject,
        max_fields=6,
        max_palette_clusters=2,
    )

    orange = [row for row in rows if row.rgb == (240, 120, 30)]
    assert len(orange) == 1
    assert orange[0].source_area > 1000


def test_global_field_budget_is_independent_of_palette_cluster_count():
    im = np.full((150, 150, 3), [20, 40, 160], np.uint8)
    blocks = (
        (4, 4, 44, 44),
        (4, 54, 44, 94),
        (4, 104, 44, 144),
        (104, 4, 144, 44),
        (104, 54, 144, 94),
        (104, 104, 144, 144),
    )
    for y0, x0, y1, x1 in blocks:
        im[y0:y1, x0:x1] = [240, 120, 30]

    subject = np.zeros((150, 150), bool)
    subject[60:90, 60:90] = 1

    rows = reauthor_background_fields(
        im,
        subject,
        max_fields=3,
        max_palette_clusters=2,
    )

    assert len(rows) == 3
    assert all(row.subject_overlap == 0 for row in rows)
    assert len({row.cluster_index for row in rows}) <= 2


def test_component_ids_are_stable_and_unique_within_cluster():
    im = np.full((120, 120, 3), [20, 40, 160], np.uint8)
    im[4:48, 4:44] = [240, 120, 30]
    im[72:116, 4:44] = [240, 120, 30]
    subject = np.zeros((120, 120), bool)
    subject[42:78, 54:82] = 1

    rows = reauthor_background_fields(
        im,
        subject,
        max_fields=6,
        max_palette_clusters=2,
    )

    identities = [
        (row.cluster_index, row.component_index)
        for row in rows
    ]
    assert len(identities) == len(set(identities))
