from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path(__file__).parent / "assets" / "approved18_manifest.json"


def test_phase15_approved18_manifest_has_18_unique_pairs_and_fixed_hashes():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data["entries"]

    assert data["schema_version"] == 1
    assert data["drive_folder_id"] == "1oWUtdUAfLE4x8_T5VS5GQyHEHn7FQ35v"
    assert data["generation_baseline"] == {
        "level": 4,
        "analysis_max_side": 320,
        "preset": "approved_reference",
    }
    assert len(entries) == 18
    assert [entry["order"] for entry in entries] == list(range(1, 19))
    assert len({entry["character"] for entry in entries}) == 18
    assert len({entry["input_file"] for entry in entries}) == 18
    assert len({entry["approved_file"] for entry in entries}) == 18

    for entry in entries:
        assert entry["input_file"].endswith("_list_thumb.png")
        assert entry["approved_file"].endswith("_APPROVED_GEOMETRIC_REFERENCE.png")
        assert len(entry["input_sha256"]) == 64
        assert len(entry["approved_sha256"]) == 64
        int(entry["input_sha256"], 16)
        int(entry["approved_sha256"], 16)


def test_phase15_approved_reference_uses_direct_coarse_planes():
    from minimalize_engine import minimalize_rinka_reference

    corpus = Path(__file__).parent / "assets" / "corpus" / "Omaru-Polka_list_thumb.png"
    scene = minimalize_rinka_reference(
        corpus,
        4,
        analysis_max_side=220,
        preset="approved_reference",
    )
    target = scene.metadata["target_style"]

    assert target["version"] == "phase15"
    assert target["preset"] == "approved_reference"
    assert target["approved_reference_direct"] is True
    assert target["macro_subject_guard"]["enabled"] is True
    assert target["phase15_face_fallback"]["face_plane_created"] is True
    assert len(scene.shapes) <= 22
