import json

from tools.research.audit_local_l02_phase5_input import audit_phase5_input


def receipt():
    return {
        "phase4": "PASS",
        "cases": {
            case: {"source_sha256": f"{case.lower():0<64}", "candidate_sha256": f"{case.lower():1<64}"}
            for case in ("H04", "H06", "H08")
        },
    }


def test_current_style_root_holds_without_full_part_mask_bundle(tmp_path):
    result = audit_phase5_input(receipt(), tmp_path)
    assert result["phase5_input"] == "HOLD"
    assert result["phase5"] == "NO_GO"
    assert all("PHASE4_PART_MASK_BUNDLE_MISSING" in case["failures"] for case in result["cases"].values())


def test_candidate_bound_complete_bundle_is_ready(tmp_path):
    value = receipt()
    for case, item in value["cases"].items():
        phase4 = tmp_path / case / "phase_04"
        masks = phase4 / "part_masks"
        masks.mkdir(parents=True)
        for part in (
            "head", "hair", "face", "neck", "torso", "left_arm", "right_arm",
            "lower_body", "major_clothing", "accessory_or_held_object", "unknown",
        ):
            (masks / f"{part}.png").write_bytes(b"mask")
        (phase4 / "metrics.json").write_text("{}", encoding="utf-8")
        (phase4 / "stage.json").write_text(
            json.dumps({
                "source": {"sha256": item["source_sha256"]},
                "l02_candidate": {"candidate_sha256": item["candidate_sha256"]},
            }),
            encoding="utf-8",
        )
    result = audit_phase5_input(value, tmp_path)
    assert result["phase5_input"] == "READY"
    assert result["phase5"] == "READY"
