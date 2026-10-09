"""SA10.60B C01: signed Phase04-to-Stage8 background-owner leakage diagnosis.

Research only. Never changes signed input, Phase04 authority, upstream semantics,
Stage8 ring budget, deployed SVG or production. RGB edge flooding is a *limited*
observation, not a semantic truth oracle. A separately versioned mask candidate
is not approved unless independently reviewed; it is not automatically used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

GC_SHA = {
    "GC001_source.png": "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
    "gc001_right.png": "4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91",
    "gc001_left.png": "49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f",
    "gc001_face.png": "b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f",
    "gc001_structure_guarded.svg": "bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939",
}
RADEN_SHA = {
    "Raden_source.png": "d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",
    "left.png": "6872bd01fb350b5ce2b5ec09b44feaa2c46cc442aa327cccc0e8681db33b404e",
    "right.png": "79829023fd293e16a619dbc7b84736ca3d2ac172ac442c04d35bc1a3eae13025",
    "face.png": "a192ef05aa3ae2cc42e249cb311349d82dd5e4115c1aa438c7a3205ba0d4ec2f",
}
STAGE8_SHA = "7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08"
EXPECTED_STAGE8_XOR = {"right_arm": 24, "left_arm": 5, "face": 0}
ROLES = ("right_arm", "left_arm", "face")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed_check(folder: Path, expected: dict[str, str]) -> None:
    for name, sha in expected.items():
        p = folder / name
        if not p.is_file() or digest(p) != sha:
            raise ValueError("SIGNED_SOURCE_CHANGED_OR_MISSING:" + name)


def mask_at(folder: Path, name: str) -> np.ndarray:
    a = np.asarray(Image.open(folder / name).convert("L"))
    if a.shape != (340, 340) or not np.isin(a, [0, 255]).all():
        raise ValueError("SIGNED_STAGE04_MASK_NOT_BINARY")
    return a > 0


def source_rgb(folder: Path, name: str) -> tuple[np.ndarray, np.ndarray]:
    rgba = np.asarray(Image.open(folder / name).convert("RGBA"))
    if rgba.shape != (340, 340, 4):
        raise ValueError("WRONG_SOURCE_CANVAS")
    return rgba[..., :3], rgba[..., 3]


def source_connected_background(photo: np.ndarray, alpha: np.ndarray) -> tuple[np.ndarray, dict]:
    """Dominant RGB on an opaque source edge, flood only 4-connected exact matches.

    No fuzzy threshold, no face/arm inference, no recoloring. Under ambiguous
    border evidence fail instead of guessing an owner.
    """
    if photo.shape != (340, 340, 3) or alpha.shape != (340, 340):
        raise ValueError("BAD_RGB_CANVAS")
    edge_color = np.concatenate([photo[0], photo[-1], photo[:, 0], photo[:, -1]])
    edge_alpha = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    opaque = edge_color[edge_alpha == 255]
    if not len(opaque):
        raise ValueError("NO_OPAQUE_BORDER_RGB_ANCHOR")
    colors, counts = np.unique(opaque, axis=0, return_counts=True)
    best = int(np.argmax(counts))
    if int(counts[best]) < 200:
        raise ValueError("BACKGROUND_RGB_ANCHOR_AMBIGUOUS")
    rgb = colors[best]
    exact = np.all(photo == rgb, axis=2)
    _, labels, _, _ = cv2.connectedComponentsWithStats(exact.astype(np.uint8), 4)
    on_border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    connected = np.isin(labels, np.unique(on_border)[1:]) if 0 in on_border else np.isin(labels, np.unique(on_border))
    connected &= labels != 0
    return connected, {"dominant_border_exact_rgb": list(map(int, rgb)),
                       "opaque_border_anchor_pixels": int(counts[best]),
                       "source_border_connected_background_pixels": int(connected.sum()),
                       "opaque_connected_background_pixels": int(np.count_nonzero(connected & (alpha == 255)))}


def ring_raster(records: list[dict], role: str) -> np.ndarray:
    found = [p for p in records if p.get("source_mask_owner") == role]
    if len(found) != 1:
        raise ValueError("STAGE8_ROLE_NOT_UNIQUE:" + role)
    rings = found[0].get("parameters", {}).get("rings", [])
    if not rings:
        raise ValueError("STAGE8_RINGS_NOT_FOUND")
    contours = []
    for ring in sorted(rings, key=lambda r: int(r["depth"])):
        depth = int(ring["depth"])
        if ring.get("role") != ("fill" if depth % 2 == 0 else "hole"):
            raise ValueError("STAGE8_RING_POLARITY_MISMATCH")
        coords = np.asarray(ring["points"], dtype=np.float64)
        if coords.ndim != 2 or coords.shape[1] != 2 or len(coords) < 1 or not np.isfinite(coords).all():
            raise ValueError("INVALID_STAGE8_RINGS")
        contours.append(np.rint(coords).astype(np.int32).reshape(-1, 1, 2))
    canvas = np.zeros((340, 340), np.uint8)
    cv2.drawContours(canvas, contours, -1, 255, thickness=cv2.FILLED, lineType=cv2.LINE_8)
    return canvas > 0


def component_stats(mask: np.ndarray) -> dict:
    labels_count, _, table, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    sizes = sorted((int(x) for x in table[1:, cv2.CC_STAT_AREA]), reverse=True)
    return {"components": int(labels_count - 1), "top_areas": sizes[:5], "total": int(mask.sum())}


def diagnose(photo: np.ndarray, alpha: np.ndarray, masks: dict, stage8: dict | None) -> tuple[dict, np.ndarray, np.ndarray]:
    connected, bg = source_connected_background(photo, alpha)
    overlaps = {role: int(np.count_nonzero(mask & connected)) for role, mask in masks.items()}
    result = {"source_observer": bg, "phase04_mask_pixels": {k: int(m.sum()) for k, m in masks.items()},
              "source_background_connected_intersection": overlaps,
        "fully_opaque_source_background_intersection": {role: int(np.count_nonzero(mask & connected & (alpha == 255))) for role,mask in masks.items()}}
    if stage8 is not None:
        records = stage8.get("primitives_back_to_front", [])
        s8 = {}
        for role in ROLES:
            observed = ring_raster(records, role)
            signed = masks[role]
            s8[role] = {"mask_pixels": int(observed.sum()),
                        "xor_pixels_vs_signed_stage04": int(np.count_nonzero(observed ^ signed)),
                        "source_background_connected_intersection": int(np.count_nonzero(observed & connected))}
            if s8[role]["xor_pixels_vs_signed_stage04"] != EXPECTED_STAGE8_XOR[role]:
                raise ValueError("STAGE8_SIGNED_SOURCE_MASK_LINEAGE_REGRESSED")
        result["stage8"] = s8
    # Do not amend the authority. An isolated candidate is a diagnostic and may
    # fragment into disconnected parts: this is evidence, not safe art.
    candidate = masks["right_arm"] & ~(connected & (alpha == 255))
    result["right_arm_candidate"] = {
        "method": "subtract-only-fully-opaque-pixels-from-4-connected-exact-border-RGB",
        "partially_transparent_exact_rgb_overlap_not_auto_removed": int(np.count_nonzero(masks["right_arm"] & connected & (alpha != 255))),
        "removed_from_signed_original": int(np.count_nonzero(masks["right_arm"] & ~candidate)),
        "added_to_signed_original": int(np.count_nonzero(candidate & ~masks["right_arm"])),
        "source_mask_connected_components_before": component_stats(masks["right_arm"]),
        "candidate_components_after": component_stats(candidate),
        "signed_face_and_left_arm_unchanged": True,
        "review": "UNAPPROVED_RESEARCH_ONLY",
    }
    return result, connected, candidate


def overlay(photo: np.ndarray, mask: np.ndarray, color: tuple[int, int, int]) -> Image.Image:
    a = photo.astype(np.float32).copy()
    a[mask] = .55 * a[mask] + .45 * np.asarray(color, dtype=np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def render_board(photo, signed, stage8, candidate, source_bg, out: Path):
    panels = [
        (Image.fromarray(photo, "RGB"), "SIGNED ORIGINAL"),
        (overlay(photo, signed, (255, 40, 175)), "SIGNED PHASE04 RIGHT ARM"),
        (overlay(photo, stage8, (40, 135, 250)), "STAGE08 INHERITED OWNER"),
        (overlay(photo, candidate, (75, 210, 110)), "CANDIDATE (NOT APPROVED)"),
    ]
    board = Image.new("RGB", (340 * 4, 382), (248, 247, 244)); draw = ImageDraw.Draw(board)
    for i, (image, title) in enumerate(panels):
        board.paste(image, (i * 340, 40)); draw.text((i * 340 + 8, 12), title, fill=(12, 12, 12))
    board.save(out / "gc001_phase04_stage8_diagnostic2_private.png")
    # All traced pixel locations and actual source imagery stay private.
    Image.fromarray((candidate.astype(np.uint8) * 255), "L").save(out / "gc001_right_arm_phase04_candidate_v1_PRIVATE.png")
    Image.fromarray((source_bg.astype(np.uint8) * 255), "L").save(out / "gc001_source_connected_bg_PRIVATE.png")


def run(gc_folder: Path, raden_folder: Path, stage8_file: Path, out: Path) -> dict:
    gc_folder, raden_folder, stage8_file, out = [Path(p).resolve() for p in (gc_folder, raden_folder, stage8_file, out)]
    for source in [gc_folder, raden_folder]:
        if out == source or source in out.parents or out in source.parents:
            raise ValueError("SIGNED_INPUT_OUTPUT_NOT_SEPARATE")
    if out == stage8_file or out in stage8_file.parents:
        raise ValueError("SIGNED_STAGE8_INPUT_OUTPUT_NOT_SEPARATE")
    if out.exists() and any(out.iterdir()):
        raise ValueError("OUTPUT_NOT_EMPTY")
    signed_check(gc_folder, GC_SHA)
    signed_check(raden_folder, RADEN_SHA)
    if not stage8_file.is_file() or digest(stage8_file) != STAGE8_SHA:
        raise ValueError("SIGNED_STAGE8_SHA_CHANGED")
    stage8 = json.loads(stage8_file.read_text(encoding="utf-8"))
    if stage8.get("original_source_sha256") != GC_SHA["GC001_source.png"] or stage8.get("production_authorized") is not False:
        raise ValueError("SIGNED_STAGE8_SOURCE_OR_STATUS_CHANGED")
    gphoto, galpha = source_rgb(gc_folder, "GC001_source.png")
    gmask = {name: mask_at(gc_folder, "gc001_" + {"right_arm":"right","left_arm":"left","face":"face"}[name] + ".png") for name in ROLES}
    g, gbg, gcandidate = diagnose(gphoto, galpha, gmask, stage8)
    rphoto, ralpha = source_rgb(raden_folder, "Raden_source.png")
    rmasks = {name: mask_at(raden_folder, {"right_arm":"right","left_arm":"left","face":"face"}[name] + ".png") for name in ROLES}
    raden, _, _ = diagnose(rphoto, ralpha, rmasks, None)
    if (g["source_background_connected_intersection"] != {"right_arm":533,"left_arm":0,"face":0}
        or g["stage8"]["right_arm"]["source_background_connected_intersection"] != 533
        or g["source_observer"]["source_border_connected_background_pixels"] != 35514):
        raise ValueError("FROZEN_GC001_DIAGNOSTIC_DRIFT")
    if raden["source_background_connected_intersection"] != {"right_arm":3,"left_arm":7,"face":0}:
        raise ValueError("INDEPENDENT_RADEN_CONTROL_DRIFT")
    out.mkdir(parents=True, exist_ok=True)
    render_board(gphoto, gmask["right_arm"], ring_raster(stage8["primitives_back_to_front"], "right_arm"), gcandidate, gbg, out)
    report = {"stage":"SA10.60B-C01", "schema":"signed-phase04-stage8-first-bad-source-owner-audit-v1",
              "first_demonstrable_bad_stage":"PHASE04_SIGNED_RIGHT_ARM_MASK",
              "origin_prior_to_phase04":"NOT_ESTABLISHED", "phase05_phase06_causal_path":"NOT_INDIVIDUALLY_REPLAYED",
              "source_background_color_semantic_authority":"CONSISTENT_SOURCE_CONNECTED_EXACT_RGB_ONLY_NOT_COMPLETE_SEGMENTATION",
              "gc001":g,"raden_independent_control":raden,
              "gc001_stage8_signature":STAGE8_SHA,
              "signed_originals_and_stage04_masks_mutated":False,
              "signed_gc001_face_and_left_arm_mask_sha_unchanged":True,
              "right_arm_new_versioned_candidate_isolated":True,
              "candidate_promotion_authorized":False,
              "golden_human_review":"PENDING", "historic_stage8_ring_gate":"HOLD",
              "phase15":"NOT_RUN", "production":"UNCHANGED",
              "evidence_type":"PRIVATE_ORIGINALS_AND_MASKS_CHECKED_BY_SHA",
              "next":"C02: independently verify part labels and topology of proposed changes before any SVG integration; still no Golden or Stage8 approval"}
    report["private_artifact_sha256"] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out / "sa1060b_c01_private_metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    return report


def sanitized(report: dict) -> dict:
    """Strict coordinate-free allowlist for GitHub publishing, never a raw private report."""
    keep = ("stage","schema","first_demonstrable_bad_stage","origin_prior_to_phase04","phase05_phase06_causal_path",
            "source_background_color_semantic_authority","candidate_promotion_authorized", "golden_human_review",
            "historic_stage8_ring_gate","phase15","production","next")
    allow = {k: report[k] for k in keep}
    allow["case_metrics"] = {
        "GC001":{"phase04_mask_pixels":report["gc001"]["phase04_mask_pixels"],
                 "source_background_connected_intersection":report["gc001"]["source_background_connected_intersection"],
                 "stage8":report["gc001"]["stage8"],
                 "candidate_removed_pixels":report["gc001"]["right_arm_candidate"]["removed_from_signed_original"],
                 "candidate_connected_components_before":report["gc001"]["right_arm_candidate"]["source_mask_connected_components_before"]["components"],
                 "candidate_connected_components_after":report["gc001"]["right_arm_candidate"]["candidate_components_after"]["components"]},
        "Raden":{"phase04_mask_pixels":report["raden_independent_control"]["phase04_mask_pixels"],
                 "source_background_connected_intersection":report["raden_independent_control"]["source_background_connected_intersection"]}
    }
    return allow


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("gc","raden","stage8","out"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    r=run(args.gc,args.raden,args.stage8,args.out)
    public=sanitized(r)
    (args.out / "sa1060b_c01_coordinate_free_public.json").write_text(json.dumps(public,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"stage":r["stage"],"first_bad_stage":r["first_demonstrable_bad_stage"],
                      "gc001":r["gc001"]["source_background_connected_intersection"],
                      "raden":r["raden_independent_control"]["source_background_connected_intersection"],
                      "candidate_gate":r["candidate_promotion_authorized"]},ensure_ascii=False))

if __name__ == "__main__":
    main()
