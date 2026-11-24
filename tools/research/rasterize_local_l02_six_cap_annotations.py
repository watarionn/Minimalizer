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
    known_person = alpha.copy() if "person" in complete_for else (person_map > 0)
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
        "known_person": known_person.astype(np.uint8),
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


def rasterize_dataset(
    dataset_dir: str | Path,
    output_dir: str | Path,
    split_manifest_path: str | Path,
    *,
    split_name: str = "train_validation",
    frozen_model_path: str | Path | None = None,
) -> dict[str, Any]:
    summary = audit_dataset(dataset_dir)
    if not summary["minimum_cross_person_annotation_coverage_present"]:
        raise IntakeError("six-capability labels or three-person-group coverage are incomplete")
    root, output = Path(dataset_dir).resolve(), Path(output_dir).resolve()
    split_path = Path(split_manifest_path)
    if split_name not in {"train_validation", "train", "validation", "blind_test"}:
        raise IntakeError("unsupported dataset split")
    frozen_model_sha256 = None
    if split_name == "blind_test":
        if frozen_model_path is None:
            raise IntakeError("blind-test labels require the frozen model checkpoint file")
        model_path = Path(frozen_model_path).resolve()
        _assert_private_output(model_path)
        if not model_path.is_file():
            raise IntakeError("frozen model checkpoint file does not exist")
        model_digest = hashlib.sha256()
        with model_path.open("rb") as model_file:
            for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
                model_digest.update(chunk)
        frozen_model_sha256 = model_digest.hexdigest()
    elif frozen_model_path is not None:
        raise IntakeError("frozen model checkpoint is only accepted for blind-test rasterization")
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise IntakeError("mask output must be outside the input dataset folder")
    _assert_private_output(output)
    try:
        split_doc = json.loads(split_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IntakeError("private split manifest cannot be read") from exc
    if (not isinstance(split_doc, dict)
            or split_doc.get("schema") != "minimalizer/local-l02-person-group-split/v1"
            or split_doc.get("dataset_fingerprint_sha256") != summary["dataset_fingerprint_sha256"]
            or not isinstance(split_doc.get("group_assignments"), dict)
            or not isinstance(split_doc.get("records"), list)):
        raise IntakeError("split manifest does not bind to this dataset fingerprint")

    image_by_sha: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            image_by_sha[hashlib.sha256(path.read_bytes()).hexdigest()] = path

    record_by_sha: dict[str, dict[str, str]] = {}
    for record in split_doc.get("records", []):
        if (not isinstance(record, dict)
                or record.get("split") not in {"train", "validation", "blind_test"}
                or not isinstance(record.get("source_sha256"), str)
                or not isinstance(record.get("subject_group_id"), str)
                or record["source_sha256"] in record_by_sha):
            raise IntakeError("split manifest contains malformed or duplicate source records")
        group_split = split_doc.get("group_assignments", {}).get(record["subject_group_id"])
        if group_split != record["split"]:
            raise IntakeError("split manifest assigns one person group to multiple splits")
        record_by_sha[record["source_sha256"]] = record
    if set(record_by_sha) != set(image_by_sha):
        raise IntakeError("split manifest source set differs from the audited dataset")

    annotations_by_sha: dict[str, dict[str, Any]] = {}
    for path in root.rglob("*.json"):
        try:
            annotation = json.loads(path.read_text(encoding="utf-8"))
            sha = annotation["image"]["source_sha256"]
        except Exception as exc:
            raise IntakeError("annotation changed after split generation") from exc
        record = record_by_sha.get(sha)
        if (record is None or annotation.get("subject_group_id") != record["subject_group_id"]):
            raise IntakeError("split manifest person-group binding changed")
        annotations_by_sha[sha] = annotation
    if set(annotations_by_sha) != set(image_by_sha):
        raise IntakeError("annotation source set differs from the audited dataset")

    if split_name == "train_validation":
        selected_splits = {"train", "validation"}
    else:
        selected_splits = {split_name}
    selected_shas = {
        sha for sha, record in record_by_sha.items() if record["split"] in selected_splits
    }
    output.mkdir(parents=True, exist_ok=True)
    existing_mask_shas = {
        path.stem.removeprefix("mask-")
        for path in output.glob("mask-*.npz") if path.is_file()
    }
    if existing_mask_shas - selected_shas:
        raise IntakeError("output directory contains masks outside the selected split; choose an empty output directory")

    count = 0
    for sha in sorted(selected_shas):
        annotation = annotations_by_sha[sha]
        arrays = rasterize_one(image_by_sha[sha].read_bytes(), annotation)
        target = output / f"mask-{sha}.npz"
        np.savez_compressed(target, **arrays)
        count += 1
    return {
        "schema": "minimalizer/local-l02-six-cap-raster-readback/v1",
        "dataset_fingerprint_sha256": summary["dataset_fingerprint_sha256"],
        "split_manifest_sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
        "selected_splits": sorted(selected_splits),
        "image_count_rasterized": count,
        "person_group_count": summary["subject_group_count"],
        "private_mask_files_written": count,
        "output_paths_emitted": False,
        "private_masks_written_inside_repository": False,
        "observer_trained": False,
        "quality_approved": False,
        "blind_test_masks_emitted": split_name == "blind_test",
        "blind_test_used_for_training_or_validation": False,
        "frozen_model_sha256": frozen_model_sha256.lower() if split_name == "blind_test" else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="非公開の六能力ポリゴンから学習用マスクを作ります")
    parser.add_argument("dataset_dir", help="元画像とラベルJSONの非公開フォルダー")
    parser.add_argument("split_manifest", help="人物群split固定器が生成した非公開manifest")
    parser.add_argument("output_dir", help="Gitリポジトリ外の非公開マスク保存先")
    parser.add_argument("--split", choices=("train_validation", "train", "validation", "blind_test"),
                        default="train_validation", help="blind_testは凍結後の評価時だけ指定")
    parser.add_argument("--frozen-model", help="blind_testを開く凍結model checkpointファイル")
    args = parser.parse_args()
    print(json.dumps(rasterize_dataset(
        args.dataset_dir, args.output_dir, args.split_manifest,
        split_name=args.split, frozen_model_path=args.frozen_model,
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
