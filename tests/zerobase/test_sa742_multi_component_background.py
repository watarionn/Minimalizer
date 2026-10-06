import numpy as np

from minimalizer_zerobase.semantic_abstraction.background_field_geometry import (
    reauthor_background_fields,
)


def test_one_palette_cluster_can_emit_multiple_major_components():
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

    a = reauthor_background_fields(
        im,
        subject,
        max_fields=6,
        max_palette_clusters=2,
    )
    b = reauthor_background_fields(
        im,
        subject,
        max_fields=6,
        max_palette_clusters=2,
    )

    a_ids = [(row.cluster_index, row.component_index) for row in a]
    b_ids = [(row.cluster_index, row.component_index) for row in b]
    assert a_ids == b_ids
    assert len(a_ids) == len(set(a_ids))


def test_retained_area_and_render_area_are_reported_separately():
    im = np.full((100, 100, 3), [20, 40, 160], np.uint8)
    im[5:45, 5:45] = [240, 120, 30]
    subject = np.zeros((100, 100), bool)
    subject[50:80, 50:80] = 1

    rows = reauthor_background_fields(
        im,
        subject,
        max_fields=4,
        max_palette_clusters=2,
    )

    assert rows
    for row in rows:
        assert row.retained_area <= row.source_area
        assert row.render_area >= row.retained_area
