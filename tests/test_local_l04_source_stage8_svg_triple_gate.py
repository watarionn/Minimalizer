import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SRC = (Path(__file__).resolve().parents[1] /
       "tools/research/local_l04_source_stage8_svg_triple_gate.py")
spec = importlib.util.spec_from_file_location("local_l04_triple_gate", SRC)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path):
    source = b"signed-private-source-fixture"
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0h1v1z"/></svg>'
    record = {
        "schema": "minimalizer/local-l04/stage8-source-triple/v1",
        "case": "LOCAL_FIXTURE",
        "signed_source_sha256": _sha(source),
        "expanded_svg_sha256": _sha(svg),
        "original_stage8_source_ring_vertices": 4,
        "original_stage8_source_ring_cap": 4,
        "expanded_svg_vertices": 4,
        "expanded_svg_vertex_cap": 8,
        "source_owner_mismatch_pixels": 0,
        "protected_face_arm_owner_mismatch_pixels": 0,
        "source_silhouette_xor_pixels": 0,
    }
    source_path = tmp_path / "source.webp"
    svg_path = tmp_path / "expanded.svg"
    source_path.write_bytes(source)
    svg_path.write_bytes(svg)
    stage8_path = tmp_path / "stage8.json"
    stage8_path.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    return source_path, stage8_path, svg_path


def _evaluate(paths):
    source, stage8, svg = paths
    return gate.evaluate_paths(
        source_path=source, stage8_json_path=stage8, expanded_svg_path=svg,
        expected_source_sha256=_sha(source.read_bytes()),
        expected_stage8_json_sha256=_sha(stage8.read_bytes()),
        expected_expanded_svg_sha256=_sha(svg.read_bytes()),
    )


def test_exact_triple_is_verified_but_never_release_authorized(tmp_path):
    result = _evaluate(_fixture(tmp_path))
    assert result["three_artifact_hashes_verified"]
    assert result["numerical_candidate_eligible_for_independent_review"]
    assert result["L04_formal"] == "HOLD"
    assert result["production_release"] == "NO_GO"
    assert not result["release_authorized"]


def test_source_tamper_is_rejected(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    expected = _sha(source.read_bytes())
    source.write_bytes(source.read_bytes() + b"tamper")
    with pytest.raises(gate.L04Hold, match="SIGNED_SOURCE_SHA_MISMATCH"):
        gate.evaluate_paths(source_path=source, stage8_json_path=stage8,
                            expanded_svg_path=svg,
                            expected_source_sha256=expected,
                            expected_stage8_json_sha256=_sha(stage8.read_bytes()),
                            expected_expanded_svg_sha256=_sha(svg.read_bytes()))


def test_svg_tamper_is_rejected(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    expected = _sha(svg.read_bytes())
    svg.write_bytes(svg.read_bytes().replace(b"h1", b"h2"))
    with pytest.raises(gate.L04Hold, match="EXPANDED_SVG_SHA_MISMATCH"):
        gate.evaluate_paths(source_path=source, stage8_json_path=stage8,
                            expanded_svg_path=svg,
                            expected_source_sha256=_sha(source.read_bytes()),
                            expected_stage8_json_sha256=_sha(stage8.read_bytes()),
                            expected_expanded_svg_sha256=expected)


def test_manifest_cross_link_is_required(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    record = json.loads(stage8.read_text(encoding="utf-8"))
    record["signed_source_sha256"] = "0" * 64
    stage8.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(gate.L04Hold, match="MANIFEST_SOURCE_SHA_MISMATCH"):
        _evaluate(paths)


def test_external_markup_is_rejected(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    svg.write_bytes(b'<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg"/>')
    with pytest.raises(gate.L04Hold, match="UNSAFE_EXPANDED_SVG_MARKUP"):
        _evaluate(paths)


@pytest.mark.parametrize(("svg_bytes", "reason"), (
    (b'<svg xmlns="http://www.w3.org/2000/svg"><script>1</script><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_CONTENT:script"),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.invalid/x"/><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_CONTENT:image"),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><use href="data:image/svg+xml,x"/><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_EXTERNAL_REFERENCE"),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><use href="javascript:run()"/><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_EXTERNAL_REFERENCE"),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><use href="//example.invalid/x"/><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_EXTERNAL_REFERENCE"),
    (b'<svg xmlns="http://www.w3.org/2000/svg"><FOREIGNOBJECT/><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_CONTENT:FOREIGNOBJECT"),
    (b'<svg xmlns="http://www.w3.org/2000/svg" onload="run()"><path d="M0 0h1"/></svg>',
     "UNSAFE_EXPANDED_SVG_EVENT_ATTRIBUTE"),
))
def test_embedded_or_external_svg_content_is_rejected(tmp_path, svg_bytes, reason):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    svg.write_bytes(svg_bytes)
    with pytest.raises(gate.L04Hold, match=reason):
        _evaluate(paths)


def test_empty_expanded_svg_geometry_is_rejected(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    empty_svg = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    svg.write_bytes(empty_svg)
    record = json.loads(stage8.read_text(encoding="utf-8"))
    record["expanded_svg_sha256"] = _sha(empty_svg)
    stage8.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(gate.L04Hold, match="EMPTY_EXPANDED_SVG_GEOMETRY"):
        _evaluate(paths)


def test_bad_quality_metrics_remain_hold(tmp_path):
    paths = _fixture(tmp_path)
    source, stage8, svg = paths
    record = json.loads(stage8.read_text(encoding="utf-8"))
    record["source_silhouette_xor_pixels"] = 1
    stage8.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    result = _evaluate(paths)
    assert result["three_artifact_hashes_verified"]
    assert not result["numerical_candidate_eligible_for_independent_review"]
    assert result["L04_formal"] == "HOLD"
