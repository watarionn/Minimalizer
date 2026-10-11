"""C02 model-route evidence preflight: metadata is not calibrated semantic inference."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CASES = {
    "GC001": "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
    "Raden": "d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",
}

def check(manifest):
    if set(manifest.get("signed_sources", {})) != set(CASES) or manifest["signed_sources"] != CASES:
        raise ValueError("SIGNED_SOURCE_PROVENANCE_MISSING")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("INSUFFICIENT_INDEPENDENT_MODEL_ROUTES")
    ids = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or not candidate.get("repo_id") or candidate["repo_id"] in ids:
            raise ValueError("DUPLICATE_OR_UNKNOWN_MODEL")
        ids.add(candidate["repo_id"])
        weight_sha = candidate.get("downloaded_weights_sha256")
        if weight_sha is not None and (not isinstance(weight_sha, str) or len(weight_sha) != 64 or
                                       any(c not in "0123456789abcdef" for c in weight_sha)):
            raise ValueError("WEIGHT_SHA_INVALID")
    claimed = all(c.get("downloaded_weights_sha256") and c.get("licensed_for_project") is True and
                  c.get("signed_original_inference_evidence_sha256") and
                  c.get("calibration_verified") is True and
                  c.get("lineage_independence_externally_audited") is True for c in candidates)
    return {"schema": "minimalizer_run41_c02_semantic_route_gate_v1",
            "candidate_count": len(candidates), "candidate_ids": sorted(ids),
            "provider_metadata_only": not bool(claimed),
            "all_evidence_fields_self_attested": bool(claimed),
            "all_weight_inference_calibration_independence_verified": False,
            "observer_independence_certified": False, "approved18_78_verified": False,
            "c02_quality": "HOLD", "release_authorized": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("REFUSE_OVERWRITE")
    output.write_text(json.dumps(check(json.loads(Path(args.manifest).read_text())),
                                 sort_keys=True, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
