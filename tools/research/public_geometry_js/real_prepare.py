"""Frozen real GC001/Raden geometry trial input preparation; no image generation.
Requires Pillow, numpy, cv2. Run with --root pointing to SA10.41 in private Drive.
Only verified originals and signed Stage04 face/arm masks are accepted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

SOURCE_HASHES = {
    "GC001": "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
    "Raden": "d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",
}
MASK_HASHES = {
    "GC001": {
        "face": "b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f",
        "left_arm": "49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f",
        "right_arm": "4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91",
    },
    "Raden": {
        "face": "a192ef05aa3ae2cc42e249cb311349d82dd5e4115c1aa438c7a3205ba0d4ec2f",
        "left_arm": "6872bd01fb350b5ce2b5ec09b44feaa2c46cc442aa327cccc0e8681db33b404e",
        "right_arm": "79829023fd293e16a619dbc7b84736ca3d2ac172ac442c04d35bc1a3eae13025",
    },
}
SIZE = (340, 340)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path, expected: str) -> None:
    if not path.is_file() or sha(path) != expected:
        raise ValueError(f"SHA256 mismatch or missing signed source: {path.name}")


def prepare(root: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    local = {"schema": "public-real-two-case-part-geometry-v1", "cases": {}, "source_trust": "frozen_sa1041_sha"}
    verified = {}
    for case in ("GC001", "Raden"):
        folder = out / case
        folder.mkdir(exist_ok=True)
        src_file = root / "original_inputs" / f"{case}_source.png"
        verify(src_file, SOURCE_HASHES[case])
        source = Image.open(src_file).convert("RGB")
        if source.size != SIZE:
            raise ValueError("signed image must have exact dimensions 340x340")
        source_bytes = source.tobytes()
        rgb_file = folder / "source_rgb.bin"
        rgb_file.write_bytes(source_bytes)
        roles = {}
        verified_case = {"source_sha256": SOURCE_HASHES[case], "masks": {}}
        for role in ("face", "left_arm", "right_arm"):
            mask_file = root / case / f"signed_{role}_stage04_mask.png"
            verify(mask_file, MASK_HASHES[case][role])
            signed_img = Image.open(mask_file).convert("L")
            if signed_img.size != SIZE:
                raise ValueError(f"misaligned signed mask: {case}/{role}")
            signed_mask = np.asarray(signed_img, dtype=np.uint8) >= 127
            if int(signed_mask.sum()) == 0:
                raise ValueError("empty signed role mask")
            signed_array = signed_mask.astype(np.uint8)
            dst_mask = folder / f"{role}_signed.bin"
            dst_mask.write_bytes(signed_array.tobytes())
            number, labels, stats, _ = cv2.connectedComponentsWithStats(signed_array, 8)
            if number <= 1:
                raise ValueError(f"no source-owned component: {case}/{role}")
            comp_index = max(range(1, number), key=lambda i: int(stats[i, cv2.CC_STAT_AREA]))
            component = (labels == comp_index).astype(np.uint8)
            y_nonzero, x_nonzero = np.where(component != 0)
            x0 = max(0, int(x_nonzero.min()) - 2)
            y0 = max(0, int(y_nonzero.min()) - 2)
            x1 = min(340, int(x_nonzero.max()) + 3)
            y1 = min(340, int(y_nonzero.max()) + 3)
            clipped = component[y0:y1, x0:x1]
            contours, _ = cv2.findContours(clipped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                raise ValueError("component has no original boundary")
            contour = max(contours, key=cv2.contourArea)
            points = contour[:, 0, :].tolist()
            if len(points) < 3:
                raise ValueError("degenerate source contour; fail closed")
            all_loops, hierarchy = cv2.findContours(signed_array, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            mask_holes = sum(1 for entry in hierarchy[0] if int(entry[3]) >= 0) if hierarchy is not None else 0
            crop_file = folder / f"{role}_component.bin"
            crop_file.write_bytes(clipped.tobytes())
            roles[role] = {
                "signedMask": str(dst_mask), "componentMask": str(crop_file),
                "mask_sha256": MASK_HASHES[case][role],
                "signedPixels": int(signed_array.sum()),
                "componentPixels": int(clipped.sum()),
                "components": number - 1,
                "maskHoleCount": mask_holes,
                "crop": [x0, y0, x1-x0, y1-y0],
                "points": points,
                "sourceContourPointCount": len(points),
                "contour_excludes_holes": True,
            }
            verified_case["masks"][role] = MASK_HASHES[case][role]
        local["cases"][case] = {"rgb": str(rgb_file), "size": [340, 340], "roles": roles}
        verified[case] = verified_case
    (out / "verified_inputs.json").write_text(json.dumps(verified, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = out / "prepared.json"
    output.write_text(json.dumps(local, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"prepared": str(output), "verified": verified}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.out), indent=2))
