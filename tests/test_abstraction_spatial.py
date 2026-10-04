import numpy as np

from minimalizer_zerobase.refine.abstraction_spatial import _mask_descriptor, abstraction_similarity


def test_identical_descriptor_scores_one():
    mask=np.zeros((16,16),dtype=bool); mask[2:10,3:12]=True
    score=abstraction_similarity(_mask_descriptor(mask),_mask_descriptor(mask))
    assert score.score == 1.0


def test_small_boundary_change_is_tolerated_better_than_raw_iou():
    a=np.zeros((32,32),dtype=bool); a[4:24,6:24]=True
    b=np.zeros((32,32),dtype=bool); b[5:25,7:25]=True
    inter=np.logical_and(a,b).sum(); union=np.logical_or(a,b).sum()
    raw=float(inter/union)
    score=abstraction_similarity(_mask_descriptor(a),_mask_descriptor(b))
    assert score.score > raw


def test_relocation_is_still_penalized():
    a=np.zeros((32,32),dtype=bool); a[2:10,2:10]=True
    b=np.zeros((32,32),dtype=bool); b[22:30,22:30]=True
    score=abstraction_similarity(_mask_descriptor(a),_mask_descriptor(b))
    assert score.centroid < .6
    assert score.bbox == 0.0
    assert score.score < .75


def test_missing_region_is_not_mistaken_for_retention():
    a=np.zeros((32,32),dtype=bool); a[5:20,5:20]=True
    b=np.zeros((32,32),dtype=bool)
    score=abstraction_similarity(_mask_descriptor(a),_mask_descriptor(b))
    assert score.coverage == 0.0
    assert score.centroid == 0.0
    assert score.bbox == 0.0
    assert score.score < .5
