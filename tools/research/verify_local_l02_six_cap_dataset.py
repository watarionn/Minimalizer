"""Source-free intake audit for private L02 six-capability annotations.

The input images and polygon vertices stay in the caller's private dataset
directory. The returned report contains aggregate counts and one opaque
fingerprint; it never emits paths, person IDs, annotator IDs, or coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

SCHEMA = "minimalizer/local-l02-six-cap-annotation/v1"
ROLES = {
    "person", "outerwear", "underlayer", "sleeve_left", "sleeve_right",
    "arm_left", "arm_right",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
# These are evaluation-only sources. They must never enter observer training.
EVALUATION_SOURCE_SHA256 = {
    "7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3",
    "c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8",
    "759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e",
}


class IntakeError(ValueError):
    """Raised when private annotation input is unsafe or inconsistent."""


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _valid_polygon(points: list[tuple[float, float]]) -> bool:
    if len(points) < 3 or len(set(points)) != len(points):
        return False
    area = sum(points[i][0] * points[(i + 1) % len(points)][1] -
               points[(i + 1) % len(points)][0] * points[i][1]
               for i in range(len(points)))
    if abs(area) < 0.5:
        return False
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        for j in range(i + 1, len(points)):
            if j == i or j == (i + 1) % len(points) or (j + 1) % len(points) == i:
                continue
            c, d = points[j], points[(j + 1) % len(points)]
            o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
            o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
            if o1 * o2 < 0 and o3 * o4 < 0:
                return False
    return True


def _validate_document(doc: Any, source_sha: str, width: int, height: int) -> tuple[str, Counter[str], int]:
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise IntakeError("unsupported annotation schema")
    image = doc.get("image")
    if not isinstance(image, dict) or image.get("source_sha256") != source_sha:
        raise IntakeError("annotation is not bound to these source bytes")
    if image.get("width") != width or image.get("height") != height or image.get("coordinate_space") != "source_image_pixels":
        raise IntakeError("source dimensions or coordinate space mismatch")
    group = doc.get("subject_group_id")
    if not isinstance(group, str) or not group.strip() or len(group) > 160:
        raise IntakeError("missing or invalid subject group ID")
    regions, complete, relations = doc.get("regions"), doc.get("complete_for"), doc.get("occlusion_relations")
    if not isinstance(regions, list) or not isinstance(complete, list) or not isinstance(relations, list):
        raise IntakeError("regions, complete_for, and occlusion_relations must be arrays")
    if not isinstance(doc.get("occlusion_relations_complete"), bool):
        raise IntakeError("occlusion completeness must be explicit")
    if any(role not in ROLES for role in complete):
        raise IntakeError("unknown role in complete_for")
    if len(regions) > 20000 or len(relations) > 50000:
        raise IntakeError("annotation exceeds intake limits")

    ids: set[str] = set()
    object_roles: dict[str, tuple[str, str]] = {}
    role_counts: Counter[str] = Counter()
    vertex_count = 0
    for region in regions:
        if not isinstance(region, dict):
            raise IntakeError("region entry must be an object")
        rid, oid, pid, role, raw_points = (region.get(k) for k in ("region_id", "object_id", "person_id", "role", "points"))
        if not all(isinstance(v, str) and v.strip() for v in (rid, oid, pid)) or rid in ids:
            raise IntakeError("blank or duplicate region/object/person ID")
        if role not in ROLES or not isinstance(raw_points, list) or len(raw_points) < 3 or len(raw_points) > 20000:
            raise IntakeError("invalid role or polygon")
        points: list[tuple[float, float]] = []
        for point in raw_points:
            if not isinstance(point, dict):
                raise IntakeError("polygon point must be an object")
            x, y = point.get("x"), point.get("y")
            if (not isinstance(x, (int, float)) or isinstance(x, bool) or
                    not isinstance(y, (int, float)) or isinstance(y, bool) or
                    not math.isfinite(x) or not math.isfinite(y) or
                    x < 0 or y < 0 or x > width or y > height):
                raise IntakeError("non-finite or out-of-bounds polygon coordinate")
            points.append((float(x), float(y)))
        if not _valid_polygon(points):
            raise IntakeError("degenerate or self-intersecting polygon")
        owner = (pid, role)
        if oid in object_roles and object_roles[oid] != owner:
            raise IntakeError("one object ID refers to multiple people or roles")
        object_roles[oid] = owner
        ids.add(rid)
        role_counts[role] += 1
        vertex_count += len(points)

    object_ids = {region["object_id"] for region in regions}
    edges: set[tuple[str, str]] = set()
    for edge in relations:
        if not isinstance(edge, dict):
            raise IntakeError("occlusion relation must be an object")
        front, back = edge.get("occluder_id"), edge.get("occluded_id")
        if edge.get("relation") != "occludes" or front not in object_ids or back not in object_ids or front == back:
            raise IntakeError("invalid occlusion edge or missing object reference")
        pair = (front, back)
        if pair in edges:
            raise IntakeError("duplicate occlusion edge")
        edges.add(pair)
    return group, role_counts, vertex_count


def audit_dataset(dataset_dir: str | Path) -> dict[str, Any]:
    root = Path(dataset_dir)
    if not root.is_dir():
        raise IntakeError("private dataset directory does not exist")
    images = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    annotations = sorted(p for p in root.rglob("*.json") if p.is_file())
    if not images or not annotations or len(images) != len(annotations):
        raise IntakeError("dataset must contain one annotation JSON for each source image")

    image_by_sha: dict[str, tuple[Path, int, int]] = {}
    for path in images:
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha in EVALUATION_SOURCE_SHA256:
            raise IntakeError("evaluation source is forbidden in training intake")
        if sha in image_by_sha:
            raise IntakeError("duplicate source image bytes")
        try:
            with Image.open(path) as im:
                width, height = im.size
                im.verify()
        except Exception as exc:
            raise IntakeError("source image cannot be decoded") from exc
        if width < 8 or height < 8 or width * height > 100_000_000:
            raise IntakeError("unsupported source image dimensions")
        image_by_sha[sha] = (path, width, height)

    seen_sources: set[str] = set()
    groups: set[str] = set()
    role_counts: Counter[str] = Counter()
    total_regions = total_vertices = total_relations = fully_reviewed_relations = 0
    fully_reviewed_roles: Counter[str] = Counter()
    fingerprint_rows: list[bytes] = []
    for path in annotations:
        try:
            raw = path.read_bytes()
            doc = json.loads(raw)
        except Exception as exc:
            raise IntakeError("annotation JSON cannot be read") from exc
        source_sha = ((doc.get("image") or {}).get("source_sha256") if isinstance(doc, dict) else None)
        if source_sha not in image_by_sha or source_sha in seen_sources:
            raise IntakeError("annotation has no unique matching source image")
        _, width, height = image_by_sha[source_sha]
        group, counts, vertices = _validate_document(doc, source_sha, width, height)
        seen_sources.add(source_sha)
        groups.add(group)
        role_counts.update(counts)
        total_regions += len(doc["regions"])
        total_vertices += vertices
        total_relations += len(doc["occlusion_relations"])
        fully_reviewed_relations += int(doc["occlusion_relations_complete"])
        fully_reviewed_roles.update(doc["complete_for"])
        fingerprint_rows.append((source_sha + ":" + hashlib.sha256(raw).hexdigest()).encode("ascii"))
    if seen_sources != set(image_by_sha):
        raise IntakeError("one or more source images have no annotation")

    fingerprint = hashlib.sha256(b"\n".join(sorted(fingerprint_rows))).hexdigest()
    missing_positive_roles = sorted(role for role in ROLES if role_counts.get(role, 0) == 0)
    missing_full_review_roles = sorted(role for role in ROLES if fully_reviewed_roles.get(role, 0) == 0)
    person_group_splits_available = len(groups) >= 3
    occlusion_supervision_available = total_relations > 0 and fully_reviewed_relations > 0
    candidate_inputs_complete = (not missing_positive_roles and not missing_full_review_roles and
                                 person_group_splits_available and occlusion_supervision_available)
    return {
        "schema": "minimalizer/local-l02-six-cap-dataset-audit/v1",
        "dataset_fingerprint_sha256": fingerprint,
        "image_count": len(images),
        "subject_group_count": len(groups),
        "region_count": total_regions,
        "polygon_vertex_count": total_vertices,
        "region_counts_by_role": {role: role_counts.get(role, 0) for role in sorted(ROLES)},
        "roles_without_positive_regions": missing_positive_roles,
        "roles_without_full_image_review": missing_full_review_roles,
        "occlusion_edge_count": total_relations,
        "images_with_complete_occlusion_review": fully_reviewed_relations,
        "minimum_three_person_group_splits_available": person_group_splits_available,
        "pairwise_occlusion_supervision_available": occlusion_supervision_available,
        "minimum_cross_person_annotation_coverage_present": candidate_inputs_complete,
        "observer_trained": False,
        "evaluation_sources_included": 0,
        "source_paths_emitted": False,
        "person_ids_emitted": False,
        "polygon_coordinates_emitted": False,
        "unknown_policy": "unmarked pixels remain unknown; only complete_for permits class-specific known negatives",
        "training_approval": "NOT_GRANTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="非公開L02六能力データの入力を読み取り専用で監査します")
    parser.add_argument("dataset_dir", help="元画像と対応JSONを置いた非公開フォルダー")
    parser.add_argument("--output", type=Path, help="監査JSONの保存先（省略時は画面表示のみ）")
    args = parser.parse_args()
    report = audit_dataset(args.dataset_dir)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
