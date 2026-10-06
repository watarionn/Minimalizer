from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np

ROLE_MASK_ARTIFACT_VERSION = "sa10.6-v1"
REQUIRED_REGRESSION_ROLES = ("hair", "major_clothing")


def write_role_mask_artifact(
    role_masks: Mapping[str, np.ndarray],
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    roles = {}
    shape = None
    for role in REQUIRED_REGRESSION_ROLES:
        if role not in role_masks:
            raise ValueError(f"missing regression role mask: {role}")
        mask = np.asarray(role_masks[role]).astype(bool)
        if mask.ndim != 2:
            raise ValueError(f"role mask must be 2D: {role}")
        if shape is None:
            shape = mask.shape
        elif mask.shape != shape:
            raise ValueError("role masks must share one image frame")
        data = (mask.astype(np.uint8) * 255)
        ok, encoded = cv2.imencode(".png", data)
        if not ok:
            raise ValueError(f"failed to encode role mask: {role}")
        payload = encoded.tobytes()
        filename = f"{role}.png"
        (output_dir / filename).write_bytes(payload)
        roles[role] = {
            "file": filename,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "pixels": int(mask.sum()),
        }
    manifest = {
        "version": ROLE_MASK_ARTIFACT_VERSION,
        "source_derived": True,
        "evaluation_only": True,
        "production_output_changed": False,
        "shape": list(shape),
        "roles": roles,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_role_mask_artifact(output_dir: Path) -> dict[str, np.ndarray]:
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("evaluation_only") is not True:
        raise ValueError("role mask artifact must remain evaluation-only")
    result = {}
    for role in REQUIRED_REGRESSION_ROLES:
        row = manifest["roles"][role]
        payload = (output_dir / row["file"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f"role mask checksum mismatch: {role}")
        image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"failed to decode role mask: {role}")
        result[role] = image > 0
    return result
