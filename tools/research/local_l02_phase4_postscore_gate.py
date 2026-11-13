"""Post-inference Phase4 gate for a frozen, source-only owner candidate.

The gate consumes only frozen-output receipts, independent review attestations,
structural booleans, and aggregate postscore counts. It never accepts image
pixels or human masks as inference inputs. A case-level PASS never authorizes
Phase5, Golden, merge, or production; the campaign-level L02 gate stays
separate.
"""
from __future__ import annotations

from collections.abc import Mapping


class Phase4Hold(ValueError):
    """Malformed or failed independent post-inference evidence."""


_REVIEW_FLAGS = (
    "signature_verified",
    "unseen_data",
    "labels_unavailable_before_inference",
    "evaluator_independent",
    "semantic_review_complete",
    "unknown_mask_is_unknown",
    "human_masks_used_in_inference",
    "review_json_used_in_inference",
    "output_frozen_before_scoring",
)
_STRUCTURAL_FLAGS = (
    "source_sha_verified",
    "prediction_sha_verified",
    "source_alpha_bounds_pass",
    "owner_provenance_pass",
    "owner_exclusivity_pass",
    "components4_pass",
    "components8_pass",
    "holes4_pass",
    "holes8_pass",
)
_COUNT_FIELDS = (
    "candidate_added_px",
    "candidate_removed_px",
    "added_known_positive_garment_px",
    "added_known_negative_owner_px",
    "added_unknown_px",
    "removed_known_positive_garment_px",
    "removed_known_negative_owner_px",
    "removed_unknown_px",
    "owner_promotions",
)
_OWNER_AUTHORITY_BINDINGS = (
    "authority_receipt_verified",
    "bound_to_case",
    "bound_to_source_sha",
    "bound_to_prediction_sha",
    "bound_to_observer_sha",
)


def _require_flags(values: Mapping[str, object], names: tuple[str, ...], label: str):
    failures = []
    for name in names:
        value = values.get(name)
        if type(value) is not bool:
            failures.append(f"{label}_MISSING_OR_NONBOOLEAN:{name}")
        elif ((label == "review" and name in {
                    "human_masks_used_in_inference", "review_json_used_in_inference"})
              and value):
            failures.append(f"{label}_FAIL:{name}")
        elif name not in {"human_masks_used_in_inference",
                          "review_json_used_in_inference"} and not value:
            failures.append(f"{label}_FAIL:{name}")
    return failures


def evaluate_frozen_candidate(*, review: Mapping[str, object],
                              structural: Mapping[str, object],
                              metrics: Mapping[str, object],
                              authority: Mapping[str, object] | None = None) -> dict:
    """Return a non-promoting case-level Phase4 decision.

    A PASS requires at least one known wrong-owner removal or garment addition,
    no known garment loss, no known wrong-owner addition, no unknown mutation,
    and either zero owner promotions or a separate explicit authority receipt
    bound to the exact case, source, frozen prediction, and observer output.
    Unknown pixels are excluded from quality counts, but any candidate mutation
    in unknown is rejected rather than treated as a negative result.
    """
    if authority is None:
        authority = {}
    if not all(isinstance(x, Mapping) for x in
               (review, structural, metrics, authority)):
        raise Phase4Hold("INVALID_PHASE4_EVIDENCE_MAPPING")
    failures = _require_flags(review, _REVIEW_FLAGS, "review")
    failures += _require_flags(structural, _STRUCTURAL_FLAGS, "structural")
    counts = {}
    for name in _COUNT_FIELDS:
        value = metrics.get(name)
        if type(value) is not int or value < 0:
            failures.append("METRIC_MISSING_OR_INVALID:" + name)
        else:
            counts[name] = value
    if failures:
        return {
            "case_phase4": "HOLD",
            "failures": failures,
            "phase5_authorized": False,
            "L02": "HOLD",
            "production": "NO_GO",
        }

    added = counts["candidate_added_px"]
    removed = counts["candidate_removed_px"]
    if added + removed == 0:
        failures.append("NO_CANDIDATE_CHANGE")
    if added != (counts["added_known_positive_garment_px"] +
                 counts["added_known_negative_owner_px"] +
                 counts["added_unknown_px"]):
        failures.append("ADDED_POSTSCORE_PARTITION_MISMATCH")
    if removed != (counts["removed_known_positive_garment_px"] +
                   counts["removed_known_negative_owner_px"] +
                   counts["removed_unknown_px"]):
        failures.append("REMOVED_POSTSCORE_PARTITION_MISMATCH")
    if counts["added_known_negative_owner_px"] != 0:
        failures.append("KNOWN_FALSE_OWNER_ADDED")
    if counts["added_unknown_px"] != 0 or counts["removed_unknown_px"] != 0:
        failures.append("UNKNOWN_MUTATION_NOT_ALLOWED")
    if counts["removed_known_positive_garment_px"] != 0:
        failures.append("KNOWN_GARMENT_LOSS")
    if counts["owner_promotions"] != 0:
        promotion_auth = authority.get("owner_promotion_authorized")
        if type(promotion_auth) is not bool:
            failures.append(
                "AUTHORITY_MISSING_OR_NONBOOLEAN:owner_promotion_authorized")
        elif not promotion_auth:
            failures.append("AUTHORITY_FAIL:owner_promotion_authorized")
        else:
            for name in _OWNER_AUTHORITY_BINDINGS:
                if authority.get(name) is not True:
                    failures.append("AUTHORITY_BINDING_FAIL:" + name)
    if (counts["added_known_positive_garment_px"] == 0 and
            counts["removed_known_negative_owner_px"] == 0):
        failures.append("NO_VERIFIED_QUALITY_IMPROVEMENT")
    decision = "PASS" if not failures else "HOLD"
    return {
        "case_phase4": decision,
        "failures": failures,
        "phase5_authorized": False,
        "L02": "HOLD",
        "production": "NO_GO",
        "unknown_not_negative": True,
        "human_masks_post_inference_only": True,
    }
