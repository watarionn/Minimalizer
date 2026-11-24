"""Turn private six-capability polygon annotations into private owner masks.

The output is suitable for later model training, not model output or approval.
It is intentionally refused inside this Git repository to avoid committing
private source masks or person-level annotation data.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from verify_local_l02_six_cap_dataset import IntakeError, audit_dataset

PART_ROLES = ("outerwear", "underlayer", "sleeve_left", "sleeve_right", "arm_left", "arm_right")
ALL_ROLES = ("person", *PART_ROLES)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _mask_from_points(width: int, height: int, points: list[dict[str, float]]) -> np.ndarray:
    layer = Image.new("1", (width, height), 0)
    ImageDraw.Draw(layer).polygon([(p["x"], p["y"]) for p in points], fill=1)
    return np.asarray(layer, dtype=bool)


def rasterize_one(source_bytes: bytes, annotation: dict[str, Any]) -> dict[str, Any]:
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    image_record = annotation["image"]
    if image_record["source_sha256"] != source_sha:
        raise IntakeError("source bytes do not match the annotation SHA")
    with Image.open(io.BytesIO(source_bytes)) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    if image_record["width"] != width or image_record["height"] != height:
        raise IntakeError("source dimensions do not match the annotation")
    alpha = rgba[:, :, 3] > 0

    people: dict[str, np.ndarray] = {}
    for region in annotation["regions"]:
        if region["role"] != "person":
            continue
        pid = region["person_id"]
        people.setdefault(pid, np.zeros((height, width), dtype=bool))
        people[pid] |= _mask_from_points(width, height, region["points"])
    if not people:
        raise IntakeError("no visible person-instance mask")
    person_ids = sorted(people)
    person_map = np.zeros((height, width), dtype=np.uint16)
    if len(person_ids) >= np.iinfo(np.uint16).max:
        raise IntakeError("too many person instances for the mask format")
    for instance, person_id in enumerate(person_ids, start=1):
        mask = people[person_id] & alpha
        if not mask.any():
            raise IntakeError("person instance has no source-visible pixels")
        if np.any((person_map > 0) & mask):
            raise IntakeError("different person-instance masks overlap")
        person_map[mask] = instance

    owners = {role: np.zeros((height, width), dtype=bool) for role in PART_ROLES}
    object_masks: dict[str, np.ndarray] = {}
    object_roles: dict[str, str] = {}
    object_people: dict[str, str] = {}
    for region in annotation["regions"]:
        role = region["role"]
        if role not in ALL_ROLES:
            continue
        person_id = region["person_id"]
        if person_id not in people:
            raise IntakeError("part mask references a missing person instance")
        mask = _mask_from_points(width, height, region["points"]) & alpha
        own_person = person_map == (person_ids.index(person_id) + 1)
        if role != "person" and np.any(mask & ~own_person):
            raise IntakeError("part mask extends outside its visible person instance")
        object_id = region["object_id"]
        if object_id in object_masks:
            if object_roles[object_id] != role or object_people[object_id] != person_id:
                raise IntakeError("one object ID refers to multiple people or roles")
            if np.any(mask & object_masks[object_id]):
                raise IntakeError("regions of one object claim the same visible pixels")
            object_masks[object_id] |= mask
        else:
            object_masks[object_id] = mask.copy()
            object_roles[object_id] = role
            object_people[object_id] = person_id
        if role in owners:
            if np.any(mask & owners[role]):
                raise IntakeError("two objects of the same role claim the same visible pixels")
            owners[role] |= mask

    occupancy = sum(mask.astype(np.uint8) for mask in owners.values())
    if np.any(occupancy > 1):
        raise IntakeError("visible semantic owner masks overlap; resolve the owner in the annotation")

    complete_for = set(annotation["complete_for"])
    known = {}
    for role in PART_ROLES:
        # Positive polygons are observed even when the rest of that class is
        # incomplete. Only a full-image review can turn remaining pixels negative.
        known[role] = alpha.copy() if role in complete_for else owners[role].copy()
    entity_ids = sorted(object_masks)
    if len(entity_ids) >= np.iinfo(np.uint16).max:
        raise IntakeError("too many annotated objects for the mask format")
    semantic_object_ids = [oid for oid in entity_ids if object_roles[oid] != "person"]
    if len(semantic_object_ids) >= np.iinfo(np.uint16).max:
        raise IntakeError("too many semantic objects for the mask format")
    object_map = np.zeros((height, width), dtype=np.uint16)
    for instance, object_id in enumerate(semantic_object_ids, start=1):
        mask = object_masks[object_id]
        if not mask.any():
            raise IntakeError("annotated object has no source-visible pixels")
        if np.any((object_map > 0) & mask):
            raise IntakeError("different object-instance masks overlap")
        object_map[mask] = instance
    role_codes = {role: code for code, role in enumerate(ALL_ROLES, start=1)}
    entity_role_codes = np.asarray([role_codes[object_roles[oid]] for oid in entity_ids], dtype=np.uint8)
    entity_person_codes = np.asarray([person_ids.index(object_people[oid]) + 1 for oid in entity_ids], dtype=np.uint16)
    entity_index = {object_id: index + 1 for index, object_id in enumerate(entity_ids)}
    try:
        relation_edges = np.asarray([
            [entity_index[edge["occluder_id"]], entity_index[edge["occluded_id"]]]
            for edge in annotation["occlusion_relations"]
        ], dtype=np.uint16).reshape((-1, 2))
    except KeyError as exc:
        raise IntakeError("occlusion relation references an object without a rasterized mask") from exc
    metadata = {
        "schema": "minimalizer/local-l02-six-cap-raster/v1",
        "source_sha256": source_sha,
        "width": width,
        "height": height,
        "subject_group_id": annotation["subject_group_id"],
        "person_ids_in_instance_map_order": person_ids,
        "semantic_object_ids_in_instance_map_order": semantic_object_ids,
        "occlusion_entity_ids_in_edge_index_order": entity_ids,
        "occlusion_entity_roles_in_edge_index_order": [object_roles[oid] for oid in entity_ids],
        "occlusion_entity_person_ids_in_edge_index_order": [object_people[oid] for oid in entity_ids],
        "object_role_codebook": role_codes,
        "complete_for": sorted(complete_for),
        "occlusion_relations": annotation["occlusion_relations"],
        "occlusion_relations_complete": annotation["occlusion_relations_complete"],
        "unknown_policy": annotation["unknown_policy"],
        "part_masks_are_exclusive": True,
        "source_alpha_applied": True,
    }
    return {
        "source_alpha": alpha.astype(np.uint8),
        "person_instance_map": person_map,
        "object_instance_map": object_map,
        "occlusion_entity_role_codes": entity_role_codes,
        "occlusion_entity_person_codes": entity_person_codes,
        "occlusion_relation_edge_index": relation_edges,
        "occlusion_relations_complete": np.asarray(annotation["occlusion_relations_complete"], dtype=np.uint8),
        **{f"owner_{role}": mask.astype(np.uint8) for role, mask in owners.items()},
        **{f"known_{role}": mask.astype(np.uint8) for role, mask in known.items()},
        "metadata_json": np.asarray(json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))),
    }


def _assert_private_output(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    for parent in (resolved, *resolved.parents):
        marker = parent / ".git"
        if marker.is_dir() and (marker / "HEAD").is_file() and (marker / "config").is_file():
            raise IntakeError("refusing to write private masks inside any Git working tree")
        if marker.is_file():
            try:
                pointer = marker.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if pointer.lower().startswith("gitdir:"):
                git_dir = Path(pointer.partition(":")[2].strip())
                if not git_dir.is_absolute():
                    git_dir = (parent / git_dir).resolve()
                if (git_dir / "HEAD").is_file():
                    raise IntakeError("refusing to write private masks inside any Git working tree")


def rasterize_dataset(dataset_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    summary = audit_dataset(dataset_dir)
    if not summary["minimum_cross_person_annotation_coverage_present"]:
        raise IntakeError("six-capability labels or three-person-group coverage are incomplete")
    root, output = Path(dataset_dir), Path(output_dir)
    _assert_private_output(output)
    output.mkdir(parents=True, exist_ok=True)
    image_by_sha: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            image_by_sha[hashlib.sha256(path.read_bytes()).hexdigest()] = path
    count = 0
    for path in root.rglob("*.json"):
        annotation = json.loads(path.read_text(encoding="utf-8"))
        sha = annotation["image"]["source_sha256"]
        arrays = rasterize_one(image_by_sha[sha].read_bytes(), annotation)
        target = output / f"mask-{sha}.npz"
        np.savez_compressed(target, **arrays)
        count += 1
    return {
        "schema": "minimalizer/local-l02-six-cap-raster-readback/v1",
        "dataset_fingerprint_sha256": summary["dataset_fingerprint_sha256"],
        "image_count_rasterized": count,
        "person_group_count": summary["subject_group_count"],
        "private_mask_files_written": count,
        "output_paths_emitted": False,
        "private_masks_written_inside_repository": False,
        "observer_trained": False,
        "quality_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="非公開の六能力ポリゴンから学習用マスクを作ります")
    parser.add_argument("dataset_dir", help="元画像とラベルJSONの非公開フォルダー")
    parser.add_argument("output_dir", help="Gitリポジトリ外の非公開マスク保存先")
    args = parser.parse_args()
    print(json.dumps(rasterize_dataset(args.dataset_dir, args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
