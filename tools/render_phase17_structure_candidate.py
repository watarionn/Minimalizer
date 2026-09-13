from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalize_engine import minimalize_rinka_reference
from minimalize_engine.alpha_structure import build_alpha_structure_shapes
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.image_loader import load_image_data
from minimalize_engine.io.svg_exporter import export_svg
from minimalize_engine.macro_subject_guard import phase15_subject_candidate
from minimalize_engine.models import Scene
from minimalize_engine.opaque_subject_rescue import prepare_rinka_opaque_subject_input
from minimalize_engine.structure_first import build_structure_first_parts
from minimalize_engine.structure_first_color import build_structure_first_color_shapes
from minimalize_engine.structure_foreground import build_structure_foreground
from minimalize_engine.structure_foreground_completion import (
    accept_structure_foreground_completion,
    complete_structure_foreground,
)
from minimalize_engine.structure_face_locator import locate_structure_face
from minimalize_engine.structure_head_anchor import build_face_anchored_head
from minimalize_engine.structure_head_silhouette import build_silhouette_head
from minimalize_engine.structure_mask_selector import select_structure_mask
from minimalize_engine.structure_sleeve_completion import (
    accept_structure_sleeve_completion,
    complete_structure_sleeves,
)
from minimalize_engine.subject_segmentation import segment_subject_without_ai

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Phase 17 structure-first candidate images without changing production."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--analysis-max-side", type=int, default=320)
    return parser.parse_args()


def _images(path: Path) -> list[Path]:
    return sorted(
        item for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
    )


