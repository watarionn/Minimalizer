from __future__ import annotations

from minimalizer_zerobase.production.blind_observation import bind_blind_observations


def _manifest():
    return {"case_id":"blind","features":[
        {"id":"hair","semantic_role":"hair","disposition":"required"},
        {"id":"tie","semantic_role":"necktie","disposition":"required"},
    ]}


def test_unlabeled_regions_do_not_become_semantic_truth():
    report=bind_blind_observations(_manifest(),[
        {"evidence_id":"slic-1","semantic_label":None,"geometry":{"bbox":[1,2,3,4]}},
    ])
    assert report["feature_evidence"]["hair"]["state"]=="unknown"
    assert report["feature_evidence"]["tie"]["state"]=="unknown"
    assert report["authorized_masks"]=={}
    assert report["manual_semantic_labels_used"] is False


def test_exact_observer_semantic_label_can_authorize_mask():
    report=bind_blind_observations(_manifest(),[
        {"evidence_id":"obs-hair","semantic_label":"hair","confidence":0.7,"geometry":{"bbox":[1,2,30,40]}},
    ])
    assert report["feature_evidence"]["hair"]["state"]=="present"
    assert report["authorized_masks"]["hair"]["authorized"] is True
    assert report["feature_evidence"]["tie"]["state"]=="unknown"


def test_ambiguous_multiple_matches_fail_to_unknown():
    report=bind_blind_observations(_manifest(),[
        {"evidence_id":"a","semantic_label":"hair","geometry":{"bbox":[1,2,3,4]}},
        {"evidence_id":"b","semantic_label":"hair","geometry":{"bbox":[5,6,7,8]}},
    ])
    assert report["feature_evidence"]["hair"]["state"]=="unknown"
    assert "hair" not in report["authorized_masks"]


def test_missing_bbox_cannot_authorize_mask():
    report=bind_blind_observations(_manifest(),[
        {"evidence_id":"a","semantic_label":"hair","geometry":{}},
    ])
    assert report["feature_evidence"]["hair"]["state"]=="unknown"
    assert report["authorized_masks"]=={}


def test_golden_is_never_part_of_binding_report():
    report=bind_blind_observations(_manifest(),[])
    assert report["golden_used"] is False
