"""Create a private, deterministic person-group split for L02 training.

The split manifest contains source hashes and private group IDs. Keep it next to
the private dataset and never commit it to the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from rasterize_local_l02_six_cap_annotations import _assert_private_output
from verify_local_l02_six_cap_dataset import IntakeError, audit_dataset


def _allocate_group_counts(group_count: int) -> dict[str, int]:
    if group_count < 3:
        raise IntakeError("at least three distinct person groups are needed for train/validation/blind-test")
    names = ("train", "validation", "blind_test")
    weights = (0.70, 0.15, 0.15)
    counts = {name: 1 for name in names}
    remaining = group_count - len(names)
    quotas = [remaining * weight for weight in weights]
    floors = [int(quota) for quota in quotas]
    for name, count in zip(names, floors):
        counts[name] += count
    leftover = remaining - sum(floors)
    order = sorted(range(len(names)), key=lambda i: (-(quotas[i] - floors[i]), i))
    for index in order[:leftover]:
        counts[names[index]] += 1
    return counts


def build_split(dataset_dir: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(dataset_dir)
    audit = audit_dataset(root)
    image_by_sha: dict[str, Path] = {}
    for image_path in root.rglob("*"):
        if image_path.is_file() and image_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            image_by_sha[hashlib.sha256(image_path.read_bytes()).hexdigest()] = image_path

    records: list[dict[str, str]] = []
    for label_path in root.rglob("*.json"):
        document = json.loads(label_path.read_text(encoding="utf-8"))
        source_sha = document["image"]["source_sha256"]
        if source_sha not in image_by_sha:
            raise IntakeError("annotation source disappeared after intake audit")
        records.append({"source_sha256": source_sha, "subject_group_id": document["subject_group_id"]})

    group_ids = sorted({record["subject_group_id"] for record in records})
    counts = _allocate_group_counts(len(group_ids))
    ranked_groups = sorted(
        group_ids,
        key=lambda group: hashlib.sha256(b"minimalizer-local-l02-person-split/v1\0" + group.encode("utf-8")).hexdigest(),
    )
    assignments: dict[str, str] = {}
    offset = 0
    for split_name in ("train", "validation", "blind_test"):
        for group_id in ranked_groups[offset:offset + counts[split_name]]:
            assignments[group_id] = split_name
        offset += counts[split_name]

    manifest = {
        "schema": "minimalizer/local-l02-person-group-split/v1",
        "dataset_fingerprint_sha256": audit["dataset_fingerprint_sha256"],
        "algorithm": "stable-sha256-group-rank/largest-remainder-70-15-15/minimum-one-group-per-split",
        "group_assignments": assignments,
        "records": [
            {"source_sha256": record["source_sha256"],
             "subject_group_id": record["subject_group_id"],
             "split": assignments[record["subject_group_id"]]}
            for record in sorted(records, key=lambda item: item["source_sha256"])
        ],
        "blind_test_labels_must_remain_sealed_until_model_freeze": True,
        "evaluation_source_count": audit["evaluation_sources_included"],
    }
    summary = {
        "schema": "minimalizer/local-l02-person-group-split-readback/v1",
        "dataset_fingerprint_sha256": audit["dataset_fingerprint_sha256"],
        "split_manifest_sha256": hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "image_count": len(records),
        "person_group_count": len(group_ids),
        "image_counts_by_split": {
            split: sum(1 for record in records if assignments[record["subject_group_id"]] == split)
            for split in ("train", "validation", "blind_test")
        },
        "group_counts_by_split": counts,
        "group_leakage": False,
        "evaluation_sources_included": 0,
        "private_group_ids_or_source_paths_emitted": False,
        "blind_test_opened": False,
    }
    return manifest, summary


def write_split(dataset_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    dataset = Path(dataset_dir).resolve()
    output = Path(output_dir).resolve()
    try:
        output.relative_to(dataset)
    except ValueError:
        pass
    else:
        raise IntakeError("split manifest output must be outside the input dataset folder")
    _assert_private_output(output)
    manifest, summary = build_split(dataset)
    output.mkdir(parents=True, exist_ok=True)
    target = output / "person-group-split.private.json"
    temporary = output / ".person-group-split.private.json.tmp"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="人物グループ単位の非公開データ分割を固定します")
    parser.add_argument("dataset_dir", help="非公開の元画像と対応ラベルJSONのフォルダー")
    parser.add_argument("output_dir", help="分割manifestを保存するGit作業ツリー外のフォルダー")
    args = parser.parse_args()
    print(json.dumps(write_split(args.dataset_dir, args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