def _structure_source(image_path: Path, width: int, height: int) -> tuple[np.ndarray, np.ndarray, str] | None:
    segmentation = segment_subject_without_ai(image_path)
    rescue = prepare_rinka_opaque_subject_input(image_path)
    candidate = phase15_subject_candidate(image_path, segmentation, rescue)
    data = load_image_data(image_path)
    rgb = data.rgb
    candidates: dict[str, np.ndarray | None] = {}

    if candidate.rgba is not None:
        rgba = np.asarray(candidate.rgba)
        if candidate.mask is not None:
            mask = (np.asarray(candidate.mask) > 0).astype(np.uint8)
            if mask.shape != rgb.shape[:2]:
                mask = cv2.resize(mask, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
            candidates["phase15_mask"] = mask
        elif rgba.shape[2] >= 4:
            mask = (rgba[:, :, 3] >= 16).astype(np.uint8)
            if mask.shape != rgb.shape[:2]:
                mask = cv2.resize(mask, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
            candidates["phase15_alpha"] = mask

    if data.alpha is not None:
        candidates["source_alpha"] = (data.alpha >= 16).astype(np.uint8)
    foreground = build_structure_foreground(rgb)
    if foreground.enabled and foreground.mask is not None:
        candidates["border_background"] = foreground.mask

    selection = select_structure_mask(rgb, candidates)
    if not selection.enabled or selection.mask is None:
        return None
    mask = selection.mask
    mask_source = selection.source

    seed_face = locate_structure_face(rgb, mask)
    if seed_face.enabled and seed_face.mask is not None:
        completion = complete_structure_foreground(rgb, mask, seed_face.mask)
        if completion.enabled and completion.mask is not None:
            completed_selection = select_structure_mask(
                rgb,
                {mask_source: mask, "face_seeded_completion": completion.mask},
            )
            if (
                completed_selection.enabled
                and completed_selection.mask is not None
                and completed_selection.source == "face_seeded_completion"
                and accept_structure_foreground_completion(
                    completion, selection.score, completed_selection.score
                )
            ):
                selection = completed_selection
                mask = completed_selection.mask
                mask_source = completed_selection.source

        seed_face = locate_structure_face(rgb, mask)
        if seed_face.enabled and seed_face.mask is not None:
            sleeve = complete_structure_sleeves(rgb, mask, seed_face.mask)
            if sleeve.enabled and sleeve.mask is not None:
                sleeve_selection = select_structure_mask(
                    rgb,
                    {mask_source: mask, "sleeve_completion": sleeve.mask},
                )
                sleeve_completed_face = locate_structure_face(rgb, sleeve_selection.mask) if sleeve_selection.mask is not None else None
                if (
                    sleeve_selection.enabled
                    and sleeve_selection.mask is not None
                    and sleeve_selection.source == "sleeve_completion"
                    and sleeve_completed_face is not None
                    and sleeve_completed_face.enabled
                    and accept_structure_sleeve_completion(
                        sleeve,
                        selection.score,
                        sleeve_selection.score,
                        seed_face.score,
                        sleeve_completed_face.score,
                    )
                ):
                    selection = sleeve_selection
                    mask = sleeve_selection.mask
                    mask_source = sleeve_selection.source

    target_size = (width, height)
    if rgb.shape[:2] != (height, width):
        rgb = cv2.resize(rgb, target_size, interpolation=cv2.INTER_AREA)
    if mask.shape != (height, width):
        mask = cv2.resize(mask, target_size, interpolation=cv2.INTER_NEAREST)
    return rgb, mask, mask_source


def render_one(image_path: Path, output_dir: Path, analysis_max_side: int) -> dict:
    baseline = minimalize_rinka_reference(
        image_path,
        4,
        analysis_max_side=analysis_max_side,
        preset="approved_reference",
    )
    source = _structure_source(image_path, baseline.width, baseline.height)
    if source is None:
        return {"file": image_path.name, "rendered": False, "reason": "subject_source_missing"}

    rgb, mask, mask_source = source
    face = locate_structure_face(rgb, mask)
    if not face.enabled:
        return {
            "file": image_path.name,
            "rendered": False,
            "reason": f"face_gate:{face.reason}",
            "mask_source": mask_source,
        }

    result = build_structure_first_parts(
        rgb,
        mask,
        face_anchor_mask=face.mask,
    )
    if not result.enabled:
        return {
            "file": image_path.name,
            "rendered": False,
            "reason": result.reason,
            "mask_source": mask_source,
        }

    color_shapes = build_structure_first_color_shapes(rgb, result)
    silhouette_head = build_silhouette_head(rgb, mask, face.mask)
    head_anchor = build_face_anchored_head(rgb, mask, face.mask)
    preferred_face = silhouette_head.face_mask if silhouette_head.enabled else face.mask
    preferred_head = (
        silhouette_head.head_mask if silhouette_head.enabled
        else head_anchor.head_mask if head_anchor.enabled else result.masks.get("head")
    )
    preferred_hair = (
        silhouette_head.hair_mask if silhouette_head.enabled
        else head_anchor.hair_mask if head_anchor.enabled else result.masks.get("hair")
    )
    alpha_shapes = build_alpha_structure_shapes(
        rgb,
        mask,
        face_mask=preferred_face,
        head_mask=preferred_head,
        hair_mask=preferred_hair,
        torso_mask=result.masks.get("torso"),
        left_arm_mask=result.masks.get("left_arm"),
        right_arm_mask=result.masks.get("right_arm"),
    )
    candidate_shapes = alpha_shapes.shapes if alpha_shapes.enabled else (color_shapes or result.shapes)
    scene = Scene(
        width=baseline.width,
        height=baseline.height,
        background=baseline.background,
        shapes=list(candidate_shapes),
        metadata={
            "phase17_candidate": True,
            "phase17_structure": result.to_dict(),
            "phase17_color_shape_count": len(color_shapes),
            "phase17_alpha_structure": alpha_shapes.to_dict(),
            "mask_source": mask_source,
        },
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / f"{image_path.stem}_phase17_structure.svg"
    png_path = output_dir / f"{image_path.stem}_phase17_structure.png"
    export_svg(scene, svg_path)
    export_png(scene, png_path)
    return {
        "file": image_path.name,
        "rendered": True,
        "mask_source": mask_source,
        "png": png_path.name,
        "svg": svg_path.name,
        **result.to_dict(),
    }


def main() -> int:
    args = _parse_args()
    rows = [
        render_one(image_path, args.output_dir, args.analysis_max_side)
        for image_path in _images(args.input_dir)
    ]
    rendered = sum(1 for row in rows if row.get("rendered"))
    print(f"rendered={rendered}/{len(rows)}")
    for row in rows:
        status = "ok" if row.get("rendered") else f"skip:{row.get('reason')}"
        print(f"{row['file']}: {status}")
    return 0 if rendered else 1


if __name__ == "__main__":
    raise SystemExit(main())
