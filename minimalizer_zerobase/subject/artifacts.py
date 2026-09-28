from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .extraction import SubjectExtraction


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(payload: dict) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
def render_subject_overlay(source: Image.Image, mask: np.ndarray) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    if mask.shape != rgb.shape[:2]:
        raise ValueError("mask must match source dimensions")
    foreground = mask > 0
    overlay = (rgb.astype(np.float32) * 0.25).astype(np.uint8)
    overlay[foreground] = rgb[foreground]

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    cv2.drawContours(bgr, contours, -1, (255, 255, 0), 2)
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), mode="RGB")


def write_phase3_artifacts(
    source_path: str | Path,
    extraction: SubjectExtraction,
    output_dir: str | Path,
    *,
    config: dict,
) -> dict:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as source:
        source_copy = source.copy()
    mask_path = output_dir / "03_subject_mask.png"
    overlay_path = output_dir / "03_subject_overlay.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    Image.fromarray(extraction.mask, mode="L").save(mask_path, format="PNG")
    overlay = render_subject_overlay(source_copy, extraction.mask)
    overlay.save(overlay_path, format="PNG")
    shutil.copyfile(overlay_path, preview_path)

    metrics = {
        "bbox_xywh": list(extraction.metadata.bbox_xywh),
        "foreground_ratio": extraction.metadata.foreground_ratio,
        "alpha_present": extraction.metadata.alpha_present,
        "alpha_foreground_ratio": extraction.metadata.alpha_foreground_ratio,
        "alpha_informative": extraction.metadata.alpha_informative,
        "evidence_source": extraction.metadata.evidence_source,
    }
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs = {
        "03_subject_mask.png": sha256_file(mask_path),
        "03_subject_overlay.png": sha256_file(overlay_path),
        "preview.png": sha256_file(preview_path),
        "metrics.json": sha256_file(metrics_path),
    }
    stage = {
        "phase": 3,
        "stage": "canonical_subject_extraction",
        "producer": "minimalizer-zerobase2-phase3",
        "producer_version": "1.0",
        "source": {
            "path": source_path.name,
            "sha256": sha256_file(source_path),
            "width": extraction.metadata.width,
            "height": extraction.metadata.height,
        },
        "config": config,
        "config_sha256": canonical_json_sha256(config),
        "metadata": extraction.metadata.to_dict(),
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    stage["outputs"]["stage.json"] = sha256_file(stage_path)
    return stage
