"""Research-only H04/H06/H08 leave-one-character-out control using ONLY explicit negatives.

Independent control for PR #407's presumed-negative experiment. Untraced source
pixels are UNKNOWN and never enter either training class. This is NOT an
outerwear observer promotion, a Golden signoff, or production authorization.
Private sources/labels and inferred masks must never be committed to GitHub.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from benchmark_leave_character_out import (
    MODEL_PARAMETERS,
    PINS,
    SEED,
    SIZE,
    predict,
    prepare,
    sample_train,
    score,
)

CASES = ("H04", "H06", "H08")


class LabelAuthorityError(ValueError):
    """A source, labelled-positive, labelled-negative, or unknown contract failed."""


def validate_known_labels(case: str, sample: Mapping) -> dict:
    """Keep partial human annotations three-valued: positive / negative / unknown."""
    required = ("alpha", "positive", "negative", "known", "features")
    if any(key not in sample for key in required):
        raise LabelAuthorityError(f"{case}: missing authority field")
    alpha, positive, negative, known = (np.asarray(sample[key]) for key in required[:4])
    if any(m.dtype != np.dtype(bool) or m.shape != alpha.shape for m in (alpha, positive, negative, known)):
        raise LabelAuthorityError(f"{case}: masks must be identically sized boolean arrays")
    if alpha.ndim != 2 or sample["features"].shape != (*alpha.shape, 18):
        raise LabelAuthorityError(f"{case}: feature geometry mismatch")
    if not np.all(np.isfinite(sample["features"])):
        raise LabelAuthorityError(f"{case}: nonfinite features")
    if np.any(positive & negative):
        raise LabelAuthorityError(f"{case}: conflicting human categories")
    if np.any((positive | negative) & ~alpha):
        raise LabelAuthorityError(f"{case}: human label extends past signed source alpha")
    if not np.array_equal(known, positive | negative):
        raise LabelAuthorityError(f"{case}: known must equal explicit positive union negative")
    pos_count, neg_count = int(positive.sum()), int(negative.sum())
    if min(pos_count, neg_count) < 100:
        raise LabelAuthorityError(f"{case}: insufficient explicit class support; ABSTAIN")
    return {
        "positive_px": pos_count,
        "explicit_negative_px": neg_count,
        "unknown_px": int(np.count_nonzero(alpha & ~known)),
        "signed_alpha_px": int(alpha.sum()),
        "labelled_alpha_fraction": round(float(known.sum() / max(1, alpha.sum())), 6),
    }


def evaluate_known_label_loco(data: Mapping[str, Mapping], *, train_cap: int = 15000):
    """Run source-only model with human-confirmed negatives; no held-out labels in inference.

    Original PR #407 all-alpha experiment stays unchanged. This new diagnostic
    must not be optimized against the three hold-out characters.
    """
    if set(data) != set(CASES):
        raise LabelAuthorityError("Exactly three independent signed cases H04/H06/H08 required")
    if not isinstance(train_cap, int) or not 100 <= train_cap <= 15000:
        raise LabelAuthorityError("Invalid predeclared training sample cap")
    coverage = {case: validate_known_labels(case, data[case]) for case in CASES}
    results = {
        "schema": "minimalizer/l02/explicit-known-negative-loco/v1",
        "evaluation_date": "2026-10-16",
        "source_sha256s": dict(PINS),
        "cases": list(CASES),
        "image_long_side_for_diagnostic": SIZE,
        "training_sample_cap_each_class_each_image": train_cap,
        "seed": SEED,
        "prediction_threshold": 0.5,
        "train_negative_authority": "ONLY_EXPLICIT_HUMAN_NEGATIVE_LABELS",
        "unknown_used_in_training": False,
        "held_out_labels_used_in_inference": False,
        "params_pinned_from_earlier_H04_experiment_not_independently_tuned": dict(MODEL_PARAMETERS),
        "label_coverage": coverage,
        "folds": {},
        "research_promotion": "NOT_AUTHORIZED",
        "L02_formal_status": "HOLD",
        "golden_status": "HOLD",
        "production_release": "NO_GO",
    }
    private_predictions = {}
    for heldout in CASES:
        train = [data[c] for c in CASES if c != heldout]
        X, y, training_counts = sample_train(train, limit=train_cap, negative_method="known")
        if set(np.unique(y)) != {0, 1} or len(X) != len(y):
            raise LabelAuthorityError(f"{heldout}: model training split has missing class")
        model = HistGradientBoostingClassifier(**MODEL_PARAMETERS)
        model.fit(X, y)
        test = data[heldout]
        prediction = predict(test, model)  # predict() only reads source features and alpha.
        if prediction.dtype != bool or prediction.shape != test["alpha"].shape:
            raise LabelAuthorityError(f"{heldout}: invalid prediction geometry")
        stats = score(test, prediction)
        results["folds"][heldout] = {
            "held_out": heldout,
            "train_cases": [t["case"] for t in train],
            "training": training_counts,
            "test": stats,
            "test_explicit_label_coverage": coverage[heldout],
        }
        private_predictions[heldout] = prediction
    return results, private_predictions


def run(private_input_dir: str | Path, private_output_dir: str | Path):
    """Fail closed before emitting results; outputs stay in caller's private directory."""
    base = Path(private_input_dir)
    data = {case: prepare(base, case, "outerwear") for case in CASES}
    results, predictions = evaluate_known_label_loco(data)
    out = Path(private_output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        np.savez_compressed(out / f"{case}_KNOWN_NEGATIVE_LOCO_PRIVATE.npz", prediction=predictions[case].astype("uint8"))
    (out / "L02_KNOWN_NEGATIVE_LOCO_PRIVATE.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_input_dir")
    parser.add_argument("private_output_dir")
    a = parser.parse_args()
    run(a.private_input_dir, a.private_output_dir)
