"""Research-only, source-free lower bound for whole-fragment-group keep/drop.

Human owner annotations are used ONLY for retrospective scoring. Never feed this
module's output into inference or production. No mask/pixel data are emitted.
"""
import hashlib
import json
from pathlib import Path

FROZEN_SHA = "48513fd9f17ac08a9aaa2a8482e8da0da9f4a9f5622ac1f2f12ea900677a5624"
ARCHIVES = {
    "source_archive_sha256": "6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598",
    "classids_archive_sha256": "a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7",
    "candidate_archive_sha256": "a1bbd358db2f113c39ad04c3b8e51466bd4753d617d1b3a9fd1da3c2f077fd2c",
}
CASES = ("H04", "H06", "H08")
GROUPS = ("retained_seed_contact4", "retained_seed_diagonal_only",
          "inherited_parent_contact_only", "no_parent_or_retained_seed_contact",
          "seed_nonclass32")
OWNERS = ("outerwear", "arm_skin", "hair", "underlayer", "other_known_negative", "unknown")
NEG = ("arm_skin", "hair", "underlayer", "other_known_negative")
RELEASE = {"L02": "HOLD", "Golden": "HOLD", "L03": "NO_GO", "production": "NO_GO"}
FALSE = ("model_weights_bytes_reverified", "new_inference_performed",
         "annotation_used_for_inference", "annotation_independence_proven",
         "independent_holdout_proven", "occluded_unknown_independently_verified",
         "semantic_quality_pass")


class EvidenceHold(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise EvidenceHold("DUPLICATE_KEY:" + k)
        out[k] = v
    return out


def _nonfinite(value):
    raise EvidenceHold("NONFINITE:" + value)


def _count(value):
    if type(value) is not int or value < 0:
        raise EvidenceHold("INVALID_COUNT")
    return value


def _release(obj):
    if any(obj.get(k) != v for k, v in RELEASE.items()):
        raise EvidenceHold("RELEASE_MISMATCH")


def audit(raw: bytes, expected_sha256: str = FROZEN_SHA) -> dict:
    """Override expected_sha256 only for synthetic tests, never for release."""
    if type(raw) is not bytes or type(expected_sha256) is not str or len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise EvidenceHold("INVALID_INPUT_OR_SHA")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise EvidenceHold("EVIDENCE_SHA_MISMATCH")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_nonfinite)
    except EvidenceHold:
        raise
    except (UnicodeError, ValueError) as exc:
        raise EvidenceHold("INVALID_JSON") from exc
    if type(data) is not dict or data.get("schema") != "minimalizer/local-l02/run20/signed-fragment-owner-postscore-sourcefree/v1":
        raise EvidenceHold("INVALID_SCHEMA")
    for k, v in ARCHIVES.items():
        if data.get(k) != v:
            raise EvidenceHold("ARCHIVE_PIN_MISMATCH:" + k)
    if any(data.get(k) is not False for k in FALSE):
        raise EvidenceHold("UNSUPPORTED_PROOF")
    _release(data)
    cases = data.get("cases")
    if type(cases) is not dict or set(cases) != set(CASES):
        raise EvidenceHold("CASE_SET")
    results = {}
    for case in CASES:
        item = cases[case]
        if type(item) is not dict:
            raise EvidenceHold("CASE_OBJECT")
        _release(item)
        if item.get("unknown_not_counted_as_negative") is not True or item.get("fragment_contact_proves_owner") is not False or _count(item.get("source_pixels_synthesized")) != 0:
            raise EvidenceHold("UNSUPPORTED_OWNER_PROOF")
        groups, fps = item.get("candidate_pixels_by_fragment_owner"), item.get("candidate_known_fp_by_fragment")
        if type(groups) is not dict or set(groups) != set(GROUPS) or type(fps) is not dict or set(fps) != set(GROUPS):
            raise EvidenceHold("GROUP_SET")
        rows = {}
        for group in GROUPS:
            row = groups[group]
            if type(row) is not dict or set(row) != set(OWNERS):
                raise EvidenceHold("OWNER_SET")
            nums = {owner: _count(row[owner]) for owner in OWNERS}
            pos, neg = nums["outerwear"], sum(nums[k] for k in NEG)
            if neg != _count(fps[group]):
                raise EvidenceHold("FP_PARTITION")
            rows[group] = {
                "known_outerwear_lost_if_drop": pos,
                "known_fp_retained_if_keep": neg,
                "unknown_not_scored": nums["unknown"],
                "uniform_binary_min_known_errors": min(pos, neg),
            }
        keep_all = sum(v["known_fp_retained_if_keep"] for v in rows.values())
        lower = sum(v["uniform_binary_min_known_errors"] for v in rows.values())
        results[case] = {
            "groups": rows,
            "keep_all_known_fp": keep_all,
            "minimum_known_errors_uniform_group_action": lower,
            "maximum_known_error_reduction": keep_all - lower,
            "mixed_owner_groups": [k for k, v in rows.items() if v["known_outerwear_lost_if_drop"] > 0 and v["known_fp_retained_if_keep"] > 0],
        }
    return {
        "schema": "minimalizer/local-l02/run21/group-identifiability/v1",
        "sourcefree_input_sha256": digest,
        "cases": results,
        "evaluation_only": True,
        "independent_holdout_proven": False,
        "semantic_quality_pass": False,
        **RELEASE,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("run20_sourcefree_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.run20_sourcefree_json.read_bytes()), indent=2, sort_keys=True))
