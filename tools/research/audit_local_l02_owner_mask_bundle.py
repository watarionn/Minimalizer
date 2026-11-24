"""Source-free structural audit for private train/validation owner masks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from verify_local_l02_six_cap_dataset import IntakeError

PART_ROLES = ("outerwear", "underlayer", "sleeve_left", "sleeve_right", "arm_left", "arm_right")
ALL_ROLES = ("person", *PART_ROLES)
MASK_KEYS = ("source_alpha", "person_instance_map", "object_instance_map", "known_person") + tuple(
    key for role in PART_ROLES for key in (f"owner_{role}", f"known_{role}")
)


def _component_and_hole_counts(mask: np.ndarray, connectivity: int) -> tuple[int, int]:
    if connectivity not in {4, 8}:
        raise ValueError("connectivity must be 4 or 8")
    binary = np.ascontiguousarray(mask.astype(np.uint8))
    components = int(cv2.connectedComponents(binary, connectivity=connectivity)[0] - 1)
    background = np.pad(1 - binary, 1, mode="constant", constant_values=1)
    # Use complementary digital adjacency so a diagonal contact cannot make
    # both foreground and background topologically connected at once.
    background_connectivity = 8 if connectivity == 4 else 4
    count, labels = cv2.connectedComponents(
        np.ascontiguousarray(background), connectivity=background_connectivity,
    )
    border_labels = np.unique(np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1])))
    holes = sum(1 for label in range(1, count) if label not in border_labels)
    return components, int(holes)


def _assert_acyclic(edge_index: np.ndarray, entity_count: int) -> None:
    adjacency = [[] for _ in range(entity_count)]
    indegree = [0] * entity_count
    for raw_front, raw_back in edge_index:
        front, back = int(raw_front) - 1, int(raw_back) - 1
        if front < 0 or back < 0 or front >= entity_count or back >= entity_count or front == back:
            raise IntakeError("occlusion edge references an invalid entity")
        adjacency[front].append(back)
        indegree[back] += 1
    ready = [node for node, degree in enumerate(indegree) if degree == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for target in adjacency[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if visited != entity_count:
        raise IntakeError("occlusion relation graph contains a cycle")


def _load_split(split_manifest_path: str | Path) -> tuple[dict[str, Any], str]:
    path = Path(split_manifest_path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IntakeError("private split manifest cannot be read") from exc
    if not isinstance(doc, dict) or doc.get("schema") != "minimalizer/local-l02-person-group-split/v1":
        raise IntakeError("unsupported person-group split manifest")
    records = doc.get("records")
    if not isinstance(records, list):
        raise IntakeError("split manifest records are missing")
    if any(not isinstance(record, dict) for record in records):
        raise IntakeError("split manifest contains an invalid record")
    source_shas = [record.get("source_sha256") for record in records]
    if any(not isinstance(sha, str) or len(sha) != 64
           or any(char not in "0123456789abcdef" for char in sha) for sha in source_shas):
        raise IntakeError("split manifest contains an invalid source SHA")
    if len(set(source_shas)) != len(source_shas):
        raise IntakeError("split manifest contains duplicate source images")
    if any(record.get("split") not in {"train", "validation", "blind_test"} for record in records):
        raise IntakeError("split manifest contains an invalid split name")
    group_split: dict[str, str] = {}
    for record in records:
        group, split_name = record.get("subject_group_id"), record.get("split")
        if not isinstance(group, str) or not group:
            raise IntakeError("split manifest contains an invalid person group")
        previous = group_split.setdefault(group, split_name)
        if previous != split_name:
            raise IntakeError("person group leaks across split assignments")
    expected = {record["source_sha256"] for record in records
                if record.get("split") in {"train", "validation"}}
    if not expected:
        raise IntakeError("split manifest has no train/validation records")
    if any(record.get("split") == "blind_test" for record in records if isinstance(record, dict)):
        blind = {record.get("source_sha256") for record in records
                 if isinstance(record, dict) and record.get("split") == "blind_test"}
        if expected & blind:
            raise IntakeError("one source is assigned to train/validation and blind-test")
    return {"expected_train_validation_source_shas": expected}, hashlib.sha256(path.read_bytes()).hexdigest()


def audit_mask_bundle(mask_dir: str | Path, split_manifest_path: str | Path) -> dict[str, Any]:
    directory = Path(mask_dir)
    if not directory.is_dir():
        raise IntakeError("private mask directory does not exist")
    split, split_sha = _load_split(split_manifest_path)
    expected = split["expected_train_validation_source_shas"]
    files = sorted(directory.glob("mask-*.npz"))
    actual = {path.stem.removeprefix("mask-") for path in files}
    if actual != expected:
        raise IntakeError("mask files do not exactly match the train/validation split")

    aggregates = {role: {"components_4": 0, "components_8": 0, "holes_4": 0, "holes_8": 0,
                         "instances": 0} for role in ("person", *PART_ROLES)}
    topology_image_count = 0
    relation_complete_image_count = 0
    relation_edge_count = 0
    total_images = 0
    for path in files:
        sha = path.stem.removeprefix("mask-")
        try:
            with np.load(path, allow_pickle=False) as archive:
                missing = set(MASK_KEYS) - set(archive.files)
                if missing:
                    raise IntakeError("mask archive is missing required arrays")
                masks = {key: archive[key] for key in MASK_KEYS}
                meta = json.loads(str(archive["metadata_json"]))
                edges = archive["occlusion_relation_edge_index"]
                entity_roles = archive["occlusion_entity_role_codes"]
                complete_relations_value = int(archive["occlusion_relations_complete"])
                complete_relations = bool(complete_relations_value)
        except IntakeError:
            raise
        except Exception as exc:
            raise IntakeError("mask archive cannot be decoded") from exc

        if meta.get("source_sha256") != sha:
            raise IntakeError("mask filename and embedded source SHA disagree")
        if meta.get("schema") != "minimalizer/local-l02-six-cap-raster/v1":
            raise IntakeError("unsupported raster metadata schema")
        alpha = masks["source_alpha"].astype(bool)
        shape = alpha.shape
        if len(shape) != 2 or any(array.shape != shape for array in masks.values()):
            raise IntakeError("mask arrays have inconsistent dimensions")
        if any(np.any((array != 0) & (array != 1)) for key, array in masks.items()
               if key.startswith("owner_") or key.startswith("known_") or key == "source_alpha"):
            raise IntakeError("binary mask contains non-binary values")
        if int(masks["source_alpha"].max()) > 1:
            raise IntakeError("source alpha is not binary")

        person_map = masks["person_instance_map"]
        object_map = masks["object_instance_map"]
        if not np.issubdtype(person_map.dtype, np.integer) or not np.issubdtype(object_map.dtype, np.integer):
            raise IntakeError("instance maps must contain integer codes")
        if np.any((person_map > 0) & ~alpha) or np.any((object_map > 0) & ~alpha):
            raise IntakeError("instance map owns pixels outside source alpha")
        if np.any((masks["known_person"] > 0) & ~alpha):
            raise IntakeError("known person pixels extend outside source alpha")
        person_known = masks["known_person"].astype(bool)
        person_foreground = person_map > 0
        if np.any(person_foreground & ~person_known):
            raise IntakeError("person instance positive is marked unknown")

        owners = [masks[f"owner_{role}"].astype(bool) for role in PART_ROLES]
        known_masks = [masks[f"known_{role}"].astype(bool) for role in PART_ROLES]
        complete_for = meta.get("complete_for")
        if not isinstance(complete_for, list) or any(role not in ALL_ROLES for role in complete_for):
            raise IntakeError("complete_for metadata is invalid")
        for role, known in zip(PART_ROLES, known_masks):
            expected_known = alpha if role in complete_for else masks[f"owner_{role}"].astype(bool)
            if not np.array_equal(known, expected_known):
                raise IntakeError("known mask violates the unknown-preservation policy")
        expected_person_known = alpha if "person" in complete_for else person_foreground
        if not np.array_equal(person_known, expected_person_known):
            raise IntakeError("person known mask violates the unknown-preservation policy")
        if any(np.any(owner & ~alpha) for owner in owners):
            raise IntakeError("semantic owner extends outside source alpha")
        if any(np.any(owner & ~known) for owner, known in zip(owners, known_masks)):
            raise IntakeError("semantic owner positive is marked unknown")
        if np.any(sum(owner.astype(np.uint8) for owner in owners) > 1):
            raise IntakeError("semantic owner masks overlap")

        semantic_ids = meta.get("semantic_object_ids_in_instance_map_order")
        object_codes = set(np.unique(object_map).astype(int).tolist()) - {0}
        if (not isinstance(semantic_ids, list) or len(semantic_ids) != int(object_map.max())
                or any(not isinstance(value, str) or not value for value in semantic_ids)
                or len(set(semantic_ids)) != len(semantic_ids)
                or object_codes != set(range(1, len(semantic_ids) + 1))):
            raise IntakeError("object instance map and metadata index disagree")
        person_ids = meta.get("person_ids_in_instance_map_order")
        person_codes = set(np.unique(person_map).astype(int).tolist()) - {0}
        if (not isinstance(person_ids, list) or len(person_ids) != int(person_map.max())
                or any(not isinstance(value, str) or not value for value in person_ids)
                or len(set(person_ids)) != len(person_ids)
                or person_codes != set(range(1, len(person_ids) + 1))):
            raise IntakeError("person instance map and metadata index disagree")
        entity_ids = meta.get("occlusion_entity_ids_in_edge_index_order")
        entity_role_names = meta.get("occlusion_entity_roles_in_edge_index_order")
        role_codebook = meta.get("object_role_codebook")
        if (not isinstance(entity_ids, list) or len(entity_ids) != len(entity_roles)
                or any(not isinstance(value, str) or not value for value in entity_ids)
                or not isinstance(entity_role_names, list) or len(entity_role_names) != len(entity_ids)
                or not isinstance(role_codebook, dict)):
            raise IntakeError("occlusion entity map and metadata index disagree")
        if len(set(entity_ids)) != len(entity_ids):
            raise IntakeError("duplicate occlusion entity IDs")
        expected_role_codes = {role: code for code, role in enumerate(ALL_ROLES, start=1)}
        if role_codebook != expected_role_codes:
            raise IntakeError("occlusion role codebook is inconsistent")
        if any(role not in ALL_ROLES for role in entity_role_names):
            raise IntakeError("occlusion entity has an unknown semantic role")
        if not np.array_equal(entity_roles, np.asarray([expected_role_codes[role] for role in entity_role_names], dtype=np.uint8)):
            raise IntakeError("occlusion entity role codes disagree with metadata")
        if edges.ndim != 2 or edges.shape[1:] != (2,) or not np.issubdtype(edges.dtype, np.integer):
            raise IntakeError("occlusion edge index has an invalid shape or type")
        if complete_relations_value not in {0, 1}:
            raise IntakeError("occlusion completeness flag is not binary")
        if len(entity_ids) != len(set(entity_ids)):
            raise IntakeError("duplicate occlusion entity IDs")
        _assert_acyclic(edges, len(entity_ids))
        relation_edge_count += int(len(edges))
        relation_complete_image_count += int(complete_relations)

        role_by_id = dict(zip(entity_ids, entity_role_names))
        for role_index, role in enumerate(PART_ROLES):
            expected_object = np.zeros(shape, dtype=bool)
            for code, object_id in enumerate(semantic_ids, start=1):
                if role_by_id.get(object_id) == role:
                    expected_object |= object_map == code
            if not np.array_equal(expected_object, masks[f"owner_{role}"].astype(bool)):
                raise IntakeError("semantic object instances do not reconstruct their exclusive owner mask")
            components4, holes4 = _component_and_hole_counts(masks[f"owner_{role}"], 4)
            components8, holes8 = _component_and_hole_counts(masks[f"owner_{role}"], 8)
            aggregates[role]["components_4"] += components4
            aggregates[role]["components_8"] += components8
            aggregates[role]["holes_4"] += holes4
            aggregates[role]["holes_8"] += holes8
            aggregates[role]["instances"] += len({object_id for object_id in semantic_ids
                                                  if role_by_id.get(object_id) == role})

        components4, holes4 = _component_and_hole_counts(person_foreground, 4)
        components8, holes8 = _component_and_hole_counts(person_foreground, 8)
        aggregates["person"]["components_4"] += components4
        aggregates["person"]["components_8"] += components8
        aggregates["person"]["holes_4"] += holes4
        aggregates["person"]["holes_8"] += holes8
        aggregates["person"]["instances"] += len(person_ids)
        topology_image_count += 1
        total_images += 1

    return {
        "schema": "minimalizer/local-l02-owner-mask-structure-audit/v1",
        "split_manifest_sha256": split_sha,
        "train_validation_image_count": total_images,
        "topology_image_count": topology_image_count,
        "owner_topology_4_8_connectivity_and_holes": aggregates,
        "occlusion_relation_edge_count": relation_edge_count,
        "images_with_complete_occlusion_review": relation_complete_image_count,
        "blind_test_masks_in_scope": False,
        "private_paths_or_instance_ids_emitted": False,
        "structural_audit_pass": True,
        "semantic_quality_approved": False,
        "observer_trained": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="非公開train/validation maskのsource-free構造監査")
    parser.add_argument("mask_dir", help="train/validation rasterizer出力フォルダー")
    parser.add_argument("split_manifest", help="非公開人物群split manifest")
    args = parser.parse_args()
    print(json.dumps(audit_mask_bundle(args.mask_dir, args.split_manifest), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
