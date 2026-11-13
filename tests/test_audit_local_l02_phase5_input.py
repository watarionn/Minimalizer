import json
import hashlib

from PIL import Image

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
            Image.new("L", (2, 2), 0).save(masks / f"{part}.png")
        metrics = phase4 / "metrics.json"
        metrics.write_text("{}", encoding="utf-8")
        outputs = {"metrics.json": hashlib.sha256(metrics.read_bytes()).hexdigest()}
        for part in (
            "head", "hair", "face", "neck", "torso", "left_arm", "right_arm",
            "lower_body", "major_clothing", "accessory_or_held_object", "unknown",
        ):
            path = masks / f"{part}.png"
            outputs[f"part_masks/{part}.png"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (phase4 / "stage.json").write_text(
            json.dumps({
                "source": {"sha256": item["source_sha256"], "width": 2, "height": 2},
                "l02_candidate": {"candidate_sha256": item["candidate_sha256"]},
                "outputs": outputs,
            }),
            encoding="utf-8",
        )
    result = audit_phase5_input(value, tmp_path)
    assert result["phase5_input"] == "READY"
    assert result["phase5"] == "READY"


def test_tampered_part_mask_is_not_ready(tmp_path):
    value = receipt()
    for case, item in value["cases"].items():
        phase4 = tmp_path / case / "phase_04"
        masks = phase4 / "part_masks"
        masks.mkdir(parents=True)
        for part in (
            "head", "hair", "face", "neck", "torso", "left_arm", "right_arm",
            "lower_body", "major_clothing", "accessory_or_held_object", "unknown",
        ):
            Image.new("L", (2, 2), 0).save(masks / f"{part}.png")
        metrics = phase4 / "metrics.json"
        metrics.write_text("{}", encoding="utf-8")
        outputs = {"metrics.json": hashlib.sha256(metrics.read_bytes()).hexdigest()}
        for path in masks.glob("*.png"):
            outputs[f"part_masks/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (phase4 / "stage.json").write_text(json.dumps({
            "source": {"sha256": item["source_sha256"], "width": 2, "height": 2},
            "l02_candidate": {"candidate_sha256": item["candidate_sha256"]},
            "outputs": outputs,
        }), encoding="utf-8")
    (tmp_path / "H06" / "phase_04" / "part_masks" / "left_arm.png").write_bytes(b"tampered")
    result = audit_phase5_input(value, tmp_path)
    assert result["phase5_input"] == "HOLD"
    assert "H06:PART_MASK_NOT_PNG:left_arm.png" in result["failures"]
