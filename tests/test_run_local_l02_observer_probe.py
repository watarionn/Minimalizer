from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

import tools.research.run_local_l02_observer_probe as probe
from tools.research.local_l02_observer_evidence_contract import (
    ObserverEvidenceHold,
    PairwiseRelationObservation,
    RoleObservation,
    ScalarObservation,
    assess_observer_evidence,
)


def _sha(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes(order="C")).hexdigest()


def _write_adapter(path: Path) -> None:
    path.write_text(
        """
import argparse
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--spec', required=True)
parser.add_argument('--weights', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--case', required=True)
args = parser.parse_args()
shape = np.asarray(Image.open(args.source).convert('RGBA')).shape[:2]
def mask(row, col):
    value = np.zeros(shape, dtype=bool)
    value[row, col] = True
    return value
unknown = np.zeros(shape, dtype=bool)
unknown[-1, -1] = True
relation = np.zeros(shape, dtype=np.int8)
relation[0, 0] = 1
grouping = np.zeros(shape, dtype=np.uint32)
grouping[0, 0] = 1
np.savez(
    args.output,
    outerwear_mask=mask(0, 0), outerwear_unknown=unknown,
    underlayer_mask=mask(0, 1), underlayer_unknown=unknown,
    sleeve_mask=mask(1, 0), sleeve_unknown=unknown,
    arm_mask=mask(1, 1), arm_unknown=unknown,
    occlusion_outerwear_underlayer=relation,
    occlusion_sleeve_arm=relation,
    occlusion_garment_body=relation,
    instance_grouping=grouping,
)
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_source(path: Path, color: tuple[int, int, int, int]) -> str:
    Image.new("RGBA", (4, 4), color).save(path, format="PNG")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_spec(spec: Path, weights: Path) -> None:
    contract = [
        "outerwear", "underlayer", "sleeve", "arm",
        "occlusion_outerwear_underlayer", "occlusion_sleeve_arm",
        "occlusion_garment_body", "instance_grouping",
    ]
    weights.write_bytes(b"fixed-test-weights")
    spec.write_text(
        json.dumps(
            {
                "schema": "minimalizer/l02/observer_checkpoint/v1",
                "observer_id": "test-six-capability-observer",
                "revision": "test-revision-1",
                "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
                "source_only": True,
                "human_labels_used_for_inference": False,
                "unknown_policy": "separate_from_negative",
                "same_config_cases": ["H04", "H06", "H08"],
                "output_contract": contract,
            }
        ),
        encoding="utf-8",
    )


def test_probe_runs_same_adapter_config_for_three_signed_sources(tmp_path, monkeypatch):
    sources = {}
    source_hashes = {}
    for case, color in zip(
        ("H04", "H06", "H08"),
        ((255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)),
    ):
        sources[case] = tmp_path / f"{case}.png"
        source_hashes[case] = _write_source(sources[case], color)
    monkeypatch.setattr(probe, "SOURCE_SHA256", source_hashes)
    monkeypatch.setattr(probe, "CASES", ("H04", "H06", "H08"))

    spec = tmp_path / "spec.json"
    weights = tmp_path / "weights.bin"
    adapter = tmp_path / "adapter.py"
    _write_spec(spec, weights)
    _write_adapter(adapter)
    receipt = tmp_path / "private" / "probe.json"
    result = probe.run_probe(
        spec=spec,
        weights=weights,
        adapter=adapter,
        sources=sources,
        output_dir=tmp_path / "private" / "outputs",
        receipt=receipt,
    )

    assert result["status"] == "PROBE_FROZEN_RESEARCH_ONLY"
    assert result["human_labels_used_for_inference"] is False
    assert result["phase4"] == "HOLD"
    cases = result["cases"]
    assert set(cases) == {"H04", "H06", "H08"}
    assert len({cases[case]["inference_config_sha256"] for case in cases}) == 1
    assert all((tmp_path / "private" / "outputs" / f"{case}_observer_output.npz").is_file() for case in cases)
    assert json.loads(receipt.read_text(encoding="utf-8"))["same_config_cases"] == ["H04", "H06", "H08"]


def test_probe_refuses_output_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    source_sha = _write_source(source, (255, 255, 255, 255))
    monkeypatch.setattr(probe, "SOURCE_SHA256", {case: source_sha for case in ("H04", "H06", "H08")})
    monkeypatch.setattr(probe, "CASES", ("H04", "H06", "H08"))
    spec = tmp_path / "spec.json"
    weights = tmp_path / "weights.bin"
    adapter = tmp_path / "adapter.py"
    _write_spec(spec, weights)
    _write_adapter(adapter)
    output_dir = tmp_path / "private" / "outputs"
    output_dir.mkdir(parents=True)
    (output_dir / "H04_observer_output.npz").write_bytes(b"protected")
    with pytest.raises(probe.ObserverProbeHold, match="REFUSE_OVERWRITE_PRIVATE_OUTPUT"):
        probe.run_probe(
            spec=spec,
            weights=weights,
            adapter=adapter,
            sources={case: source for case in ("H04", "H06", "H08")},
            output_dir=output_dir,
            receipt=tmp_path / "private" / "probe.json",
        )


def test_one_six_capability_observer_identity_is_required():
    alpha = np.ones((2, 2), dtype=bool)
    masks = []
    for role in ("outerwear", "underlayer", "sleeve", "arm"):
        mask = np.zeros_like(alpha)
        mask[0, 0] = True
        masks.append(RoleObservation(role, mask, _sha(mask), "observer-a", np.zeros_like(alpha)))
    relation = np.zeros((2, 2), dtype=np.int8)
    relation[0, 0] = 1
    grouping = np.zeros((2, 2), dtype=np.uint32)
    grouping[0, 0] = 1
    with pytest.raises(ObserverEvidenceHold, match="MULTIPLE_OBSERVERS_IN_BUNDLE"):
        assess_observer_evidence(
            source_alpha=alpha,
            role_observations=tuple(masks),
            occlusion_relation=tuple(
                PairwiseRelationObservation(
                    role_a,
                    role_b,
                    relation,
                    _sha(relation),
                    "observer-b" if role_a == "sleeve" else "observer-a",
                )
                for role_a, role_b in (
                    ("outerwear", "underlayer"),
                    ("sleeve", "arm"),
                    ("garment", "body"),
                )
            ),
            instance_grouping=ScalarObservation(
                "instance_grouping", grouping, _sha(grouping), "observer-a"
            ),
        )
