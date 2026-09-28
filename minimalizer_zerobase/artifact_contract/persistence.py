from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from minimalizer_zerobase.core.serialization import CanonicalModel

from .contracts import ArtifactManifest, ArtifactRecord, RunManifest


@dataclass(frozen=True)
class ContractBundleWriteResult(CanonicalModel):
    run_manifest_path: str
    run_manifest_sha256: str
    artifact_manifest_path: str
    artifact_manifest_sha256: str


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_canonical_json(path: Path, model: CanonicalModel) -> str:
    payload = (model.to_json() + "\n").encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def write_contract_bundle(
    output_dir: str | Path,
    run_manifest: RunManifest,
    artifacts: tuple[ArtifactRecord, ...],
) -> ContractBundleWriteResult:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    ordered = tuple(sorted(artifacts, key=lambda item: item.artifact_id))
    artifact_manifest = ArtifactManifest(
        run_id=run_manifest.run_id,
        artifacts=ordered,
    )

    run_path = root / "run.json"
    artifact_path = root / "artifacts.json"
    run_sha = _write_canonical_json(run_path, run_manifest)
    artifact_sha = _write_canonical_json(artifact_path, artifact_manifest)
    return ContractBundleWriteResult(
        run_manifest_path=run_path.name,
        run_manifest_sha256=run_sha,
        artifact_manifest_path=artifact_path.name,
        artifact_manifest_sha256=artifact_sha,
    )
