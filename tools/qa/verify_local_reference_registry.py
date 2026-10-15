#!/usr/bin/env python3
"""Source-free, read-only MinimalizerLocal L01 provenance/Golden registry gate.

This tool never edits signed assets and never promotes a model's prediction or
human review. Optional private inputs are verified only locally, not uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PARTS = frozenset(("accessory_or_held_object", "face", "hair", "head", "left_arm",
                   "lower_body", "major_clothing", "neck", "right_arm", "torso", "unknown"))
CRITERIA = ("faceless_and_no_skin_plate", "hair_and_head", "clothing_and_accessories",
            "both_arms_and_pose", "silhouette_and_identity", "source_only_no_generated_detail")


class AuthorityError(ValueError):
    pass


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def git_blob_sha(blob: bytes) -> str:
    return hashlib.sha1(f"blob {len(blob)}\0".encode("ascii") + blob).hexdigest()


def load_registry(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != "minimalizer-local-golden-input-registry/v1":
        raise AuthorityError("wrong registry schema")
    if doc.get("purpose") != "evaluation_preparation_only":
        raise AuthorityError("registry cannot certify Golden or release")
    cases = doc.get("signed_cases")
    if not isinstance(cases, list) or len(cases) != 3 or [c.get("id") for c in cases] != ["H04", "GC001", "Raden"]:
        raise AuthorityError("signed-case authority list mismatch")
    if len({c["source_sha256"] for c in cases}) != 3 or any(not HEX64.fullmatch(c["source_sha256"]) for c in cases):
        raise AuthorityError("invalid/duplicate signed original SHA")
    if any(c.get("human_golden") != "HOLD" for c in cases):
        raise AuthorityError("signed human Golden authority must stay HOLD")
    if any(c.get("actual_signed_original_rehashed_this_run") is not False for c in cases):
        raise AuthorityError("unverified original cannot be marked byte verified")
    h04 = cases[0]
    if not HEX64.fullmatch(h04.get("phase4_stage_sha256", "")) or h04.get("part_mask_count") != 11:
        raise AuthorityError("H04 original Stage4/mask authority not pinned")
    if doc.get("golden_criteria") != list(CRITERIA):
        raise AuthorityError("Golden criteria changed")
    manual = doc.get("manual_reference", {})
    if manual.get("id") != "KYOKO_MANUAL_REFERENCE_V1" or not HEX64.fullmatch(manual.get("underlay_sha256", "")):
        raise AuthorityError("manual reference identity missing")
    if manual["underlay_sha256"] == cases[1]["source_sha256"] or manual.get("pixel_aligned_to_signed_gc001") is not False:
        raise AuthorityError("manual underlay falsely aligned to signed GC001")
    if doc.get("local_release_authorized") is not False or doc.get("production_changed") is not False:
        raise AuthorityError("registry not a release approval")
    expected = doc.get("approved78", {})
    if expected.get("count") != 78 or expected.get("approved18_prefix_count") != 18 or not HEX40.fullmatch(expected.get("git_blob_sha", "")):
        raise AuthorityError("Approved78 manifest lock missing")
    return doc


def verify_approved78(registry: dict, manifest: Path) -> dict:
    data = manifest.read_bytes()
    if git_blob_sha(data) != registry["approved78"]["git_blob_sha"]:
        raise AuthorityError("Approved78 manifest content differs from pinned Git blob")
    doc = json.loads(data)
    items = doc.get("references")
    if doc.get("corpus_id") != "Approved-78" or not isinstance(items, list) or len(items) != 78:
        raise AuthorityError("Approved78 not complete")
    if [x.get("index") for x in items] != list(range(1, 79)):
        raise AuthorityError("Approved78 index gap/duplicate")
    filenames = [x.get("reference_filename") for x in items]
    if len(set(filenames)) != 78 or not all(isinstance(x, str) and x.endswith(".png") for x in filenames):
        raise AuthorityError("Approved78 filename invalid/duplicated")
    if not all(x.get("scene_artifact") and x.get("candidate_artifact") for x in items):
        raise AuthorityError("Approved78 evaluation pointers missing")
    return {"approved78_entries": 78, "approved18_prefix_entries": 18,
            "manifest_git_blob_sha": git_blob_sha(data), "manifest_structure_pass": True,
            "original_images_byte_verified": False, "human_golden": "HOLD"}


def _zip_entries(z: zipfile.ZipFile) -> dict[str, bytes]:
    result = {}
    for member in z.infolist():
        key = member.filename.replace("\\", "/")
        if key in result:
            raise AuthorityError("duplicate canonical ZIP member")
        if key.startswith("/") or ".." in Path(key).parts:
            raise AuthorityError("unsafe ZIP member")
        result[key] = z.read(member)
    return result


def verify_h04_private(registry: dict, run122_zip: Path, run107_zip: Path) -> dict:
    h04 = registry["signed_cases"][0]
    if sha256(run122_zip.read_bytes()) != h04["run122_zip_sha256"]:
        raise AuthorityError("Run122 private archive SHA mismatch")
    if sha256(run107_zip.read_bytes()) != h04["run107_zip_sha256"]:
        raise AuthorityError("Run107 private archive SHA mismatch")
    with zipfile.ZipFile(run122_zip) as f, zipfile.ZipFile(run107_zip) as g:
        left = _zip_entries(f)
        right = _zip_entries(g)
    if left["phase4_stage.json"] != right["phase_04/stage.json"]:
        raise AuthorityError("phase4 stage archive mismatch")
    if sha256(left["phase4_stage.json"]) != h04["phase4_stage_sha256"]:
        raise AuthorityError("signed phase4 stage digest mismatch")
    expected = {f"part_masks/{p}.png" for p in PARTS}
    actual = {name for name in left if name.startswith("part_masks/")}
    if actual != expected:
        raise AuthorityError("part mask set missing, extra, or misspelled")
    for name in sorted(expected):
        if right.get("phase_04/" + name) != left[name]:
            raise AuthorityError("part-mask byte mismatch: " + name)
    for x,y in (("05_structure_graph.json", "phase_05/05_structure_graph.json"),
                ("phase5_stage.json", "phase_05/stage.json")):
        if left[x] != right[y]:
            raise AuthorityError("phase5 diagnostic archive mismatch: " + x)
    return {"h04_phase4_sha256": sha256(left["phase4_stage.json"]),
            "signed_part_masks_byte_identical": len(expected),
            "phase5_original_diagnostic_identical": True,
            "h04_original_image_bytes_verified": False,
            "semantic_quality_pass": False,
            "human_golden": "HOLD"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--approved78", type=Path)
    parser.add_argument("--run122-private", type=Path)
    parser.add_argument("--run107-private", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if bool(args.run122_private) != bool(args.run107_private):
        parser.error("Both private archives must be supplied together")
    try:
        reg = load_registry(args.registry)
        report = {"schema": "minimalizer-local-l01-validator-report/v1",
                  "registry_pass": True, "human_golden": "HOLD", "release_authorized": False}
        if args.approved78:
            report["approved78"] = verify_approved78(reg, args.approved78)
        if args.run122_private:
            report["h04_private"] = verify_h04_private(reg, args.run122_private, args.run107_private)
        data = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except (AuthorityError, ValueError, KeyError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"FAIL_CLOSED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
