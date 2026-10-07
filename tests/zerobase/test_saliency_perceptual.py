import numpy as np

from minimalizer_zerobase.evaluation.saliency_perceptual import evaluate_saliency_perceptual


def _case():
    source = np.full((32, 32, 3), 128, dtype=np.uint8)
    masks = {"face": np.zeros((32, 32), bool), "left_arm": np.zeros((32, 32), bool),
             "right_arm": np.zeros((32, 32), bool), "torso": np.zeros((32, 32), bool)}
    masks["face"][8:16, 12:20] = True
    masks["torso"][16:28, 10:22] = True
    return source, masks


def test_face_distortion_is_stronger_evidence_than_equal_area_non_salient_distortion():
    source, masks = _case()
    candidate = source.copy()
    candidate[8:16, 12:20] = 255
    face = evaluate_saliency_perceptual(source, candidate, masks)
    candidate = source.copy()
    candidate[16:24, 10:18] = 255
    torso = evaluate_saliency_perceptual(source, candidate, masks)
    assert face["regions"]["face"]["score"] < torso["regions"]["face"]["score"]
    assert face["aggregate_score"] < torso["aggregate_score"]


def test_missing_heavy_backends_are_explicit_and_non_authoritative():
    source, masks = _case()
    report = evaluate_saliency_perceptual(source, source, masks)
    assert report["backend"]["dinov3"] == "unavailable"
    assert report["backend"]["lpips"] == "unavailable"
    assert report["authority"] is False
    assert report["fail_open"] is True
