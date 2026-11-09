import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/research/local_l04_delivery_triple_audit.py"
spec = importlib.util.spec_from_file_location("local_l04_delivery", SRC)
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_delivery_pass_is_independent_of_a_vertex_policy(tmp_path):
    source = tmp_path / "source.webp"
    svg = tmp_path / "expanded.svg"
    stage8 = tmp_path / "stage8.json"
    source.write_bytes(b"signed-source")
    svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0h1v1z"/></svg>')
    record = {
        "schema": "minimalizer/local-l04/stage8-source-triple/v1",
        "case": "FIXTURE",
        "signed_source_sha256": _sha(source.read_bytes()),
        "expanded_svg_sha256": _sha(svg.read_bytes()),
        "original_stage8_source_ring_vertices": 9,
        "original_stage8_source_ring_cap": 1,
        "expanded_svg_vertices": 9,
        "expanded_svg_vertex_cap": 1,
        "source_owner_mismatch_pixels": 0,
        "protected_face_arm_owner_mismatch_pixels": 0,
        "source_silhouette_xor_pixels": 0,
    }
    stage8.write_text(json.dumps(record), encoding="utf-8")

    result = delivery.audit_delivery(
        source_path=source, stage8_json_path=stage8, expanded_svg_path=svg,
        expected_source_sha256=_sha(source.read_bytes()),
        expected_stage8_json_sha256=_sha(stage8.read_bytes()),
        expected_expanded_svg_sha256=_sha(svg.read_bytes()),
    )

    assert result["B_L04_delivery"] == "PASS"
    assert result["vertex_policy"] == "OUT_OF_SCOPE_FOR_LANE_B_DELIVERY"
    assert result["A_L04_quality"] == "NOT_JUDGED"
    assert not result["release_authorized"]
